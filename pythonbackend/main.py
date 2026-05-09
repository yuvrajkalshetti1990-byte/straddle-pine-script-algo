import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from app.config import CORS_ORIGINS, PORT
from app.models.auth_model import is_connected, load_persisted_token
from app.models import fyers_model, zerodha_model
import logging
from app.routes.api_routes import router as api_router
from app.routes.auth_routes import router as auth_router
from app.routes.strategy_routes import router as strategy_router
from app.models.indicator_model import calc_rsi, calc_roc, calc_dmi_adx, calc_chop
from db.database import init_db
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import Request


logger = logging.getLogger(__name__)

load_persisted_token()
fyers_model.load_token()
zerodha_model.load_token()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database on startup
    await init_db()
    yield
    # Shutdown logic can go here (e.g. stop_runner)

app = FastAPI(title="Trading Platform Python Backend", lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal Server Error", "detail": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(api_router, prefix="/api/v1")
app.include_router(strategy_router)


@app.get("/")
async def health_check():
    connected = is_connected() or (fyers_model._access_token is not None) or (zerodha_model._access_token is not None)
    broker = "HDFC Sky"
    if fyers_model._access_token:
        broker = "Fyers"
    elif zerodha_model._access_token:
        broker = "Zerodha"

    return {
        "message": "Python backend running",
        "status": "active",
        "broker": broker if connected else None,
        "connected": connected,
        "fyersConnected": fyers_model._access_token is not None,
        "zerodhaConnected": zerodha_model._access_token is not None,
        "hdfcConnected": is_connected(),
    }


@app.get("/indicators")
async def get_indicators():
    # Example data structure for market prices
    data = {
        "close": [357.65, 358.00, 357.75, 358.50, 359.00, 358.75, 358.25, 357.50, 357.00, 356.50],
        "high": [358.00, 358.50, 358.25, 359.00, 359.50, 359.25, 358.75, 358.00, 357.50, 357.00],
        "low": [357.00, 357.50, 357.25, 358.00, 358.50, 358.25, 357.75, 357.00, 356.50, 356.00],
        "volume": [1000, 1200, 1100, 1300, 1250, 1150, 1050, 1000, 950, 900]
    }

    df = pd.DataFrame(data)

    rsi = calc_rsi(df)
    roc = calc_roc(df)
    plus_di, minus_di, adx = calc_dmi_adx(df)
    chop = calc_chop(df)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)

    return {
        "RSI": rsi.iloc[-1],
        "ROC": roc.iloc[-1],
        "+DI": plus_di.iloc[-1],
        "-DI": minus_di.iloc[-1],
        "DX": dx.iloc[-1],
        "ADX": adx.iloc[-1],
        "CHOP": chop.iloc[-1]
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT))

