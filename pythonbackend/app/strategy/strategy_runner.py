"""
Strategy Runner — Pine Script parity execution engine.

Processes candles bar-by-bar with per-strike sequential processing:
    For each bar:
        For each strike (S1→S5):
            1. Short exit check
            2. Short entry check
            3. Long exit check
            4. Long entry check

This preserves Pine Script's deterministic execution order where
state transitions, counters, and P&L banking within a single bar
depend on sequential processing.
"""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.strategy.config import StrategyConfig
from app.strategy.constants import (
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    get_index_config,
)
from app.strategy.directional_state import DirectionalEngine
from app.strategy.entry_engine import can_enter_short, can_enter_long, is_in_session, can_long_start
from app.strategy.exit_engine import check_short_exit, check_long_exit
from app.strategy.data_engine import fetch_all_strikes, fetch_strike_candles, StrikeCandleSet
from app.strategy.indicators import compute_all_indicators, get_latest_snapshot, get_snapshot_at
from app.strategy.regime_engine import (
    classify_ind_reg,
    classify_indicator_regime,
    classify_price_regime,
    classify_trade_type,
)
from app.strategy.signal_engine import proc_signal, BarData, SignalResult
from app.strategy.strike_state import StrikeState, PINE_LABEL_MAP
from app.strategy.trade_state import (
    close_trade,
    create_trade,
    ensure_daily_counters,
    get_state_summary,
    record_trade_entry,
    record_trade_exit,
    update_floating_pnl,
)
from app.strategy.types import (
    ExitReason,
    IndicatorSnapshot,
    IndexType,
    OptionType,
    RegimeState,
    SignalType,
    StrikeLabel,
    StrategyState,
    TradeDirection,
    TradeSource,
    TradeState,
)
from app.strategy.alert_engine import AlertEngine
from app.strategy.broker_adapters import get_broker_adapter
from db.models import load_active_trades, load_strategy_state
from db.database import init_db

MARKET_TZ = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)

# Ordered list of strike labels — processing order matches Pine Script
STRIKE_ORDER = [StrikeLabel.S1, StrikeLabel.S2, StrikeLabel.S3, StrikeLabel.S4, StrikeLabel.S5]


class StrategyRunner:
    """
    Main strategy execution engine with per-strike state machines.
    """

    def __init__(self, config: StrategyConfig) -> None:
        self.config = config
        self.index_name = config.index.value
        self.state = StrategyState(index=config.index)
        self.state.account.initial_capital = config.initial_capital
        self.state.account.current_capital = config.initial_capital
        self.directional_engine = DirectionalEngine()
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._index_config = get_index_config(config.index)
        self.broker_adapter = get_broker_adapter(self.config.broker, self.config)
        self.alert_engine = AlertEngine()

        # Per-strike state machines — the core Pine Script parity structure
        self.strikes: dict[StrikeLabel, StrikeState] = {}
        for label in STRIKE_ORDER:
            self.strikes[label] = StrikeState(label=label)

        # bars_since_cross tracker for crossover window (per strike)
        self._bars_since_cross: dict[StrikeLabel, int | None] = {
            label: None for label in STRIKE_ORDER
        }

        # Per-strike candle buffers for indicator computation
        self._strike_buffers: dict[StrikeLabel, list[dict[str, Any]]] = {
            label: [] for label in STRIKE_ORDER
        }

        # Telemetry trackers
        self._telemetry = {
            "fetch_ms": 0,
            "process_ms": 0,
            "drift_ms": 0,
            "retries": 0,
            "skipped_candles": 0
        }

    def reset_state(self) -> None:
        """Reset all strike states and buffers for a clean replay."""
        for label, strike in self.strikes.items():
            strike.__init__(label=label)
            self._strike_buffers[label] = []
            self._bars_since_cross[label] = None
        
        self.state.bar_index = 0
        self.state.account.current_capital = self.config.initial_capital
        logger.info(f"Runner state reset for {self.config.index.value}")

    async def start(self) -> None:
        """Start the live strategy runner as a background task."""
        if self.state.engine_running:
            logger.warning("Strategy engine already running")
            return

        # Always reset before starting to ensure determinism, especially in paper/replay
        self.reset_state()

        await init_db()

        now = datetime.now(MARKET_TZ)
        date_str = now.strftime("%Y-%m-%d")

        # Rehydrate state from database
        # Rehydrate state from database and reconcile with broker
        try:
            # 1. Initial rehydration from execution history (trades table)
            await self._sync_strike_state_from_db()

            # 2. MANDATORY BROKER RECONCILIATION
            if self.config.trading_mode == "live":
                from app.models.fyers_model import fetch_positions
                from app.strategy.data_engine import build_fyers_symbol
                
                logger.info("Starting broker reconciliation...")
                live_positions = await asyncio.to_thread(fetch_positions)
                if live_positions is not None:
                    pos_map = {p['symbol']: p for p in live_positions if p['netQty'] != 0}
                    
                    for label, strike in self.strikes.items():
                        ce_sym = build_fyers_symbol(self.config.index.value, strike.strike_price, "CE")
                        pe_sym = build_fyers_symbol(self.config.index.value, strike.strike_price, "PE")
                        
                        ce_pos = pos_map.get(ce_sym)
                        pe_pos = pos_map.get(pe_sym)
                        
                        # Reconcile Short (Sell CE + Sell PE)
                        if strike.lSig == -1: # Engine thinks we are SHORT
                            if not ce_pos or not pe_pos:
                                logger.warning(f"RECONCILIATION [{label.value}]: Engine SHORT but Broker flat. Resetting to flat.")
                                strike.lSig = 0
                                strike.ep = None
                        elif strike.lSig == 0: # Engine thinks we are FLAT
                            if ce_pos and pe_pos and ce_pos['netQty'] < 0 and pe_pos['netQty'] < 0:
                                logger.warning(f"RECONCILIATION [{label.value}]: Engine FLAT but Broker SHORT. Syncing state.")
                                strike.lSig = -1
                                # Try to get real average price from broker if possible
                                ce_avg = abs(ce_pos['buyAvg'] or ce_pos['sellAvg'])
                                pe_avg = abs(pe_pos['buyAvg'] or pe_pos['sellAvg'])
                                strike.ep = ce_avg + pe_avg
                        
                        # Reconcile Long (Buy CE or Buy PE)
                        if strike.lSigLong == 2: # Engine thinks we are LONG
                             if not ce_pos and not pe_pos:
                                 logger.warning(f"RECONCILIATION [{label.value}]: Engine LONG but Broker flat. Resetting to flat.")
                                 strike.lSigLong = 0
                                 strike.epLong = None
                else:
                    logger.error("Failed to fetch live positions for reconciliation. Safety skip.")
        except Exception as e:
            logger.error(f"Failed to reconcile with broker: {e}", exc_info=True)



        self.state.engine_running = True
        self._stop_event.clear()

        # Warmup: seed indicator buffers from historical data.
        # Required in BOTH modes — ADX/DMI/VWMA need ~20 bars before producing valid values.
        # In paper mode: also replays today's bars and executes BACKFILL trades.
        # In live mode:  only seeds indicators. Trade execution is blocked during warmup
        #                because _backfill_strikes uses TradeSource.BACKFILL for today's bars,
        #                which are then filtered out by the LIVE-only API route.
        self.state.is_warming_up = True
        await self._backfill_strikes()
        self.state.is_warming_up = False
        # IMPORTANT: Re-sync after backfill — daily_reset() inside backfill wipes lSig.
        await self._sync_strike_state_from_db()

        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Strategy engine started for {self.config.index.value} in [{self.config.trading_mode}] mode")

    async def stop(self, square_off: bool = True) -> None:
        """Stop the strategy engine."""
        self._stop_event.set()
        self.state.engine_running = False

        if square_off:
            await self._square_off_all()

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        await self.alert_engine.close()
        logger.info(f"Strategy engine stopped for {self.config.index.value}")

    async def _run_loop(self) -> None:
        """Main polling loop."""
        tf = self._index_config.timeframe_minutes

        while not self._stop_event.is_set():
            try:
                now = datetime.now(MARKET_TZ)
                
                # Align poll to the next candle close + 3 seconds safety buffer
                # Example: If tf=5, at 09:16:00, wait until 09:20:03 (4 mins 3 secs)
                minutes = now.minute
                remainder = minutes % tf
                seconds_to_next = ((tf - remainder) * 60) - now.second + 3
                
                # If we are somehow exactly on the tick, process immediately
                if seconds_to_next <= 3:
                    seconds_to_next = 0
                
                if seconds_to_next > 0:
                    try:
                        await asyncio.wait_for(self._stop_event.wait(), timeout=seconds_to_next)
                    except asyncio.TimeoutError:
                        pass
                
                if self._stop_event.is_set():
                    break

                now = datetime.now(MARKET_TZ)

                # 1. Check Risk Kill Switches
                if await self._check_risk_limits():
                    logger.critical("Stopping strategy due to risk limit breach.")
                    self.state.engine_running = False
                    break

                # 2. Check for Stale Data
                if self.state.current_time:
                    age = (now - self.state.current_time).total_seconds()
                    if age > self.config.risk.stale_data_halt_sec:
                        msg = f"RISK HALT: Data is stale ({age:.0f}s old). Last update: {self.state.current_time}"
                        logger.error(msg)
                        await self.alert_engine.send_alert(msg, "CRITICAL")
                        self.state.engine_running = False
                        break

                if self._is_market_hours(now):
                    # Check for ATM migration before processing the bar
                    await self._check_atm_migration(now)
                    await self._process_bar(now)
                else:
                    logger.debug("Outside market hours, waiting...")
                    # Sleep 1 minute if outside hours
                    try:
                        await asyncio.wait_for(self._stop_event.wait(), timeout=60)
                    except asyncio.TimeoutError:
                        pass

            except Exception as e:
                logger.exception(f"Error in strategy runner loop: {e}")
                # Backoff on error
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=tf * 60)
                except asyncio.TimeoutError:
                    pass

    async def _process_bar(self, current_time: datetime) -> None:
        """Process a single bar — the core Pine Script parity loop."""
        import time
        start_process = time.perf_counter()
        
        date_str = current_time.strftime("%Y-%m-%d")
        if self.state.daily.date != date_str:
            logger.info(f"DATE CHANGE DETECTED: {self.state.daily.date} -> {date_str}. Performing daily reset.")
            self.day_reset()
            
        await ensure_daily_counters(self.state, date_str)

        self.state.current_time = current_time
        self.state.bar_index += 1

        # Fetch per-strike CE+PE candle data and update strike state
        await self._update_strike_data(current_time)

        # Session checks (computed once per bar)
        session_active = is_in_session(current_time)
        long_start_ok = can_long_start(current_time, self.config.long.start_time)

        # Determine strict mode (Pine: useStrict = Auto ? volume > 0 : setting)
        use_strict = self.config.logic.calc_mode.value != "Simple"

        # Process each strike sequentially
        for label in STRIKE_ORDER:
            strike = self.strikes[label]
            strike_cfg = self._get_strike_config(label)
            if not strike_cfg or not strike_cfg.enabled:
                continue

            # Get bar data for this strike
            bar = self._build_bar_data(strike, label)
            if not strike.is_ready:
                continue

            # Compute regime and trade type for this strike
            ce_gain = strike.ce_close - (strike.ce_day_open or 0)
            pe_gain = strike.pe_close - (strike.pe_day_open or 0)
            regime_str = self._calc_regime_str(strike.close, strike.day_open or 0, ce_gain, pe_gain)
            mode_str = self._calc_mode_str(strike.indicators)
            t_type = self._calc_trade_type(strike.close, strike.day_open or 0, ce_gain, pe_gain, mode_str, strike.indicators.chop or 0)

            # Update regime transition tracking
            if strike.current_regime != regime_str:
                strike.prev_regime = strike.current_regime
                strike.current_regime = regime_str
                logger.debug(f"REGIME TRANSITION [{label.value}]: {strike.prev_regime} -> {strike.current_regime}")

            # Generate signal
            signal = proc_signal(
                bar=bar,
                ready=strike.is_ready,
                enabled=strike_cfg.enabled,
                in_session=session_active,
                use_strict=use_strict,
                filter_chop=self.config.logic.filter_chop,
                chop_limit=self.config.logic.chop_threshold,
                use_old_logic=self.config.logic.use_momentum,
                use_new_logic=self.config.logic.use_trend,
                use_vwap_reversal=self.config.logic.use_vwap_rev,
                rev_min_size=self.config.logic.min_reversal_size,
                crossover_window=self.config.logic.breakdown_window,
                t_type=t_type,
                regime=regime_str,
                vwap_scope_en=self.config.logic.restrict_vwap_scope,
                vwap_scope_me=self.config.logic.vwap_scope.is_in_scope(label.value),
                bars_since_cross=self._bars_since_cross.get(label),
            )
            
            last_rejection = "NONE"

            # --- 1. Short Exit ---
            if strike.has_short:
                exit_result, new_ll, new_sl_safe = check_short_exit(
                    lSig=strike.lSig,
                    ep=strike.ep,
                    ll=strike.ll,
                    sl_safe=strike.sl_safe,
                    bar_open=strike.open,
                    bar_high=strike.high,
                    bar_low=strike.low,
                    bar_close=strike.close,
                    ema=bar.ema,
                    vwma=bar.vwma,
                    fixed_sl=self.config.short.fixed_sl,
                    fixed_target=self.config.short.fixed_target,
                    disable_sl_en=self.config.short.smart_sl_disable,
                    disable_sl_pts=self.config.short.smart_sl_points,
                    use_tsl=self.config.short.trailing_sl.enabled,
                    tsl_trigger=self.config.short.trailing_sl.activation_points,
                    tsl_dist=self.config.short.trailing_sl.trailing_distance,
                    use_hard_exit=self.config.short.time_exit_enabled,
                    hard_exit_hour=self.config.short.time_exit_hour,
                    hard_exit_min=self.config.short.time_exit_minute,
                    current_time=current_time,
                    buy_cond=signal.buy,
                )
                strike.ll = new_ll
                strike.sl_safe = new_sl_safe

                if exit_result.should_exit:
                    await self._execute_exit(label, exit_result, TradeSource.LIVE, current_time)

            # --- 2. Short Entry ---
            if not strike.has_short and not strike.has_long:
                scope_ok = self.config.short.scope.is_in_scope(label.value) if self.config.short.restrict_scope else True
                allowed, reason = can_enter_short(
                    sell_cond=signal.sell,
                    lSig=strike.lSig,
                    lSigLong=strike.lSigLong,
                    cnt_short=strike.cnt_short,
                    short_en=self.config.short.enabled,
                    strike_en=strike_cfg.enabled,
                    max_short_trades=self.config.short.max_trades,
                    restrict_scope=self.config.short.restrict_scope,
                    scope_allowed=scope_ok,
                )
                if allowed:
                    await self._execute_entry(label, signal, TradeSource.LIVE, current_time, bar)
                else:
                    if signal.sell: last_rejection = reason

            # --- 3. Long Exit ---
            if strike.has_long:
                exit_result, new_hh = check_long_exit(
                    lSigLong=strike.lSigLong,
                    epLong=strike.epLong,
                    hh=strike.hh,
                    bar_open=strike.open,
                    bar_high=strike.high,
                    bar_low=strike.low,
                    bar_close=strike.close,
                    ema=bar.ema,
                    vwap=bar.vwap,
                    vwma=bar.vwma,
                    long_fixed_sl=self.config.long.fixed_sl,
                    long_target=self.config.long.fixed_target,
                    use_long_tsl=self.config.long.trailing_sl.enabled,
                    tsl_long_trigger=self.config.long.trailing_sl.activation_points,
                    tsl_long_dist=self.config.long.trailing_sl.trailing_distance,
                    use_hard_exit=self.config.long.time_exit_enabled,
                    hard_exit_hour=self.config.long.time_exit_hour,
                    hard_exit_min=self.config.long.time_exit_minute,
                    current_time=current_time,
                    panic_long=signal.panic_long,
                )
                strike.hh = new_hh

                if exit_result.should_exit:
                    await self._execute_exit(label, exit_result, TradeSource.LIVE, current_time)

            # --- 4. Long Entry ---
            if not strike.has_long and strike.lSig == 0:
                scope_ok = self.config.long.scope.is_in_scope(label.value) if self.config.long.restrict_scope else True
                allowed, reason = can_enter_long(
                    close=strike.close,
                    ema=bar.ema,
                    vwma=bar.vwma,
                    vwap=bar.vwap,
                    t_type=t_type,
                    regime=regime_str,
                    lSig=strike.lSig,
                    lSigLong=strike.lSigLong,
                    cnt_long=strike.cnt_long,
                    long_en=self.config.long.enabled,
                    strike_en=strike_cfg.enabled,
                    max_long_trades=self.config.long.max_trades,
                    restrict_scope=self.config.long.restrict_scope,
                    scope_allowed=scope_ok,
                    use_strict_long=self.config.long.strict_entry,
                    in_session=session_active,
                    can_long_start=long_start_ok,
                    current_time=current_time,
                )
                if allowed:
                    await self._execute_entry(label, signal, TradeSource.LIVE, current_time, bar)
                else:
                    last_rejection = reason

            # --- Audit Logging & Persistence ---
            from db.models import save_strike_state, save_audit_log
            
            # Record decision for audit
            decision = "FLAT"
            if strike.has_short: decision = "SHORT"
            if strike.has_long: decision = "LONG"
            
            # Save detailed audit log
            await save_audit_log(
                timestamp=current_time.isoformat(),
                index_name=self.config.index.value,
                strike_price=strike.strike_price,
                ohlc={"o": strike.open, "h": strike.high, "l": strike.low, "c": strike.close},
                indicators=strike.indicators.__dict__ if strike.indicators else {},
                regime=regime_str,
                trade_type=t_type,
                signal=signal.signal.value if signal else "NONE",
                decision=decision,
                rejection_reason=last_rejection,
                telemetry=self._telemetry,
                date_str=date_str
            )

            await save_strike_state(strike.strike_price, strike.to_dict())

        # Update floating P&L for all active trades and sync to DB
        await update_floating_pnl(self.state, self._index_config.lot_size, date_str)

        # --- 15-minute HEARTBEAT for Parity Verification ---
        if current_time.minute % 15 == 0:
            logger.info(f"PARITY_AUDIT HEARTBEAT [{current_time.strftime('%H:%M')}]:")
            for label, strike in self.strikes.items():
                pnl_pts = strike.current_pnl_points
                pos = "FLAT"
                if strike.lSig == -1: pos = "SHORT"
                elif strike.lSigLong == 2: pos = "LONG"
                
                logger.info(
                    f"  {label.value}: {pos} | Banked: {strike.banked:.2f} | Total PTS: {pnl_pts:.2f} | "
                    f"Counters: S={strike.cnt_short} B={strike.cnt_long} | EP: {strike.ep or strike.epLong or '—'}"
                )

        # Final processing telemetry
        self._telemetry["process_ms"] = int((time.perf_counter() - start_process) * 1000)
        logger.debug(f"Telemetry: process_ms={self._telemetry['process_ms']}")

    def _build_bar_data(self, strike: StrikeState, label: StrikeLabel) -> BarData:
        """Build BarData from strike state for signal engine."""
        prev = strike.prev_indicators
        ind = strike.indicators
        buf = self._strike_buffers.get(label, [])

        # Previous bar OHLC from candle buffer
        prev_o = buf[-2]["open"] if len(buf) >= 2 else 0
        prev_c = buf[-2]["close"] if len(buf) >= 2 else 0
        prev2_c = buf[-3]["close"] if len(buf) >= 3 else 0

        # Previous bar VWAP from indicator history
        prev2_vwap = 0  # Would need 3-bar indicator history

        return BarData(
            o=strike.open,
            c=strike.close,
            h=strike.high,
            l=strike.low,
            ema=ind.ema,
            vwap=ind.vwap,
            vwma=ind.vwma,
            rsi=ind.rsi,
            di_plus=ind.plus_di,
            di_minus=ind.minus_di,
            roc=ind.roc,
            chop=ind.chop,
            prev_o=prev_o,
            prev_c=prev_c,
            prev_ema=prev.ema if prev else None,
            prev_vwap=prev.vwap if prev else None,
            prev_vwma=prev.vwma if prev else None,
            prev2_c=prev2_c,
            prev2_vwap=prev2_vwap,
        )

    async def _backfill_strikes(self) -> None:
        """
        Backfill per-strike candle data.
        Fetches CE+PE candle history with a 3-day warmup, builds straddle candles,
        computes indicators, then replays bar-by-bar.
        """
        now = datetime.now(MARKET_TZ)
        today_str = now.strftime('%Y-%m-%d')
        
        # 3-day warmup
        from datetime import timedelta
        start_dt = now - timedelta(days=3)
        start_dt = start_dt.replace(
            hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0
        )

        logger.info(f"Backfill: fetching per-strike data (3-day warmup) {start_dt.strftime('%Y-%m-%d %H:%M')} → {now.strftime('%Y-%m-%d %H:%M')}")
        
        use_snapshots = (self.config.trading_mode == "replay")
        strike_data = await fetch_all_strikes(self.config, start_dt, now, use_snapshots=use_snapshots)

        if not strike_data:
            logger.warning("Backfill: no strike data returned")
            return

        # For each strike, populate candle buffer and compute indicators
        for label, candle_set in strike_data.items():
            strike = self.strikes[label]
            buf = candle_set.straddle_candles

            if not buf:
                continue

            # Store the full candle buffer
            self._strike_buffers[label] = buf.copy()

            # Set day opens
            strike.day_open = candle_set.str_day_open
            strike.ce_day_open = candle_set.ce_day_open
            strike.pe_day_open = candle_set.pe_day_open
            strike.strike_price = candle_set.strike_price

            # Compute indicators on full series
            indicator_series = compute_all_indicators(buf)

            # Replay bar-by-bar to build state
            for bar_idx, candle in enumerate(buf):
                strike.open = candle["open"]
                strike.high = candle["high"]
                strike.low = candle["low"]
                strike.close = candle["close"]
                strike.ce_close = candle.get("ce_close", 0)
                strike.pe_close = candle.get("pe_close", 0)

                # Update indicators
                strike.prev_indicators = strike.indicators if strike.indicators.has_values() else None
                strike.indicators = get_snapshot_at(indicator_series, bar_idx)

            logger.info(
                f"Backfill [{label.value}]: {len(buf)} candles, "
                f"close={strike.close:.2f}, dayOpen={strike.day_open:.2f}"
            )

        # Now replay the full bar sequence for trade decisions
        if strike_data:
            first_set = next(iter(strike_data.values()))
            num_bars = len(first_set.straddle_candles)

            # Compute full indicator series for all strikes once
            full_indicators = {}
            for label, candle_set in strike_data.items():
                full_indicators[label] = compute_all_indicators(candle_set.straddle_candles)

            prev_date = None
            for bar_idx in range(num_bars):
                # Parse timestamp
                ts_str = first_set.straddle_candles[bar_idx].get("date", "")
                try:
                    bar_time = datetime.fromisoformat(ts_str)
                    if bar_time.tzinfo is None:
                        bar_time = bar_time.replace(tzinfo=MARKET_TZ)
                except (ValueError, TypeError):
                    bar_time = now

                is_today = (bar_time.date() == now.date())
                is_new_day = (prev_date is not None and bar_time.date() != prev_date)
                prev_date = bar_time.date()

                # Set each strike to bar_idx data
                for label, candle_set in strike_data.items():
                    if bar_idx >= len(candle_set.straddle_candles):
                        continue
                    candle = candle_set.straddle_candles[bar_idx]
                    strike = self.strikes[label]
                    
                    if is_new_day:
                        strike.daily_reset()
                        strike.day_open = candle["open"]
                        strike.ce_day_open = candle.get("ce_open", candle["open"])
                        strike.pe_day_open = candle.get("pe_open", candle["open"])

                    strike.open = candle["open"]
                    strike.high = candle["high"]
                    strike.low = candle["low"]
                    strike.close = candle["close"]
                    strike.ce_close = candle.get("ce_close", 0)
                    strike.pe_close = candle.get("pe_close", 0)

                    # Fast O(1) snapshot extraction
                    ind_series = full_indicators[label]
                    if bar_idx > 0:
                        strike.prev_indicators = get_snapshot_at(ind_series, bar_idx - 1)
                    strike.indicators = get_snapshot_at(ind_series, bar_idx)

                # Skip trade execution logic for warmup days
                if not is_today:
                    continue

                self.state.bar_index += 1
                self.state.current_time = bar_time

                # IMPORTANT: In LIVE/PAPER modes, warmup should only build indicator state.
                # Do NOT execute backfill trades for today's bars during warmup.
                if self.state.is_warming_up and self.config.trading_mode != "replay":
                    continue

                # Run the per-strike processing for this bar
                session_active = is_in_session(bar_time)
                long_start_ok = can_long_start(bar_time, self.config.long.start_time)
                use_strict = self.config.logic.calc_mode.value != "Simple"

                for label in STRIKE_ORDER:
                    if label not in strike_data:
                        continue
                    strike = self.strikes[label]
                    strike_cfg = self._get_strike_config(label)
                    if not strike_cfg or not strike_cfg.enabled:
                        continue
                    if not strike.is_ready:
                        continue

                    bar = self._build_bar_data(strike, label)
                    ce_gain = strike.ce_close - (strike.ce_day_open or 0)
                    pe_gain = strike.pe_close - (strike.pe_day_open or 0)
                    regime_str = self._calc_regime_str(strike.close, strike.day_open or 0, ce_gain, pe_gain)
                    mode_str = self._calc_mode_str(strike.indicators)
                    t_type = self._calc_trade_type(strike.close, strike.day_open or 0, ce_gain, pe_gain, mode_str, strike.indicators.chop or 0)

                    signal = proc_signal(
                        bar=bar, ready=strike.is_ready, enabled=True,
                        in_session=session_active, use_strict=use_strict,
                        filter_chop=self.config.logic.filter_chop,
                        chop_limit=self.config.logic.chop_threshold,
                        use_old_logic=self.config.logic.use_momentum,
                        use_new_logic=self.config.logic.use_trend,
                        use_vwap_reversal=self.config.logic.use_vwap_rev,
                        rev_min_size=self.config.logic.min_reversal_size,
                        crossover_window=self.config.logic.breakdown_window,
                        t_type=t_type, regime=regime_str,
                        vwap_scope_en=self.config.logic.restrict_vwap_scope,
                        vwap_scope_me=self.config.logic.vwap_scope.is_in_scope(label.value),
                        bars_since_cross=self._bars_since_cross.get(label),
                    )

                    # Short exit → Short entry → Long exit → Long entry
                    if strike.has_short:
                        exit_result, new_ll, new_sl_safe = check_short_exit(
                            lSig=strike.lSig, ep=strike.ep, ll=strike.ll, sl_safe=strike.sl_safe,
                            bar_open=strike.open, bar_high=strike.high, bar_low=strike.low, bar_close=strike.close,
                            ema=bar.ema, vwma=bar.vwma,
                            fixed_sl=self.config.short.fixed_sl, fixed_target=self.config.short.fixed_target,
                            disable_sl_en=self.config.short.smart_sl_disable, disable_sl_pts=self.config.short.smart_sl_points,
                            use_tsl=self.config.short.trailing_sl.enabled,
                            tsl_trigger=self.config.short.trailing_sl.activation_points,
                            tsl_dist=self.config.short.trailing_sl.trailing_distance,
                            use_hard_exit=self.config.short.time_exit_enabled,
                            hard_exit_hour=self.config.short.time_exit_hour, hard_exit_min=self.config.short.time_exit_minute,
                            current_time=bar_time, buy_cond=signal.buy,
                        )
                        strike.ll = new_ll
                        strike.sl_safe = new_sl_safe
                        if exit_result.should_exit:
                            await self._execute_exit(label, exit_result, TradeSource.BACKFILL, bar_time)

                    if not strike.has_short and not strike.has_long:
                        scope_ok = self.config.short.scope.is_in_scope(label.value) if self.config.short.restrict_scope else True
                        allowed, _ = can_enter_short(
                            sell_cond=signal.sell, lSig=strike.lSig, lSigLong=strike.lSigLong,
                            cnt_short=strike.cnt_short, short_en=self.config.short.enabled,
                            strike_en=True, max_short_trades=self.config.short.max_trades,
                            restrict_scope=self.config.short.restrict_scope, scope_allowed=scope_ok,
                        )
                        if allowed:
                            await self._execute_entry(label, signal, TradeSource.BACKFILL, bar_time, bar)

                    if strike.has_long:
                        exit_result, new_hh = check_long_exit(
                            lSigLong=strike.lSigLong, epLong=strike.epLong, hh=strike.hh,
                            bar_open=strike.open, bar_high=strike.high, bar_low=strike.low, bar_close=strike.close,
                            ema=bar.ema, vwap=bar.vwap, vwma=bar.vwma,
                            long_fixed_sl=self.config.long.fixed_sl, long_target=self.config.long.fixed_target,
                            use_long_tsl=self.config.long.trailing_sl.enabled,
                            tsl_long_trigger=self.config.long.trailing_sl.activation_points,
                            tsl_long_dist=self.config.long.trailing_sl.trailing_distance,
                            use_hard_exit=self.config.long.time_exit_enabled,
                            hard_exit_hour=self.config.long.time_exit_hour, hard_exit_min=self.config.long.time_exit_minute,
                            current_time=bar_time, panic_long=signal.panic_long,
                        )
                        strike.hh = new_hh
                        if exit_result.should_exit:
                            await self._execute_exit(label, exit_result, TradeSource.BACKFILL, bar_time)

                    if not strike.has_long and strike.lSig == 0:
                        scope_ok = self.config.long.scope.is_in_scope(label.value) if self.config.long.restrict_scope else True
                        allowed, _ = can_enter_long(
                            close=strike.close, ema=bar.ema, vwma=bar.vwma, vwap=bar.vwap,
                            t_type=t_type, regime=regime_str,
                            lSig=strike.lSig, lSigLong=strike.lSigLong, cnt_long=strike.cnt_long,
                            long_en=self.config.long.enabled, strike_en=True,
                            max_long_trades=self.config.long.max_trades,
                            restrict_scope=self.config.long.restrict_scope, scope_allowed=scope_ok,
                            use_strict_long=self.config.long.strict_entry,
                            in_session=session_active, can_long_start=long_start_ok,
                            current_time=bar_time,
                        )
                        if allowed:
                            await self._execute_entry(label, signal, TradeSource.BACKFILL, bar_time, bar)
        
        self.state.is_warming_up = False
        logger.info(
            f"Backfill complete. "
            + " | ".join(
                f"{l.value}: pnl={s.current_pnl_points:.2f} short={s.has_short} long={s.has_long}"
                for l, s in self.strikes.items()
                if s.is_ready
            )
        )

    async def _update_strike_data(self, current_time: datetime) -> None:
        """
        Fetch latest candle for each enabled strike and update strike state.
        """
        import time
        start_fetch = time.perf_counter()
        
        from app.models import fyers_model
        from app.strategy.data_engine import build_fyers_symbol

        index_config = self._index_config
        resolution = str(index_config.timeframe_minutes)

        for label in STRIKE_ORDER:
            strike = self.strikes[label]
            strike_cfg = self._get_strike_config(label)
            if not strike_cfg or not strike_cfg.enabled:
                continue
            if strike_cfg.price <= 0:
                continue

            # Build CE and PE symbols
            ce_sym = build_fyers_symbol(
                self.config.index.value, strike_cfg.price, "CE",
                self.config.expiry_yy, self.config.expiry_mm, self.config.expiry_dd,
            )
            pe_sym = build_fyers_symbol(
                self.config.index.value, strike_cfg.price, "PE",
                self.config.expiry_yy, self.config.expiry_mm, self.config.expiry_dd,
            )

            try:
                # Fetch latest quotes for CE and PE (using to_thread to avoid blocking event loop)
                from app.models.fyers_model import fetch_quotes
                import asyncio
                response = await asyncio.to_thread(fetch_quotes, [ce_sym, pe_sym])
                if response and response.get("s") == "ok":
                    quotes = response.get("d", [])
                    ce_data = None
                    pe_data = None
                    for q in quotes:
                        sym = q.get("n", "")
                        v = q.get("v", {})
                        if "CE" in sym:
                            ce_data = v
                        elif "PE" in sym:
                            pe_data = v

                    if not ce_data or not pe_data:
                        from db.models import log_data_quality_event
                        missing = []
                        if not ce_data: missing.append("CE")
                        if not pe_data: missing.append("PE")
                        msg = f"Alignment failure for {label.value}: Missing {', '.join(missing)} quotes"
                        logger.warning(msg)
                        await log_data_quality_event("ALIGNMENT_FAILURE", f"{ce_sym}/{pe_sym}", msg)
                    else:
                        ce_c = ce_data.get("lp", 0)
                        pe_c = pe_data.get("lp", 0)
                        str_close = ce_c + pe_c

                        # Fix Live Candle Generation: Fyers open_price is 09:15 daily open
                        # For 1-minute polled candles, use previous close as current open
                        if strike.close > 0:
                            str_open = strike.close
                            ce_o = strike.ce_close
                            pe_o = strike.pe_close
                        else:
                            str_open = str_close
                            ce_o = ce_c
                            pe_o = pe_c

                        str_high = max(str_open, str_close)
                        str_low = min(str_open, str_close)

                        # Microstructure Telemetry
                        ce_spread = abs(ce_data.get("ask", 0) - ce_data.get("bid", 0))
                        pe_spread = abs(pe_data.get("ask", 0) - pe_data.get("bid", 0))

                        # Execution Feasibility Score
                        exec_score = self._calculate_execution_score(ce_data, pe_data, str_close)
                        setattr(strike, "current_execution_score", exec_score)
                        
                        exec_class = "High"
                        if exec_score < 40: exec_class = "Dangerous"
                        elif exec_score < 70: exec_class = "Medium"

                        candle = {
                            "date": current_time.isoformat(),
                            "open": str_open,
                            "high": str_high,
                            "low": str_low,
                            "close": str_close,
                            "volume": 0,
                            "ce_open": ce_o,
                            "ce_close": ce_c,
                            "pe_open": pe_o,
                            "pe_close": pe_c,
                            "microstructure": {
                                "ce_spread": ce_spread,
                                "pe_spread": pe_spread,
                                "ce_vol": ce_data.get("volume", 0),
                                "pe_vol": pe_data.get("volume", 0)
                            }
                        }

                        # Append to buffer
                        self._strike_buffers[label].append(candle)
                        if len(self._strike_buffers[label]) > 1000:
                            self._strike_buffers[label] = self._strike_buffers[label][-1000:]

                        # Update strike state
                        strike.open = str_open
                        strike.high = str_high
                        strike.low = str_low
                        strike.close = str_close
                        strike.ce_close = ce_c
                        strike.pe_close = pe_c
                        strike.strike_price = strike_cfg.price

                        if strike.day_open is None:
                            strike.day_open = str_open
                            strike.ce_day_open = ce_o
                            strike.pe_day_open = pe_o

                        # Recompute indicators on full buffer
                        buf = self._strike_buffers[label]
                        if len(buf) >= 2:
                            indicator_series = compute_all_indicators(buf)
                            strike.prev_indicators = strike.indicators if strike.indicators.has_values() else None
                            strike.indicators = get_latest_snapshot(indicator_series)
                        
                        # Save detailed audit log with microstructure
                        from db.models import save_audit_log
                        await save_audit_log(
                            timestamp=current_time.isoformat(),
                            index_name=self.config.index.value,
                            strike_price=strike_cfg.price,
                            ohlc=candle,
                            indicators=strike.indicators.to_dict(),
                            regime=regime_str,
                            trade_type=t_type,
                            signal=signal.to_dict().get("signal", "NONE"),
                            decision="PROCESS" if strike.is_ready else "WARMUP",
                            rejection_reason="NONE",
                            telemetry={
                                "ce_spread": ce_spread,
                                "pe_spread": pe_spread,
                                "combined_spread": ce_spread + pe_spread,
                                "latency_ms": self._telemetry["fetch_ms"]
                            },
                            date_str=current_time.strftime("%Y-%m-%d")
                        )

            except Exception as e:
                logger.error(f"Error updating {label.value}: {e}")
                self._telemetry["retries"] += 1

        # Record fetch telemetry
        self._telemetry["fetch_ms"] = int((time.perf_counter() - start_fetch) * 1000)
        # Drift: difference between candle target time and actual completion
        # For simplicity, we just log it as a diagnostic
        logger.debug(f"Telemetry: fetch_ms={self._telemetry['fetch_ms']}")

    async def _execute_entry(
        self, 
        label: StrikeLabel, 
        signal: SignalResult, 
        source: TradeSource, 
        current_time: datetime,
        bar: BarData
    ) -> None:
        """Canonical entry execution logic."""
        strike = self.strikes[label]
        is_long = signal.buy
        
        if is_long:
            strike.lSigLong = 2
            strike.epLong = strike.close
            strike.et = current_time
            strike.trig = "BUY-V"
            strike.hh = strike.close
            strike.is_long = True
            strike.cnt_long += 1
        else:
            strike.lSig = -1
            strike.ep = strike.close
            strike.et = current_time
            strike.trig = signal.trig
            strike.is_long = False
            strike.sl_safe = False
            strike.ll = None
            strike.cnt_short += 1

        # Calculate entry metadata
        ce_gain = strike.ce_close - (strike.ce_day_open or 0)
        pe_gain = strike.pe_close - (strike.pe_day_open or 0)
        regime_str = self._calc_regime_str(strike.close, strike.day_open or 0, ce_gain, pe_gain)
        mode_str = self._calc_mode_str(strike.indicators)
        t_type = self._calc_trade_type(strike.close, strike.day_open or 0, ce_gain, pe_gain, mode_str, strike.indicators.chop or 0)

        # Persistence
        from app.strategy.trade_state import record_trade_entry
        
        # Map trigger to SignalType
        stype = SignalType.TREND
        if signal.trig == "VWAP.REV":
            stype = SignalType.VWAP_REV
        elif signal.buy:
            stype = SignalType.MOMENTUM # Buy signals currently don't have separate types in proc_signal

        trade = create_trade(
            index=self.config.index,
            strike_label=label.value,
            strike_price=self._get_strike_config(label).price,
            option_type=OptionType.STR,
            direction=TradeDirection.LONG if is_long else TradeDirection.SHORT,
            signal_type=stype,
            entry_price=strike.close,
            entry_time=current_time,
            lots=self.config.long.lots if is_long else self.config.short.lots,
            prev_regime=regime_str,
            execution_score=getattr(strike, "current_execution_score", 100.0)
        )
        trade.source = source
        trade.is_replay = (source != TradeSource.LIVE)
        
        await record_trade_entry(self.state, trade, current_time.strftime("%Y-%m-%d"))
        strike.current_trade_id = trade.trade_id
        
        # PARITY EVIDENCE COLLECTION
        logger.info(
            f"[{source.value}] ENTRY_EVIDENCE: {trade.trade_id} | Strike: {label.value} | Price: {strike.close} | "
            f"Time: {current_time.strftime('%H:%M:%S')} | Trigger: {signal.trig} | "
            f"Indicators: EMA={bar.ema:.2f} VWMA={bar.vwma:.2f} ADX={bar.adx if hasattr(bar, 'adx') else '—'}"
        )

    async def _execute_exit(
        self, 
        label: StrikeLabel, 
        exit_result: Any, 
        source: TradeSource, 
        current_time: datetime
    ) -> None:
        """Canonical exit execution logic."""
        strike = self.strikes[label]
        trade_id = strike.current_trade_id
        
        # Update strike state
        if strike.has_short:
            strike.lSig = 0
            strike.ep = 0.0
        else:
            strike.lSigLong = 0
            strike.epLong = 0.0
        strike.xt = current_time
        strike.sl_safe = False
        
        # Persistence
        from app.strategy.trade_state import close_trade, record_trade_exit
        trade = next((t for t in self.state.active_trades if t.trade_id == trade_id), None)
        if trade:
            close_trade(trade, strike.close, current_time, exit_result.reason, self._index_config.lot_size)
            await record_trade_exit(self.state, trade, current_time.strftime("%Y-%m-%d"))
            await self.capture_drift(trade_id, "EXIT", strike.close, current_time)
            strike.current_trade_id = None
            
            # PARITY EVIDENCE COLLECTION
            logger.info(
                f"[{source.value}] EXIT_EVIDENCE: {trade_id} | Strike: {label.value} | Price: {strike.close} | "
                f"Time: {current_time.strftime('%H:%M:%S')} | Reason: {exit_result.reason} | "
                f"Banked: {strike.banked:.2f}"
            )
        else:
            logger.warning(f"[{source.value}] EXIT failed: trade_id {trade_id} not found in active_trades")

    async def _sync_strike_state_from_db(self) -> None:
        """
        Re-sync all per-strike position state (lSig, ep, hh, ll, etc.)
        from the ACTIVE trades currently in DB.

        Must be called:
          1. At startup (before backfill) — initial hydration
          2. After _backfill_strikes() — backfill's daily_reset() may have zeroed lSig

        This ensures strike.has_short / strike.has_long always match DB truth,
        preventing duplicate entries after a restart.
        """
        try:
            from db.models import load_active_trades, load_trade_history
            from zoneinfo import ZoneInfo
            from datetime import datetime
            
            IST = ZoneInfo("Asia/Kolkata")
            today_str = datetime.now(IST).strftime("%Y-%m-%d")
            
            logger.info(f"SYNCHRONIZING StrikeState from DB for {self.index_name} on {today_str}...")

            # 1. Load active trades for rehydration
            active_trades = await load_active_trades(self.config.index.value)
            self.state.active_trades = active_trades
            
            # 2. Load today's trade history to reconstruct banked P&L and counters
            all_db_trades = await load_trade_history(limit=500)
            today_trades = [
                t for t in all_db_trades 
                if t["index_name"] == self.index_name 
                and str(t["entry_time"]).startswith(today_str)
                and t["source"] == "LIVE"
            ]
            
            # Map active trades by strike for easy lookup
            db_active_by_strike: dict[StrikeLabel, list[TradeState]] = {}
            for t in active_trades:
                db_active_by_strike.setdefault(t.strike_label, []).append(t)

            for label, strike in self.strikes.items():
                # Get all today's trades for THIS strike
                strike_label_val = label.value
                strike_trades = [t for t in today_trades if t["strike_label"] == strike_label_val]
                
                # Reset strike's daily counters before rehydrating
                strike.banked = 0.0
                strike.cnt_short = 0
                strike.cnt_long = 0
                strike.xt = None
                
                # Rehydrate banked, counts and last exit time from today's trades
                for t_dict in strike_trades:
                    is_closed = t_dict["status"] == "CLOSED"
                    is_short = t_dict["direction"] == "SHORT"
                    
                    if is_short:
                        strike.cnt_short += 1
                    else:
                        strike.cnt_long += 1
                        
                    if is_closed:
                        # Reconstruct points from realized_pnl
                        lots = t_dict["lots"] or 1
                        lot_size = self._index_config.lot_size or 25
                        pnl_rupees = t_dict["realized_pnl"] or 0.0
                        points = pnl_rupees / (lots * lot_size)
                        strike.banked += points
                        
                        # Last exit time
                        exit_t = None
                        if t_dict["exit_time"]:
                            try:
                                exit_t = datetime.fromisoformat(t_dict["exit_time"])
                            except Exception:
                                pass
                        if exit_t and (not strike.xt or exit_t > strike.xt):
                            strike.xt = exit_t

                # Now rehydrate ACTIVE trade state (lSig, ep, etc.)
                strike_active_trades = db_active_by_strike.get(label, [])

                if not strike_active_trades:
                    # If we have no active DB trade but memory thinks we do, force flat
                    if strike.lSig != 0 or strike.lSigLong != 0:
                        logger.critical(
                            f"CRITICAL_STATE_MISMATCH [{label.value}]: "
                            f"No active DB trade but lSig={strike.lSig} lSigLong={strike.lSigLong}. Forcing flat."
                        )
                        strike.lSig = 0
                        strike.lSigLong = 0
                        strike.ep = None
                        strike.epLong = None
                    continue

                # Use most recent active trade if multiple found
                db_trade = sorted(strike_active_trades, key=lambda t: t.entry_time or datetime.min.replace(tzinfo=IST), reverse=True)[0]

                if db_trade.is_short:
                    strike.lSig = -1
                    strike.lSigLong = 0
                    strike.ep = db_trade.entry_price
                    strike.et = db_trade.entry_time
                    strike.is_long = False
                    strike.sl_safe = db_trade.sl_safe
                    strike.trailing_sl_active = db_trade.trailing_sl_active
                    if db_trade.trailing_sl_active and db_trade.trailing_sl_level:
                        strike.ll = db_trade.trailing_sl_level
                    else:
                        strike.ll = db_trade.lowest_low if db_trade.lowest_low != math.inf else None
                    strike.current_trade_id = db_trade.trade_id
                else:
                    strike.lSigLong = 2
                    strike.lSig = 0
                    strike.epLong = db_trade.entry_price
                    strike.et = db_trade.entry_time
                    strike.is_long = True
                    strike.sl_safe = db_trade.sl_safe
                    strike.trailing_sl_active = db_trade.trailing_sl_active
                    strike.hh = db_trade.highest_high if db_trade.highest_high else db_trade.entry_price
                    strike.current_trade_id = db_trade.trade_id

                logger.info(
                    f"REHYDRATION [{label.value}]: ID={db_trade.trade_id} "
                    f"lSig={strike.lSig}/{strike.lSigLong} "
                    f"banked={strike.banked:.2f} S={strike.cnt_short} B={strike.cnt_long}"
                )

            total_synced = sum(1 for s in self.strikes.values() if s.lSig != 0 or s.lSigLong != 0)
            logger.info(f"REHYDRATION COMPLETE: Synced {total_synced} active positions.")
            
        except Exception as e:
            logger.error(f"_sync_strike_state_from_db failed: {e}", exc_info=True)

    def _get_strike_config(self, label: StrikeLabel) -> Any:
        """Get the strike configuration for a label."""
        for sc in self.config.strikes:
            if sc.label == label.value:
                return sc
        return None

    def _calc_regime_str(self, close: float, day_open: float, ce_gain: float, pe_gain: float) -> str:
        """Pine's calcRegime()."""
        if close > day_open:
            return "BULLISH" if ce_gain >= pe_gain else "SHORT COV"
        elif close < day_open:
            return "BEARISH" if pe_gain >= ce_gain else "DECAY"
        return "SIDEWAYS"

    def _calc_mode_str(self, ind: IndicatorSnapshot) -> str:
        """Pine's getMode()."""
        rsi = ind.rsi or 0
        adx = ind.adx or 0
        di_p = ind.plus_di or 0
        di_m = ind.minus_di or 0
        if adx < 15:
            return "SHORT"
        if rsi > 50 and di_p > di_m:
            return "BUY CE"
        if rsi < 40 and di_m > di_p:
            return "BUY PE"
        if adx > 20 and 40 <= rsi <= 60:
            return "LONG STR"
        return "SHORT"

    def _calc_trade_type(self, close: float, day_open: float, ce_gain: float, pe_gain: float, mode: str, chop: float) -> str:
        """Pine's calcTType()."""
        if chop > 61.8 or mode == "WAIT...":
            return "NoTrade"
        if mode == "SHORT" and close < day_open:
            return "Sell Str"
        if mode in ("BUY CE", "LONG STR", "BUY PE"):
            if ce_gain >= pe_gain:
                return "Buy CE"
            elif pe_gain > ce_gain:
                return "Buy PE"
            return "Buy Str"
        return "NoTrade"

    async def _square_off_all(self) -> None:
        """Square off all active positions."""
        now = datetime.now(MARKET_TZ)
        date_str = now.strftime("%Y-%m-%d")
        from app.strategy.types import ExitReason
        from app.strategy.trade_state import close_trade, record_trade_exit

        for label, strike in self.strikes.items():
            if strike.has_short or strike.has_long:
                exit_price = strike.close
                # Calculate P&L points
                if strike.has_short:
                    strike.banked += (strike.ep or 0) - exit_price
                    strike.lSig = 0
                else:
                    strike.banked += exit_price - (strike.epLong or 0)
                    strike.lSigLong = 0
                
                strike.xt = now
                
                # Record exit
                trade = next((t for t in self.state.active_trades if t.trade_id == strike.current_trade_id), None)
                if trade:
                    close_trade(trade, exit_price, now, ExitReason.SQUARE_OFF, self._index_config.lot_size)
                    await record_trade_exit(self.state, trade, date_str)
                    await self.capture_drift(trade.trade_id, "EXIT", exit_price, now)
                
                strike.current_trade_id = None
                logger.info(f"SQUARE-OFF [{label.value}]")

    def _is_market_hours(self, now: datetime) -> bool:
        market_open = now.replace(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, second=0, microsecond=0)
        market_close = now.replace(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, second=0, microsecond=0)
        return market_open <= now <= market_close

    def get_status(self) -> dict[str, Any]:
        """Get current strategy status for API."""
        summary = get_state_summary(self.state)
        # Add per-strike state
        summary["strikes"] = {
            label.value: strike.to_dict()
            for label, strike in self.strikes.items()
        }
        return summary

    def day_reset(self) -> None:
        """Reset day-specific state."""
        for strike in self.strikes.values():
            strike.daily_reset()
        self.directional_engine.reset()
        logger.info("Day reset complete")

    def _calculate_slippage(self, base_price: float, is_entry: bool, is_long: bool, bar: BarData = None) -> float:
        """Calculate slippage based on the configured model."""
        cfg = self.config.slippage
        from app.strategy.types import SlippageMode
        
        slippage_amt = 0.0
        if cfg.mode == SlippageMode.FIXED:
            slippage_amt = cfg.fixed_points
        elif cfg.mode == SlippageMode.PERCENTAGE:
            slippage_amt = base_price * cfg.percentage
        elif cfg.mode == SlippageMode.VOLATILITY and bar:
            # Volatility-scaled slippage: % of candle range (H-L)
            candle_range = bar.h - bar.l
            slippage_amt = candle_range * cfg.vol_multiplier
            
        # Entry: Buy higher / Sell lower
        # Exit: Buy higher / Sell lower
        # Short Entry (Sell): price decreases
        # Short Exit (Buy): price increases
        # Long Entry (Buy): price increases
        # Long Exit (Sell): price decreases
        
        if is_entry:
            return base_price + slippage_amt if is_long else base_price - slippage_amt
        else:
            return base_price - slippage_amt if is_long else base_price + slippage_amt

    async def _check_risk_limits(self) -> bool:
        """Check if any risk kill switches have been triggered."""
        cfg = self.config.risk
        
        # 1. Max Daily Loss
        daily_pnl = sum(s.banked for s in self.strikes.values())
        if daily_pnl < -cfg.max_daily_loss:
            msg = f"RISK HALT: Daily loss {daily_pnl:.2f} exceeded limit {cfg.max_daily_loss}"
            logger.error(msg)
            await self.alert_engine.emit_critical_halt(msg)
            return True
            
        # 2. Max Consecutive Losses
        from db.models import load_trade_history
        recent_trades = await load_trade_history(limit=cfg.max_consecutive_losses)
        if len(recent_trades) >= cfg.max_consecutive_losses:
            if all((t.get('realized_pnl') or 0) < 0 for t in recent_trades):
                msg = f"RISK HALT: {cfg.max_consecutive_losses} consecutive losses reached"
                logger.error(msg)
                await self.alert_engine.send_alert(msg, "CRITICAL")
                return True
                
        return False

    async def capture_drift(self, trade_id: str, event_type: str, live_price: float, live_time: datetime):
        """Capture drift between live execution and replay price."""
        from db.database import get_db_connection
        # 1. Get replay price for the same bar
        # In a real implementation, we'd fetch snapshotted candle close
        replay_price = live_price # Placeholder
        
        price_drift = live_price - replay_price
        time_drift = 0.0 # Placeholder
        
        async with get_db_connection() as db:
            await db.execute(
                "INSERT INTO drift_analysis (trade_id, timestamp, event_type, live_price, replay_price, live_time, replay_time, price_drift, time_drift_sec) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (trade_id, datetime.now().isoformat(), event_type, live_price, replay_price, live_time.isoformat(), live_time.isoformat(), price_drift, time_drift)
            )
            await db.commit()

# ---------------------------------------------------------------------------
# Module-level singleton for the running engine
# ---------------------------------------------------------------------------

_active_runners: dict[str, StrategyRunner] = {}


def get_runner(index: IndexType) -> StrategyRunner | None:
    return _active_runners.get(index.value)


async def start_runner(config: StrategyConfig) -> StrategyRunner:
    key = config.index.value
    existing = _active_runners.get(key)
    if existing:
        await existing.stop()
    runner = StrategyRunner(config)
    _active_runners[key] = runner
    await runner.start()
    return runner


async def stop_runner(index: IndexType, square_off: bool = True) -> None:
    runner = _active_runners.pop(index.value, None)
    if runner:
        await runner.stop(square_off=square_off)


def get_all_runners() -> dict[str, StrategyRunner]:
    return dict(_active_runners)
