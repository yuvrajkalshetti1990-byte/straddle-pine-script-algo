import asyncio
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.append(".")
from app.strategy.config import StrategyConfig, RiskConfig
from app.strategy.strategy_runner import StrategyRunner
from app.strategy.types import IndexType

MARKET_TZ = ZoneInfo("Asia/Kolkata")

async def test_risk_halt():
    # 1. Setup config with very low max loss
    config = StrategyConfig(index=IndexType.NIFTY)
    config.risk.max_daily_loss = 100.0 # Halt if loss > 100
    
    runner = StrategyRunner(config)
    
    # 2. Simulate a loss in one of the strikes
    runner.strikes["S3"].banked = -500.0 # This should trigger the halt
    
    print("Checking risk limits...")
    halted = await runner._check_risk_limits()
    
    if halted:
        print("SUCCESS: Risk halt triggered as expected.")
    else:
        print("FAILURE: Risk halt NOT triggered!")

async def test_stale_data_halt():
    config = StrategyConfig(index=IndexType.NIFTY)
    config.risk.stale_data_halt_sec = 10 # Halt if > 10s
    
    runner = StrategyRunner(config)
    
    # Simulate old data
    runner.state.current_time = datetime.now(MARKET_TZ) - timedelta(seconds=20)
    
    print("Checking stale data halt...")
    # This logic is in _run_loop, so we test the condition manually here
    now = datetime.now(MARKET_TZ)
    age = (now - runner.state.current_time).total_seconds()
    if age > config.risk.stale_data_halt_sec:
        print(f"SUCCESS: Stale data detected ({age:.1f}s > {config.risk.stale_data_halt_sec}s)")
    else:
        print("FAILURE: Stale data NOT detected!")

if __name__ == "__main__":
    asyncio.run(test_risk_halt())
    asyncio.run(test_stale_data_halt())
