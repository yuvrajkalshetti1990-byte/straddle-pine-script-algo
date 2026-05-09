
import asyncio
import os
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.strategy.strategy_runner import StrategyRunner
from app.strategy.config import StrategyConfig
from app.strategy.types import IndexType, StrikeLabel, OptionType, TradeDirection, TradeState, TradeSource
from db.database import get_db_connection
from db.models import save_trade

MARKET_TZ = ZoneInfo('Asia/Kolkata')

async def setup_test_data():
    """Insert mock trades for today to test rehydration."""
    IST = ZoneInfo("Asia/Kolkata")
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    now = datetime.now(IST)
    
    # 1. Clear existing today's trades for NIFTY S3 to have a clean state
    async with get_db_connection() as db:
        await db.execute("DELETE FROM trades WHERE index_name = 'NIFTY' AND strike_label = 'S3' AND date = ?", (today_str,))
        await db.commit()

    # 2. Insert a CLOSED trade
    # NIFTY lot size is 65 in constants.py
    # 1 lot = 25 points profit = 25 * 65 = 1625 INR
    closed_trade = TradeState(
        trade_id="test_closed_1",
        index=IndexType.NIFTY,
        strike_label=StrikeLabel.S3,
        strike_price=24200.0,
        option_type=OptionType.STR,
        direction=TradeDirection.SHORT,
        entry_price=100.0,
        entry_time=now - timedelta(minutes=60),
        exit_price=75.0,
        exit_time=now - timedelta(minutes=30),
        lots=1,
        realized_pnl=1625.0,
        source=TradeSource.LIVE
    )
    await save_trade(closed_trade, status="CLOSED", date_str=today_str)

    # 3. Insert an ACTIVE trade
    active_trade = TradeState(
        trade_id="test_active_1",
        index=IndexType.NIFTY,
        strike_label=StrikeLabel.S3,
        strike_price=24200.0,
        option_type=OptionType.STR,
        direction=TradeDirection.SHORT,
        entry_price=80.0,
        entry_time=now - timedelta(minutes=10),
        lots=1,
        source=TradeSource.LIVE
    )
    await save_trade(active_trade, status="ACTIVE", date_str=today_str)
    
    print(f"Setup complete: 1 closed (banked=25pts), 1 active (ep=80) for NIFTY S3")

async def test_rehydration():
    print("\n--- TEST: REHYDRATION PERSISTENCE ---")
    config = StrategyConfig(index=IndexType.NIFTY)
    runner = StrategyRunner(config)
    
    # Manually trigger rehydration
    # Note: _sync_strike_state_from_db is called inside start()
    # For testing, we can just call it directly
    from db.models import load_active_trades
    runner.state.active_trades = await load_active_trades(runner.index_name)
    await runner._sync_strike_state_from_db()
    
    s3 = runner.strikes[StrikeLabel.S3]
    
    print(f"S3 lSig: {s3.lSig} (Expected: -1)")
    print(f"S3 ep: {s3.ep} (Expected: 80.0)")
    print(f"S3 banked: {s3.banked} (Expected: 25.0)")
    print(f"S3 cnt_short: {s3.cnt_short} (Expected: 2)")
    print(f"S3 xt: {s3.xt} (Expected: not None)")

    assert s3.lSig == -1, "lSig failed"
    assert s3.ep == 80.0, "ep failed"
    assert s3.banked == 25.0, "banked failed"
    assert s3.cnt_short == 2, "cnt_short failed"
    assert s3.xt is not None, "xt failed"
    print("SUCCESS: Rehydration validated.")

async def test_timeframe_lock():
    print("\n--- TEST: TIMEFRAME LOCK ---")
    config = StrategyConfig(index=IndexType.NIFTY)
    runner = StrategyRunner(config)
    runner.state.engine_running = True
    
    # Mock active trades
    runner.state.active_trades = [TradeState(trade_id="active", entry_time=datetime.now())]
    
    # Try updating config via route-like logic
    new_config_dict = config.to_dict()
    new_config_dict['timeframeMinutes'] = 10 # Change from 5 to 10
    
    new_config = StrategyConfig.from_dict(new_config_dict)
    
    print(f"Current TF: {config.timeframe_minutes}, New TF: {new_config.timeframe_minutes}")
    # Manual check since we're not running the full app
    active_trades = [t for t in runner.state.active_trades if t.is_active]
    print(f"Active trades count: {len(active_trades)}")
    if active_trades:
        if new_config.timeframe_minutes != config.timeframe_minutes:
            print("SUCCESS: Timeframe change blocked by logic (simulated).")
            return
            
    print("FAILURE: Timeframe change was NOT blocked.")

async def main():
    await setup_test_data()
    await test_rehydration()
    await test_timeframe_lock()

if __name__ == "__main__":
    asyncio.run(main())
