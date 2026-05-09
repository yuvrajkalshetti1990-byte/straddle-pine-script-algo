"""
Database Models — functions for persisting strategy objects.
"""

from __future__ import annotations

import json
from typing import Any
import logging
from datetime import datetime

from db.database import get_db_connection
from app.strategy.types import TradeState, IndexType, StrikeLabel, OptionType, TradeDirection, SignalType, ExitReason

logger = logging.getLogger(__name__)


async def save_trade(trade: TradeState, status: str = "CLOSED", date_str: str = "") -> None:
    """Save or update a trade in the database."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO trades 
            (trade_id, index_name, strike_label, strike_price, direction, option_type, 
             entry_price, entry_time, exit_price, exit_time, exit_reason, lots, 
             realized_pnl, status, current_price, highest_high, lowest_low,
             sl_safe, trailing_sl_active, trailing_sl_level, floating_pnl, date,
             source, is_replay, prev_regime, execution_score, signal_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.trade_id,
                trade.index.value if hasattr(trade.index, "value") else trade.index,
                trade.strike_label.value if hasattr(trade.strike_label, "value") else trade.strike_label,
                trade.strike_price,
                trade.direction.value if hasattr(trade.direction, "value") else trade.direction,
                trade.option_type.value if hasattr(trade.option_type, "value") else trade.option_type,
                trade.entry_price,
                trade.entry_time.isoformat() if trade.entry_time else None,
                trade.exit_price if trade.exit_time else None,
                trade.exit_time.isoformat() if trade.exit_time else None,
                trade.exit_reason.value if hasattr(trade.exit_reason, "value") else trade.exit_reason,
                trade.lots,
                trade.realized_pnl if trade.exit_time else None,
                status,
                trade.current_price,
                trade.highest_high,
                trade.lowest_low,
                1 if trade.sl_safe else 0,
                1 if trade.trailing_sl_active else 0,
                trade.trailing_sl_level,
                trade.floating_pnl,
                date_str,
                getattr(trade, "source", "LIVE").value if hasattr(getattr(trade, "source", "LIVE"), "value") else getattr(trade, "source", "LIVE"),
                1 if getattr(trade, "is_replay", False) else 0,
                getattr(trade, "prev_regime", None),
                getattr(trade, "execution_score", None),
                trade.signal_type.value if hasattr(trade, "signal_type") and hasattr(trade.signal_type, "value") else getattr(trade, "signal_type", "base")
            )
        )
        await db.commit()


async def load_active_trades(index_name: str) -> list[TradeState]:
    """Load all active trades for an index to rehydrate memory state."""
    trades = []
    async with get_db_connection() as db:
        async with db.execute(
            "SELECT * FROM trades WHERE index_name = ? AND status = 'ACTIVE'",
            (index_name,)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                t = TradeState(
                    trade_id=row["trade_id"],
                    index=IndexType(row["index_name"]),
                    strike_label=StrikeLabel(row["strike_label"]),
                    strike_price=row["strike_price"],
                    option_type=OptionType(row["option_type"]),
                    direction=TradeDirection(row["direction"]),
                    signal_type=SignalType(row["signal_type"]) if row.get("signal_type") else SignalType.TREND,
                    entry_price=row["entry_price"],
                    entry_time=datetime.fromisoformat(row["entry_time"]) if row["entry_time"] else None,
                    lots=row["lots"],
                    highest_high=row["highest_high"] or row["entry_price"],
                    lowest_low=row["lowest_low"] or row["entry_price"],
                    current_price=row["current_price"] or row["entry_price"],
                )
                t.sl_safe = bool(row["sl_safe"])
                t.trailing_sl_active = bool(row["trailing_sl_active"])
                t.trailing_sl_level = row["trailing_sl_level"] or 0.0
                t.floating_pnl = row["floating_pnl"] or 0.0
                setattr(t, "prev_regime", row["prev_regime"])
                setattr(t, "execution_score", row["execution_score"])
                from app.strategy.types import TradeSource
                t.source = TradeSource(row["source"]) if row["source"] else TradeSource.LIVE
                t.is_replay = bool(row["is_replay"])
                trades.append(t)
    return trades


async def save_strategy_state(
    index_name: str, day_open: float, short_trades: int, long_trades: int, date_str: str
) -> None:
    """Save global strategy state variables."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO strategy_state 
            (index_name, day_open, short_trades, long_trades, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (index_name, day_open, short_trades, long_trades, date_str)
        )
        await db.commit()


async def load_strategy_state(index_name: str, current_date: str) -> dict[str, Any]:
    """Load global strategy state. Resets counters if date doesn't match."""
    async with get_db_connection() as db:
        async with db.execute(
            "SELECT * FROM strategy_state WHERE index_name = ?",
            (index_name,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                if row["date"] == current_date:
                    return {
                        "day_open": row["day_open"],
                        "short_trades": row["short_trades"],
                        "long_trades": row["long_trades"],
                        "date": row["date"]
                    }
                else:
                    return {
                        "day_open": 0.0,
                        "short_trades": 0,
                        "long_trades": 0,
                        "date": current_date
                    }
            return {
                "day_open": 0.0,
                "short_trades": 0,
                "long_trades": 0,
                "date": current_date
            }


async def save_signal(
    index_name: str, strike_label: str, signal_type: str, direction: str,
    strength: float, reason: str, timestamp: str
) -> None:
    """Save a generated signal."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO signals 
            (timestamp, index_name, strike_label, signal_type, direction, strength, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, index_name, strike_label, signal_type, direction, strength, reason)
        )
        await db.commit()

async def save_strike_state(strike_price: float, state_dict: dict):
    """Save the current strike state as JSON to the database."""
    async with get_db_connection() as db:
        await db.execute('''
            INSERT INTO strike_state (strike_price, data)
            VALUES (?, ?)
            ON CONFLICT(strike_price) DO UPDATE SET data=excluded.data
        ''', (strike_price, json.dumps(state_dict)))
        await db.commit()

async def load_strike_state_json(strike_price: float) -> dict | None:
    """Load the strike state from the database."""
    async with get_db_connection() as db:
        async with db.execute('SELECT data FROM strike_state WHERE strike_price = ?', (strike_price,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
    return None

async def load_trade_history(strike_price: float = None, limit: int = None) -> list[dict]:
    """Load trade history from the database."""
    async with get_db_connection() as db:
        query = "SELECT * FROM trades"
        params = []
        if strike_price:
            query += " WHERE strike_price = ?"
            params.append(strike_price)
        query += " ORDER BY entry_time DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def save_audit_log(
    timestamp: str, index_name: str, strike_price: float, ohlc: dict, 
    indicators: dict, regime: str, trade_type: str, signal: str, 
    decision: str, rejection_reason: str, telemetry: dict, date_str: str
) -> None:
    """Save a detailed audit log entry."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO audit_logs 
            (timestamp, index_name, strike_price, ohlc, indicators, regime, 
             trade_type, signal, decision, rejection_reason, telemetry, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp, index_name, strike_price, json.dumps(ohlc), 
                json.dumps(indicators), regime, trade_type, signal, 
                decision, rejection_reason, json.dumps(telemetry), date_str
            )
        )
        await db.commit()

import hashlib

def calculate_candle_signature(ohlc: dict) -> str:
    """Calculate a stable hash of OHLC values."""
    s = f"{ohlc.get('open')}|{ohlc.get('high')}|{ohlc.get('low')}|{ohlc.get('close')}|{ohlc.get('volume')}"
    return hashlib.md5(s.encode()).hexdigest()

async def save_candle_snapshot(symbol: str, timestamp: str, ohlc: dict, is_straddle: bool = False) -> None:
    """Save a candle snapshot to the database."""
    sig = calculate_candle_signature(ohlc)
    now_str = datetime.now().isoformat()
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO candles 
            (symbol, timestamp, open, high, low, close, volume, signature, fetch_time, is_straddle)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                symbol, timestamp, ohlc.get('open'), ohlc.get('high'), ohlc.get('low'), 
                ohlc.get('close'), ohlc.get('volume', 0), sig, now_str, 1 if is_straddle else 0
            )
        )
        await db.commit()

async def detect_candle_revision(symbol: str, timestamp: str, new_ohlc: dict) -> bool:
    """Detect if a candle has been revised by the broker."""
    new_sig = calculate_candle_signature(new_ohlc)
    async with get_db_connection() as db:
        async with db.execute(
            "SELECT signature FROM candles WHERE symbol = ? AND timestamp = ?", 
            (symbol, timestamp)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0] != new_sig:
                return True
    return False

async def log_data_quality_event(event_type: str, symbol: str, message: str, details: dict = None) -> None:
    """Log a data quality event."""
    now_str = datetime.now().isoformat()
    async with get_db_connection() as db:
        await db.execute(
            "INSERT INTO data_quality_logs (timestamp, event_type, symbol, message, details) VALUES (?, ?, ?, ?, ?)",
            (now_str, event_type, symbol, message, json.dumps(details) if details else None)
        )
        await db.commit()

async def save_strike_migration(
    index_name: str, timestamp: str, old_strike: float, new_strike: float, 
    old_premium: float, new_premium: float, reason: str, details: dict = None
) -> None:
    """Save a strike migration event."""
    async with get_db_connection() as db:
        await db.execute(
            """
            INSERT INTO strike_migrations 
            (index_name, timestamp, old_strike, new_strike, old_premium, new_premium, reason, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                index_name, timestamp, old_strike, new_strike, 
                old_premium, new_premium, reason, json.dumps(details) if details else None
            )
        )
        await db.commit()
