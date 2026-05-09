import asyncio
import logging
import sys
import json
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Setup path to import app modules
sys.path.append(".")

from app.strategy.config import StrategyConfig
from app.strategy.strategy_runner import StrategyRunner
from app.strategy.types import IndexType
from db.database import init_db

MARKET_TZ = ZoneInfo("Asia/Kolkata")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("parity_validator")

async def run_parity_validation(index_name="NIFTY", slippage=0.0):
    """
    Runs the strategy runner in deterministic replay mode and exports audit logs.
    """
    await init_db()
    
    idx = IndexType(index_name)
    config = StrategyConfig(index=idx)
    config.trading_mode = "paper"
    config.slippage_points = slippage
    
    runner = StrategyRunner(config)
    
    logger.info(f"Starting Parity Validation for {index_name} with {slippage} pts slippage")
    
    # Run backfill (Deterministic Replay)
    # The runner.start() method calls reset_state() and then _backfill_strikes()
    await runner._backfill_strikes()
    
    # Fetch Audit Logs for today from DB
    from db.models import get_db_connection
    async with get_db_connection() as db:
        query = "SELECT * FROM audit_logs WHERE index_name = ? ORDER BY timestamp ASC"
        async with db.execute(query, (index_name,)) as cursor:
            rows = await cursor.fetchall()
            
            if not rows:
                logger.warning("No audit logs found in database.")
                return

            filename = f"parity_audit_{index_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow([
                    "Timestamp", "Strike", "OHLC", "Indicators", "Regime", 
                    "TradeType", "Signal", "Decision", "RejectionReason", "FetchMS", "ProcessMS"
                ])
                
                for row in rows:
                    r = dict(row)
                    telemetry = json.loads(r['telemetry'])
                    writer.writerow([
                        r['timestamp'],
                        r['strike_price'],
                        r['ohlc'],
                        r['indicators'],
                        r['regime'],
                        r['trade_type'],
                        r['signal'],
                        r['decision'],
                        r['rejection_reason'],
                        telemetry.get('fetch_ms', 0),
                        telemetry.get('process_ms', 0)
                    ])
            
            logger.info(f"Audit log exported to {filename}")

    # Fetch Performance Metrics
    from app.strategy.stats_engine import calculate_strategy_metrics
    from db.models import load_trade_history
    trades = await load_trade_history()
    metrics = calculate_strategy_metrics(trades, config.initial_capital)
    
    logger.info("="*40)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("="*40)
    for k, v in metrics.items():
        if k != "exit_distribution":
            logger.info(f"{k.upper():<20}: {v}")
    logger.info("="*40)

if __name__ == "__main__":
    index = "NIFTY"
    slip = 0.0
    if len(sys.argv) > 1:
        index = sys.argv[1]
    if len(sys.argv) > 2:
        slip = float(sys.argv[2])
    
    asyncio.run(run_parity_validation(index, slip))
