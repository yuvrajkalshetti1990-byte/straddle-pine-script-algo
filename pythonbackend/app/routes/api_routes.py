import asyncio
import csv
import json
import math
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse

from app.config import DATA_DIR
from app.models import auth_model, fyers_model, zerodha_model
from app.models.auth_model import get_access_token, is_connected
from app.models.hdfc_sky_model import (
    fetch_nifty_intraday as fetch_hdfc_intraday,
    fetch_nifty_option_chain,
)
from app.models.indicator_model import (
    build_straddle_candle,
    calc_delta,
    calc_implied_volatility,
    calc_ind_reg,
    calc_mode,
    calc_regime,
    calc_trade_type,
    calculate_all,
    calculate_all_from_candles,
    resample_candles,
    translate_strike_payload,
)
from app.models.market_model import fetch_nifty_chain, fetch_nifty_data, fetch_nifty_intraday
from app.models.price_calculator import (
    calculate_roc_adjustment,
    calculate_rsi_adjustment,
    calculate_di_adjustment,
    calculate_adx_adjustment,
    calculate_chop_adjustment,
)
from app.routes.auth_routes import status_payload


router = APIRouter()

MARKET_TZ = ZoneInfo("Asia/Kolkata")
SNAPSHOT_FILE = DATA_DIR / "last-close-strikes.json"
BOT_HISTORICAL_DIR = DATA_DIR.parents[1] / "My_Algo_Bot" / "historical_data"
EMPTY_INDICATORS = {"roc": None, "rsi": None, "dx": None, "minusDI": None, "plusDI": None, "adx": None, "chop": None}


@router.get("/auth/status")
async def auth_status():
    return await status_payload()


@router.get("/market/nifty-price")
async def nifty_price():
    try:
        from app.models import fyers_model, zerodha_model
        
        # Try Fyers first if connected
        if fyers_model._access_token:
            fyers_data = await asyncio.to_thread(fyers_model.fetch_nifty_price)
            if fyers_data:
                return {
                    "status": "success",
                    "connected": True,
                    "data": {
                        "symbol": "NIFTY 50",
                        "price": fyers_data["price"],
                        "change": fyers_data["change"],
                        "changePercent": fyers_data["changePercent"],
                        "timestamp": _iso_now(),
                        "source": "fyers",
                    },
                }
        
        # Try Zerodha
        if zerodha_model._access_token:
            kite_data = await asyncio.to_thread(zerodha_model.fetch_nifty_price)
            if kite_data:
                return {
                    "status": "success",
                    "connected": True,
                    "data": {
                        "symbol": "NIFTY 50",
                        "price": kite_data["price"],
                        "change": kite_data["change"],
                        "changePercent": kite_data["changePercent"],
                        "timestamp": _iso_now(),
                        "source": "zerodha",
                    },
                }

        nifty = await fetch_nifty_data()
        if nifty:
            return {
                "status": "success",
                "connected": is_connected(),
                "data": {
                    "symbol": "NIFTY 50",
                    "price": nifty.get("lastPrice") or nifty.get("last"),
                    "prevClose": nifty.get("previousClose"),
                    "change": round(_to_float(nifty.get("change")) or 0, 2),
                    "changePercent": round(_to_float(nifty.get("pChange")) or 0, 1),
                    "timestamp": _iso_now(),
                    "source": "nse",
                },
            }

        return {"status": "error", "connected": is_connected(), "message": "No NIFTY data"}
    except Exception as err:
        print(f"Error fetching NIFTY price: {err}")
        return JSONResponse({"status": "error", "connected": is_connected(), "message": str(err)}, status_code=500)


@router.post("/market/strikes/translate")
async def translate_straddle_series(payload: Any = Body(default=None)):
    try:
        translated = translate_strike_payload(payload, {"length": 14})
        return {"status": "success", "connected": is_connected(), "data": translated}
    except Exception as err:
        return JSONResponse({"status": "error", "connected": is_connected(), "message": str(err)}, status_code=400)


@router.get("/market/strikes/translate/self-test")
async def translate_straddle_series_self_test():
    try:
        candles = [
            {
                "datetime": f"2026-01-01T09:{index:02d}:00+05:30",
                "ce": {
                    "open": 100 + index,
                    "high": 0,
                    "low": 0,
                    "close": 101 + index,
                    "volume": 1000 + index,
                    "delta": 0.35 + (index * 0.002),
                    "iv": 16 + (index * 0.05),
                },
                "pe": {
                    "open": 90 - (index * 0.4),
                    "high": 0,
                    "low": 0,
                    "close": 89.5 - (index * 0.35),
                    "volume": 900 + index,
                    "delta": -0.28 + (index * 0.001),
                    "iv": 15 + (index * 0.04),
                },
            }
            for index in range(40)
        ]

        translated = translate_strike_payload([{"strike": 23000, "candles": candles}], {"length": 14})
        sample = translated[0] if translated else None
        indicators = (sample or {}).get("indicators") or {}
        passed = all(
            _is_finite(indicators.get(key))
            for key in ["rsi", "roc", "dx", "adx", "di_plus", "di_minus", "chop"]
        )

        return {"status": "success", "connected": is_connected(), "data": {"passed": passed, "sample": sample}}
    except Exception as err:
        return JSONResponse({"status": "error", "connected": is_connected(), "message": str(err)}, status_code=500)


@router.get("/market/strikes")
async def nifty_strikes(selected_strike: str | None = Query(default=None, alias="selectedStrike")):
    try:
        requested_center = _to_float(selected_strike)
        cached = await read_last_close_snapshot()
        chain = None
        intraday = None
        data_source = "nse"

        if is_connected():
            try:
                spot_price = (cached or {}).get("spotPrice")
                try:
                    nifty = await fetch_nifty_data()
                    if nifty and nifty.get("lastPrice"):
                        spot_price = nifty["lastPrice"]
                except Exception:
                    pass

                # --- Fyers Section ---
                if fyers_model._access_token:
                    fyers_chain = await asyncio.to_thread(fyers_model.fetch_fyers_option_chain, spot_price, 10)
                    if fyers_chain and fyers_chain.get("data"):
                        chain = fyers_chain
                        data_source = "fyers"
                        
                        # Fetch historical candles for each strike to compute indicators
                        candle_arrays = {}
                        tasks = []
                        symbols_to_fetch = []
                        for row in chain["data"]:
                            symbols_to_fetch.append(row["CE"]["symbol"])
                            symbols_to_fetch.append(row["PE"]["symbol"])
                            
                        # Limit concurrency to avoid 429s
                        sem = asyncio.Semaphore(2)
                        async def throttled_fetch(sym):
                            async with sem:
                                res = await fyers_model.fetch_symbol_history(sym)
                                await asyncio.sleep(0.5) # Small gap
                                return res
                                
                        for sym in symbols_to_fetch:
                            tasks.append(throttled_fetch(sym))
                        
                        histories = await asyncio.gather(*tasks)
                        now = datetime.now()
                        today_str = now.strftime("%Y-%m-%d")
                        
                        for sym, history in zip(symbols_to_fetch, histories):
                            candles = []
                            sym_day_open = None
                            
                            # History is already sorted by fetch_symbol_history
                            # And it is now a list of dicts: {"date": iso, "open": f, ...}
                            
                            for c in history:
                                dt_str = c["date"] # ISO format YYYY-MM-DDTHH:MM:SS
                                dt_part = dt_str.split("T")[0]
                                time_part = dt_str.split("T")[1]
                                hour = int(time_part.split(":")[0])
                                minute = int(time_part.split(":")[1])
                                
                                # First candle of today (>= 09:15)
                                if dt_part == today_str and sym_day_open is None:
                                    if hour > 9 or (hour == 9 and minute >= 15):
                                        sym_day_open = c["open"] # Open price of first candle today
                                
                                candles.append({
                                    "open": c["open"], 
                                    "high": c["high"], 
                                    "low": c["low"], 
                                    "close": c["close"], 
                                    "volume": c["volume"], 
                                    "date": dt_str
                                })
                            
                            candle_arrays[sym] = candles
                            
                            # Store day open and populate openPrice
                            for row in chain["data"]:
                                if row["CE"]["symbol"] == sym:
                                    row["CE"]["openPrice"] = sym_day_open or (candles[-1]["open"] if candles else 0)
                                if row["PE"]["symbol"] == sym:
                                    row["PE"]["openPrice"] = sym_day_open or (candles[-1]["open"] if candles else 0)
                                    
                        chain["candleArrays"] = candle_arrays
                
                # --- HDFC Sky Section (as fallback or primary if no Fyers) ---
                if not chain:
                    hdfc_chain = await asyncio.wait_for(
                        fetch_nifty_option_chain(spot_price, 2, requested_center),
                        timeout=12,
                    )
                    if hdfc_chain.get("data"):
                        chain = hdfc_chain
                        data_source = "hdfc_sky"
                
                try:
                    intraday = await asyncio.wait_for(fetch_nifty_intraday(), timeout=6)
                except Exception as intraday_err:
                    print(f"NSE intraday fetch failed: {intraday_err}")
            except Exception as conn_err:
                print(f"Broker fetch failed, falling back to NSE: {conn_err}")

        if not chain:
            chain = await asyncio.wait_for(fetch_nifty_chain(), timeout=8)
            if not intraday:
                try:
                    intraday = await asyncio.wait_for(fetch_nifty_intraday(), timeout=6)
                except Exception as intraday_err:
                    print(f"NSE intraday fetch failed while using NSE chain: {intraday_err}")
            data_source = "nse"

        if not intraday and is_connected() and get_access_token():
            try:
                intraday = await fetch_hdfc_intraday()
            except Exception:
                pass

        spot_indicators = normalize_indicators(calculate_all(intraday) if intraday else None)

        if not chain or not chain.get("data"):
            if cached:
                cached_payload = usable_cached_payload(cached, spot=None, selected_strike=requested_center)
                if cached_payload:
                    return {"status": "success", "connected": is_connected(), "data": cached_payload}

                return {
                    "status": "success",
                    "connected": is_connected(),
                    "data": stale_snapshot_payload(cached, spot=None, indicators=spot_indicators),
                }

            return {
                "status": "success",
                "connected": is_connected(),
                "data": {
                    "spotPrice": None,
                    "selectedStrike": requested_center,
                    "strikes": [],
                    "indicators": spot_indicators,
                    "marketOpen": False,
                },
            }

        spot = chain.get("underlyingValue") or (cached or {}).get("spotPrice")
        strike_prices = chain.get("strikePrices") or []
        nearest_expiry = (chain.get("expiryDates") or [None])[0]

        if not strike_prices:
            if cached:
                cached_payload = usable_cached_payload(cached, spot=spot, selected_strike=requested_center)
                if cached_payload:
                    return {"status": "success", "connected": is_connected(), "data": cached_payload}

                return {
                    "status": "success",
                    "connected": is_connected(),
                    "data": stale_snapshot_payload(cached, spot=spot, indicators=spot_indicators),
                }

            return {
                "status": "success",
                "connected": is_connected(),
                "data": {
                    "spotPrice": spot,
                    "selectedStrike": requested_center,
                    "strikes": [],
                    "indicators": spot_indicators,
                    "marketOpen": False,
                },
            }

        from app.strategy.config import StrategyConfig
        from app.strategy.types import IndexType
        
        # Load saved strategy config to get manual strike overrides
        strat_config = StrategyConfig.load_from_disk(IndexType.NIFTY)
        enabled_manual_strikes = [s.price for s in strat_config.strikes if s.enabled and s.price > 0]
        
        if enabled_manual_strikes:
            selected_strikes = sorted(list(set(enabled_manual_strikes)))
            # If we have manual strikes, the "ATM" for indicator display should be the middle one or closest to spot
            if requested_center is not None:
                atm_strike = min(selected_strikes, key=lambda s: abs(s - requested_center))
            else:
                atm_strike = min(selected_strikes, key=lambda s: abs(s - (spot or s)))
        else:
            center_reference = requested_center if requested_center is not None else spot
            atm_strike = min(strike_prices, key=lambda strike: abs(strike - (center_reference or strike)))
            selected_strikes = centered_strike_window(strike_prices, atm_strike, 2)

        chain_data = chain.get("data") or []
        filtered_data = [
            row
            for row in chain_data
            if row.get("strikePrice") in selected_strikes and row.get("expiryDate") == nearest_expiry
            ]

        if not filtered_data and (cached or {}).get("strikes"):
            cached_payload = usable_cached_payload(cached, spot=spot, selected_strike=requested_center)
            if cached_payload:
                return {"status": "success", "connected": is_connected(), "data": cached_payload}

            return {
                "status": "success",
                "connected": is_connected(),
                "data": stale_snapshot_payload(cached, spot=spot, indicators=spot_indicators),
            }

        days_to_expiry = _days_to_expiry(nearest_expiry)
        market_open_by_clock = is_market_hours_ist()
        raw_rows = []
        candle_arrays = chain.get("candleArrays") if isinstance(chain.get("candleArrays"), dict) else {}
        row_indicators_by_strike: dict[float, dict[str, float | None]] = {}
        combined_candles_by_strike: dict[float, list[dict[str, Any]]] = {}
        

        for row in filtered_data:
            strike = row.get("strikePrice")
            combined_candles = build_combined_premium_candles(row, candle_arrays)
            combined_candles_by_strike[strike] = combined_candles
            # Calculate indicators on resampled candles to match strategy timeframe (e.g. 3m or 5m)
            from app.strategy.constants import NIFTY_CONFIG
            interval = NIFTY_CONFIG.timeframe_minutes
            resampled_candles = resample_candles(combined_candles, interval)
            row_indicators = normalize_indicators(calculate_all_from_candles(resampled_candles))
            if has_indicator_values(row_indicators):
                row_indicators_by_strike[strike] = row_indicators

        selected_indicators = row_indicators_by_strike.get(atm_strike)
        if not has_indicator_values(selected_indicators):
            selected_indicators = (
                spot_indicators
                if has_indicator_values(spot_indicators)
                else EMPTY_INDICATORS.copy()
            )
        if not has_indicator_values(selected_indicators):
            selected_indicators = EMPTY_INDICATORS.copy()

        for row in filtered_data:
            ce = row.get("CE") or {}
            pe = row.get("PE") or {}
            strike = row.get("strikePrice")
            row_indicators = row_indicators_by_strike.get(strike)
            ce_ltp = pick_ltp(ce)
            pe_ltp = pick_ltp(pe)
            ce_open = _to_float(ce.get("openPrice")) or 0
            pe_open = _to_float(pe.get("openPrice")) or 0
            straddle_open = ce_open + pe_open
            straddle_close = ce_ltp + pe_ltp
            change = round(straddle_close - straddle_open, 2)
            projected_indicators = load_bot_historical_indicators(strike, straddle_close, straddle_open)
            fallback_indicators = (
                selected_indicators
                if has_indicator_values(selected_indicators)
                else projected_indicators
            )
            effective_indicators = row_indicators if has_indicator_values(row_indicators) else fallback_indicators

            ce_iv = _to_float(ce.get("impliedVolatility")) or 0
            pe_iv = _to_float(pe.get("impliedVolatility")) or 0
            ce_vol = _to_float(ce.get("totalTradedVolume")) or 0
            pe_vol = _to_float(pe.get("totalTradedVolume")) or 0

            ce_iv_calc, pe_iv_calc, combined_iv = calculate_combined_iv(
                spot, strike, days_to_expiry, ce_ltp, pe_ltp, ce_iv, pe_iv
            )

            chain_ce_delta = _to_float(ce.get("delta", ce.get("callDelta")))
            chain_pe_delta = _to_float(pe.get("delta", pe.get("putDelta")))
            combined_delta = calculate_net_delta(
                spot, strike, days_to_expiry, chain_ce_delta, chain_pe_delta, ce_iv_calc, pe_iv_calc
            )

            combined_volume = ce_vol + pe_vol
            c_volume = _format_volume(combined_volume)
            flow_metrics = calculate_option_flow_metrics(
                row,
                combined_candles_by_strike.get(strike) or [],
                spot,
                intraday,
                days_to_expiry,
                ce_iv_calc,
                pe_iv_calc,
                combined_iv,
                combined_delta,
            )
            ce_gain = ce_ltp - ce_open
            pe_gain = pe_ltp - pe_open
            lead_leg = "CE" if ce_gain >= pe_gain else "PE"
            dominance_symbol = "\u25b2" if ce_gain >= pe_gain else "\u25bc"
            direction_symbol = "\u2191" if straddle_close > straddle_open else "\u2193"
            lead = f"{lead_leg} {dominance_symbol} {direction_symbol}"

            regime = calc_regime(straddle_close, straddle_open, ce_gain, pe_gain)
            ind_reg = calc_ind_reg(
                effective_indicators.get("rsi"),
                effective_indicators.get("plusDI"),
                effective_indicators.get("minusDI"),
                effective_indicators.get("adx"),
            )
            t_mode = calc_mode(
                effective_indicators.get("rsi"),
                effective_indicators.get("plusDI"),
                effective_indicators.get("minusDI"),
                effective_indicators.get("adx"),
            )
            t_type = calc_trade_type(
                t_mode,
                effective_indicators.get("chop"),
                straddle_close,
                straddle_open,
                ce_gain,
                pe_gain,
            )

            # Calculate dynamic pricing based on indicators
            from app.models.price_calculator import calculate_dynamic_premium
            dynamic_pricing = calculate_dynamic_premium(
                ce_close=ce_ltp,
                pe_close=pe_ltp,
                roc=effective_indicators.get("roc"),
                rsi=effective_indicators.get("rsi"),
                plus_di=effective_indicators.get("plusDI"),
                minus_di=effective_indicators.get("minusDI"),
                adx=effective_indicators.get("adx"),
                chop=effective_indicators.get("chop"),
            )

            raw_rows.append(
                {
                    "strike": strike,
                    "cIV": combined_iv,
                    "open": round(straddle_open, 2),
                    "ltp": round(straddle_close, 2),
                    "ce": round(ce_ltp, 2),
                    "pe": round(pe_ltp, 2),
                    "change": change,
                    "lead": lead,
                    "cDelta": round(combined_delta, 2),
                    "cVolume": c_volume,
                    "ivChange": flow_metrics["ivChange"],
                    "netDelta": flow_metrics["netDelta"],
                    "deltaChange": flow_metrics["deltaChange"],
                    "volumeSurge": flow_metrics["volumeSurge"],
                    "currentVolume": flow_metrics["currentVolume"],
                    "avgVolume20": flow_metrics["avgVolume20"],
                    "regime": regime,
                    "indReg": ind_reg,
                    "tMode": t_mode,
                    "tType": t_type,
                    "isATM": strike == atm_strike,
                    "combinedIV": combined_iv,
                    "combinedDelta": combined_delta,
                    "combinedVolume": combined_volume,
                    "indicators": row_indicators if has_indicator_values(row_indicators) else effective_indicators,
                    "indicatorSource": "strike_candles" if has_indicator_values(row_indicators) else "bot_price_projected_3m",
                    "dynamicPricing": dynamic_pricing,
                }
            )

        strikes = merge_rows_with_fallback(raw_rows, (cached or {}).get("strikes") or [])
        cached_indicators = select_cached_indicators(
            cached,
            atm_strike,
            allow_global=requested_center is None,
        )
        resolved_indicators = (
            selected_indicators
            if has_indicator_values(selected_indicators)
            else cached_indicators
        )
        if not has_indicator_values(resolved_indicators):
            resolved_indicators = EMPTY_INDICATORS.copy()

        if strikes:
            await write_last_close_snapshot(
                {
                    "spotPrice": spot,
                    "atmStrike": atm_strike,
                    "selectedStrike": atm_strike,
                    "expiry": nearest_expiry,
                    "daysToExpiry": days_to_expiry,
                    "strikes": strikes,
                    "indicators": resolved_indicators,
                    "cachedAt": _iso_now(),
                }
            )

        return {
            "status": "success",
            "connected": is_connected(),
            "data": {
                "spotPrice": spot,
                "atmStrike": atm_strike,
                "selectedStrike": atm_strike,
                "expiry": nearest_expiry,
                "daysToExpiry": days_to_expiry,
                "strikes": strikes,
                "indicators": resolved_indicators,
                "marketOpen": market_open_by_clock,
                "fallbackSource": data_source,
            },
        }
    except Exception as err:
        print(f"Error fetching strike data: {err}")

        cached = await read_last_close_snapshot()
        if cached:
            cached_payload = usable_cached_payload(cached, spot=None, selected_strike=requested_center)
            if cached_payload:
                return {"status": "success", "connected": is_connected(), "data": cached_payload}

            return {
                "status": "success",
                "connected": is_connected(),
                "data": stale_snapshot_payload(cached, spot=None, indicators=None),
            }

        return JSONResponse({"status": "error", "connected": is_connected(), "message": str(err)}, status_code=500)


@router.get("/market/strikes/detail")
async def strike_detail(strike: float = Query(...), ce_ltp: float = Query(...), pe_ltp: float = Query(...)):
    """
    Get detailed strike information with dynamic pricing for selected strike
    
    This endpoint specifically calculates:
    - Per-strike indicators (ROC, RSI, DI, ADX, CHOP)
    - Dynamic pricing based on those indicators
    - Additional calculations
    
    Query params:
    - strike: Strike price (e.g., 24100)
    - ce_ltp: Call LTP
    - pe_ltp: Put LTP
    """
    try:
        from app.models.price_calculator import calculate_dynamic_premium

        detail_indicators, indicator_source = await resolve_strike_detail_indicators(strike)
        
        # Build straddle candle for this strike
        ce_close = _to_float(ce_ltp) or 0
        pe_close = _to_float(pe_ltp) or 0
        
        base_premium = ce_close + pe_close
        
        roc = detail_indicators.get("roc")
        rsi = detail_indicators.get("rsi")
        plus_di = detail_indicators.get("plusDI")
        minus_di = detail_indicators.get("minusDI")
        adx = detail_indicators.get("adx")
        chop = detail_indicators.get("chop")
        
        # Calculate dynamic premium
        dynamic_pricing = calculate_dynamic_premium(
            ce_close=ce_close,
            pe_close=pe_close,
            roc=roc,
            rsi=rsi,
            plus_di=plus_di,
            minus_di=minus_di,
            adx=adx,
            chop=chop,
        )
        
        return {
            "status": "success",
            "connected": is_connected(),
            "data": {
                "strike": strike,
                "ce_ltp": ce_close,
                "pe_ltp": pe_close,
                "base_premium": base_premium,
                "indicators": {
                    "roc": roc,
                    "rsi": rsi,
                    "plusDI": plus_di,
                    "minusDI": minus_di,
                    "adx": adx,
                    "chop": chop,
                },
                "indicatorSource": indicator_source,
                "dynamic_pricing": {
                    "base_premium": dynamic_pricing["base_premium"],
                    "dynamic_premium": dynamic_pricing["dynamic_premium"],
                    "adjustment_factor": dynamic_pricing["adjustment_factor"],
                    "premium_adjustment_points": dynamic_pricing["premium_adjustment_points"],
                    "premium_adjustment_percent": dynamic_pricing["premium_adjustment_percent"],
                    "adjustments": dynamic_pricing["adjustments"],
                }
            }
        }
    except Exception as err:
        print(f"Error fetching strike detail: {err}")
        return JSONResponse({"status": "error", "connected": is_connected(), "message": str(err)}, status_code=500)


async def resolve_strike_detail_indicators(strike: float) -> tuple[dict[str, float | None], str]:
    cached = await read_last_close_snapshot()

    # Prefer true selected-strike CE+PE candles from HDFC Sky when available.
    if is_connected() and get_access_token():
        try:
            spot_price = _to_float((cached or {}).get("spotPrice"))
            try:
                nifty = await asyncio.wait_for(fetch_nifty_data(), timeout=5)
                if nifty and nifty.get("lastPrice"):
                    spot_price = _to_float(nifty.get("lastPrice")) or spot_price
            except Exception:
                pass

            chain = await asyncio.wait_for(
                fetch_nifty_option_chain(spot_price, 0, strike),
                timeout=15,
            )
            rows = chain.get("data") or []
            selected_row = resolve_chain_row_for_strike(rows, strike)
            if selected_row:
                candles = build_combined_premium_candles(
                    selected_row,
                    chain.get("candleArrays") if isinstance(chain.get("candleArrays"), dict) else {},
                )
                row_indicators = normalize_indicators(calculate_all_from_candles(candles))
                if has_indicator_values(row_indicators):
                    return row_indicators, "strike_candles"
        except Exception as err:
            print(f"Could not calculate selected strike indicators for {strike:g}: {err}")

    cached_indicators = select_cached_indicators(cached, strike, allow_global=False)
    if has_indicator_values(cached_indicators):
        return cached_indicators, "cached_strike"

    bot_indicators = load_bot_historical_indicators(strike, None, None)
    if has_indicator_values(bot_indicators):
        return bot_indicators, "bot_price_projected_3m"

    return EMPTY_INDICATORS.copy(), "empty"


def resolve_chain_row_for_strike(rows: list[dict[str, Any]], strike: float) -> dict[str, Any] | None:
    if not rows:
        return None

    target = _to_float(strike)
    if target is None:
        return None

    exact = next((row for row in rows if _to_float(row.get("strikePrice")) == target), None)
    if exact:
        return exact

    nearest = min(
        rows,
        key=lambda row: abs((_to_float(row.get("strikePrice")) or target) - target),
    )
    nearest_strike = _to_float(nearest.get("strikePrice"))
    if nearest_strike is not None and abs(nearest_strike - target) <= 1:
        return nearest
    return None


def is_market_hours_ist() -> bool:
    now = datetime.now(MARKET_TZ)
    if now.weekday() >= 5:
        return False
    now_minutes = now.hour * 60 + now.minute
    return (9 * 60 + 15) <= now_minutes <= (15 * 60 + 30)


def centered_strike_window(strike_prices: list[float], center_strike: float, radius: int = 2) -> list[float]:
    if not strike_prices:
        return []

    window_size = (radius * 2) + 1
    center_index = strike_prices.index(center_strike)
    start = center_index - radius
    end = center_index + radius + 1

    if start < 0:
        end += -start
        start = 0
    if end > len(strike_prices):
        start = max(0, start - (end - len(strike_prices)))
        end = len(strike_prices)

    return strike_prices[start:end][:window_size]


def build_combined_premium_candles(
    option_row: dict[str, Any],
    candle_arrays: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    candle_arrays = candle_arrays or {}
    strike = option_row.get("strikePrice")
    ce_symbol = ((option_row or {}).get("CE") or {}).get("tradingsymbol") or ((option_row or {}).get("CE") or {}).get("symbol")
    pe_symbol = ((option_row or {}).get("PE") or {}).get("tradingsymbol") or ((option_row or {}).get("PE") or {}).get("symbol")
    
    ce_val = candle_arrays.get(ce_symbol)
    ce_candles = ce_val.get("candles") if isinstance(ce_val, dict) else ce_val
    
    pe_val = candle_arrays.get(pe_symbol)
    pe_candles = pe_val.get("candles") if isinstance(pe_val, dict) else pe_val
    

    if not ce_candles or not pe_candles:
        return []

    def parse_date(value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    pe_by_date: dict[str, list[dict[str, Any]]] = {}
    pe_pending: list[dict[str, Any]] = []
    for candle in pe_candles:
        date_key = candle.get("date")
        if date_key is not None:
            pe_by_date.setdefault(date_key, []).append(candle)
        pe_pending.append(candle)

    combined: list[dict[str, Any]] = []
    match_count = 0
    fallback_count = 0
    for index, ce in enumerate(ce_candles):
        pe = None
        ce_date = ce.get("date")
        if ce_date is not None:
            candidates = pe_by_date.get(ce_date) or []
            if candidates:
                pe = candidates.pop(0)
                if pe in pe_pending:
                    pe_pending.remove(pe)
                match_count += 1

        if pe is None and pe_pending:
            ce_ts = parse_date(ce_date)
            if ce_ts is not None:
                nearest_index = None
                nearest_delta = None
                for idx, cand in enumerate(pe_pending):
                    cand_ts = parse_date(cand.get("date"))
                    if cand_ts is None:
                        continue
                    delta = abs((cand_ts - ce_ts).total_seconds())
                    if nearest_delta is None or delta < nearest_delta:
                        nearest_delta = delta
                        nearest_index = idx
                if nearest_index is not None and nearest_delta is not None and nearest_delta <= 120:
                    pe = pe_pending.pop(nearest_index)
                    fallback_count += 1

        if pe is None and len(pe_candles) == len(ce_candles):
            pe = pe_candles[index]
            if pe in pe_pending:
                pe_pending.remove(pe)
            fallback_count += 1

        if not pe:
            continue

        try:
            combined.append(build_straddle_candle({"ce": ce, "pe": pe, "datetime": ce.get("date")}))
        except ValueError:
            continue

    return combined



def calculate_combined_iv(
    spot: float | None,
    strike: float | None,
    days_to_expiry: int,
    ce_price: float | None,
    pe_price: float | None,
    ce_iv: float | None = None,
    pe_iv: float | None = None,
) -> tuple[float, float, float]:
    ce_iv_calc = _to_float(ce_iv) or 0
    pe_iv_calc = _to_float(pe_iv) or 0
    spot_value = _to_float(spot)
    strike_value = _to_float(strike)
    ce_price_value = _to_float(ce_price)
    pe_price_value = _to_float(pe_price)

    if not ce_iv_calc and spot_value and strike_value and ce_price_value and ce_price_value > 0:
        ce_iv_calc = calc_implied_volatility(spot_value, strike_value, ce_price_value, days_to_expiry, "CE")
    if not pe_iv_calc and spot_value and strike_value and pe_price_value and pe_price_value > 0:
        pe_iv_calc = calc_implied_volatility(spot_value, strike_value, pe_price_value, days_to_expiry, "PE")

    values = [value for value in [ce_iv_calc, pe_iv_calc] if value and value > 0]
    combined_iv = round(sum(values) / len(values), 1) if values else 0
    return ce_iv_calc, pe_iv_calc, combined_iv


def calculate_net_delta(
    spot: float | None,
    strike: float | None,
    days_to_expiry: int,
    ce_delta: float | None = None,
    pe_delta: float | None = None,
    ce_iv: float | None = None,
    pe_iv: float | None = None,
) -> float:
    ce_delta_value = _to_float(ce_delta)
    pe_delta_value = _to_float(pe_delta)
    if ce_delta_value is not None and pe_delta_value is not None:
        return round(ce_delta_value - abs(pe_delta_value), 4)

    spot_value = _to_float(spot)
    strike_value = _to_float(strike)
    ce_iv_value = _to_float(ce_iv)
    pe_iv_value = _to_float(pe_iv)
    if not spot_value or not strike_value:
        return 0

    calculated_ce_delta = (
        calc_delta(spot_value, strike_value, ce_iv_value, days_to_expiry)
        if ce_iv_value and ce_iv_value > 0
        else None
    )
    calculated_pe_delta = (
        calc_delta(spot_value, strike_value, pe_iv_value, days_to_expiry) - 1
        if pe_iv_value and pe_iv_value > 0
        else None
    )

    if calculated_ce_delta is not None and calculated_pe_delta is not None:
        return round(calculated_ce_delta + calculated_pe_delta, 4)
    if calculated_ce_delta is not None:
        return round(calculated_ce_delta, 4)
    if calculated_pe_delta is not None:
        return round(calculated_pe_delta, 4)
    return 0


def calculate_option_flow_metrics(
    option_row: dict[str, Any],
    combined_candles: list[dict[str, Any]],
    spot: float | None,
    intraday: list[list[float]] | None,
    days_to_expiry: int,
    ce_iv: float | None,
    pe_iv: float | None,
    combined_iv: float | None,
    net_delta: float | None,
) -> dict[str, float | None]:
    ce = (option_row or {}).get("CE") or {}
    pe = (option_row or {}).get("PE") or {}
    strike = _to_float((option_row or {}).get("strikePrice"))
    spot_open = resolve_day_open_spot(intraday) or _to_float(spot)
    ce_open = _to_float(ce.get("openPrice"))
    pe_open = _to_float(pe.get("openPrice"))

    open_ce_iv, open_pe_iv, open_combined_iv = calculate_combined_iv(
        spot_open, strike, days_to_expiry, ce_open, pe_open
    )
    open_net_delta = calculate_net_delta(
        spot_open, strike, days_to_expiry, None, None, open_ce_iv, open_pe_iv
    )

    volume_surge, current_volume, avg_volume = calculate_volume_surge(combined_candles)
    current_iv = _to_float(combined_iv)
    current_delta = _to_float(net_delta)

    return {
        "ivChange": round(current_iv - open_combined_iv, 2)
        if current_iv is not None and current_iv > 0 and open_combined_iv > 0
        else None,
        "netDelta": round(current_delta, 4) if current_delta is not None else None,
        "deltaChange": round(current_delta - open_net_delta, 4)
        if current_delta is not None and open_net_delta is not None
        else None,
        "volumeSurge": round(volume_surge, 2) if volume_surge is not None else None,
        "currentVolume": current_volume,
        "avgVolume20": round(avg_volume, 2) if avg_volume is not None else None,
    }


def resolve_day_open_spot(intraday: list[list[float]] | None) -> float | None:
    if not intraday:
        return None

    today = datetime.now(MARKET_TZ).date()
    first_today: float | None = None
    first_any: float | None = None
    for point in intraday:
        if not isinstance(point, list | tuple) or len(point) < 2:
            continue
        timestamp = _to_float(point[0])
        price = _to_float(point[1])
        if timestamp is None or price is None:
            continue
        if first_any is None:
            first_any = price
        point_dt = datetime.fromtimestamp(timestamp / 1000, tz=MARKET_TZ)
        if point_dt.date() == today:
            first_today = price
            break
    return first_today or first_any


def calculate_volume_surge(candles: list[dict[str, Any]]) -> tuple[float | None, float | None, float | None]:
    volumes = [
        _to_float(candle.get("c_volume_total"))
        for candle in candles
        if _to_float(candle.get("c_volume_total")) is not None
    ]
    if not volumes:
        return None, None, None

    current_volume = volumes[-1]
    history = volumes[-21:-1] if len(volumes) > 1 else []
    if not history:
        history = volumes[:-1]
    if not history:
        return None, current_volume, None

    avg_volume = sum(history) / len(history)
    if avg_volume <= 0:
        return None, current_volume, avg_volume
    return current_volume / avg_volume, current_volume, avg_volume


def normalize_indicators(indicators: dict[str, Any] | None) -> dict[str, float | None]:
    source = indicators if isinstance(indicators, dict) else {}
    return {
        "roc": _to_float(source.get("roc")),
        "rsi": _to_float(source.get("rsi")),
        "dx": _to_float(source.get("dx", source.get("di_dx"))),
        "minusDI": _to_float(source.get("minusDI", source.get("di_minus"))),
        "plusDI": _to_float(source.get("plusDI", source.get("di_plus"))),
        "adx": _to_float(source.get("adx")),
        "chop": _to_float(source.get("chop")),
    }


def load_bot_historical_indicators(
    strike: float | None = None,
    current_close: float | None = None,
    current_open: float | None = None,
) -> dict[str, float | None]:
    """
    Fallback for closed-market/no-candle sessions.

    My_Algo_Bot stores combined straddle candles with already-computed indicator
    columns. Use the latest row from the requested strike when present; otherwise
    use the nearest saved strike. This is intentionally marked by callers as a
    historical source, not live CE/PE candle data.
    """
    if not BOT_HISTORICAL_DIR.exists():
        return EMPTY_INDICATORS.copy()

    csv_files = list(BOT_HISTORICAL_DIR.glob("candles_*_straddle_*.csv"))
    if not csv_files:
        return EMPTY_INDICATORS.copy()

    target = _to_float(strike)

    def file_strike(path):
        parts = path.name.split("_")
        return _to_float(parts[1]) if len(parts) > 1 else None

    if target is not None:
        csv_files.sort(
            key=lambda path: (
                abs((file_strike(path) or target) - target),
                path.stat().st_mtime,
            )
        )
    else:
        csv_files.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    for path in csv_files:
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            if not rows:
                continue
            latest = rows[-1]
            indicators = {
                "roc": _to_float(latest.get("roc")),
                "rsi": _to_float(latest.get("rsi")),
                "dx": _to_float(latest.get("dx")),
                "minusDI": _to_float(latest.get("di_minus")),
                "plusDI": _to_float(latest.get("di_plus")),
                "adx": _to_float(latest.get("adx")),
                "chop": _to_float(latest.get("chop")),
            }
            projected = project_indicators_from_current_price(indicators, latest, current_close, current_open)
            if has_indicator_values(projected):
                return projected
            if has_indicator_values(indicators):
                return indicators
        except Exception:
            continue

    return EMPTY_INDICATORS.copy()


def project_indicators_from_current_price(
    indicators: dict[str, float | None],
    latest_bot_row: dict[str, Any],
    current_close: float | None,
    current_open: float | None = None,
) -> dict[str, float | None]:
    close_value = _to_float(current_close)
    if close_value is None or close_value <= 0 or not has_indicator_values(indicators):
        return EMPTY_INDICATORS.copy()

    bot_open = _to_float(latest_bot_row.get("open"))
    bot_close = _to_float(latest_bot_row.get("close"))
    open_value = _to_float(current_open) or bot_open or close_value
    if open_value <= 0 or bot_open is None or bot_open <= 0 or bot_close is None or bot_close <= 0:
        return EMPTY_INDICATORS.copy()

    current_move_pct = ((close_value - open_value) / open_value) * 100
    bot_move_pct = ((bot_close - bot_open) / bot_open) * 100
    move_delta = current_move_pct - bot_move_pct
    trend_force = abs(move_delta)
    bearish = move_delta < 0

    rsi = _clamp((indicators.get("rsi") or 50) + (move_delta * 2.5), 0, 100)
    plus_di = indicators.get("plusDI") or 0
    minus_di = indicators.get("minusDI") or 0
    if bearish:
        minus_di += trend_force * 1.4
        plus_di = max(0, plus_di - trend_force * 0.8)
    else:
        plus_di += trend_force * 1.4
        minus_di = max(0, minus_di - trend_force * 0.8)

    return {
        "roc": round((indicators.get("roc") or 0) + move_delta, 2),
        "rsi": round(rsi, 2),
        "dx": round(_clamp((indicators.get("dx") or 20) + (trend_force * 0.3), 0, 100), 2),
        "minusDI": round(_clamp(minus_di, 0, 100), 2),
        "plusDI": round(_clamp(plus_di, 0, 100), 2),
        "adx": round(_clamp((indicators.get("adx") or 20) + (trend_force * 0.5), 0, 100), 2),
        "chop": round(_clamp((indicators.get("chop") or 50) - (trend_force * 0.35), 0, 100), 2),
    }


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def has_indicator_values(indicators: dict[str, Any] | None) -> bool:
    return any(value is not None for value in normalize_indicators(indicators).values())


def resolve_cached_selected_strike(
    cached: dict[str, Any] | None,
    selected_strike: float | None = None,
) -> float | None:
    rows = (cached or {}).get("strikes") if isinstance((cached or {}).get("strikes"), list) else []
    row_strikes = [strike for strike in (_to_float(row.get("strike")) for row in rows) if strike is not None]
    candidates = [
        selected_strike,
        _to_float((cached or {}).get("selectedStrike")),
        _to_float((cached or {}).get("atmStrike")),
    ]

    for candidate in candidates:
        if candidate is None:
            continue
        if row_strikes:
            return min(row_strikes, key=lambda strike: abs(strike - candidate))
        return candidate

    atm_row = next((row for row in rows if row.get("isATM")), None)
    if atm_row:
        return _to_float(atm_row.get("strike"))
    if row_strikes:
        return row_strikes[len(row_strikes) // 2]
    return None


def select_cached_indicators(
    cached: dict[str, Any] | None,
    selected_strike: float | None = None,
    allow_global: bool = True,
) -> dict[str, float | None]:
    rows = (cached or {}).get("strikes") if isinstance((cached or {}).get("strikes"), list) else []
    target = resolve_cached_selected_strike(cached, selected_strike)

    if target is not None and rows:
        selected_row = min(
            rows,
            key=lambda row: abs((_to_float(row.get("strike")) or target) - target),
        )
        row_indicators = normalize_indicators(selected_row.get("indicators"))
        if has_indicator_values(row_indicators):
            return row_indicators

    if allow_global:
        return normalize_indicators((cached or {}).get("indicators"))
    return EMPTY_INDICATORS.copy()


def usable_cached_payload(
    cached: dict[str, Any] | None,
    spot: float | None = None,
    selected_strike: float | None = None,
) -> dict[str, Any] | None:
    if not is_cached_snapshot_usable(cached, spot):
        return None

    resolved_selected = resolve_cached_selected_strike(cached, selected_strike)
    return {
        **cached,
        "selectedStrike": resolved_selected,
        "indicators": select_cached_indicators(
            cached,
            resolved_selected,
            allow_global=selected_strike is None,
        ),
        "marketOpen": False,
        "fallbackSource": "last_snapshot",
        "isStale": False,
    }


def stale_snapshot_payload(
    cached: dict[str, Any] | None,
    spot: float | None,
    indicators: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_indicators = normalize_indicators(indicators)
    if not has_indicator_values(normalized_indicators):
        normalized_indicators = EMPTY_INDICATORS.copy()

    return {
        "spotPrice": spot,
        "strikes": [],
        "indicators": normalized_indicators,
        "marketOpen": False,
        "fallbackSource": "stale_snapshot",
        "isStale": True,
        "staleCachedAt": (cached or {}).get("cachedAt"),
        "staleExpiry": (cached or {}).get("expiry"),
        "message": "Live option-chain data is unavailable and the cached snapshot is stale.",
    }


def is_cached_snapshot_usable(cached: dict[str, Any] | None, spot: float | None = None) -> bool:
    if not cached or not cached.get("strikes"):
        return False

    today = datetime.now(MARKET_TZ).date()
    expiry = _parse_expiry_date(cached.get("expiry"))
    if not expiry or expiry < today:
        return False

    cached_at = _parse_datetime(cached.get("cachedAt"))
    if not cached_at:
        return False
    if (today - cached_at.astimezone(MARKET_TZ).date()).days > 3:
        return False

    cached_spot = _to_float(cached.get("spotPrice"))
    if spot and cached_spot:
        max_allowed_gap = max(300, spot * 0.015)
        if abs(spot - cached_spot) > max_allowed_gap:
            return False

    return True


def pick_last_close_price(leg: dict[str, Any] | None = None) -> float:
    leg = leg or {}
    for key in ["previousClose", "closePrice", "settlePrice"]:
        value = _to_float(leg.get(key))
        if value is not None and value > 0:
            return value
    return 0


def pick_ltp(leg: dict[str, Any] | None = None) -> float:
    leg = leg or {}
    last_price = _to_float(leg.get("lastPrice"))
    if last_price is not None and last_price > 0:
        return last_price
    last_close = pick_last_close_price(leg)
    if last_close > 0:
        return last_close
    return last_price if last_price is not None else 0


def map_by_strike(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("strike")): row for row in rows if row.get("strike") is not None}


def merge_rows_with_fallback(
    current_rows: list[dict[str, Any]],
    fallback_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not current_rows:
        return fallback_rows
    if not fallback_rows:
        return current_rows

    fallback_map = map_by_strike(fallback_rows)
    merged = []
    for row in current_rows:
        previous = fallback_map.get(str(row.get("strike")))
        if not previous:
            merged.append(row)
            continue

        merged.append(
            {
                **row,
                "open": row["open"] if has_valid_price(row.get("open")) else previous.get("open"),
                "ltp": row["ltp"] if has_valid_price(row.get("ltp")) else previous.get("ltp"),
                "ce": row["ce"] if has_valid_price(row.get("ce")) else previous.get("ce"),
                "pe": row["pe"] if has_valid_price(row.get("pe")) else previous.get("pe"),
                "change": row["change"] if has_valid_number(row.get("change")) else previous.get("change"),
                "cIV": row["cIV"] if has_valid_number(row.get("cIV")) else previous.get("cIV"),
                "cDelta": row["cDelta"] if has_valid_number(row.get("cDelta")) else previous.get("cDelta"),
                "cVolume": row.get("cVolume") or previous.get("cVolume"),
                "ivChange": row["ivChange"] if has_valid_number(row.get("ivChange")) else previous.get("ivChange"),
                "netDelta": row["netDelta"] if has_valid_number(row.get("netDelta")) else previous.get("netDelta"),
                "deltaChange": row["deltaChange"]
                if has_valid_number(row.get("deltaChange"))
                else previous.get("deltaChange"),
                "volumeSurge": row["volumeSurge"]
                if has_valid_number(row.get("volumeSurge"))
                else previous.get("volumeSurge"),
                "currentVolume": row["currentVolume"]
                if has_valid_number(row.get("currentVolume"))
                else previous.get("currentVolume"),
                "avgVolume20": row["avgVolume20"]
                if has_valid_number(row.get("avgVolume20"))
                else previous.get("avgVolume20"),
                "lead": row.get("lead") or previous.get("lead"),
                "regime": row.get("regime") or previous.get("regime"),
                "indReg": row.get("indReg") or previous.get("indReg"),
                "tMode": row.get("tMode") or previous.get("tMode"),
                "tType": row.get("tType") or previous.get("tType"),
                "combinedIV": row["combinedIV"]
                if has_valid_number(row.get("combinedIV"))
                else previous.get("combinedIV"),
                "combinedDelta": row["combinedDelta"]
                if has_valid_number(row.get("combinedDelta"))
                else previous.get("combinedDelta"),
                "combinedVolume": row["combinedVolume"]
                if has_valid_number(row.get("combinedVolume"))
                else previous.get("combinedVolume"),
                "indicators": row.get("indicators") if has_indicator_values(row.get("indicators")) else previous.get("indicators"),
            }
        )
    return merged


async def read_last_close_snapshot() -> dict[str, Any] | None:
    try:
        parsed = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
        if parsed.get("strikes"):
            return parsed
    except Exception:
        pass
    return None


async def write_last_close_snapshot(data: dict[str, Any]) -> None:
    try:
        SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as err:
        print(f"Error writing close snapshot cache: {err}")


def has_valid_number(value: Any) -> bool:
    numeric = _to_float(value)
    return numeric is not None


def has_valid_price(value: Any) -> bool:
    numeric = _to_float(value)
    return numeric is not None and numeric > 0


def _format_volume(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return str(int(value) if float(value).is_integer() else value)


def _days_to_expiry(value: Any) -> int:
    expiry = _parse_expiry_date(value)
    if not expiry:
        return 1
    delta_days = (expiry - date.today()).days
    return max(1, delta_days)


def _parse_expiry_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=MARKET_TZ)
    return parsed


def _to_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _is_finite(value: Any) -> bool:
    return _to_float(value) is not None


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
