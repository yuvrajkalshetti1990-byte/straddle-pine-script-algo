"""
Indicator wrapper for the strategy engine.

Wraps existing indicator functions from indicator_model.py and adds
the missing SuperTrend indicator. All calculations match TradingView
Pine Script output as closely as possible.
"""

from __future__ import annotations

import math
from typing import Any

from app.models.indicator_model import (
    compute_chop_series,
    compute_dmi_series,
    compute_ema_series,
    compute_rma_series,
    compute_roc_series,
    compute_rsi_series,
    compute_vwap_series,
    compute_vwma_series,
    get_last_finite_value,
)
from app.strategy.constants import (
    EMA_LENGTH,
    INDICATOR_LENGTH,
    ROC_LENGTH,
    SUPERTREND_FACTOR,
    SUPERTREND_PERIOD,
    VWMA_LENGTH,
)
from app.strategy.types import IndicatorSnapshot, StraddleCandle


# ---------------------------------------------------------------------------
# SuperTrend — missing from indicator_model.py
# ---------------------------------------------------------------------------

def compute_supertrend_series(
    candles: list[dict[str, Any]],
    factor: float = SUPERTREND_FACTOR,
    period: int = SUPERTREND_PERIOD,
) -> tuple[list[float | None], list[int | None]]:
    """
    SuperTrend indicator — matches Pine Script ta.supertrend().

    Returns:
        (supertrend_values, directions)
        direction: 1 = uptrend (bullish), -1 = downtrend (bearish)
    """
    n = len(candles)
    supertrend: list[float | None] = [None] * n
    direction: list[int | None] = [None] * n

    if n < period:
        return supertrend, direction

    # Compute ATR using RMA (Wilder's smoothing) — matches Pine Script
    tr_raw: list[float | None] = [None] * n
    for i in range(n):
        if i == 0:
            tr_raw[i] = candles[i]["high"] - candles[i]["low"]
            continue
        prev_close = candles[i - 1]["close"]
        tr_raw[i] = max(
            candles[i]["high"] - candles[i]["low"],
            abs(candles[i]["high"] - prev_close),
            abs(candles[i]["low"] - prev_close),
        )

    atr = compute_rma_series(tr_raw, period)

    # Calculate SuperTrend
    upper_band: list[float | None] = [None] * n
    lower_band: list[float | None] = [None] * n

    for i in range(n):
        if atr[i] is None:
            continue

        hl2 = (candles[i]["high"] + candles[i]["low"]) / 2
        upper_band[i] = hl2 + factor * atr[i]
        lower_band[i] = hl2 - factor * atr[i]

    # Apply Pine Script SuperTrend logic
    prev_upper = None
    prev_lower = None
    prev_dir = 1
    prev_st = None

    for i in range(n):
        if upper_band[i] is None or lower_band[i] is None:
            continue

        close = candles[i]["close"]
        prev_close = candles[i - 1]["close"] if i > 0 else close

        # Adjust bands based on previous values (Pine Script behavior)
        if prev_lower is not None and lower_band[i] is not None:
            if lower_band[i] > prev_lower or prev_close < prev_lower:
                pass  # Keep new lower band
            else:
                lower_band[i] = prev_lower

        if prev_upper is not None and upper_band[i] is not None:
            if upper_band[i] < prev_upper or prev_close > prev_upper:
                pass  # Keep new upper band
            else:
                upper_band[i] = prev_upper

        # Determine direction
        if prev_st is not None:
            if prev_st == prev_upper:
                # Was in downtrend
                if close > upper_band[i]:
                    direction[i] = 1   # Switch to uptrend
                else:
                    direction[i] = -1  # Stay in downtrend
            else:
                # Was in uptrend
                if close < lower_band[i]:
                    direction[i] = -1  # Switch to downtrend
                else:
                    direction[i] = 1   # Stay in uptrend
        else:
            direction[i] = 1 if close > upper_band[i] else -1

        # Set SuperTrend value based on direction
        if direction[i] == 1:
            supertrend[i] = lower_band[i]
        else:
            supertrend[i] = upper_band[i]

        prev_upper = upper_band[i]
        prev_lower = lower_band[i]
        prev_dir = direction[i]
        prev_st = supertrend[i]

    return supertrend, direction


# ---------------------------------------------------------------------------
# Full indicator computation for a series of straddle candles
# ---------------------------------------------------------------------------

def compute_all_indicators(
    candles: list[dict[str, Any]],
    indicator_length: int = INDICATOR_LENGTH,
    roc_length: int = ROC_LENGTH,
    ema_length: int = EMA_LENGTH,
    vwma_length: int = VWMA_LENGTH,
    supertrend_factor: float = SUPERTREND_FACTOR,
    supertrend_period: int = SUPERTREND_PERIOD,
) -> dict[str, list[float | None]]:
    """
    Compute all indicator series from straddle candle data.

    Returns a dict with full series for each indicator.
    Wraps existing indicator_model.py functions + SuperTrend.
    """
    if not candles:
        return {}

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c.get("c_volume_total", c.get("volume", 0)) for c in candles]

    rsi = compute_rsi_series(closes, indicator_length)
    roc = compute_roc_series(closes, roc_length)
    dmi = compute_dmi_series(candles, indicator_length)
    chop = compute_chop_series(candles, indicator_length)
    ema = compute_ema_series(closes, ema_length)
    vwma = compute_vwma_series(closes, volumes, vwma_length)
    vwap = compute_vwap_series(highs, lows, closes, volumes)
    st_values, st_dirs = compute_supertrend_series(
        candles, supertrend_factor, supertrend_period
    )

    return {
        "rsi": rsi,
        "roc": roc,
        "plus_di": dmi["diPlus"],
        "minus_di": dmi["diMinus"],
        "adx": dmi["adx"],
        "dx": dmi["dx"],
        "chop": chop,
        "ema": ema,
        "vwma": vwma,
        "vwap": vwap,
        "supertrend": st_values,
        "supertrend_dir": st_dirs,
    }


def get_latest_snapshot(
    indicator_series: dict[str, list[float | None]],
) -> IndicatorSnapshot:
    """
    Extract the latest valid indicator values from full series
    and return an IndicatorSnapshot.
    """
    if not indicator_series:
        return IndicatorSnapshot()

    return IndicatorSnapshot(
        rsi=get_last_finite_value(indicator_series.get("rsi", [])),
        roc=get_last_finite_value(indicator_series.get("roc", [])),
        plus_di=get_last_finite_value(indicator_series.get("plus_di", [])),
        minus_di=get_last_finite_value(indicator_series.get("minus_di", [])),
        adx=get_last_finite_value(indicator_series.get("adx", [])),
        chop=get_last_finite_value(indicator_series.get("chop", [])),
        ema=get_last_finite_value(indicator_series.get("ema", [])),
        vwap=get_last_finite_value(indicator_series.get("vwap", [])),
        vwma=get_last_finite_value(indicator_series.get("vwma", [])),
        supertrend=get_last_finite_value(indicator_series.get("supertrend", [])),
        supertrend_direction=_last_int(indicator_series.get("supertrend_dir", [])),
    )


def get_snapshot_at(
    indicator_series: dict[str, list[float | None]],
    bar_index: int,
) -> IndicatorSnapshot:
    """
    Extract indicator values at a specific bar index.
    Used by the backtest engine for candle-by-candle replay.
    """
    if not indicator_series:
        return IndicatorSnapshot()

    def _val(key: str) -> float | None:
        series = indicator_series.get(key, [])
        if 0 <= bar_index < len(series):
            v = series[bar_index]
            if v is not None and math.isfinite(v):
                return v
        return None

    def _int_val(key: str) -> int | None:
        series = indicator_series.get(key, [])
        if 0 <= bar_index < len(series):
            v = series[bar_index]
            if v is not None:
                return int(v)
        return None

    return IndicatorSnapshot(
        rsi=_val("rsi"),
        roc=_val("roc"),
        plus_di=_val("plus_di"),
        minus_di=_val("minus_di"),
        adx=_val("adx"),
        chop=_val("chop"),
        ema=_val("ema"),
        vwap=_val("vwap"),
        vwma=_val("vwma"),
        supertrend=_val("supertrend"),
        supertrend_direction=_int_val("supertrend_dir"),
    )


# ---------------------------------------------------------------------------
# Crossover / crossunder helpers — matches Pine Script ta.crossover()
# ---------------------------------------------------------------------------

def crossover(series: list[float | None], threshold: float, bar: int) -> bool:
    """True when series crosses above threshold at the given bar."""
    if bar < 1 or bar >= len(series):
        return False
    curr = series[bar]
    prev = series[bar - 1]
    if curr is None or prev is None:
        return False
    return curr > threshold and prev <= threshold


def crossunder(series: list[float | None], threshold: float, bar: int) -> bool:
    """True when series crosses below threshold at the given bar."""
    if bar < 1 or bar >= len(series):
        return False
    curr = series[bar]
    prev = series[bar - 1]
    if curr is None or prev is None:
        return False
    return curr < threshold and prev >= threshold


def series_crossover(
    series_a: list[float | None],
    series_b: list[float | None],
    bar: int,
) -> bool:
    """True when series_a crosses above series_b at the given bar."""
    if bar < 1 or bar >= len(series_a) or bar >= len(series_b):
        return False
    a_curr, a_prev = series_a[bar], series_a[bar - 1]
    b_curr, b_prev = series_b[bar], series_b[bar - 1]
    if any(v is None for v in (a_curr, a_prev, b_curr, b_prev)):
        return False
    return a_curr > b_curr and a_prev <= b_prev


def series_crossunder(
    series_a: list[float | None],
    series_b: list[float | None],
    bar: int,
) -> bool:
    """True when series_a crosses below series_b at the given bar."""
    if bar < 1 or bar >= len(series_a) or bar >= len(series_b):
        return False
    a_curr, a_prev = series_a[bar], series_a[bar - 1]
    b_curr, b_prev = series_b[bar], series_b[bar - 1]
    if any(v is None for v in (a_curr, a_prev, b_curr, b_prev)):
        return False
    return a_curr < b_curr and a_prev >= b_prev


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _last_int(values: list[int | None]) -> int | None:
    for v in reversed(values):
        if v is not None:
            return v
    return None
