import os
import json
import logging
import re
import asyncio
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fyers_apiv3 import fyersModel

MARKET_TZ = ZoneInfo("Asia/Kolkata")
from app.config import FYERS_CLIENT_ID, FYERS_SECRET_KEY, FYERS_REDIRECT_URI, DATA_DIR

logger = logging.getLogger(__name__)

TOKEN_FILE = DATA_DIR / "fyers-token.json"

_fyers_instance = None
_access_token = None

def load_token():
    global _access_token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "r") as f:
            try:
                data = json.load(f)
                _access_token = data.get("access_token")
                logger.info("Fyers token loaded from disk.")
            except Exception as e:
                logger.error(f"Failed to load Fyers token: {e}")

# Load token on startup
load_token()

def get_fyers_instance():
    global _fyers_instance, _access_token
    if _fyers_instance:
        return _fyers_instance
    
    if not _access_token:
        load_token()
        
    if _access_token:
        try:
            _fyers_instance = fyersModel.FyersModel(
                client_id=FYERS_CLIENT_ID,
                token=_access_token,
                is_async=False,
                log_path=str(DATA_DIR)
            )
            return _fyers_instance
        except Exception as e:
            logger.error(f"Failed to initialize FyersModel: {e}")
            return None
    return None

def save_token(token):
    global _access_token
    _access_token = token
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": token}, f)
    logger.info("Fyers token saved.")

def get_login_url():
    session = fyersModel.SessionModel(
        client_id=FYERS_CLIENT_ID,
        secret_key=FYERS_SECRET_KEY,
        redirect_uri=FYERS_REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )
    return session.generate_authcode()

def handle_callback(auth_code):
    session = fyersModel.SessionModel(
        client_id=FYERS_CLIENT_ID,
        secret_key=FYERS_SECRET_KEY,
        redirect_uri=FYERS_REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )
    session.set_token(auth_code)
    response = session.generate_token()
    
    if response.get("s") == "ok":
        token = response.get("access_token")
        save_token(token)
        return {"status": "success", "message": "Fyers connected!"}
    else:
        logger.error(f"Fyers auth failed: {response}")
        return {"status": "error", "message": response.get("message", "Unknown error")}

def fetch_market_price(symbol: str):
    """Generic fetch for any market symbol (NIFTY, BANKNIFTY, VIX)"""
    fyers = get_fyers_instance()
    if not fyers:
        return None
    
    data = {"symbols": symbol}
    
    try:
        response = fyers.quotes(data)
        if response.get("s") == "ok":
            quotes = response.get("d", [])
            if quotes:
                quote_data = quotes[0]
                quote = quote_data.get("v", {})
                return {
                    "price": quote.get("lp"),
                    "change": quote.get("ch"),
                    "changePercent": quote.get("chp"),
                    "symbol": symbol
                }
    except Exception as e:
        logger.error(f"Fyers fetch error for {symbol}: {e}")
        
    return None

def fetch_nifty_price():
    return fetch_market_price("NSE:NIFTY50-INDEX")

_oc_cache = {}
_oc_cache_expiry = 30 # seconds

def fetch_fyers_option_chain(spot_price, count=5):
    """Fetch option chain with caching"""
    cache_key = f"{spot_price}_{count}"
    now = time.time()
    
    if cache_key in _oc_cache:
        cached_data, timestamp = _oc_cache[cache_key]
        if now - timestamp < _oc_cache_expiry:
            return cached_data
            
    fyers = get_fyers_instance()
    if not fyers:
        return None
    
    # Fyers expects "NSE:NIFTY50-INDEX" or "NSE:NIFTY24O0325850CE"
    data = {
        "symbol": "NSE:NIFTY50-INDEX",
        "strikecount": count
    }
    
    try:
        response = fyers.optionchain(data)
        if response.get("s") == "ok":
            oc_data = response.get("data", {}) # Fyers V3 uses 'data'
            options = oc_data.get("optionsChain", [])
            
            # Reformat to our standard structure (group CE/PE by strike)
            strikes_map = {}
            expiry_date = "N/A"
            underlying_lp = oc_data.get("underlying_lp")
            
            for opt in options:
                symbol = opt.get("symbol", "")
                strike = opt.get("strike_price")
                
                # Extract spot price from the index item if we don't have it
                if (strike is None or strike < 0) and "INDEX" in symbol:
                    if not underlying_lp:
                        underlying_lp = opt.get("ltp")
                    continue
                
                if strike is None or strike < 0:
                    continue
                
                if strike not in strikes_map:
                    strikes_map[strike] = {"strikePrice": strike, "CE": {}, "PE": {}}
                
                otype = opt.get("option_type")
                
                # Extract expiry date if not already found
                if expiry_date == "N/A" and symbol:
                    match_w = re.search(r"NIFTY(\d{2})([1-9|O|N|D])(\d{2})", symbol)
                    match_m = re.search(r"NIFTY(\d{2})([A-Z]{3})", symbol)
                    
                    months_map = {
                        "1":"JAN","2":"FEB","3":"MAR","4":"APR","5":"MAY","6":"JUN","7":"JUL","8":"AUG","9":"SEP","O":"OCT","N":"NOV","D":"DEC",
                        "JAN":"JAN","FEB":"FEB","MAR":"MAR","APR":"APR","MAY":"MAY","JUN":"JUN","JUL":"JUL","AUG":"AUG","SEP":"SEP","OCT":"OCT","NOV":"NOV","DEC":"DEC"
                    }
                    
                    if match_w:
                        y, m, d = match_w.groups()
                        expiry_date = f"{d}-{months_map.get(m, m)}-20{y}"
                    elif match_m:
                        y, m = match_m.groups()
                        expiry_date = f"30-{months_map.get(m, m)}-20{y}"

                # Fill standard fields
                standard_opt = {
                    "lastPrice": opt.get("ltp"),
                    "openPrice": opt.get("open"),
                    "totalTradedVolume": opt.get("volume"),
                    "impliedVolatility": opt.get("iv"),
                    "symbol": symbol
                }
                
                if otype == "CE":
                    strikes_map[strike]["CE"] = standard_opt
                elif otype == "PE":
                    strikes_map[strike]["PE"] = standard_opt

            formatted_data = []
            strike_prices = sorted(strikes_map.keys())
            for s in strike_prices:
                row = strikes_map[s]
                row["expiryDate"] = expiry_date
                formatted_data.append(row)
                
            result = {
                "underlyingValue": underlying_lp or spot_price,
                "strikePrices": strike_prices,
                "expiryDates": [expiry_date] if expiry_date != "N/A" else [],
                "data": formatted_data
            }
            _oc_cache[cache_key] = (result, time.time())
            return result
        else:
            logger.error(f"Fyers optionchain failed: {response}")
    except Exception as e:
        logger.error(f"Fyers optionchain error: {e}")
        
    return None

_history_cache = {}
_history_cache_expiry = 300 # seconds (5 minutes)

async def fetch_symbol_history(symbol, resolution="1", range_from=None, range_to=None):
    """Fetch historical data for a symbol with basic caching"""
    cache_key = f"{symbol}_{resolution}_{range_from}_{range_to}"
    now = time.time()
    
    if cache_key in _history_cache:
        cached_data, timestamp = _history_cache[cache_key]
        if now - timestamp < _history_cache_expiry:
            return cached_data
            
    fyers = get_fyers_instance()
    if not fyers:
        return []
        
    if not range_from:
        # Fetch since yesterday to ensure 100+ candles for warm-up
        to_dt = datetime.now()
        from_dt = to_dt - timedelta(days=2) # 2 days to be safe for weekends
        range_from = from_dt.strftime("%Y-%m-%d")
        range_to = to_dt.strftime("%Y-%m-%d")
        
    data = {
        "symbol": symbol,
        "resolution": resolution,
        "date_format": "1",
        "range_from": range_from,
        "range_to": range_to,
        "cont_flag": "1"
    }
    
    logger.info(f"Fetching history for {symbol}: {data}")
    try:
        # Run synchronous SDK call in a thread to avoid blocking event loop
        response = await asyncio.to_thread(fyers.history, data)
        if response.get("s") == "ok":
            raw_candles = response.get("candles", [])
            logger.info(f"Fyers history success for {symbol}: {len(raw_candles)} raw candles")
            candles = []
            for c in raw_candles:
                # Fyers format: [timestamp, open, high, low, close, volume]
                if len(c) >= 6:
                    dt = datetime.fromtimestamp(c[0], MARKET_TZ)
                    candles.append({
                        "date": dt.isoformat(),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": int(c[5])
                    })
            _history_cache[cache_key] = (candles, time.time())
            return candles
        else:
            logger.warning(f"Fyers history failed for {symbol}: {response}")
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        
    return []

_quotes_cache = {}
_quotes_cache_expiry = 5 # seconds

def fetch_positions():
    """Fetch live positions from Fyers."""
    fyers = get_fyers_instance()
    if not fyers:
        return None
    
    try:
        response = fyers.positions()
        if response and response.get("s") == "ok":
            return response.get("netPositions", [])
        else:
            logger.error(f"Fyers positions failed: {response}")
    except Exception as e:
        logger.error(f"Fyers positions error: {e}")
        
    return None

def fetch_quotes(symbols):
    """Fetch quotes with a short cache to avoid 429s"""
    cache_key = ",".join(sorted(symbols))
    now = time.time()
    
    if cache_key in _quotes_cache:
        cached_data, timestamp = _quotes_cache[cache_key]
        if now - timestamp < _quotes_cache_expiry:
            return cached_data
            
    fyers = get_fyers_instance()
    if not fyers:
        return None
    
    data = {"symbols": ",".join(symbols)}
    response = fyers.quotes(data)
    
    if response and response.get("s") == "ok":
        _quotes_cache[cache_key] = (response, time.time())
        
    return response
