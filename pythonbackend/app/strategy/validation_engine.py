"""
Validation Engine — Read-only telemetry aggregation for operational visibility.
"""

from __future__ import annotations
import logging
import json
from datetime import datetime
from typing import Any
import pandas as pd

from db.database import get_db_connection
from app.strategy.types import IndexType

logger = logging.getLogger(__name__)

async def get_validation_metrics(index_name: str) -> dict[str, Any]:
    """
    Aggregate validation metrics from existing database tables.
    """
    async with get_db_connection() as db:
        # 1. Daily Summary
        # Get all trades for the index
        async with db.execute(
            "SELECT * FROM trades WHERE index_name = ? ORDER BY entry_time DESC",
            (index_name,)
        ) as cursor:
            rows = await cursor.fetchall()
            trades = [dict(row) for row in rows]

        if not trades:
            return {
                "summary": {},
                "integrity": {},
                "regime": {},
                "status": "No data"
            }

        df = pd.DataFrame(trades)
        df['pnl'] = pd.to_numeric(df['realized_pnl'], errors='coerce').fillna(0)
        df['entry_dt'] = pd.to_datetime(df['entry_time'])
        
        wins = df[df['pnl'] > 0]
        losses = df[df['pnl'] <= 0]
        total_pnl = df['pnl'].sum()
        win_rate = (len(wins) / len(df)) * 100 if len(df) > 0 else 0
        
        gp = wins['pnl'].sum()
        gl = abs(losses['pnl'].sum())
        profit_factor = (gp / gl) if gl > 0 else (gp if gp > 0 else 0)

        # 2. Engine Integrity
        # Duplicate Entries: multiple trades for same strike/direction in same minute
        async with db.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT entry_time, strike_label, direction, COUNT(*) as c 
                FROM trades 
                WHERE index_name = ? 
                GROUP BY entry_time, strike_label, direction 
                HAVING c > 1
            )
            """, (index_name,)
        ) as cursor:
            row = await cursor.fetchone()
            duplicate_count = row[0] if row else 0

        # Restart Events: looking for initialization/rehydration logs
        async with db.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE index_name = ? AND decision LIKE '%Initialization%'",
            (index_name,)
        ) as cursor:
            row = await cursor.fetchone()
            restart_count = row[0] if row else 0

        # Drift Alerts: entries in drift_analysis with non-zero drift
        async with db.execute(
            "SELECT COUNT(*) FROM drift_analysis d JOIN trades t ON d.trade_id = t.trade_id WHERE t.index_name = ? AND (d.price_drift > 0.01 OR ABS(d.time_drift_sec) > 1)",
            (index_name,)
        ) as cursor:
            row = await cursor.fetchone()
            drift_alerts = row[0] if row else 0

        # 3. Regime Breakdown
        regime_stats = {}
        if 'signal_type' in df:
            for stype in df['signal_type'].unique():
                if not stype: continue
                sub = df[df['signal_type'] == stype]
                regime_stats[stype] = {
                    "pnl": round(sub['pnl'].sum(), 2),
                    "trades": len(sub),
                    "win_rate": round((len(sub[sub['pnl'] > 0]) / len(sub)) * 100, 1)
                }

        # Session Breakdown
        df['hour'] = df['entry_dt'].dt.hour
        df['session'] = df['hour'].apply(lambda h: 'Morning' if h < 12 else 'Afternoon')
        session_stats = {
            "Morning": {
                "pnl": round(df[df['session'] == 'Morning']['pnl'].sum(), 2),
                "trades": len(df[df['session'] == 'Morning'])
            },
            "Afternoon": {
                "pnl": round(df[df['session'] == 'Afternoon']['pnl'].sum(), 2),
                "trades": len(df[df['session'] == 'Afternoon'])
            }
        }

        # 4. Status Badges logic
        badges = {
            "pine_match": drift_alerts == 0,
            "restart_safe": restart_count < 5, # Threshold for warning
            "duplicate_free": duplicate_count == 0,
            "data_healthy": True # Placeholder
        }

        return {
            "summary": {
                "net_pnl": round(total_pnl, 2),
                "win_rate": round(win_rate, 1),
                "profit_factor": round(profit_factor, 2),
                "total_trades": len(df),
                "max_drawdown": 0 # Simplified for this view
            },
            "integrity": {
                "duplicates": duplicate_count,
                "restarts": restart_count,
                "drift_alerts": drift_alerts,
                "stale_data": 0
            },
            "regime": {
                "by_type": regime_stats,
                "by_session": session_stats
            },
            "badges": badges
        }
