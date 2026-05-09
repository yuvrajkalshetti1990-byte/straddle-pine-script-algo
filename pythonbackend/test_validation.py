import asyncio
import sys
import pandas as pd
from datetime import datetime, timedelta

sys.path.append(".")
from app.strategy.stats_engine import calculate_strategy_metrics
from app.strategy.types import IndexType

def test_rolling_stats():
    # Mock trade history (100 trades)
    trades = []
    capital = 1000000
    pnl_sequence = [10, -5, 20, -10, 30, -5] * 20 # 120 trades
    
    for i, pts in enumerate(pnl_sequence):
        regimes = ["BULLISH", "BEARISH", "SIDEWAYS", "DECAY"]
        reg = regimes[i % 4]
        prev_reg = regimes[(i-1) % 4]
        
        trades.append({
            "points": pts,
            "pnl": pts * 50, # 1 lot
            "entry_time": (datetime.now() - timedelta(hours=i)).isoformat(),
            "exit_time": (datetime.now() - timedelta(hours=i, minutes=30)).isoformat(),
            "index_name": "NIFTY",
            "trigger": "LX" if pts > 0 else "SL",
            "regime": reg,
            "prev_regime": prev_reg,
            "execution_score": 85.0 if i % 2 == 0 else 35.0
        })
    
    metrics = calculate_strategy_metrics(trades, capital)
    
    print("--- Performance Metrics ---")
    print(f"Total Trades: {metrics['total']['trades']}")
    print(f"Win Rate: {metrics['total']['win_rate']}% {metrics['total']['win_rate_ci']}")
    print(f"Rolling Exp (20): {metrics['rolling']['exp_20']}")
    print(f"Stability Score: {metrics['rolling']['stability_score']}")
    print(f"Warnings: {metrics['warnings']}")
    
    # Check transitions
    transitions = metrics['segmented']['transitions']
    print(f"Regime Transitions found: {list(transitions.keys())[:3]}...")
    
    # Check execution segments
    exec_seg = metrics['segmented']['execution']
    print(f"Execution Segments: {list(exec_seg.keys())}")
    
    assert metrics['total']['trades'] == 120
    assert "High" in exec_seg
    assert "Dangerous" in exec_seg
    assert len(transitions) > 0
    
    # Test small sample warning
    small_trades = trades[:5]
    small_metrics = calculate_strategy_metrics(small_trades, capital)
    print(f"Small Dataset Warnings: {small_metrics['warnings']}")
    assert any("Sample size too small" in w for w in small_metrics['warnings'])

async def test_atm_migration_logging():
    from db.database import init_db
    from db.models import save_strike_migration
    import sqlite3
    from db.database import DB_PATH
    
    await init_db()
    
    print("Testing strike migration logging...")
    await save_strike_migration(
        index_name="NIFTY",
        timestamp=datetime.now().isoformat(),
        old_strike=25000,
        new_strike=25050,
        old_premium=100.0,
        new_premium=105.0,
        reason="Spot moved above threshold"
    )
    
    # Verify in DB
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM strike_migrations ORDER BY id DESC LIMIT 1").fetchone()
        print(f"Logged Migration: {row['old_strike']} -> {row['new_strike']} reason={row['reason']}")
        assert row['old_strike'] == 25000
        assert row['new_strike'] == 25050

async def test_drift_analysis():
    from app.strategy.strategy_runner import StrategyRunner
    from app.strategy.config import StrategyConfig
    from app.strategy.types import IndexType
    from db.database import init_db, DB_PATH
    import sqlite3
    
    await init_db()
    
    cfg = StrategyConfig(index=IndexType.NIFTY)
    runner = StrategyRunner(cfg)
    
    trade_id = "test_drift_123"
    live_price = 150.5
    live_time = datetime.now()
    
    print("Testing drift analysis logging...")
    await runner.capture_drift(trade_id, "ENTRY", live_price, live_time)
    
    # Verify in DB
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM drift_analysis WHERE trade_id = ?", (trade_id,)).fetchone()
        assert row is not None
        assert row['live_price'] == live_price
        print(f"Drift Analysis verified for {trade_id}")

if __name__ == "__main__":
    test_rolling_stats()
    asyncio.run(test_atm_migration_logging())
    asyncio.run(test_drift_analysis())

