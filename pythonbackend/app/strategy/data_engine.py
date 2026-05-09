"""
Data Engine — per-strike CE+PE option candle fetching and synthetic straddle construction.

Replicates Pine Script's data pipeline exactly:

Pine Script:
    buildSym(_strike, _type) =>
        exchPrefix = (indexName == "SENSEX") ? "BSE:" : "NSE:"
        symRoot    = (indexName == "SENSEX") ? "BSX" : indexName
        exchPrefix + symRoot + expYY + expMM + expDD + _type + str.tostring(_strike)

    getOC(_s) =>
        ceO = request.security(buildSym(_s,"C"), timeframe.period, open)
        ceC = request.security(buildSym(_s,"C"), timeframe.period, close)
        peO = request.security(buildSym(_s,"P"), timeframe.period, open)
        peC = request.security(buildSym(_s,"P"), timeframe.period, close)

    // Synthetic straddle candle
    o = ceO + peO
    c = ceC + peC
    h = max(o, c)
    l = min(o, c)

This module fetches independent CE and PE candle series per strike
then aligns them to construct synthetic straddle candles.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.strategy.config import StrategyConfig
from app.strategy.constants import get_index_config
from app.strategy.types import IndexType, StrikeLabel

logger = logging.getLogger(__name__)


@dataclass
class StrikeCandleSet:
    """Aligned CE + PE + synthetic straddle candles for one strike."""
    label: StrikeLabel
    strike_price: float
    ce_candles: list[dict[str, Any]]
    pe_candles: list[dict[str, Any]]
    straddle_candles: list[dict[str, Any]]

    # Day open values (set from first candle of the day)
    ce_day_open: float = 0.0
    pe_day_open: float = 0.0
    str_day_open: float = 0.0


def build_fyers_symbol(
    index_name: str,
    strike_price: float,
    opt_type: str,  # "CE" or "PE"
    expiry_yy: int,
    expiry_mm: int,
    expiry_dd: int,
) -> str:
    """
    Build Fyers option symbol matching Pine Script's buildSym().

    Pine: exchPrefix + symRoot + expYY + expMM + expDD + _type + strike
    Fyers format: NSE:NIFTY2510626000CE

    Pine uses "C"/"P" suffix; Fyers uses "CE"/"PE".
    """
    if index_name == "SENSEX":
        prefix = "BSE"
        sym_root = "SENSEX"
    elif index_name == "BANKNIFTY":
        prefix = "NSE"
        sym_root = "BANKNIFTY"
    else:
        prefix = "NSE"
        sym_root = "NIFTY"

    # Format: NIFTY + YY + M + DD(0-padded) + strike + CE/PE
    # Fyers weekly expiry uses 1-9 for Jan-Sep, and O, N, D for Oct, Nov, Dec
    yy = str(expiry_yy).zfill(2)[-2:]  # last 2 digits
    
    month_map = {
        1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
        7: "7", 8: "8", 9: "9", 10: "O", 11: "N", 12: "D"
    }
    m = month_map.get(int(expiry_mm), str(expiry_mm))
    
    dd = str(expiry_dd).zfill(2)
    strike_int = int(strike_price)

    symbol = f"{prefix}:{sym_root}{yy}{m}{dd}{strike_int}{opt_type}"
    return symbol


async def fetch_strike_candles(
    config: StrategyConfig,
    strike_price: float,
    label: StrikeLabel,
    from_dt: datetime,
    to_dt: datetime,
    use_snapshots: bool = False,
) -> StrikeCandleSet | None:
    """
    Fetch CE and PE candle history for a single strike,
    then construct synthetic straddle candles.

    This replicates Pine Script's getOC() + straddle construction.
    """
    from app.models import fyers_model
    from db.models import save_candle_snapshot, log_data_quality_event

    index_config = get_index_config(config.index)
    resolution = str(index_config.timeframe_minutes)

    # Build CE and PE symbols
    ce_sym = build_fyers_symbol(
        config.index.value, strike_price, "CE",
        config.expiry_yy, config.expiry_mm, config.expiry_dd,
    )
    pe_sym = build_fyers_symbol(
        config.index.value, strike_price, "PE",
        config.expiry_yy, config.expiry_mm, config.expiry_dd,
    )

    from_str = from_dt.strftime("%Y-%m-%d")
    to_str = to_dt.strftime("%Y-%m-%d")

    logger.info(f"Fetching {label.value} ({strike_price}): CE={ce_sym}, PE={pe_sym}, res={resolution} snap={use_snapshots}")

    if use_snapshots:
        # Replay from Database
        from db.models import get_db_connection
        async with get_db_connection() as db:
            ce_query = "SELECT * FROM candles WHERE symbol = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp ASC"
            async with db.execute(ce_query, (ce_sym, from_dt.isoformat(), to_dt.isoformat())) as cursor:
                ce_candles = [dict(row) for row in await cursor.fetchall()]
            
            pe_query = "SELECT * FROM candles WHERE symbol = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp ASC"
            async with db.execute(pe_query, (pe_sym, from_dt.isoformat(), to_dt.isoformat())) as cursor:
                pe_candles = [dict(row) for row in await cursor.fetchall()]
    else:
        # Live/Adaptive Fetch from Broker
        # Adaptive Retry Logic
        max_retries = 3
        retry_delay = 2 # seconds
        ce_candles, pe_candles = [], []

        for attempt in range(max_retries):
            ce_task = fyers_model.fetch_symbol_history(ce_sym, resolution, from_str, to_str)
            pe_task = fyers_model.fetch_symbol_history(pe_sym, resolution, from_str, to_str)
            ce_candles, pe_candles = await asyncio.gather(ce_task, pe_task)

            if ce_candles and pe_candles:
                break
            
            logger.warning(f"Attempt {attempt+1} failed for {label.value}. Retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2 # Exponential backoff

    if not ce_candles or not pe_candles:
        msg = f"Permanent data failure for {label.value}: CE={len(ce_candles or [])}, PE={len(pe_candles or [])}"
        logger.error(msg)
        if not use_snapshots:
            await log_data_quality_event("FETCH_FAILURE", f"{ce_sym}/{pe_sym}", msg)
        return None
    
    if not use_snapshots:
        # Snapshot raw candles and detect revisions
        from db.models import detect_candle_revision, save_candle_snapshot, log_data_quality_event
        for c in ce_candles:
            if await detect_candle_revision(ce_sym, c['date'], c):
                await log_data_quality_event("CANDLE_REVISION", ce_sym, f"Revision detected for {c['date']}", details=c)
            await save_candle_snapshot(ce_sym, c['date'], c)
            
        for p in pe_candles:
            if await detect_candle_revision(pe_sym, p['date'], p):
                await log_data_quality_event("CANDLE_REVISION", pe_sym, f"Revision detected for {p['date']}", details=p)
            await save_candle_snapshot(pe_sym, p['date'], p)

    # Align candles by timestamp and build synthetic straddle
    straddle = align_and_build_straddle(ce_candles, pe_candles)

    if not straddle:
        logger.warning(f"No aligned straddle candles for {label.value}")
        return None

    result = StrikeCandleSet(
        label=label,
        strike_price=strike_price,
        ce_candles=ce_candles,
        pe_candles=pe_candles,
        straddle_candles=straddle,
    )

    # Set day opens from first candle
    if straddle:
        result.str_day_open = straddle[0]["open"]
    if ce_candles:
        result.ce_day_open = ce_candles[0]["open"]
    if pe_candles:
        result.pe_day_open = pe_candles[0]["open"]

    logger.info(
        f"Strike {label.value} ({strike_price}): "
        f"{len(straddle)} straddle candles built "
        f"(CE={len(ce_candles)}, PE={len(pe_candles)})"
    )
    return result


def align_and_build_straddle(
    ce_candles: list[dict[str, Any]],
    pe_candles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Align CE and PE candles by timestamp and build synthetic straddle candles.

    Pine Script logic:
        o = ceO + peO
        c = ceC + peC
        h = max(o, c)
        l = min(o, c)
    """
    # Index PE candles by timestamp for fast lookup
    pe_by_date: dict[str, dict] = {}
    for p in pe_candles:
        pe_by_date[p["date"]] = p

    straddle: list[dict[str, Any]] = []

    for ce in ce_candles:
        ts = ce["date"]
        pe = pe_by_date.get(ts)
        if pe is None:
            continue  # Skip unaligned candles

        # Pine: o = ceO + peO, c = ceC + peC
        str_open = ce["open"] + pe["open"]
        str_close = ce["close"] + pe["close"]

        # Pine: h = max(o, c), l = min(o, c)
        str_high = max(str_open, str_close)
        str_low = min(str_open, str_close)

        # Volume = combined
        str_vol = ce.get("volume", 0) + pe.get("volume", 0)

        straddle.append({
            "date": ts,
            "open": str_open,
            "high": str_high,
            "low": str_low,
            "close": str_close,
            "volume": str_vol,
            # Keep individual leg data for regime calculation
            "ce_open": ce["open"],
            "ce_close": ce["close"],
            "pe_open": pe["open"],
            "pe_close": pe["close"],
        })

    return straddle


async def fetch_all_strikes(
    config: StrategyConfig,
    from_dt: datetime,
    to_dt: datetime,
    use_snapshots: bool = False,
) -> dict[StrikeLabel, StrikeCandleSet]:
    """
    Fetch candle data for all enabled strikes.
    Returns a mapping of StrikeLabel → StrikeCandleSet.
    """
    results: dict[StrikeLabel, StrikeCandleSet] = {}

    label_map = {
        "S1": StrikeLabel.S1,
        "S2": StrikeLabel.S2,
        "S3": StrikeLabel.S3,
        "S4": StrikeLabel.S4,
        "S5": StrikeLabel.S5,
    }

    tasks = []
    labels = []

    # Resolve ATM if needed
    spot_price = None
    for strike_cfg in config.strikes:
        if strike_cfg.enabled and strike_cfg.price <= 0:
            from app.models.fyers_model import fetch_nifty_price
            nifty_data = fetch_nifty_price()
            if nifty_data:
                spot_price = nifty_data["price"]
                logger.info(f"Resolved spot price for ATM: {spot_price}")
                break

    for strike_cfg in config.strikes:
        if not strike_cfg.enabled:
            continue
            
        strike_price = strike_cfg.price
        if strike_price <= 0:
            if spot_price:
                # Basic ATM rounding: NIFTY=50, BANKNIFTY=100
                step = 100 if config.index == IndexType.BANKNIFTY else 50
                strike_price = round(spot_price / step) * step
                logger.info(f"Auto-resolved strike {strike_cfg.label} to ATM {strike_price}")
            else:
                logger.warning(f"Could not resolve ATM for {strike_cfg.label} (no spot price)")
                continue

        label = label_map.get(strike_cfg.label)
        if label is None:
            continue
        labels.append(label)
        tasks.append(
            fetch_strike_candles(config, strike_price, label, from_dt, to_dt, use_snapshots=use_snapshots)
        )

    if not tasks:
        logger.warning("No strikes to fetch (all disabled or no prices set)")
        return results

    # Fetch all strikes concurrently (CE+PE per strike are already concurrent)
    fetched = await asyncio.gather(*tasks, return_exceptions=True)

    for label, result in zip(labels, fetched):
        if isinstance(result, Exception):
            logger.error(f"Error fetching {label.value}: {result}")
            continue
        if result is not None:
            results[label] = result

    logger.info(f"Fetched {len(results)}/{len(tasks)} strikes successfully")
    return results
