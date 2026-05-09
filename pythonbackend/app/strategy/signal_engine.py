"""
Signal Engine — exact Pine Script procSignal() parity.

This module produces (buy_cond, sell_cond, trig_str, panic_long)
for a single strike on a single bar, exactly as Pine does.

Pine Script reference (procSignal parameters):
    _o, _c, _h, _l      → candle OHLC
    _ema, _vwap, _vwma   → overlay indicators
    _rsi, _diP, _diM, _roc, _chop  → momentum indicators
    _ready, _en           → data readiness, strike enabled
    _tType                → trade type classification
    _revMinSize           → minimum VWAP reversal body size
    _scopeEn, _scopeMe   → VWAP scope restriction
    _regime               → price regime
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SignalResult:
    """
    Return value from proc_signal().
    Maps to Pine's [_buyCond, _sellCond, _trigStr, _panicLong].
    """
    buy: bool = False
    sell: bool = False
    trig: str = "—"
    panic_long: bool = False


@dataclass
class BarData:
    """OHLC + overlay values for a single bar."""
    o: float = 0.0
    c: float = 0.0
    h: float = 0.0
    l: float = 0.0
    ema: float | None = None
    vwap: float | None = None
    vwma: float | None = None
    rsi: float | None = None
    di_plus: float | None = None
    di_minus: float | None = None
    roc: float | None = None
    chop: float | None = None

    # Previous bar values (needed for crossover detection, VWAP reversal)
    prev_o: float = 0.0
    prev_c: float = 0.0
    prev_ema: float | None = None
    prev_vwap: float | None = None
    prev_vwma: float | None = None

    # Two bars ago (for VWAP reversal)
    prev2_c: float = 0.0
    prev2_vwap: float | None = None


def proc_signal(
    bar: BarData,
    ready: bool,
    enabled: bool,
    in_session: bool,
    use_strict: bool,
    filter_chop: bool,
    chop_limit: float,
    use_old_logic: bool,
    use_new_logic: bool,
    use_vwap_reversal: bool,
    rev_min_size: float,
    crossover_window: int,
    t_type: str,
    regime: str,
    vwap_scope_en: bool,
    vwap_scope_me: bool,
    bars_since_cross: int | None,
) -> SignalResult:
    """
    Exact translation of Pine Script's procSignal().

    Parameters match Pine's function arguments 1:1.
    """
    result = SignalResult()

    c = _nz(bar.c)
    ema = _nz(bar.ema)
    vwap = _nz(bar.vwap)
    vwma = _nz(bar.vwma)
    rsi = _nz(bar.rsi)
    di_p = _nz(bar.di_plus)
    di_m = _nz(bar.di_minus)
    roc = _nz(bar.roc)

    data_ready = ready and ema > 0 and rsi > 0
    is_choppy = filter_chop and (bar.chop > chop_limit)

    # --- Panic (always computed) ---
    # Pine: _panicLong = (_safeClose < _safeVWAP) and (_safeVWAP < _safeVWMA)
    result.panic_long = (c < vwap) and (vwap < vwma)

    # --- Buy condition ---
    buy_cond = False
    if data_ready and in_session and not is_choppy and enabled:
        if use_strict:
            price_buy = (c > ema) and (c > vwap or c > vwma)
        else:
            price_buy = c > ema

        ind_buy = (rsi > 40) and (di_p > di_m) and (roc > 0)
        buy_cond = (price_buy and ind_buy) or ((c > vwap) and (vwap > vwma))

    result.buy = buy_cond

    # --- Sell condition ---
    sell_cond = False
    trig_str = "—"

    if data_ready and in_session and not is_choppy and enabled:
        # Old logic (Momentum)
        if use_strict:
            price_sell = (c < ema) and (c < vwap or c < vwma)
        else:
            price_sell = c < ema

        old_part = price_sell and (rsi < 40) and (di_m > di_p) and (roc < 0)

        # New logic (Trend crossover)
        # Pine: _xUnderEMA = ta.crossunder(EMA, VWAP)
        # Pine: _xUnderVWMA = ta.crossunder(VWMA, VWAP)
        x_under_ema = (bar.prev_ema >= bar.prev_vwap) and (ema < vwap)
        x_under_vwma = (bar.prev_vwma >= bar.prev_vwap) and (vwma < vwap)
        cross_event = x_under_ema or x_under_vwma

        if crossover_window == 0:
            new_part = (ema < vwap) or (vwma < vwap)
        else:
            new_part = (
                bars_since_cross is not None
                and bars_since_cross <= crossover_window
            )

        # VWAP Reversal
        rev_part = False
        if use_vwap_reversal:
            scope_allowed = vwap_scope_me if vwap_scope_en else True
            if scope_allowed and t_type == "Buy PE" and regime != "SHORT COV":
                prev_green = bar.prev_c > bar.prev_o
                prev_above_vwap = bar.prev_c > bar.prev_vwap
                curr_red = c < bar.o
                prev_body = abs(bar.prev_c - bar.prev_o)
                curr_body = abs(c - bar.o)

                size_met = False
                if prev_green and prev_above_vwap and curr_red:
                    if prev_body <= 3.0:
                        if curr_body >= rev_min_size:
                            size_met = True
                    else:
                        if curr_body >= rev_min_size and curr_body >= (0.8 * prev_body):
                            size_met = True

                if size_met:
                    rev_part = True
                else:
                    # Secondary check: 2 bars ago above VWAP
                    if (
                        bar.prev2_c > bar.prev2_vwap
                        and c < bar.o
                        and curr_body >= rev_min_size
                    ):
                        rev_part = True

        # Combine sell conditions — exact Pine logic
        satisfy_old = old_part if use_old_logic else True
        satisfy_new = new_part if use_new_logic else True
        base_met = (
            False
            if (not use_old_logic and not use_new_logic)
            else (satisfy_old and satisfy_new)
        )

        sell_cond = base_met or rev_part

        # Determine trigger string
        if rev_part:
            trig_str = "VWAP.REV"
        elif base_met:
            if use_old_logic and use_new_logic:
                trig_str = "BASE"
            elif use_old_logic:
                trig_str = "OLD"
            elif use_new_logic:
                trig_str = "NEW"

    result.sell = sell_cond
    result.trig = trig_str

    return result


def _nz(val: float | None, default: float = 0.0) -> float:
    """Pine Script nz() equivalent."""
    return val if val is not None else default
