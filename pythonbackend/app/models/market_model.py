import json
import logging
import time
from typing import Any

import httpx

from app.config import USER_AGENT

logger = logging.getLogger(__name__)

nse_cookies = ""
cookie_timestamp = 0.0
COOKIE_TTL = 60_000


async def get_nse_cookies() -> str:
    global cookie_timestamp, nse_cookies

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(
            "https://www.nseindia.com",
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
    nse_cookies = "; ".join(f"{key}={value}" for key, value in response.cookies.items())
    cookie_timestamp = time.time() * 1000
    return nse_cookies


async def fetch_market_index_data(index_name: str) -> dict[str, Any] | None:
    """Generic NSE scraper for any index (NIFTY 50, NIFTY BANK, INDIA VIX)"""
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name.replace(' ', '%20')}"
    try:
        response = await nse_fetch(url, "https://www.nseindia.com/market-data/live-equity-market")
        data = response.json()
        rows = data.get("data")
        return rows[0] if isinstance(rows, list) and rows else None
    except Exception:
        return None

async def fetch_nifty_data() -> dict[str, Any] | None:
    return await fetch_market_index_data("NIFTY 50")


async def nse_fetch(url: str, referer: str) -> httpx.Response:
    global nse_cookies

    if not nse_cookies or (time.time() * 1000) - cookie_timestamp > COOKIE_TTL:
        await get_nse_cookies()

    async def do_fetch() -> httpx.Response:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            return await client.get(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Cookie": nse_cookies,
                    "Accept": "application/json",
                    "Referer": referer,
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )

    response = await do_fetch()
    if response.status_code in {401, 403}:
        await get_nse_cookies()
        response = await do_fetch()
    return response


async def fetch_nifty_chain() -> dict[str, Any] | None:
    response = await nse_fetch(
        "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
        "https://www.nseindia.com/option-chain",
    )
    try:
        data = response.json()
        return data.get("records")
    except (json.JSONDecodeError, AttributeError, Exception) as e:
        logger.error(f"Failed to parse Nifty chain JSON: {e}")
        return None


async def fetch_nifty_intraday() -> list[list[float]] | None:
    response = await nse_fetch(
        "https://www.nseindia.com/api/chart-databyindex?index=NIFTY%2050",
        "https://www.nseindia.com/market-data/live-equity-market",
    )
    try:
        data = response.json()
    except (json.JSONDecodeError, AttributeError, Exception) as e:
        logger.error(f"Failed to parse Nifty intraday JSON: {e}")
        return None
    raw_series = data.get("grapthData") or data.get("grappiData") or data.get("graphData")
    if not isinstance(raw_series, list):
        return None

    normalized: list[list[float]] = []
    for point in raw_series:
        if isinstance(point, (list, tuple)) and len(point) >= 2:
            ts = _to_float(point[0])
            price = _to_float(point[1])
        elif isinstance(point, dict):
            ts = _to_float(point.get("x") or point.get("time") or point.get("timestamp"))
            price = _to_float(point.get("y") or point.get("price") or point.get("close") or point.get("value"))
        else:
            continue

        if ts is not None and price is not None:
            normalized.append([ts, price])

    return normalized or None


def _to_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric == numeric and numeric not in {float("inf"), float("-inf")} else None
