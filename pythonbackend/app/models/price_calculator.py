"""
Dynamic Price Calculator - Calculates adjusted premium prices based on indicators
Mirrors My_Algo_Bot indicator-based logic for CE/PE premium adjustments

Key Logic:
- Base Price = CE_close + PE_close (straddle premium)
- Adjustment factors based on ROC, RSI, DI, ADX, CHOP
- ROC: Momentum adjustment (higher ROC = lower premium needed)
- RSI: Trend strength (higher RSI = uptrend adjustment)
- DI (±DI): Directional trend (plus_di vs minus_di balance)
- ADX: Trend strength confirmation (higher ADX = stronger trend)
- CHOP: Volatility/Consolidation (lower CHOP = trending, higher CHOP = choppy)
"""

import math
from typing import Any


def to_finite_number(value: Any) -> float | None:
    """Convert to finite number or None"""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def calculate_roc_adjustment(roc: float | None) -> float:
    """
    ROC Adjustment Factor
    ROC (Rate of Change) indicates momentum/velocity
    
    Higher ROC (positive momentum) → premium decreases (less risk buffer needed)
    Lower ROC (negative momentum) → premium increases (more risk buffer needed)
    
    Range: ROC typically -100 to +100
    Adjustment factor range: 0.85 to 1.15 (±15% premium adjustment)
    """
    roc_val = to_finite_number(roc) or 0.0
    
    # Clamp ROC to practical range (-50 to +50)
    roc_clamped = max(-50, min(50, roc_val))
    
    # Convert to adjustment: -50 ROC → +15%, +50 ROC → -15%
    # Formula: 1.0 - (roc / 500)
    adjustment = 1.0 - (roc_clamped / 350.0)
    
    return max(0.85, min(1.15, adjustment))


def calculate_rsi_adjustment(rsi: float | None) -> float:
    """
    RSI Adjustment Factor
    RSI indicates overbought/oversold conditions
    
    RSI < 30: Oversold → premium increases (support level, less risk)
    RSI 30-70: Normal → premium neutral (1.0)
    RSI > 70: Overbought → premium decreases (resistance level, more risk)
    
    Adjustment factor range: 0.90 to 1.10 (±10% premium adjustment)
    """
    rsi_val = to_finite_number(rsi) or 50.0
    
    # Normalize RSI to -1 to +1 scale (50 = 0)
    rsi_normalized = (rsi_val - 50.0) / 50.0
    rsi_normalized = max(-1.0, min(1.0, rsi_normalized))
    
    # When RSI > 50 (bullish), reduce premium slightly
    # When RSI < 50 (bearish), increase premium slightly
    # Formula: 1.0 - (rsi_normalized * 0.10)
    adjustment = 1.0 - (rsi_normalized * 0.10)
    
    return max(0.90, min(1.10, adjustment))


def calculate_di_adjustment(plus_di: float | None, minus_di: float | None) -> float:
    """
    Directional Index (±DI) Adjustment
    Measures directional strength
    
    Strong uptrend (+DI >> -DI): Premium decreases slightly (bullish, less protection)
    Strong downtrend (-DI >> +DI): Premium increases slightly (bearish, more protection)
    Weak trend (±DI similar): Premium neutral
    
    Adjustment factor range: 0.95 to 1.05 (±5% premium adjustment)
    """
    plus_di_val = to_finite_number(plus_di) or 0.0
    minus_di_val = to_finite_number(minus_di) or 0.0
    
    # Calculate DI difference normalized
    di_diff = plus_di_val - minus_di_val
    di_diff = max(-50, min(50, di_diff))  # Clamp to practical range
    
    # Normalize to -1 to +1 scale
    di_normalized = di_diff / 50.0
    di_normalized = max(-1.0, min(1.0, di_normalized))
    
    # Formula: 1.0 - (di_normalized * 0.05)
    adjustment = 1.0 - (di_normalized * 0.05)
    
    return max(0.95, min(1.05, adjustment))


def calculate_adx_adjustment(adx: float | None) -> float:
    """
    ADX (Average Directional Index) Adjustment
    ADX measures trend strength (0-100)
    
    ADX < 20: Weak trend → premium increases (uncertain, more risk buffer)
    ADX 20-40: Moderate trend → premium neutral
    ADX > 40: Strong trend → premium decreases (clear direction, less buffer)
    
    Adjustment factor range: 0.95 to 1.10 (±10% premium adjustment)
    """
    adx_val = to_finite_number(adx) or 20.0
    
    if adx_val < 20:
        # Weak trend: increase premium for safety
        # Linear from 20→1.0 to 0→1.10
        adjustment = 1.0 + ((20 - adx_val) / 200.0)
    elif adx_val > 40:
        # Strong trend: can reduce premium slightly
        # Linear from 40→1.0 to 100→0.95
        adjustment = 1.0 - ((adx_val - 40) / 1000.0)
    else:
        # Moderate trend: neutral
        adjustment = 1.0
    
    return max(0.95, min(1.10, adjustment))


def calculate_chop_adjustment(chop: float | None) -> float:
    """
    Choppiness Index (CHOP) Adjustment
    CHOP indicates trend vs consolidation (0-100)
    
    CHOP < 38.2: Strong trending → premium decreases (directional confidence)
    CHOP 38.2-61.8: Neutral → premium neutral
    CHOP > 61.8: Choppy/Consolidating → premium increases (uncertain, more buffer)
    
    Adjustment factor range: 0.93 to 1.10 (±10% premium adjustment)
    """
    chop_val = to_finite_number(chop) or 50.0
    
    if chop_val < 38.2:
        # Strong trending: reduce premium
        # Linear from 38.2→1.0 to 0→0.93
        adjustment = 1.0 - ((38.2 - chop_val) / 410.0)
    elif chop_val > 61.8:
        # Choppy/consolidating: increase premium for safety
        # Linear from 61.8→1.0 to 100→1.10
        adjustment = 1.0 + ((chop_val - 61.8) / 385.0)
    else:
        # Neutral zone
        adjustment = 1.0
    
    return max(0.93, min(1.10, adjustment))


def calculate_dynamic_premium(
    ce_close: float,
    pe_close: float,
    roc: float | None = None,
    rsi: float | None = None,
    plus_di: float | None = None,
    minus_di: float | None = None,
    adx: float | None = None,
    chop: float | None = None,
) -> dict[str, Any]:
    """
    Calculate dynamic combined premium price with indicator adjustments
    
    Returns:
    {
        "base_premium": ce_close + pe_close,
        "ce_close": ce_close,
        "pe_close": pe_close,
        "dynamic_premium": adjusted_price,
        "adjustment_factor": combined_factor,
        "adjustments": {
            "roc_factor": ...,
            "rsi_factor": ...,
            "di_factor": ...,
            "adx_factor": ...,
            "chop_factor": ...
        }
    }
    """
    base_premium = ce_close + pe_close
    
    # Calculate individual adjustment factors
    roc_factor = calculate_roc_adjustment(roc)
    rsi_factor = calculate_rsi_adjustment(rsi)
    di_factor = calculate_di_adjustment(plus_di, minus_di)
    adx_factor = calculate_adx_adjustment(adx)
    chop_factor = calculate_chop_adjustment(chop)
    
    # Combine all factors using geometric mean (multiplicative)
    # This prevents extreme adjustments and creates balanced effect
    combined_factor = (roc_factor * rsi_factor * di_factor * adx_factor * chop_factor) ** (1/5)
    
    # Apply adjustment to base premium
    dynamic_premium = base_premium * combined_factor
    
    return {
        "base_premium": round(base_premium, 2),
        "ce_close": round(ce_close, 2),
        "pe_close": round(pe_close, 2),
        "dynamic_premium": round(dynamic_premium, 2),
        "adjustment_factor": round(combined_factor, 4),
        "premium_adjustment_points": round(dynamic_premium - base_premium, 2),
        "premium_adjustment_percent": round(((dynamic_premium - base_premium) / base_premium * 100), 2) if base_premium != 0 else 0,
        "adjustments": {
            "roc_factor": round(roc_factor, 4),
            "rsi_factor": round(rsi_factor, 4),
            "di_factor": round(di_factor, 4),
            "adx_factor": round(adx_factor, 4),
            "chop_factor": round(chop_factor, 4),
        },
        "indicators": {
            "roc": round(roc, 2) if roc is not None else None,
            "rsi": round(rsi, 2) if rsi is not None else None,
            "plus_di": round(plus_di, 2) if plus_di is not None else None,
            "minus_di": round(minus_di, 2) if minus_di is not None else None,
            "adx": round(adx, 2) if adx is not None else None,
            "chop": round(chop, 2) if chop is not None else None,
        }
    }


def calculate_dynamic_high_low(
    ce_high: float | None,
    ce_low: float | None,
    pe_high: float | None,
    pe_low: float | None,
    adjustment_factor: float,
) -> tuple[float, float]:
    """
    Adjust high/low prices based on indicator adjustment factor
    
    Returns (adjusted_high, adjusted_low)
    """
    # Handle None values
    ce_h = ce_high if ce_high is not None else 0
    ce_l = ce_low if ce_low is not None else 0
    pe_h = pe_high if pe_high is not None else 0
    pe_l = pe_low if pe_low is not None else 0
    
    # Combined high/low using straddle logic:
    # High: CE_high + PE_low (when underlying at intrabar high)
    # Low: CE_low + PE_high (when underlying at intrabar low)
    combined_high = max(ce_h + pe_l, ce_l + pe_h)
    combined_low = min(ce_h + pe_l, ce_l + pe_h)
    
    # Apply adjustment factor
    adjusted_high = combined_high * adjustment_factor
    adjusted_low = combined_low * adjustment_factor
    
    return (round(adjusted_high, 2), round(adjusted_low, 2))


def calculate_price_with_indicators(candle: dict[str, Any]) -> dict[str, Any]:
    """
    Process a single candle and calculate dynamic premium
    Input candle should have: ce (dict), pe (dict), indicators (dict)
    
    Returns augmented candle with dynamic pricing
    """
    ce = candle.get("ce") or {}
    pe = candle.get("pe") or {}
    indicators = candle.get("indicators") or {}
    
    ce_close = to_finite_number(ce.get("close")) or 0.0
    pe_close = to_finite_number(pe.get("close")) or 0.0
    
    pricing = calculate_dynamic_premium(
        ce_close,
        pe_close,
        roc=indicators.get("roc"),
        rsi=indicators.get("rsi"),
        plus_di=indicators.get("plus_di"),
        minus_di=indicators.get("minus_di"),
        adx=indicators.get("adx"),
        chop=indicators.get("chop"),
    )
    
    # Adjust high/low if available
    ce_high = to_finite_number(ce.get("high"))
    ce_low = to_finite_number(ce.get("low"))
    pe_high = to_finite_number(pe.get("high"))
    pe_low = to_finite_number(pe.get("low"))
    
    if all([ce_high, ce_low, pe_high, pe_low]):
        adjusted_high, adjusted_low = calculate_dynamic_high_low(
            ce_high, ce_low, pe_high, pe_low,
            pricing["adjustment_factor"]
        )
        pricing["high"] = adjusted_high
        pricing["low"] = adjusted_low
    
    return pricing
