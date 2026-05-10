import os
import json
import logging
from kiteconnect import KiteConnect
from app.config import ZERODHA_API_KEY, ZERODHA_API_SECRET, ZERODHA_REDIRECT_URI, DATA_DIR

logger = logging.getLogger(__name__)

TOKEN_FILE = DATA_DIR / "zerodha-token.json"

_kite_instance = None
_access_token = None

def get_kite_instance():
    global _kite_instance, _access_token
    if _kite_instance:
        return _kite_instance
    
    if not _access_token:
        load_token()
        
    if _access_token:
        _kite_instance = KiteConnect(api_key=ZERODHA_API_KEY)
        _kite_instance.set_access_token(_access_token)
        return _kite_instance
    return None

def save_token(token):
    global _access_token
    _access_token = token
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": token}, f)
    logger.info("Zerodha token saved.")

def load_token():
    global _access_token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            _access_token = data.get("access_token")
            logger.info("Zerodha token loaded.")

def get_login_url():
    kite = KiteConnect(api_key=ZERODHA_API_KEY)
    return kite.login_url()

def handle_callback(request_token):
    kite = KiteConnect(api_key=ZERODHA_API_KEY)
    try:
        data = kite.generate_session(request_token, api_secret=ZERODHA_API_SECRET)
        token = data["access_token"]
        save_token(token)
        return {"status": "success", "message": "Zerodha connected!"}
    except Exception as e:
        logger.error(f"Zerodha auth failed: {e}")
        return {"status": "error", "message": str(e)}

def fetch_market_price(symbol: str):
    kite = get_kite_instance()
    if not kite:
        return None
    
    try:
        quote = kite.quote([symbol])
        data = quote.get(symbol, {})
        return {
            "price": data.get("last_price"),
            "change": data.get("ohlc", {}).get("close", 0) - data.get("last_price", 0),
            "changePercent": data.get("change"),
            "symbol": symbol
        }
    except Exception:
        return None

def fetch_nifty_price():
    return fetch_market_price("NSE:NIFTY 50")
