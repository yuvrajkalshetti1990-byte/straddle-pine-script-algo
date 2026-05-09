"""
Symbol Generator — dynamically constructs broker-specific symbols.

Handles translating strategy-level concepts (e.g., NIFTY, S1, CE)
into broker-specific trading symbols (e.g., NIFTY25JAN25850CE)
by interfacing with the HDFC Sky security master.
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any

from app.models.hdfc_sky_model import get_security_master, parse_expiry
from app.strategy.constants import STRIKE_OFFSETS, IndexConfig
from app.strategy.types import OptionType

logger = logging.getLogger(__name__)


async def generate_symbols(
    config: IndexConfig,
    atm_strike: float,
    current_date: date,
    target_expiry: str | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Generate symbols for all required strikes based on current ATM.
    
    Returns a mapping of strike_label (e.g. "S3") to symbol info:
    {
        "S3": {
            "strike_price": 25850.0,
            "ce_symbol": "NIFTY...",
            "ce_token": "12345",
            "pe_symbol": "NIFTY...",
            "pe_token": "12346",
            "expiry": "2025-01-13"
        },
        ...
    }
    """
    try:
        instruments = await get_security_master()
    except Exception as e:
        logger.error(f"Failed to fetch security master: {e}")
        return {}

    # Filter for options matching our index
    opts = [
        inst for inst in instruments
        if inst.get("exchange") == config.exchange
        and inst.get("name") == config.underlying_symbol.split()[0]  # e.g., NIFTY
        and inst.get("instrumentType") == "OPTIDX"
        and inst.get("optionType") in {"CE", "PE"}
    ]

    if not opts:
        logger.warning(f"No options found for {config.index.value} in security master")
        return {}

    # Find valid expiries
    expiries_iso = sorted({parse_expiry(item["expiry"]) for item in opts if parse_expiry(item["expiry"])})
    today_iso = current_date.isoformat()
    future_expiries = [exp for exp in expiries_iso if exp >= today_iso]
    
    if not future_expiries:
        logger.warning("No future expiries found")
        return {}
        
    selected_expiry = target_expiry if target_expiry in future_expiries else future_expiries[0]

    # Filter to selected expiry
    expiry_opts = [item for item in opts if parse_expiry(item["expiry"]) == selected_expiry]

    result = {}
    
    for label, offset in STRIKE_OFFSETS.items():
        strike_price = atm_strike + (offset * config.strike_step)
        
        ce_opt = next((item for item in expiry_opts if item["strike"] == strike_price and item["optionType"] == "CE"), None)
        pe_opt = next((item for item in expiry_opts if item["strike"] == strike_price and item["optionType"] == "PE"), None)
        
        if ce_opt or pe_opt:
            result[label] = {
                "strike_price": strike_price,
                "ce_symbol": ce_opt["tradingsymbol"] if ce_opt else None,
                "ce_token": ce_opt["token"] if ce_opt else None,
                "pe_symbol": pe_opt["tradingsymbol"] if pe_opt else None,
                "pe_token": pe_opt["token"] if pe_opt else None,
                "expiry": selected_expiry,
            }
            
    return result
