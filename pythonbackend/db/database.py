"""
Database Layer — SQLite connection manager.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
import json
from typing import Any

# Use aiosqlite in production, sqlite3 for basic initialization
import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = Path("strategy_data.db")


async def init_db() -> None:
    """Initialize database tables."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    index_name TEXT NOT NULL,
                    strike_label TEXT NOT NULL,
                    strike_price REAL NOT NULL,
                    direction TEXT NOT NULL,
                    option_type TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    entry_time TEXT,
                    exit_price REAL,
                    exit_time TEXT,
                    exit_reason TEXT,
                    lots INTEGER NOT NULL,
                    realized_pnl REAL,
                    status TEXT NOT NULL,
                    current_price REAL,
                    highest_high REAL,
                    lowest_low REAL,
                    sl_safe INTEGER DEFAULT 0,
                    trailing_sl_active INTEGER DEFAULT 0,
                    trailing_sl_level REAL,
                    floating_pnl REAL,
                    date TEXT,
                    prev_regime TEXT,
                    execution_score REAL,
                    source TEXT DEFAULT 'LIVE',
                    is_replay INTEGER DEFAULT 0,
                    signal_type TEXT DEFAULT 'TREND'
                )
            """)

            # Migration: Add signal_type column to trades if it doesn't exist
            try:
                await db.execute("ALTER TABLE trades ADD COLUMN signal_type TEXT DEFAULT 'TREND'")
                await db.commit()
                logger.info("Database Migration: Added signal_type column to trades table.")
            except Exception:
                # Column likely already exists, ignore error
                pass
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS strategy_state (
                    index_name TEXT PRIMARY KEY,
                    day_open REAL,
                    short_trades INTEGER DEFAULT 0,
                    long_trades INTEGER DEFAULT 0,
                    date TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    index_name TEXT NOT NULL,
                    strike_label TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    strength REAL,
                    reason TEXT
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_pnl (
                    date TEXT PRIMARY KEY,
                    index_name TEXT NOT NULL,
                    short_trades INTEGER NOT NULL,
                    long_trades INTEGER NOT NULL,
                    realized_pnl REAL NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS strike_state (
                    strike_price REAL PRIMARY KEY,
                    data TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    index_name TEXT NOT NULL,
                    strike_price REAL NOT NULL,
                    ohlc TEXT,
                    indicators TEXT,
                    regime TEXT,
                    trade_type TEXT,
                    signal TEXT,
                    decision TEXT,
                    rejection_reason TEXT,
                    telemetry TEXT,
                    date TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS candles (
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    signature TEXT,
                    fetch_time TEXT,
                    is_straddle INTEGER DEFAULT 0,
                    PRIMARY KEY (symbol, timestamp)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT,
                    details TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS drift_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL, -- ENTRY or EXIT
                    live_price REAL,
                    replay_price REAL,
                    live_time TEXT,
                    replay_time TEXT,
                    price_drift REAL,
                    time_drift_sec REAL,
                    details TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS strike_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    old_strike REAL,
                    new_strike REAL,
                    old_premium REAL,
                    new_premium REAL,
                    reason TEXT,
                    details TEXT
                )
            """)
            
            await db.commit()
            logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


@asynccontextmanager
async def get_db_connection():
    """Context manager for database connections."""
    conn = await aiosqlite.connect(DB_PATH)
    try:
        conn.row_factory = aiosqlite.Row
        yield conn
    finally:
        await conn.close()
