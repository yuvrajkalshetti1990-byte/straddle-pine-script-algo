import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"

load_dotenv(BACKEND_ROOT / ".env")

PORT = int(os.getenv("PORT", "8000"))
HDFC_BASE_URL = "https://developer.hdfcsky.com/oapi/v1"
HDFC_API_KEY = os.getenv("HDFC_API_KEY", "")
HDFC_API_SECRET = os.getenv("HDFC_API_SECRET", "")
HDFC_ACCESS_TOKEN = os.getenv("HDFC_ACCESS_TOKEN") or None
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://cbamoon.com",
    "https://www.cbamoon.com",
]

# Fyers Configuration
FYERS_CLIENT_ID = os.getenv("FYERS_CLIENT_ID", "")
FYERS_SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "")
FYERS_REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI", "http://127.0.0.1:8000/auth/fyers/callback")

# Zerodha Configuration
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", "")
ZERODHA_REDIRECT_URI = os.getenv("ZERODHA_REDIRECT_URI", "http://127.0.0.1:8000/auth/zerodha/callback")
def update_env_file(updates: dict[str, str]):
    """Update .env file with new values and reload them."""
    env_path = BACKEND_ROOT / ".env"
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    for key, value in updates.items():
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")
            
    with open(env_path, "w") as f:
        f.writelines(lines)
        
    # Reload variables into global scope
    global FYERS_CLIENT_ID, FYERS_SECRET_KEY, ZERODHA_API_KEY, ZERODHA_API_SECRET, HDFC_API_KEY, HDFC_API_SECRET
    if "FYERS_CLIENT_ID" in updates: FYERS_CLIENT_ID = updates["FYERS_CLIENT_ID"]
    if "FYERS_SECRET_KEY" in updates: FYERS_SECRET_KEY = updates["FYERS_SECRET_KEY"]
    if "ZERODHA_API_KEY" in updates: ZERODHA_API_KEY = updates["ZERODHA_API_KEY"]
    if "ZERODHA_API_SECRET" in updates: ZERODHA_API_SECRET = updates["ZERODHA_API_SECRET"]
    if "HDFC_API_KEY" in updates: HDFC_API_KEY = updates["HDFC_API_KEY"]
    if "HDFC_API_SECRET" in updates: HDFC_API_SECRET = updates["HDFC_API_SECRET"]
