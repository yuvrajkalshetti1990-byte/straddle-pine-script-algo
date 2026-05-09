import asyncio
import sys
from datetime import datetime

sys.path.append(".")
from db.database import init_db
from db.models import save_candle_snapshot, detect_candle_revision, log_data_quality_event, get_db_connection

async def test_revision_detection():
    await init_db()
    
    symbol = "NSE:NIFTY2611324000CE"
    ts = "2026-05-08T09:15:00"
    ohlc = {"open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000}
    
    print(f"Saving initial snapshot for {ts}...")
    await save_candle_snapshot(symbol, ts, ohlc)
    
    # Revision
    revised_ohlc = {"open": 100, "high": 115, "low": 90, "close": 105, "volume": 1100}
    print(f"Detecting revision for {ts}...")
    is_revised = await detect_candle_revision(symbol, ts, revised_ohlc)
    
    if is_revised:
        print("SUCCESS: Revision detected!")
        await log_data_quality_event("TEST_REVISION", symbol, "Revision detected in test", details=revised_ohlc)
    else:
        print("FAILURE: Revision NOT detected!")

    # Check logs
    async with get_db_connection() as db:
        async with db.execute("SELECT * FROM data_quality_logs WHERE event_type = 'TEST_REVISION'") as cursor:
            row = await cursor.fetchone()
            if row:
                print(f"Log entry found: {row[4]}")

if __name__ == "__main__":
    asyncio.run(test_revision_detection())
