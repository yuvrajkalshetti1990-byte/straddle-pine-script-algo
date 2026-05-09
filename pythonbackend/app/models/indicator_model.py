import math
import numpy as np
import pandas as pd
from typing import Any

from app.models.price_calculator import calculate_dynamic_premium


# Indicator lengths matching My_Algo_Bot/strategy_config.py
INDICATOR_LENGTH = 14  # General length for RSI, DMI, CHOP
ROC_LENGTH = 9         # ROC period
EMA_LENGTH = 20        # EMA period (for reference)
VWMA_LENGTH = 15       # VWMA period (for reference)


def to_finite_number(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def to_positive_number(value: Any) -> float | None:
    numeric = to_finite_number(value)
    return numeric if numeric is not None and numeric > 0 else None


def resolve_combined_delta_from_candle(candle: dict[str, Any] | None = None) -> float | None:
    candle = candle or {}
    ce = candle.get("ce") or {}
    pe = candle.get("pe") or {}

    direct = to_finite_number(candle.get("c_delta"))
    if direct is not None:
        return direct

    ce_delta = to_finite_number(candle.get("ce_delta", ce.get("delta")))
    pe_delta = to_finite_number(candle.get("pe_delta", pe.get("delta")))

    if ce_delta is not None and pe_delta is not None:
        return ce_delta - pe_delta
    return None


def resolve_iv_from_candle(candle: dict[str, Any] | None = None) -> float | None:
    candle = candle or {}
    ce = candle.get("ce") or {}
    pe = candle.get("pe") or {}

    direct = to_finite_number(candle.get("iv"))
    if direct is not None:
        return direct

    ce_iv = to_finite_number(candle.get("ce_iv", ce.get("iv")))
    pe_iv = to_finite_number(candle.get("pe_iv", pe.get("iv")))

    if ce_iv is not None and pe_iv is not None:
        return (ce_iv + pe_iv) / 2
    return None


def build_straddle_candle(candle: dict[str, Any] | None = None) -> dict[str, Any]:
    candle = candle or {}
    ce = candle.get("ce") or {}
    pe = candle.get("pe") or {}

    ce_open = to_finite_number(ce.get("open"))
    ce_close = to_finite_number(ce.get("close"))
    pe_open = to_finite_number(pe.get("open"))
    pe_close = to_finite_number(pe.get("close"))
    ce_volume = to_finite_number(ce.get("volume")) or 0
    pe_volume = to_finite_number(pe.get("volume")) or 0

    if ce_open is None or ce_close is None or pe_open is None or pe_close is None:
        raise ValueError("Each candle must include finite ce/pe open and close values")

    ce_high = to_positive_number(ce.get("high"))
    ce_low = to_positive_number(ce.get("low"))
    pe_high = to_positive_number(pe.get("high"))
    pe_low = to_positive_number(pe.get("low"))

    open_value = ce_open + pe_open
    close = ce_close + pe_close

    combined_high = max(open_value, close)
    combined_low = min(open_value, close)
    if ce_high is not None and ce_low is not None and pe_high is not None and pe_low is not None:
        # Mirrors My_Algo_Bot/yuvi_data.py: straddle H/L comes from opposite leg extremes.
        high_at_underlying_high = ce_high + pe_low
        high_at_underlying_low = ce_low + pe_high
        combined_high = max(open_value, close, high_at_underlying_high, high_at_underlying_low)
        combined_low = min(open_value, close, high_at_underlying_high, high_at_underlying_low)

    return {
        "date": candle.get("datetime") or candle.get("date"),
        "open": open_value,
        "high": combined_high,
        "low": combined_low,
        "close": close,
        "volume": ce_volume + pe_volume,
        "ce_ltp": ce_close,
        "pe_ltp": pe_close,
        "ce_open": ce_open,
        "pe_open": pe_open,
        "ce_volume": ce_volume,
        "pe_volume": pe_volume,
        "c_volume_total": ce_volume + pe_volume,
        "c_delta_total": resolve_combined_delta_from_candle(candle),
        "iv_total": resolve_iv_from_candle(candle),
    }


def build_straddle_candles(candles: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    return [build_straddle_candle(candle) for candle in candles or []]


def compute_rma_series(values: list[float | None], length: int) -> list[float | None]:
    """
    Wilder's smoothing (RMA) - matches My_Algo_Bot/yuvi_indicators.py rma function
    """
    result: list[float | None] = [None] * len(values)
    if length <= 0 or len(values) < length:
        return result

    # Seed with mean of first 'length' values
    seed_values = []
    for i in range(length):
        if values[i] is not None and math.isfinite(values[i]):
            seed_values.append(values[i])

    if not seed_values:
        return result

    result[length - 1] = sum(seed_values) / len(seed_values)
    alpha = 1.0 / length

    # Apply smoothing for remaining values
    for i in range(length, len(values)):
        value = values[i]
        if value is None or not math.isfinite(value) or result[i - 1] is None:
            result[i] = None
        else:
            result[i] = alpha * value + (1 - alpha) * result[i - 1]

    return result


def compute_ema_series(values: list[float | None], length: int = EMA_LENGTH) -> list[float | None]:
    """
    Exponential Moving Average - matches pandas-ta ta.ema
    """
    result: list[float | None] = [None] * len(values)
    if length <= 0 or len(values) < length:
        return result

    # Simple moving average for seed
    seed_sum = 0.0
    seed_count = 0
    for i in range(length):
        if values[i] is not None and math.isfinite(values[i]):
            seed_sum += values[i]
            seed_count += 1

    if seed_count == 0:
        return result

    result[length - 1] = seed_sum / seed_count
    multiplier = 2.0 / (length + 1)

    for i in range(length, len(values)):
        value = values[i]
        if value is None or not math.isfinite(value) or result[i - 1] is None:
            result[i] = None
        else:
            result[i] = (value * multiplier) + (result[i - 1] * (1 - multiplier))

    return result


def compute_vwma_series(
    closes: list[float | None], volumes: list[float | None], length: int = VWMA_LENGTH
) -> list[float | None]:
    """
    Volume Weighted Moving Average - matches pandas-ta ta.vwma
    """
    result: list[float | None] = [None] * len(closes)
    if length <= 0 or len(closes) != len(volumes) or len(closes) < length:
        return result

    for i in range(length - 1, len(closes)):
        price_volume_sum = 0.0
        volume_sum = 0.0
        valid_count = 0

        for j in range(i - length + 1, i + 1):
            close = closes[j]
            volume = volumes[j]
            if (
                close is not None
                and math.isfinite(close)
                and volume is not None
                and math.isfinite(volume)
                and volume > 0
            ):
                price_volume_sum += close * volume
                volume_sum += volume
                valid_count += 1

        if valid_count > 0 and volume_sum > 0:
            result[i] = price_volume_sum / volume_sum
        else:
            result[i] = None

    return result


def compute_vwap_series(
    highs: list[float | None],
    lows: list[float | None],
    closes: list[float | None],
    volumes: list[float | None],
) -> list[float | None]:
    """
    Volume Weighted Average Price - matches pandas-ta ta.vwap
    Cumulative VWAP calculation
    """
    result: list[float | None] = [None] * len(closes)
    if len(highs) != len(lows) or len(lows) != len(closes) or len(closes) != len(volumes):
        return result

    price_volume_sum = 0.0
    volume_sum = 0.0

    for i in range(len(closes)):
        high = highs[i]
        low = lows[i]
        close = closes[i]
        volume = volumes[i]

        if (
            high is not None
            and math.isfinite(high)
            and low is not None
            and math.isfinite(low)
            and close is not None
            and math.isfinite(close)
            and volume is not None
            and math.isfinite(volume)
            and volume > 0
        ):
            typical_price = (high + low + close) / 3
            price_volume_sum += typical_price * volume
            volume_sum += volume
            result[i] = price_volume_sum / volume_sum
        else:
            result[i] = None

    return result


def compute_rsi_series(closes: list[float], length: int = INDICATOR_LENGTH) -> list[float | None]:
    changes = [None if index == 0 else close - closes[index - 1] for index, close in enumerate(closes)]
    gains = [None if change is None else max(change, 0) for change in changes]
    losses = [None if change is None else max(-change, 0) for change in changes]
    avg_gain = compute_rma_series(gains, length)
    avg_loss = compute_rma_series(losses, length)

    result: list[float | None] = []
    for gain, loss in zip(avg_gain, avg_loss):
        if gain is None or loss is None:
            result.append(None)
        elif loss == 0:
            result.append(100)
        elif gain == 0:
            result.append(0)
        else:
            rs = gain / loss
            result.append(100 - (100 / (1 + rs)))
    return result


def compute_roc_series(closes: list[float], length: int = ROC_LENGTH) -> list[float | None]:
    result: list[float | None] = []
    for index, close in enumerate(closes):
        if index < length:
            result.append(None)
            continue
        previous = closes[index - length]
        if not math.isfinite(previous) or previous == 0:
            result.append(None)
        else:
            result.append(((close - previous) / previous) * 100)
    return result


def compute_true_range_series(candles: list[dict[str, Any]]) -> list[float | None]:
    true_range: list[float | None] = []
    for index, current in enumerate(candles):
        previous = candles[index - 1] if index > 0 else None
        if previous is None:
            true_range.append(None)
            continue

        true_range.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous["close"]),
                abs(current["low"] - previous["close"]),
            )
        )
    return true_range


def compute_dmi_series(candles: list[dict[str, Any]], length: int = INDICATOR_LENGTH) -> dict[str, list[float | None]]:
    tr_raw: list[float | None] = []
    plus_dm_raw: list[float | None] = []
    minus_dm_raw: list[float | None] = []

    for index, current in enumerate(candles):
        previous = candles[index - 1] if index > 0 else None
        up = None if previous is None else current["high"] - previous["high"]
        down = None if previous is None else -(current["low"] - previous["low"])
        tr_raw.append(
            None
            if previous is None
            else max(
                current["high"] - current["low"],
                abs(current["high"] - previous["close"]),
                abs(current["low"] - previous["close"]),
            )
        )
        plus_dm_raw.append(up if up is not None and down is not None and up > down and up > 0 else 0.0)
        minus_dm_raw.append(down if up is not None and down is not None and down > up and down > 0 else 0.0)

    tr_rma = compute_rma_series(tr_raw, length)
    plus_rma = compute_rma_series(plus_dm_raw, length)
    minus_rma = compute_rma_series(minus_dm_raw, length)

    di_plus: list[float | None] = [None] * len(candles)
    di_minus: list[float | None] = [None] * len(candles)
    dx: list[float | None] = [None] * len(candles)

    for index, (tr, plus, minus) in enumerate(zip(tr_rma, plus_rma, minus_rma)):
        if tr is None or plus is None or minus is None or tr == 0:
            continue
        plus_value = (100 * plus) / tr
        minus_value = (100 * minus) / tr
        denominator = plus_value + minus_value
        di_plus[index] = plus_value
        di_minus[index] = minus_value
        dx[index] = 0 if denominator == 0 else (100 * abs(plus_value - minus_value)) / denominator

    dx_for_adx = [0.0 if value is None or not math.isfinite(value) else value for value in dx]
    return {
        "diPlus": di_plus,
        "diMinus": di_minus,
        "dx": dx,
        "adx": compute_rma_series(dx_for_adx, length),
    }


def compute_chop_series(candles: list[dict[str, Any]], length: int = INDICATOR_LENGTH) -> list[float | None]:
    tr_raw = compute_true_range_series(candles)
    chop: list[float | None] = [None] * len(candles)
    for index in range(len(candles)):
        if index < length - 1:
            continue

        tr_window = tr_raw[index - length + 1 : index + 1]
        if any(value is None or not math.isfinite(value) for value in tr_window):
            continue

        tr_sum = sum(value for value in tr_window if value is not None)
        highest = -math.inf
        lowest = math.inf
        for cursor in range(index - length + 1, index + 1):
            highest = max(highest, candles[cursor]["high"])
            lowest = min(lowest, candles[cursor]["low"])

        price_range = highest - lowest
        if tr_sum > 0 and price_range > 0:
            chop[index] = 100 * (math.log10(tr_sum / price_range) / math.log10(length))
    return chop


def get_last_finite_value(values: list[float | None]) -> float | None:
    for value in reversed(values):
        if value is not None and math.isfinite(value):
            return value
    return None


def calculate_latest_straddle_indicators(
    straddle_candles: list[dict[str, Any]] | None,
    length: int = INDICATOR_LENGTH,
    roc_length: int = ROC_LENGTH,
) -> dict[str, float | None]:
    if not straddle_candles:
        return {
            "ema": None,
            "vwma": None,
            "vwap": None,
            "rsi": None,
            "roc": None,
            "dx": None,
            "adx": None,
            "di_plus": None,
            "di_minus": None,
            "chop": None,
        }

    closes = [candle["close"] for candle in straddle_candles]
    # Use 'volume' as fallback for 'c_volume_total' (supports resampled candles)
    volumes = [candle.get("c_volume_total") if candle.get("c_volume_total") is not None else candle.get("volume", 0) for candle in straddle_candles]
    highs = [candle["high"] for candle in straddle_candles]
    lows = [candle["low"] for candle in straddle_candles]

    ema_series = compute_ema_series(closes, EMA_LENGTH)
    vwma_series = compute_vwma_series(closes, volumes, VWMA_LENGTH)
    vwap_series = compute_vwap_series(highs, lows, closes, volumes)
    rsi_series = compute_rsi_series(closes, length)
    roc_series = compute_roc_series(closes, roc_length)
    dmi_series = compute_dmi_series(straddle_candles, length)
    chop_series = compute_chop_series(straddle_candles, length)

    return {
        "ema": get_last_finite_value(ema_series),
        "vwma": get_last_finite_value(vwma_series),
        "vwap": get_last_finite_value(vwap_series),
        "rsi": get_last_finite_value(rsi_series),
        "roc": get_last_finite_value(roc_series),
        "dx": get_last_finite_value(dmi_series["dx"]),
        "adx": get_last_finite_value(dmi_series["adx"]),
        "di_plus": get_last_finite_value(dmi_series["diPlus"]),
        "di_minus": get_last_finite_value(dmi_series["diMinus"]),
        "chop": get_last_finite_value(chop_series),
    }


def resolve_combined_volume_change(latest: dict[str, Any], previous: dict[str, Any] | None) -> float | None:
    if not previous:
        return None
    return latest["c_volume_total"] - previous["c_volume_total"]


def resolve_combined_delta_change(latest: dict[str, Any], previous: dict[str, Any] | None) -> float | None:
    if not previous or latest["c_delta_total"] is None or previous["c_delta_total"] is None:
        return None
    return latest["c_delta_total"] - previous["c_delta_total"]


def resolve_iv_change(latest: dict[str, Any], previous: dict[str, Any] | None) -> float | None:
    if not previous or latest["iv_total"] is None or previous["iv_total"] is None:
        return None
    return latest["iv_total"] - previous["iv_total"]


def translate_strike_series(series: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    strike = to_finite_number(series.get("strike"))
    if strike is None:
        raise ValueError("Strike payload must include a finite strike")

    source_candles = series.get("candles") if isinstance(series.get("candles"), list) else []
    if not source_candles:
        raise ValueError(f"Strike {strike:g} must include a non-empty candles array")

    straddle_candles = build_straddle_candles(source_candles)
    latest = straddle_candles[-1]
    previous = straddle_candles[-2] if len(straddle_candles) > 1 else None
    
    # Calculate Day Open from first candle of today if possible
    # For now, we take the open of the first candle in the series
    day_open = straddle_candles[0]["open"]
    
    indicators = calculate_latest_straddle_indicators(
        straddle_candles,
        (options or {}).get("length", INDICATOR_LENGTH),
        (options or {}).get("roc_length", ROC_LENGTH),
    )
    
    # Calculate dynamic premium based on indicators
    dynamic_pricing = calculate_dynamic_premium(
        ce_close=latest["ce_ltp"],
        pe_close=latest["pe_ltp"],
        roc=indicators.get("roc"),
        rsi=indicators.get("rsi"),
        plus_di=indicators.get("di_plus"),
        minus_di=indicators.get("di_minus"),
        adx=indicators.get("adx"),
        chop=indicators.get("chop"),
    )

    return {
        "strike": strike,
        "straddle_open": day_open,
        "straddle_close": latest["close"],
        "straddle_high": latest["high"],
        "straddle_low": latest["low"],
        "straddle_ltp": latest["close"],
        "change": round(latest["close"] - day_open, 2),
        "ce_ltp": latest["ce_ltp"],
        "pe_ltp": latest["pe_ltp"],
        "c_volume": resolve_combined_volume_change(latest, previous),
        "c_delta": resolve_combined_delta_change(latest, previous),
        "iv": resolve_iv_change(latest, previous),
        "indicators": indicators,
        # Dynamic pricing information
        "dynamic_pricing": {
            "base_premium": dynamic_pricing["base_premium"],
            "dynamic_premium": dynamic_pricing["dynamic_premium"],
            "adjustment_factor": dynamic_pricing["adjustment_factor"],
            "premium_adjustment_points": dynamic_pricing["premium_adjustment_points"],
            "premium_adjustment_percent": dynamic_pricing["premium_adjustment_percent"],
            "adjustments": dynamic_pricing["adjustments"],
        }
    }


def translate_strike_payload(payload: Any, options: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        strike_series = payload
    elif isinstance(payload, dict) and isinstance(payload.get("strikes"), list):
        strike_series = payload["strikes"]
    else:
        strike_series = []

    if not strike_series:
        raise ValueError("Payload must be an array of strike series or an object with a strikes array")
    return [translate_strike_series(series, options) for series in strike_series]


def to_candles(price_points: list[Any] | None, interval_ms: int = 5 * 60 * 1000) -> list[dict[str, float]]:
    if not price_points:
        return []

    candles: list[dict[str, float]] = []
    current: dict[str, float] | None = None
    bucket: int | None = None

    for point in price_points:
        if not isinstance(point, list | tuple) or len(point) < 2:
            continue
        timestamp = to_finite_number(point[0])
        price = to_finite_number(point[1])
        if timestamp is None or price is None:
            continue

        next_bucket = math.floor(timestamp / interval_ms)
        if current is None or next_bucket != bucket:
            if current:
                candles.append(current)
            bucket = next_bucket
            current = {"time": timestamp, "open": price, "high": price, "low": price, "close": price}
        else:
            current["high"] = max(current["high"], price)
            current["low"] = min(current["low"], price)
            current["close"] = price

    if current:
        candles.append(current)
    return candles


def calculate_all(price_points: list[Any] | None) -> dict[str, float | None]:
    candles = to_candles(price_points, 5 * 60 * 1000)
    indicators = calculate_latest_straddle_indicators(candles, INDICATOR_LENGTH, ROC_LENGTH)
    return {
        "rsi": indicators["rsi"],
        "roc": indicators["roc"],
        "dx": indicators["dx"],
        "adx": indicators["adx"],
        "plusDI": indicators["di_plus"],
        "minusDI": indicators["di_minus"],
        "chop": indicators["chop"],
    }


def resample_candles(candles: list[dict[str, Any]], interval_minutes: int = 5) -> list[dict[str, Any]]:
    """Resample 1-minute candles into any timeframe."""
    if not candles:
        return []
        
    buckets: dict[str, dict[str, Any]] = {}
    for candle in candles or []:
        date_value = str(candle.get("date") or "")
        # Support both "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DDTHH:MM:SS"
        if "T" in date_value:
            parts = date_value.split("T")
        else:
            parts = date_value.split(" ")
            
        if len(parts) < 2:
            continue
        date_part, time_part = parts[0], parts[1]
        
        # Parse time: HH:MM:SS
        time_parts = time_part.split(":")
        if len(time_parts) < 2:
            continue
        hour, minute = int(time_parts[0]), int(time_parts[1])
        
        # Round minute down to interval
        resampled_minute = (minute // interval_minutes) * interval_minutes
        bucket_key = f"{date_part} {hour:02d}:{resampled_minute:02d}:00"
        
        if bucket_key not in buckets:
            buckets[bucket_key] = {
                "date": bucket_key,
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle.get("volume", 0),
                "ce_ltp": candle.get("ce_ltp", 0),
                "pe_ltp": candle.get("pe_ltp", 0),
                "ce_open": candle.get("ce_open", 0),
                "pe_open": candle.get("pe_open", 0)
            }
        else:
            buckets[bucket_key]["high"] = max(buckets[bucket_key]["high"], candle["high"])
            buckets[bucket_key]["low"] = min(buckets[bucket_key]["low"], candle["low"])
            buckets[bucket_key]["close"] = candle["close"]
            buckets[bucket_key]["volume"] += candle.get("volume", 0)
            buckets[bucket_key]["ce_ltp"] = candle.get("ce_ltp", 0)
            buckets[bucket_key]["pe_ltp"] = candle.get("pe_ltp", 0)

    return sorted(buckets.values(), key=lambda x: x["date"])


def calculate_all_from_candles(candles: list[dict[str, Any]] | None) -> dict[str, float | None]:
    if not candles:
        return {"rsi": None, "roc": None, "dx": None, "adx": None, "plusDI": None, "minusDI": None, "chop": None}
    indicators = calculate_latest_straddle_indicators(candles, INDICATOR_LENGTH, ROC_LENGTH)
    return {
        "rsi": indicators["rsi"],
        "roc": indicators["roc"],
        "dx": indicators["dx"],
        "adx": indicators["adx"],
        "plusDI": indicators["di_plus"],
        "minusDI": indicators["di_minus"],
        "chop": indicators["chop"],
    }


def calc_regime(combined_ltp: float, combined_open: float, ce_gain: float, pe_gain: float) -> str:
    direction = "UP" if combined_ltp > combined_open else "DOWN" if combined_ltp < combined_open else "FLAT"
    dominance = "CE" if ce_gain >= pe_gain else "PE"
    if direction == "UP" and dominance == "CE":
        return "BULLISH"
    if direction == "UP" and dominance == "PE":
        return "SHORT COV"
    if direction == "DOWN" and dominance == "PE":
        return "BEARISH"
    if direction == "DOWN" and dominance == "CE":
        return "DECAY"
    return "SIDEWAYS"


def calc_ind_reg(rsi: float | None, plus_di: float | None, minus_di: float | None, adx: float | None) -> str:
    if adx is None or rsi is None:
        return "NoTrend"
    plus_di = plus_di or 0
    minus_di = minus_di or 0
    if adx < 15:
        return "NoTrend"
    if rsi > 55 and plus_di > minus_di:
        return "Bullish"
    if rsi < 45 and minus_di > plus_di:
        return "Bearish"
    return "Neutral"


def calc_mode(rsi: float | None, plus_di: float | None, minus_di: float | None, adx: float | None) -> str:
    if rsi is None or adx is None:
        return "WAIT..."
    plus_di = plus_di or 0
    minus_di = minus_di or 0
    if adx < 15:
        return "SHORT"
    if rsi > 50 and plus_di > minus_di:
        return "BUY CE"
    if rsi < 40 and minus_di > plus_di:
        return "BUY PE"
    if adx > 20 and 40 <= rsi <= 60:
        return "LONG STR"
    return "SHORT"


def calc_trade_type(
    mode: str,
    chop: float | None,
    combined_ltp: float,
    combined_open: float,
    ce_gain: float,
    pe_gain: float,
) -> str:
    if mode == "WAIT..." or (chop is not None and chop > 61.8):
        return "NoTrade"
    if mode == "SHORT":
        return "Sell Str" if combined_ltp < combined_open else "NoTrade"
    if mode in {"BUY CE", "BUY PE", "LONG STR"}:
        if ce_gain >= pe_gain:
            return "Buy CE"
        if pe_gain > ce_gain:
            return "Buy PE"
        return "Buy Str"
    return "NoTrade"


def calc_delta(spot: float, strike: float, iv: float, days_to_expiry: int) -> float:
    if not iv or not days_to_expiry or days_to_expiry <= 0:
        return 0
    t = days_to_expiry / 365
    sigma = iv / 100
    rate = 0.07
    d1 = (math.log(spot / strike) + (rate + sigma * sigma / 2) * t) / (sigma * math.sqrt(t))
    return 0.5 * (1 + math.erf(d1 / math.sqrt(2)))


def bs_call_price(spot: float, strike: float, t: float, sigma: float, rate: float) -> float:
    if sigma <= 0 or t <= 0:
        return max(spot - strike, 0)
    d1 = (math.log(spot / strike) + (rate + sigma * sigma / 2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    nd1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    nd2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    return spot * nd1 - strike * math.exp(-rate * t) * nd2


def calc_implied_volatility(
    spot: float,
    strike: float,
    price: float,
    days_to_expiry: int,
    option_type: str,
) -> float:
    if not spot or not strike or not price or price <= 0 or days_to_expiry <= 0:
        return 0
    t = days_to_expiry / 365
    rate = 0.07
    intrinsic = max(strike - spot, 0) if option_type == "PE" else max(spot - strike, 0)
    if price <= intrinsic:
        return 0

    sigma = 0.3
    for _ in range(50):
        if option_type == "PE":
            model_price = bs_call_price(spot, strike, t, sigma, rate) - spot + strike * math.exp(-rate * t)
        else:
            model_price = bs_call_price(spot, strike, t, sigma, rate)
        diff = model_price - price
        if abs(diff) < 0.01:
            break

        d1 = (math.log(spot / strike) + (rate + sigma * sigma / 2) * t) / (sigma * math.sqrt(t))
        vega = spot * math.sqrt(t) * math.exp(-d1 * d1 / 2) / math.sqrt(2 * math.pi)
        if vega < 1e-10:
            break
        sigma -= diff / vega
        if sigma <= 0.001:
            sigma = 0.001
        if sigma > 5:
            sigma = 5
    return round(sigma * 100, 1)


def calc_rsi(df, length=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.ewm(alpha=1/length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_roc(df, length=9):
    return ((df['close'] - df['close'].shift(length)) / df['close'].shift(length)) * 100


def calc_dmi_adx(df, length=14):
    up_move = df['high'].diff()
    down_move = -df['low'].diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low'] - df['close'].shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/length, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/length, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/length, adjust=False).mean() / atr)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/length, adjust=False).mean()

    return plus_di, minus_di, adx


def calc_chop(df, length=14):
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low'] - df['close'].shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(window=length).sum()
    high_low_range = df['high'].rolling(window=length).max() - df['low'].rolling(window=length).min()

    chop = 100 * np.log10(atr / high_low_range) / np.log10(length)
    chop = chop.where(high_low_range > 0)
    return chop
