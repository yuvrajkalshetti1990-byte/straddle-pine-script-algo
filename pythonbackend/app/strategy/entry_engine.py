"""
Entry Engine — exact Pine Script entry logic parity.

Short entry:
    Pine: s_sig AND lSig != -1 AND allowShort AND triggerShort
    - allowShort = (maxShortTrades == 0 OR cntShort < max) AND lSigLong == 0
    - triggerShort = short_en AND s_en AND (shortRestrict_en ? shortS_N : true)
    - NO regime filter (the sell signal from procSignal IS the filter)

Long entry:
    Pine: lSigLong == 0 AND allowLong AND inSession AND canLongStart AND finalEntry
    - allowLong = (maxLongTrades == 0 OR cntLong < max) AND lSig == 0
    - sigVal = triggerLong OR triggerTrap
    - triggerLong = long_en AND s_en AND tType == "Buy CE" AND (scope restricted)
    - triggerTrap = long_en AND s_en AND tType == "Buy PE" AND regime == "SHORT COV" AND (scope restricted)
    - strVal = close > EMA AND close > VWMA AND close > VWAP
    - finalEntry = useStrictLong ? (sigVal AND strVal) : sigVal
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

MARKET_TZ = ZoneInfo("Asia/Kolkata")


def can_enter_short(
    sell_cond: bool,
    lSig: int,
    lSigLong: int,
    cnt_short: int,
    short_en: bool,
    strike_en: bool,
    max_short_trades: int,
    restrict_scope: bool,
    scope_allowed: bool,
) -> tuple[bool, str]:
    """
    Check if short entry is allowed — exact Pine parity.

    Pine: s_sig AND lSig != -1 AND allowShort AND triggerShort
    Note: lSig != -1 means "not already in a short"
    """
    # triggerShort = short_en AND s_en AND (restrict ? scope : true)
    trigger = short_en and strike_en and (scope_allowed if restrict_scope else True)
    if not trigger:
        return False, "short_trigger_disabled"

    # allowShort = (max == 0 OR cnt < max) AND lSigLong == 0
    if lSigLong != 0:
        return False, "long_active_blocks_short"
    if max_short_trades > 0 and cnt_short >= max_short_trades:
        return False, f"max_short_trades ({cnt_short}/{max_short_trades})"

    # Must not already be in short
    if lSig == -1:
        return False, "already_in_short"

    # Need sell signal
    if not sell_cond:
        return False, "no_sell_signal"

    return True, "short_entry_allowed"


def can_enter_long(
    close: float,
    ema: float,
    vwma: float,
    vwap: float,
    t_type: str,
    regime: str,
    lSig: int,
    lSigLong: int,
    cnt_long: int,
    long_en: bool,
    strike_en: bool,
    max_long_trades: int,
    restrict_scope: bool,
    scope_allowed: bool,
    use_strict_long: bool,
    in_session: bool,
    can_long_start: bool,
    current_time: datetime,
) -> tuple[bool, str]:
    """
    Check if long entry is allowed — exact Pine parity.

    Pine: lSigLong == 0 AND allowLong AND inSession AND canLongStart AND finalEntry
    """
    # Must be in session and past long start time
    if not in_session:
        return False, "outside_session"
    if not can_long_start:
        return False, "before_long_start"

    # allowLong = (max == 0 OR cnt < max) AND lSig == 0
    if lSig != 0:
        return False, "short_active_blocks_long"
    if lSigLong != 0:
        return False, "already_in_long"
    if max_long_trades > 0 and cnt_long >= max_long_trades:
        return False, f"max_long_trades ({cnt_long}/{max_long_trades})"

    # triggerLong = long_en AND s_en AND tType == "Buy CE" AND scope
    scope_ok = scope_allowed if restrict_scope else True
    trigger_long = long_en and strike_en and t_type == "Buy CE" and scope_ok

    # triggerTrap = long_en AND s_en AND tType == "Buy PE" AND regime == "SHORT COV" AND scope
    trigger_trap = (
        long_en
        and strike_en
        and t_type == "Buy PE"
        and regime == "SHORT COV"
        and scope_ok
    )

    sig_val = trigger_long or trigger_trap
    if not sig_val:
        return False, "no_long_trigger"

    # Structure validation
    str_val = close > ema and close > vwma and close > vwap

    # Final entry
    final_entry = (sig_val and str_val) if use_strict_long else sig_val
    if not final_entry:
        return False, "strict_long_structure_fail"

    return True, "long_entry_allowed"


def is_in_session(current_time: datetime) -> bool:
    """Check if within 09:15–14:30 IST (Pine's inSession)."""
    ist = current_time.astimezone(MARKET_TZ) if current_time.tzinfo else current_time
    minutes = ist.hour * 60 + ist.minute
    return 9 * 60 + 15 <= minutes <= 14 * 60 + 30


def can_long_start(current_time: datetime, start_time_str: str) -> bool:
    """
    Check if past long start time.
    Pine: t_longStart = time(timeframe.period, cleanStart + "-1515")
    """
    ist = current_time.astimezone(MARKET_TZ) if current_time.tzinfo else current_time
    clean = start_time_str.replace(":", "")
    if len(clean) >= 4:
        start_h = int(clean[:2])
        start_m = int(clean[2:4])
    else:
        start_h, start_m = 9, 30

    minutes = ist.hour * 60 + ist.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = 15 * 60 + 15  # 15:15

    return start_minutes <= minutes <= end_minutes
