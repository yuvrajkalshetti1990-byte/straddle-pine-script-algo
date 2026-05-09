import asyncio
import csv
import io
import json
import re
import time
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import DATA_DIR, HDFC_API_KEY, HDFC_BASE_URL, USER_AGENT
from app.models.auth_model import get_access_token, set_access_token


SECURITY_MASTER_URL = "https://hdfcsky.com/api/v1/contract/Compact?info=download"
CACHE_DIR = DATA_DIR
MASTER_CACHE = CACHE_DIR / "security-master.json"
MASTER_TTL = 6 * 60 * 60 * 1000

master_cache: dict[str, Any] | None = None


def handle_hdfc_auth_error(status: int, context: str) -> None:
    if status in {401, 403}:
        print(f"HDFC Sky: {context} returned {status} - token expired, disconnecting")
        set_access_token(None)
        raise RuntimeError(f"HDFC Sky token expired ({status}) - please re-login at /auth/login")


def hdfc_headers() -> dict[str, str]:
    return {
        "Authorization": get_access_token() or "",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }


def today_date_str() -> str:
    return datetime.now(UTC).date().isoformat()


async def download_security_master() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(SECURITY_MASTER_URL, headers={"User-Agent": USER_AGENT})
    if response.status_code >= 400:
        raise RuntimeError(f"Security master download failed: {response.status_code}")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = CACHE_DIR / "security-master.zip"
    extract_dir = CACHE_DIR / "sm-extract"
    zip_path.write_bytes(response.content)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(extract_dir)
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        csv_name = csv_names[0] if csv_names else archive.namelist()[0]
        csv_text = (extract_dir / csv_name).read_text(encoding="utf-8", errors="replace")

    return parse_security_master_csv(csv_text)


def parse_security_master_csv(csv_text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    instruments: list[dict[str, Any]] = []

    for row in reader:
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        instruments.append(
            {
                "exchange": normalized.get("exchange") or "",
                "token": normalized.get("exchange_token") or "",
                "tradingsymbol": normalized.get("trading_symbol") or "",
                "name": normalized.get("company_name") or "",
                "closePrice": _to_float(normalized.get("close_price")) or 0,
                "expiry": normalized.get("expiry") or "",
                "strike": _to_float(normalized.get("strike")) or 0,
                "lotSize": int(_to_float(normalized.get("lot_size")) or 0),
                "instrumentType": normalized.get("instrument_name") or "",
                "optionType": normalized.get("option_type") or "",
            }
        )
    return instruments


async def get_security_master() -> list[dict[str, Any]]:
    global master_cache

    now_ms = time.time() * 1000
    if master_cache and now_ms - master_cache["ts"] < MASTER_TTL:
        return master_cache["instruments"]

    try:
        parsed = json.loads(MASTER_CACHE.read_text(encoding="utf-8"))
        if parsed.get("ts") and now_ms - parsed["ts"] < MASTER_TTL and parsed.get("instruments"):
            master_cache = parsed
            return parsed["instruments"]
    except Exception:
        pass

    instruments = await download_security_master()
    master_cache = {"ts": now_ms, "instruments": instruments}

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        MASTER_CACHE.write_text(json.dumps(master_cache), encoding="utf-8")
    except Exception:
        pass

    return instruments


def parse_expiry(expiry_str: str) -> str:
    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    parts = str(expiry_str).split("-")
    if len(parts) != 3:
        return ""
    dd, mmm, yyyy = parts
    return f"{yyyy}-{months.get(mmm, '00')}-{dd.zfill(2)}"


async def get_nifty_option_tokens(target_strikes: list[float] | None = None) -> dict[float, dict[str, Any]]:
    instruments = await get_security_master()
    nifty_opts = [
        instrument
        for instrument in instruments
        if instrument["exchange"] == "NFO"
        and instrument["name"] == "NIFTY"
        and instrument["instrumentType"] == "OPTIDX"
        and instrument["optionType"] in {"CE", "PE"}
    ]

    if not nifty_opts:
        return {}

    today = today_date_str()
    expiries_iso = sorted({parse_expiry(item["expiry"]) for item in nifty_opts if parse_expiry(item["expiry"])})
    future_expiries = [expiry for expiry in expiries_iso if expiry >= today]
    nearest_expiry_iso = future_expiries[0] if future_expiries else expiries_iso[-1]
    expiry_opts = [item for item in nifty_opts if parse_expiry(item["expiry"]) == nearest_expiry_iso]
    strike_set = {float(strike) for strike in target_strikes} if target_strikes else None

    token_map: dict[float, dict[str, Any]] = {}
    for option in expiry_opts:
        if strike_set and option["strike"] not in strike_set:
            continue

        key = option["strike"]
        entry = token_map.setdefault(
            key,
            {
                "ceToken": None,
                "peToken": None,
                "ceSymbol": "",
                "peSymbol": "",
                "expiry": option["expiry"],
                "ceClose": 0,
                "peClose": 0,
            },
        )

        if option["optionType"] == "CE":
            entry["ceToken"] = option["token"]
            entry["ceSymbol"] = option["tradingsymbol"]
            entry["ceClose"] = option["closePrice"]
        elif option["optionType"] == "PE":
            entry["peToken"] = option["token"]
            entry["peSymbol"] = option["tradingsymbol"]
            entry["peClose"] = option["closePrice"]

    return token_map


async def fetch_ltp(tokens: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    if not tokens:
        return {}

    batch_size = 10
    result: dict[str, dict[str, float]] = {}

    for index in range(0, len(tokens), batch_size):
        batch = tokens[index : index + batch_size]
        url = f"{HDFC_BASE_URL}/fetch-ltp?{urlencode({'api_key': HDFC_API_KEY})}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.put(url, headers=hdfc_headers(), json={"data": batch})

        if response.status_code >= 400:
            handle_hdfc_auth_error(response.status_code, "fetch-ltp")
            print(f"fetch-ltp failed: status={response.status_code}, response={response.text[:500]}")
            raise RuntimeError(f"fetch-ltp {response.status_code}: {response.text}")

        payload = response.json()
        for item in payload.get("data") or []:
            result[str(item.get("token"))] = {
                "ltp": item.get("ltp") or 0,
                "prevClose": item.get("prev_close") or 0,
            }

    return result


async def fetch_candle(
    symbol: str,
    exchange: str,
    series_type: str = "EQ",
    chart_type: str = "MINUTE",
    start: str | None = None,
    end: str | None = None,
) -> list[dict[str, Any]]:
    if start and end:
        return await _fetch_candle_once(symbol, exchange, series_type, chart_type, start, end)

    today = datetime.now(UTC)
    for back in range(6):
        day = today - timedelta(days=back)
        if day.weekday() >= 5:
            continue
        date_str = day.date().isoformat()
        results = await _fetch_candle_once(symbol, exchange, series_type, chart_type, date_str, date_str)
        if results:
            return results
    return []


async def _fetch_candle_once(
    symbol: str,
    exchange: str,
    series_type: str,
    chart_type: str,
    start: str,
    end: str,
) -> list[dict[str, Any]]:
    params = urlencode(
        {
            "api_key": HDFC_API_KEY,
            "symbol": symbol,
            "exchange": exchange,
            "chartType": chart_type,
            "seriesType": series_type,
            "start": start,
            "end": end,
        }
    )
    base_url = HDFC_BASE_URL.replace("/oapi/v1", "")
    url = f"{base_url}/oapi/charts-api/charts/v1/fetch-candle?{params}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, headers={"Authorization": get_access_token() or "", "User-Agent": USER_AGENT})

    if response.status_code >= 400:
        handle_hdfc_auth_error(response.status_code, "fetch-candle")
        print(f"fetch-candle failed: status={response.status_code}, response={response.text[:500]}")
        raise RuntimeError(f"fetch-candle {response.status_code}: {response.text}")

    payload = response.json()
    results = payload.get("data", {}).get("results") or []
    candles: list[dict[str, Any]] = []
    for row in results:
        if not isinstance(row, list | tuple) or len(row) < 7:
            continue
        candles.append(
            {
                "open": row[0],
                "high": row[1],
                "low": row[2],
                "close": row[3],
                "volume": row[4],
                "date": row[6],
            }
        )
    return candles


async def fetch_nifty_option_chain(
    spot_price: float | None,
    range_strikes: int = 4,
    center_strike: float | None = None,
) -> dict[str, Any]:
    all_tokens = await get_nifty_option_tokens()
    if not all_tokens:
        raise RuntimeError("No NIFTY option tokens found in security master")

    all_strikes = sorted(strike for strike in all_tokens.keys() if strike > 0)
    if not all_strikes:
        raise RuntimeError("No valid strikes found")

    if center_strike and _is_finite(center_strike):
        atm_strike = min(all_strikes, key=lambda strike: abs(strike - center_strike))
    elif spot_price and _is_finite(spot_price):
        atm_strike = min(all_strikes, key=lambda strike: abs(strike - spot_price))
    else:
        atm_strike = all_strikes[len(all_strikes) // 2]

    atm_index = all_strikes.index(atm_strike)
    start = max(0, atm_index - range_strikes)
    end = min(len(all_strikes) - 1, atm_index + range_strikes)
    selected_strikes = all_strikes[start : end + 1]

    ltp_tokens: list[dict[str, str]] = []
    token_to_strike: dict[str, dict[str, Any]] = {}
    for strike in selected_strikes:
        info = all_tokens.get(strike) or {}
        if info.get("ceToken"):
            ltp_tokens.append({"exchange": "NFO", "token": str(info["ceToken"])})
            token_to_strike[str(info["ceToken"])] = {"strike": strike, "type": "CE"}
        if info.get("peToken"):
            ltp_tokens.append({"exchange": "NFO", "token": str(info["peToken"])})
            token_to_strike[str(info["peToken"])] = {"strike": strike, "type": "PE"}

    ltp_map = await fetch_ltp(ltp_tokens)

    candle_data_map: dict[str, dict[str, Any]] = {}
    candle_symbols: list[dict[str, str]] = []
    for strike in selected_strikes:
        info = all_tokens.get(strike) or {}
        if info.get("ceSymbol"):
            candle_symbols.append({"symbol": info["ceSymbol"], "key": info["ceSymbol"]})
        if info.get("peSymbol"):
            candle_symbols.append({"symbol": info["peSymbol"], "key": info["peSymbol"]})

    candle_batch = 2
    for index in range(0, len(candle_symbols), candle_batch):
        batch = candle_symbols[index : index + candle_batch]
        await asyncio.gather(
            *[
                _fetch_and_store_candle(symbol_info["symbol"], symbol_info["key"], candle_data_map)
                for symbol_info in batch
            ]
        )
        if index + candle_batch < len(candle_symbols):
            await asyncio.sleep(0.3)

    data: list[dict[str, Any]] = []
    for strike in selected_strikes:
        info = all_tokens.get(strike) or {}
        ce_ltp = ltp_map.get(str(info.get("ceToken")))
        pe_ltp = ltp_map.get(str(info.get("peToken")))
        ce_candle = candle_data_map.get(info.get("ceSymbol", ""), {})
        pe_candle = candle_data_map.get(info.get("peSymbol", ""), {})

        ce_prev_close = (ce_ltp or {}).get("prevClose") or info.get("ceClose") or 0
        pe_prev_close = (pe_ltp or {}).get("prevClose") or info.get("peClose") or 0
        ce_open = ce_candle.get("open") or ce_prev_close
        pe_open = pe_candle.get("open") or pe_prev_close

        ce_last = (ce_ltp or {}).get("ltp", 0)
        pe_last = (pe_ltp or {}).get("ltp", 0)
        data.append(
            {
                "strikePrice": strike,
                "expiryDate": info.get("expiry") or "",
                "CE": {
                    "strikePrice": strike,
                    "lastPrice": ce_last,
                    "previousClose": ce_prev_close,
                    "openPrice": ce_open,
                    "change": ce_last - ce_prev_close if ce_ltp else 0,
                    "impliedVolatility": 0,
                    "totalTradedVolume": ce_candle.get("volume") or 0,
                    "token": info.get("ceToken"),
                    "tradingsymbol": info.get("ceSymbol"),
                },
                "PE": {
                    "strikePrice": strike,
                    "lastPrice": pe_last,
                    "previousClose": pe_prev_close,
                    "openPrice": pe_open,
                    "change": pe_last - pe_prev_close if pe_ltp else 0,
                    "impliedVolatility": 0,
                    "totalTradedVolume": pe_candle.get("volume") or 0,
                    "token": info.get("peToken"),
                    "tradingsymbol": info.get("peSymbol"),
                },
            }
        )

    expiry = data[0].get("expiryDate") if data else ""
    return {
        "spotPrice": spot_price or None,
        "underlyingValue": spot_price or None,
        "expiryDates": [expiry] if expiry else [],
        "strikePrices": selected_strikes,
        "data": data,
        "candleArrays": candle_data_map,
    }


async def _fetch_and_store_candle(symbol: str, key: str, candle_data_map: dict[str, dict[str, Any]]) -> None:
    try:
        candles = await fetch_candle(symbol, "NFO", "XX", "MINUTE5")
        if candles:
            total_volume = sum(candle.get("volume") or 0 for candle in candles)
            candle_data_map[key] = {"open": candles[0].get("open") or 0, "volume": total_volume, "candles": candles}
    except Exception:
        pass


async def fetch_nifty_intraday() -> list[list[float]] | None:
    instruments = await get_security_master()
    now = datetime.now(UTC).date()
    nifty_futs = []
    for instrument in instruments:
        if not (
            instrument["exchange"] == "NFO"
            and str(instrument["tradingsymbol"]).startswith("NIFTY")
            and instrument["instrumentType"] == "FUTIDX"
        ):
            continue
        expiry = _parse_iso_date(parse_expiry(instrument["expiry"]))
        if expiry and expiry >= now:
            nifty_futs.append({**instrument, "expiryDate": expiry})

    nifty_futs.sort(key=lambda item: item["expiryDate"])
    if not nifty_futs:
        return None

    fut_symbol = nifty_futs[0]["tradingsymbol"]
    candles = await fetch_candle(fut_symbol, "NFO", "XX", "MINUTE")
    if not candles:
        return None

    series: list[list[float]] = []
    for candle in candles:
        timestamp = _date_to_ms(candle.get("date"))
        close = _to_float(candle.get("close"))
        if timestamp is not None and close is not None:
            series.append([timestamp, close])
    return series or None


def _to_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if _is_finite(numeric) else None


def _is_finite(value: Any) -> bool:
    try:
        return float(value) not in {float("inf"), float("-inf")} and float(value) == float(value)
    except (TypeError, ValueError):
        return False


def _parse_iso_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def _date_to_ms(value: Any) -> float | None:
    if not value:
        return None

    date_text = str(value).strip()
    date_text = re.sub(r"^(\d{2})-(\d{2})-(\d{4})", r"\3-\2-\1", date_text)
    try:
        parsed = datetime.fromisoformat(date_text.replace(" ", "T"))
    except Exception:
        return time.time() * 1000

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.timestamp() * 1000
