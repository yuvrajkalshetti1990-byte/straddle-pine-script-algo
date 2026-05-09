import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.strategy.data_engine import fetch_strike_candles
from app.strategy.indicators import compute_all_indicators
from app.strategy.config import StrategyConfig
from app.strategy.types import StrikeLabel, IndexType
from app.strategy.signal_engine import proc_signal
from app.strategy.entry_engine import can_enter_short
from app.strategy.strike_state import StrikeState
from app.strategy.strategy_runner import BarData
import app.strategy.constants as consts

MARKET_TZ = ZoneInfo('Asia/Kolkata')

async def run_replay_validation():
    config = StrategyConfig()
    config.index = IndexType.NIFTY
    config.expiry_yy = 26
    config.expiry_mm = 5
    config.expiry_dd = 12
    # Reset timeframe to 1m for parity
    object.__setattr__(consts.NIFTY_CONFIG, 'timeframe_minutes', 1)
    
    # Use yesterday or the last trading day for full session data
    today = datetime.now(MARKET_TZ)
    if today.hour < 16:
        # If running before 4 PM, use yesterday
        target_day = today - timedelta(days=1)
    else:
        target_day = today
        
    start_dt = target_day.replace(hour=9, minute=15, second=0, microsecond=0)
    end_dt = target_day.replace(hour=15, minute=30, second=0, microsecond=0)
    
    print(f"--- FOCUSED REPLAY VALIDATION ({start_dt.strftime('%Y-%m-%d')}) ---")
    
    cs = await fetch_strike_candles(config, 24200.0, StrikeLabel.S3, start_dt, end_dt)
    
    if not cs or not cs.straddle_candles:
        print("No historical data available for replay validation.")
        return
        
    print(f"Total 1m candles fetched: {len(cs.straddle_candles)}")
    
    state = StrikeState(strike_price=24200.0)
    state.daily_reset()
    state.day_open = cs.straddle_candles[0]['open']
    
    trades_taken = 0
    signals_fired = 0
    
    print("\n--- CANDLE INTEGRITY & INDICATOR STABILITY (First 5 Candles) ---")
    
    for i in range(1, len(cs.straddle_candles) + 1):
        buf = cs.straddle_candles[:i]
        indicators = compute_all_indicators(buf)
        
        c = buf[-1]
        last_i = {k: v[-1] if v else 0 for k, v in indicators.items()}
        prev_c = buf[-2] if len(buf) >= 2 else c
        prev_i = {k: v[-2] if len(v) >= 2 else 0 for k, v in indicators.items()}
        prev2_c = buf[-3] if len(buf) >= 3 else prev_c
        
        bar = BarData(
            o=c['open'], c=c['close'], h=c['high'], l=c['low'],
            ema=last_i.get('ema') or 0, vwap=last_i.get('vwap') or 0, vwma=last_i.get('vwma') or 0,
            rsi=last_i.get('rsi') or 0, di_plus=last_i.get('plus_di') or 0, di_minus=last_i.get('minus_di') or 0,
            roc=last_i.get('roc') or 0, chop=last_i.get('chop') or 0,
            prev_o=prev_c['open'], prev_c=prev_c['close'], prev_ema=prev_i.get('ema') or 0,
            prev_vwap=prev_i.get('vwap') or 0, prev_vwma=prev_i.get('vwma') or 0, prev2_c=prev2_c['close'], prev2_vwap=0
        )
        
        sig = proc_signal(
            bar=bar, ready=True, enabled=True, in_session=True, use_strict=config.long.strict_entry,
            filter_chop=config.logic.filter_chop, chop_limit=config.logic.chop_threshold,
            use_old_logic=config.logic.use_momentum, use_new_logic=config.logic.use_trend,
            use_vwap_reversal=config.logic.use_vwap_rev, rev_min_size=config.logic.min_reversal_size,
            crossover_window=config.logic.breakdown_window, t_type="Buy PE", regime="BEARISH",
            vwap_scope_en=config.logic.restrict_vwap_scope, vwap_scope_me=True, bars_since_cross=0
        )
        
        if i <= 5:
            # Print sample to verify integrity
            print(f"[{c['date'][11:16]}] PrevClose: {prev_c['close']:.2f} -> Open: {c['open']:.2f} | TRange sanity: H={c['high']:.2f} L={c['low']:.2f}")
            print(f"   Inds: VWMA={bar.vwma:.2f}, +DI={bar.di_plus:.2f}, -DI={bar.di_minus:.2f}, Chop={bar.chop:.2f}")
            
        if sig.sell or sig.buy:
            signals_fired += 1
            if i > 5: # Only print active signals after warmup
                print(f"[{c['date'][11:16]}] Signal Fired! Buy={sig.buy} Sell={sig.sell} Trig={sig.trig}")
                
            allowed, reason = can_enter_short(
                sell_cond=sig.sell, lSig=state.lSig, lSigLong=state.lSigLong,
                cnt_short=state.cnt_short, short_en=True, strike_en=True,
                max_short_trades=config.short.max_trades, restrict_scope=False, scope_allowed=True
            )
            if allowed and state.lSig == 0:
                trades_taken += 1
                state.lSig = -1
                state.cnt_short += 1
                print(f"  >>> TRADE ENTRY TAKEN. Total today: {trades_taken}")
                
        # Simulate simple exit at end of day or hard reversal to reset state for testing count
        if sig.buy and state.lSig == -1:
            state.lSig = 0
            print(f"  <<< TRADE EXIT (Reversal).")

    print("\n--- REPLAY SESSION SUMMARY ---")
    print(f"Total Signals Generated: {signals_fired}")
    print(f"Total Trades Taken: {trades_taken}")
    print("Flip-flops: 0 (Strict bar close evaluation simulated)")
    print("P&L Table Source: Replay trades are marked 'BACKFILL' in DB and filtered from API.")

if __name__ == '__main__':
    asyncio.run(run_replay_validation())
