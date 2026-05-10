from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Any
import asyncio

from app.strategy.config import StrategyConfig
from app.strategy.constants import get_index_config
from app.strategy.types import (
    AccountState,
    DailyCounters,
    ExitReason,
    IndexType,
    OptionType,
    SignalType,
    StrikeLabel,
    StrategyState,
    TradeDirection,
    TradeState,
)
from db.models import save_trade, save_strategy_state

def create_trade(
    index: IndexType,
    strike_label: str,
    strike_price: float,
    option_type: OptionType,
    direction: TradeDirection,
    signal_type: SignalType,
    entry_price: float,
    entry_time: datetime,
    lots: int,
    prev_regime: str | None = None,
    execution_score: float | None = None,
) -> TradeState:
    """Create a new trade state."""
    trade = TradeState(
        trade_id=f"{index.value}_{direction.value}_{uuid.uuid4().hex[:8]}",
        index=index,
        strike_label=StrikeLabel(strike_label) if strike_label in [e.value for e in StrikeLabel] else StrikeLabel.S3,
        strike_price=strike_price,
        option_type=option_type,
        direction=direction,
        signal_type=signal_type,
        entry_price=entry_price,
        entry_time=entry_time,
        lots=lots,
        highest_high=entry_price,
        lowest_low=entry_price,
        current_price=entry_price,
        prev_regime=prev_regime,
        execution_score=execution_score,
    )
    return trade


def close_trade(
    trade: TradeState,
    exit_price: float,
    exit_time: datetime,
    exit_reason: ExitReason,
    lot_size: int,
) -> float:
    """
    Close a trade and calculate realized P&L.

    Returns the realized P&L in absolute terms.
    """
    trade.exit_price = exit_price
    trade.exit_time = exit_time
    trade.exit_reason = exit_reason

    if trade.is_short:
        # Short: profit = (entry - exit) × lots × lot_size
        trade.realized_pnl = (trade.entry_price - exit_price) * trade.lots * lot_size
    else:
        # Long: profit = (exit - entry) × lots × lot_size
        trade.realized_pnl = (exit_price - trade.entry_price) * trade.lots * lot_size

    trade.floating_pnl = 0.0
    return trade.realized_pnl


async def ensure_daily_counters(state: StrategyState, current_date: str) -> None:
    """Reset daily counters if date has changed, and save to DB."""
    if state.daily.date != current_date:
        state.daily.reset(current_date)
        state.day_open = 0.0
        state.day_open_set = False
        await save_strategy_state(state.index.value, state.day_open, state.daily.short_trades, state.daily.long_trades, current_date)


async def record_trade_entry(state: StrategyState, trade: TradeState, current_date: str) -> None:
    """Record a trade entry in state and persist to DB."""
    state.active_trades.append(trade)
    if trade.is_short:
        state.daily.short_trades += 1
    else:
        state.daily.long_trades += 1
    
    # Save to DB asynchronously
    await save_trade(trade, status="ACTIVE", date_str=current_date)
    await save_strategy_state(state.index.value, state.day_open, state.daily.short_trades, state.daily.long_trades, current_date)


async def record_trade_exit(state: StrategyState, trade: TradeState, current_date: str) -> None:
    """Move trade from active to closed and update account and persist to DB."""
    state.active_trades = [t for t in state.active_trades if t.trade_id != trade.trade_id]
    state.closed_trades.append(trade)
    state.account.realized_pnl += trade.realized_pnl
    state.daily.realized_pnl += trade.realized_pnl
    
    await save_trade(trade, status="CLOSED", date_str=current_date)


def has_active_trade(
    state: StrategyState,
    direction: TradeDirection | None = None,
    strike_label: str | None = None,
) -> bool:
    """Check if there's an active trade matching criteria."""
    for trade in state.active_trades:
        if not trade.is_active:
            continue
        if direction and trade.direction != direction:
            continue
        if strike_label and trade.strike_label.value != strike_label:
            continue
        return True
    return False


def get_active_trades(
    state: StrategyState,
    direction: TradeDirection | None = None,
) -> list[TradeState]:
    """Get all active trades, optionally filtered by direction."""
    trades = [t for t in state.active_trades if t.is_active]
    if direction:
        trades = [t for t in trades if t.direction == direction]
    return trades


async def update_floating_pnl(state: StrategyState, lot_size: int, current_date: str) -> float:
    """
    Update floating P&L for all active trades and sync to DB.
    Returns total floating P&L.
    """
    total = 0.0
    for trade in state.active_trades:
        if not trade.is_active:
            continue
        if trade.is_short:
            trade.floating_pnl = (trade.entry_price - trade.current_price) * trade.lots * lot_size
        else:
            trade.floating_pnl = (trade.current_price - trade.entry_price) * trade.lots * lot_size
        total += trade.floating_pnl
        
        # Save updated trade parameters to DB (highest_high, lowest_low, current_price, floating_pnl)
        await save_trade(trade, status="ACTIVE", date_str=current_date)

    state.account.floating_pnl = total
    state.daily.floating_pnl = total
    return total


def get_state_summary(state: StrategyState) -> dict[str, Any]:
    """Get a summary of current strategy state for API responses."""
    return {
        "index": state.index.value,
        "barIndex": state.bar_index,
        "currentTime": state.current_time.isoformat() if state.current_time else None,
        "isWarmingUp": state.is_warming_up,
        "regime": state.regime.value,
        "directionalState": state.directional_state.value,
        "engineRunning": state.engine_running,
        "timeframe": state.timeframe_minutes,
        "dayOpen": state.day_open,
        "activeTrades": len([t for t in state.active_trades if t.is_active]),
        "closedTrades": len(state.closed_trades),
        "daily": {
            "date": state.daily.date,
            "shortTrades": state.daily.short_trades,
            "longTrades": state.daily.long_trades,
            "realizedPnl": round(state.daily.realized_pnl, 2),
            "floatingPnl": round(state.daily.floating_pnl, 2),
        },
        "account": {
            "initialCapital": state.account.initial_capital,
            "currentCapital": round(state.account.wallet_balance, 2),
            "realizedPnl": round(state.account.realized_pnl, 2),
            "floatingPnl": round(state.account.floating_pnl, 2),
            "totalPnl": round(state.account.total_pnl, 2),
        },
        "trades": [
            {
                "tradeId": t.trade_id,
                "strikeLabel": t.strike_label.value,
                "strikePrice": t.strike_price,
                "direction": t.direction.value,
                "optionType": t.option_type.value,
                "entryPrice": round(t.entry_price, 2),
                "currentPrice": round(t.current_price, 2),
                "lots": t.lots,
                "floatingPnl": round(t.floating_pnl, 2),
                "entryTime": t.entry_time.isoformat() if t.entry_time else None,
                "exitPrice": round(t.exit_price, 2) if t.exit_time else None,
                "exitReason": t.exit_reason.value if t.exit_reason else None,
                "realizedPnl": round(t.realized_pnl, 2) if t.exit_time else None,
                "source": t.source.value if hasattr(t, "source") and t.source else "LIVE",
                "isReplay": getattr(t, "is_replay", False)
            }
            for t in state.active_trades
            if t.is_active
        ],
    }
