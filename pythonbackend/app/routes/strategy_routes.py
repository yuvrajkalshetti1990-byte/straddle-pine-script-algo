"""
Strategy API routes — control endpoints for the strategy engine.

These are ADDITIVE routes — they do NOT modify any existing endpoints.
They are mounted alongside the existing api_routes.py and auth_routes.py.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.strategy.config import StrategyConfig
from app.strategy.strategy_runner import (
    get_all_runners,
    get_runner,
    start_runner,
    stop_runner,
)
from app.strategy.types import IndexType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    index: str = "NIFTY"
    config: dict[str, Any] | None = None


class StopRequest(BaseModel):
    index: str = "NIFTY"
    squareOff: bool = True


class ConfigUpdateRequest(BaseModel):
    config: dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status")
async def strategy_status(index: str = "NIFTY") -> dict[str, Any]:
    """Get the current strategy engine status."""
    try:
        idx = IndexType(index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index}")

    runner = get_runner(idx)
    if runner is None:
        return {
            "status": "success",
            "data": {
                "engineRunning": False,
                "index": index,
                "message": "Engine not started",
            },
        }

    return {"status": "success", "data": runner.get_status()}


@router.post("/start")
async def strategy_start(request: StartRequest) -> dict[str, Any]:
    """Start the strategy engine for a given index."""
    try:
        idx = IndexType(request.index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {request.index}")

    config = StrategyConfig(index=idx)
    if request.config:
        config = StrategyConfig.from_dict({**request.config, "index": request.index})

    runner = await start_runner(config)
    logger.info(f"Strategy engine started for {request.index}")

    return {
        "status": "success",
        "data": {
            "engineRunning": True,
            "index": request.index,
            "message": f"Engine started for {request.index}",
        },
    }


@router.post("/stop")
async def strategy_stop(request: StopRequest) -> dict[str, Any]:
    """Stop the strategy engine for a given index."""
    try:
        idx = IndexType(request.index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {request.index}")

    runner = get_runner(idx)
    if runner is None:
        return {
            "status": "success",
            "data": {"message": f"Engine not running for {request.index}"},
        }

    await stop_runner(idx, square_off=request.squareOff)
    logger.info(f"Strategy engine stopped for {request.index}")

    return {
        "status": "success",
        "data": {
            "engineRunning": False,
            "index": request.index,
            "squaredOff": request.squareOff,
            "message": f"Engine stopped for {request.index}",
        },
    }


@router.get("/config")
async def get_config(index: str = "NIFTY") -> dict[str, Any]:
    """Get the current strategy configuration."""
    try:
        idx = IndexType(index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index}")

    # Try loading from disk first
    config = StrategyConfig.load_from_disk(idx)
    return {"status": "success", "data": config.to_dict()}


@router.put("/config")
async def update_config(request: ConfigUpdateRequest) -> dict[str, Any]:
    """Update strategy configuration. Restarts engine if running."""
    index_str = request.config.get("index", "NIFTY")
    try:
        idx = IndexType(index_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index_str}")

    config = StrategyConfig.from_dict(request.config)
    config.save_to_disk()

    # If engine is running, check for active trades before allowing config update
    runner = get_runner(idx)
    if runner and runner.state.engine_running:
        active_trades = [t for t in runner.state.active_trades if t.is_active]
        if active_trades:
            # Check if timeframe is actually changing
            current_config = runner.config
            if config.timeframe_minutes != current_config.timeframe_minutes:
                logger.warning(f"TIMEFRAME_LOCK: Attempted to change timeframe from {current_config.timeframe_minutes} to {config.timeframe_minutes} while trades are active.")
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot change timeframe while trades are active. Please square off positions first."
                )
        
        # If no active trades (or same timeframe), proceed with restart
        await stop_runner(idx, square_off=False)
        await start_runner(config)
        logger.info(f"Strategy engine restarted with new config for {index_str}")
        return {
            "status": "success",
            "data": {
                "message": f"Config updated and engine restarted for {index_str}",
                "config": config.to_dict(),
            },
        }

    return {
        "status": "success",
        "data": {
            "message": f"Config updated for {index_str} (engine not running)",
            "config": config.to_dict(),
        },
    }


@router.get("/trades")
async def get_trades(
    index: str = "NIFTY",
    active: bool | None = None,
) -> dict[str, Any]:
    """Get trade history."""
    try:
        idx = IndexType(index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index}")

    runner = get_runner(idx)
    if runner is None:
        return {"status": "success", "data": {"trades": []}}

    trades = []
    
    # We are moving away from in-memory arrays as the source of truth for the API.
    # The database will be queried directly for both ACTIVE and CLOSED trades.
    from db.models import load_trade_history
    db_trades = await load_trade_history()
    
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today_str = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%Y-%m-%d")

    active_count = 0
    closed_count = 0

    for row in db_trades:
        # Check index match
        if row["index_name"] != idx.value:
            continue
            
        # Enforce LIVE filtering
        if row.get("source") != "LIVE":
            continue
            
        # Enforce TODAY filtering (must match entry_time or exit_time)
        entry_t = row.get("entry_time", "")
        if not entry_t.startswith(today_str):
            continue
            
        # Include both ACTIVE and CLOSED trades from DB
        is_active = (row["status"] == "ACTIVE")
        if is_active:
            active_count += 1
        else:
            closed_count += 1

        trades.append({
            "tradeId": row["trade_id"],
            "index": row["index_name"],
            "strikeLabel": row["strike_label"],
            "strikePrice": row["strike_price"],
            "direction": row["direction"],
            "optionType": row["option_type"],
            "signalType": row.get("signal_type", "TREND"),
            "entryPrice": round(row["entry_price"] or 0, 2),
            "currentPrice": round(row["current_price"] or 0, 2),
            "lots": row["lots"],
            "floatingPnl": round(row["floating_pnl"] or 0, 2),
            "realizedPnl": round(row["realized_pnl"] or 0, 2),
            "entryTime": row["entry_time"],
            "exitTime": row["exit_time"],
            "exitReason": row["exit_reason"],
            "active": is_active,
            "slSafe": bool(row["sl_safe"]),
            "trailingSLActive": bool(row["trailing_sl_active"]),
            "trailingSLLevel": round(row["trailing_sl_level"] or 0, 2),
        })

    import logging
    logger = logging.getLogger(__name__)
    memory_active = len([t for t in runner.state.active_trades if t.is_active])
    logger.info(f"API /trades | DB Active: {active_count} | Memory Active: {memory_active} | DB Closed: {closed_count} | Response Total: {len(trades)}")

    return {"status": "success", "data": {"trades": trades}}


@router.get("/pnl")
async def get_pnl(index: str = "NIFTY") -> dict[str, Any]:
    """Get P&L summary."""
    try:
        idx = IndexType(index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index}")

    runner = get_runner(idx)
    if runner is None:
        return {
            "status": "success",
            "data": {
                "realizedPnl": 0,
                "floatingPnl": 0,
                "totalPnl": 0,
                "tradeCount": 0,
            },
        }

    return {
        "status": "success",
        "data": {
            "realizedPnl": round(runner.state.account.realized_pnl, 2),
            "floatingPnl": round(runner.state.account.floating_pnl, 2),
            "totalPnl": round(runner.state.account.total_pnl, 2),
            "tradeCount": len(runner.state.closed_trades),
            "activeTrades": len([t for t in runner.state.active_trades if t.is_active]),
            "daily": {
                "date": runner.state.daily.date,
                "shortTrades": runner.state.daily.short_trades,
                "longTrades": runner.state.daily.long_trades,
                "realizedPnl": round(runner.state.daily.realized_pnl, 2),
                "floatingPnl": round(runner.state.daily.floating_pnl, 2),
            },
        },
    }

class TimeframeRequest(BaseModel):
    index: str = "NIFTY"
    timeframe: int = 5

@router.post("/config/timeframe")
async def update_timeframe(request: TimeframeRequest) -> dict[str, Any]:
    """Update timeframe for an index safely."""
    try:
        idx = IndexType(request.index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {request.index}")

    runner = get_runner(idx)
    if not runner:
        raise HTTPException(status_code=400, detail="Engine not running")

    # Safety lock: Reject if active trades exist on any strike
    for label, strike in runner.strikes.items():
        if not strike.is_flat:
            raise HTTPException(
                status_code=400, 
                detail="Cannot switch timeframe while positions are active. Please close open trades first."
            )

    # Re-initialize safely
    config = runner.config
    config.logic.timeframe_minutes = request.timeframe
    
    # Restart the runner to trigger warmup correctly
    await stop_runner(idx, square_off=False)
    await start_runner(config)
    
    return {
        "status": "success",
        "message": f"Timeframe changed to {request.timeframe}m. Engine restarted."
    }

@router.get("/history")
async def strategy_history(index: str = "NIFTY", strike_price: float = None) -> dict[str, Any]:
    """Get the trade history ledger."""
    from db.models import load_trade_history
    history = await load_trade_history(strike_price)
    return {
        "status": "success",
        "data": history
    }


@router.get("/runners")
async def list_runners() -> dict[str, Any]:
    """List all active strategy runners."""
    runners = get_all_runners()
    return {
        "status": "success",
        "data": {
            "runners": [
                {
                    "index": key,
                    "running": runner.state.engine_running,
                    "barIndex": runner.state.bar_index,
                    "regime": runner.state.regime.value,
                    "activeTrades": len(
                        [t for t in runner.state.active_trades if t.is_active]
                    ),
                }
                for key, runner in runners.items()
            ],
        },
    }


@router.get("/performance")
async def get_performance(index: str = "NIFTY") -> dict[str, Any]:
    """Get advanced performance analytics for a strategy."""
    try:
        idx = IndexType(index)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index}")

    runner = get_runner(idx)
    if runner is None:
        return {"status": "success", "data": {}}

    from app.strategy.stats_engine import calculate_strategy_metrics
    from db.models import load_trade_history
    
    # Load historical trades from DB for this index
    trades = await load_trade_history() # For simplicity, loading all for now
    
    # Filter by index
    trades = [t for t in trades if t["index_name"] == index]
    
    metrics = calculate_strategy_metrics(trades, runner.config.initial_capital)
    
    return {
        "status": "success",
        "data": metrics
    }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trade_to_dict(trade: Any) -> dict[str, Any]:
    return {
        "tradeId": trade.trade_id,
        "index": trade.index.value if hasattr(trade.index, "value") else trade.index,
        "strikeLabel": trade.strike_label.value if hasattr(trade.strike_label, "value") else trade.strike_label,
        "strikePrice": trade.strike_price,
        "direction": trade.direction.value if hasattr(trade.direction, "value") else trade.direction,
        "optionType": trade.option_type.value if hasattr(trade.option_type, "value") else trade.option_type,
        "signalType": trade.signal_type.value if hasattr(trade, "signal_type") and hasattr(trade.signal_type, "value") else getattr(trade, "signal_type", "base"),
        "entryPrice": round(trade.entry_price, 2),
        "currentPrice": round(trade.current_price, 2),
        "lots": trade.lots,
        "floatingPnl": round(trade.floating_pnl, 2),
        "realizedPnl": round(trade.realized_pnl, 2),
        "entryTime": trade.entry_time.isoformat() if hasattr(trade.entry_time, "isoformat") else trade.entry_time,
        "exitTime": trade.exit_time.isoformat() if hasattr(trade.exit_time, "isoformat") else trade.exit_time,
        "exitReason": trade.exit_reason.value if hasattr(trade.exit_reason, "value") else trade.exit_reason,
        "active": trade.is_active,
        "slSafe": trade.sl_safe,
        "trailingSLActive": trade.trailing_sl_active,
        "trailingSLLevel": round(trade.trailing_sl_level, 2),
    }
