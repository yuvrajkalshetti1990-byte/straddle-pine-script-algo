"""
Exit Engine — exact Pine Script exit priority parity.

Short exit priority (checked in order, first match wins):
1. Time Exit (isHardExitShort)
2. Target Hit (fixedTarget > 0 AND low <= ep - target)
3. Smart Guard Exit (TSL trigger met AND close > EMA AND close > VWMA)
4. TSL Hit (profit from ll >= trigger AND high >= ll + dist)
5. Smart SL Disable (profit >= points → set slSafe, NO exit)
6. Fixed SL Hit (high >= ep + SL AND NOT slSafe)
7. Buy signal reversal exit (buy_cond is True)

Long exit priority:
1. Time Exit (isHardExitLong)
2. Target Hit
3. Fixed SL Hit
4. TSL Hit
5. Structure Break (close < EMA AND close < VWMA AND close < VWAP)
6. Panic Exit (close < VWAP AND VWAP < VWMA)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

MARKET_TZ = ZoneInfo("Asia/Kolkata")


@dataclass
class ExitResult:
    """Result of exit check."""
    should_exit: bool = False
    reason: str = ""
    pnl_points: float = 0.0


def check_short_exit(
    lSig: int,
    ep: float | None,
    ll: float | None,
    sl_safe: bool,
    # Current bar OHLC
    bar_open: float,
    bar_high: float,
    bar_low: float,
    bar_close: float,
    # Overlays
    ema: float,
    vwma: float,
    # Config
    fixed_sl: float,
    fixed_target: float,
    disable_sl_en: bool,
    disable_sl_pts: float,
    use_tsl: bool,
    tsl_trigger: float,
    tsl_dist: float,
    use_hard_exit: bool,
    hard_exit_hour: int,
    hard_exit_min: int,
    # State
    current_time: datetime,
    buy_cond: bool,
) -> tuple[ExitResult, float | None, bool]:
    """
    Check short exit conditions in exact Pine Script priority order.

    Returns: (exit_result, updated_ll, updated_sl_safe)
    """
    if lSig != -1 or ep is None:
        return ExitResult(), ll, sl_safe

    ist = current_time.astimezone(MARKET_TZ) if current_time.tzinfo else current_time

    # 1. Time Exit
    if use_hard_exit:
        is_hard = ist.hour > hard_exit_hour or (
            ist.hour == hard_exit_hour and ist.minute >= hard_exit_min
        )
        if is_hard:
            pnl = ep - _nz(bar_close)
            return ExitResult(True, "TIME_EXIT", pnl), ll, False

    # Update ll tracking
    if ll is None:
        ll = bar_low
    else:
        ll = min(ll, bar_low)

    # 2. Target Hit: low <= ep - target
    if fixed_target > 0 and bar_low <= (ep - fixed_target):
        pnl = fixed_target  # ep - (ep - target) = target
        return ExitResult(True, "FIXED_TARGET", pnl), ll, False

    # 3. Smart Guard Exit: TSL trigger met AND close > EMA AND close > VWMA
    tsl_trigger_met = use_tsl and (ep - ll) >= tsl_trigger
    if tsl_trigger_met and bar_close > ema and bar_close > vwma:
        pnl = ep - _nz(bar_close)
        return ExitResult(True, "SMART_EXIT", pnl), ll, False

    # 4. TSL Hit: profit from ll >= trigger AND high >= ll + dist
    if use_tsl and (ep - ll) >= tsl_trigger and bar_high >= (ll + tsl_dist):
        pnl = ep - (ll + tsl_dist)
        return ExitResult(True, "TRAILING_SL", pnl), ll, False

    # 5. Smart SL Disable: set flag, do NOT exit
    if disable_sl_en and (ep - bar_low) >= disable_sl_pts:
        sl_safe = True

    # 6. Fixed SL Hit: high >= ep + SL AND NOT slSafe
    if fixed_sl > 0 and bar_high >= (ep + fixed_sl) and not sl_safe:
        pnl = -(fixed_sl)  # ep - (ep + SL) = -SL
        return ExitResult(True, "FIXED_SL", pnl), ll, False

    # 7. Buy signal reversal exit
    if buy_cond:
        pnl = ep - _nz(bar_close)
        return ExitResult(True, "SIGNAL_EXIT", pnl), ll, False

    return ExitResult(), ll, sl_safe


def check_long_exit(
    lSigLong: int,
    epLong: float | None,
    hh: float | None,
    # Current bar OHLC
    bar_open: float,
    bar_high: float,
    bar_low: float,
    bar_close: float,
    # Overlays
    ema: float,
    vwap: float,
    vwma: float,
    # Config
    long_fixed_sl: float,
    long_target: float,
    use_long_tsl: bool,
    tsl_long_trigger: float,
    tsl_long_dist: float,
    use_hard_exit: bool,
    hard_exit_hour: int,
    hard_exit_min: int,
    # State
    current_time: datetime,
    panic_long: bool,
) -> tuple[ExitResult, float | None]:
    """
    Check long exit conditions in exact Pine Script priority order.

    Returns: (exit_result, updated_hh)
    """
    if lSigLong != 2 or epLong is None:
        return ExitResult(), hh

    ist = current_time.astimezone(MARKET_TZ) if current_time.tzinfo else current_time

    # Update hh tracking
    if hh is None:
        hh = bar_high
    else:
        hh = max(hh, bar_high)

    # Collect all exit conditions
    cond_hard = use_hard_exit and (
        ist.hour > hard_exit_hour
        or (ist.hour == hard_exit_hour and ist.minute >= hard_exit_min)
    )
    cond_tgt = long_target > 0 and bar_high >= epLong + long_target
    cond_sl = long_fixed_sl > 0 and bar_low <= epLong - long_fixed_sl
    cond_tsl = (
        use_long_tsl
        and (hh - epLong) >= tsl_long_trigger
        and bar_low <= hh - tsl_long_dist
    )
    cond_str = bar_close < ema and bar_close < vwma and bar_close < vwap
    cond_panic = panic_long

    if not (cond_hard or cond_tgt or cond_sl or cond_tsl or cond_str or cond_panic):
        return ExitResult(), hh

    # Determine P&L and reason following Pine's priority
    pnl = _nz(bar_close) - epLong
    reason = ""

    if cond_tgt:
        pnl = long_target
        reason = "FIXED_TARGET"
    elif cond_sl:
        pnl = -(long_fixed_sl)
        reason = "FIXED_SL"
    elif cond_tsl:
        pnl = (hh - tsl_long_dist) - epLong
        reason = "TRAILING_SL"
    elif cond_str:
        reason = "STRUCTURE_BREAK"
    elif cond_hard:
        reason = "TIME_EXIT"
    elif cond_panic:
        reason = "PANIC_EXIT"

    return ExitResult(True, reason, pnl), hh


def _nz(v: float | None, default: float = 0.0) -> float:
    return v if v is not None else default
