"""
Regime Engine — full 10-state regime classification.

Extends the existing calc_regime/calc_ind_reg/calc_mode/calc_trade_type
from indicator_model.py to match the complete Pine Script regime logic.

This module does NOT replace the existing functions — it provides the
full-fidelity versions used by the strategy engine.
"""

from __future__ import annotations

from app.strategy.types import IndicatorSnapshot, RegimeState


def classify_price_regime(
    combined_ltp: float,
    combined_open: float,
    ce_gain: float,
    pe_gain: float,
) -> RegimeState:
    """
    Price-action regime classification.
    Matches Pine Script's regime label logic exactly.

    BULLISH:   price > open AND CE leading
    BEARISH:   price < open AND PE leading
    SHORT COV: price > open AND PE leading
    DECAY:     price < open AND CE leading
    SIDEWAYS:  price ≈ open (within tolerance)
    """
    if combined_ltp > combined_open:
        if ce_gain >= pe_gain:
            return RegimeState.BULLISH
        return RegimeState.SHORT_COV
    elif combined_ltp < combined_open:
        if pe_gain >= ce_gain:
            return RegimeState.BEARISH
        return RegimeState.DECAY
    return RegimeState.SIDEWAYS


def classify_indicator_regime(
    indicators: IndicatorSnapshot,
) -> RegimeState:
    """
    Indicator-based regime classification.
    Combines price regime with indicator data to produce
    the full 10-state regime.

    This maps to the Pine Script's combined regime/tMode logic.
    """
    rsi = indicators.rsi
    adx = indicators.adx
    plus_di = indicators.plus_di or 0
    minus_di = indicators.minus_di or 0

    if adx is None or rsi is None:
        return RegimeState.WAIT

    # ADX < 15: No trend → SHORT regime
    if adx < 15:
        return RegimeState.SHORT

    # Strong bullish indicators
    if rsi > 50 and plus_di > minus_di:
        return RegimeState.BUY_CE

    # Strong bearish indicators
    if rsi < 40 and minus_di > plus_di:
        return RegimeState.BUY_PE

    # Moderate trend with ranging RSI → straddle buy
    if adx > 20 and 40 <= rsi <= 60:
        return RegimeState.LONG_STR

    return RegimeState.SHORT


def classify_trade_type(
    indicator_regime: RegimeState,
    chop: float | None,
    combined_ltp: float,
    combined_open: float,
    ce_gain: float,
    pe_gain: float,
) -> str:
    """
    Final trade type classification.
    Matches Pine Script's trade type column exactly.

    Returns: "Buy CE", "Buy PE", "Buy Str", "Sell Str", "NoTrade"
    """
    if indicator_regime == RegimeState.WAIT:
        return "NoTrade"

    # Chop filter: if choppy, no trade
    if chop is not None and chop > 61.8:
        return "NoTrade"

    if indicator_regime == RegimeState.SHORT:
        # Only sell straddle if price is declining
        return "Sell Str" if combined_ltp < combined_open else "NoTrade"

    if indicator_regime in {RegimeState.BUY_CE, RegimeState.BUY_PE, RegimeState.LONG_STR}:
        if ce_gain >= pe_gain:
            return "Buy CE"
        if pe_gain > ce_gain:
            return "Buy PE"
        return "Buy Str"

    return "NoTrade"


def classify_ind_reg(indicators: IndicatorSnapshot) -> str:
    """
    Indicator regime label for the dashboard table.
    Matches Pine Script's IND.REG column.

    Returns: "Bullish", "Bearish", "Neutral", "NoTrend"
    """
    rsi = indicators.rsi
    adx = indicators.adx
    plus_di = indicators.plus_di or 0
    minus_di = indicators.minus_di or 0

    if adx is None or rsi is None:
        return "NoTrend"

    if adx < 15:
        return "NoTrend"

    if rsi > 55 and plus_di > minus_di:
        return "Bullish"

    if rsi < 45 and minus_di > plus_di:
        return "Bearish"

    return "Neutral"
