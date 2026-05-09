from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import FRONTEND_URL, HDFC_API_KEY, HDFC_BASE_URL
from app.models.auth_model import (
    authorize,
    exchange_token,
    get_token_id,
    get_token_id_value,
    is_connected,
    login_validate,
    set_access_token,
    validate_2fa,
    validate_otp,
)


from app.models import auth_model, fyers_model, zerodha_model


router = APIRouter()


@router.get("/fyers/login")
async def fyers_login():
    url = fyers_model.get_login_url()
    return RedirectResponse(url)


@router.get("/fyers/callback")
async def fyers_callback(auth_code: str | None = Query(None), code: str | None = Query(None)):
    code_to_use = auth_code or code
    if not code_to_use:
        return JSONResponse({"status": "error", "message": "No code provided"}, status_code=400)
    res = fyers_model.handle_callback(code_to_use)
    if res["status"] == "success":
        return RedirectResponse(FRONTEND_URL)
    return JSONResponse(res, status_code=400)


@router.get("/zerodha/login")
async def zerodha_login():
    url = zerodha_model.get_login_url()
    return RedirectResponse(url)


@router.get("/zerodha/callback")
async def zerodha_callback(request_token: str | None = Query(None), code: str | None = Query(None)):
    token_to_use = request_token or code
    if not token_to_use:
        return JSONResponse({"status": "error", "message": "No code provided"}, status_code=400)
    res = zerodha_model.handle_callback(token_to_use)
    if res["status"] == "success":
        return RedirectResponse(FRONTEND_URL)
    return JSONResponse(res, status_code=400)


@router.get("/login")
async def login():
    login_url = f"{HDFC_BASE_URL}/login?{urlencode({'api_key': HDFC_API_KEY})}"
    return RedirectResponse(login_url)


@router.get("/callback")
async def callback(
    request_token: str | None = Query(default=None),
    requestToken: str | None = Query(default=None),
):
    final_request_token = request_token or requestToken
    if not final_request_token:
        return JSONResponse({"status": "error", "message": "Missing request_token"}, status_code=400)

    try:
        data = await exchange_token(final_request_token)
        if data.get("accessToken"):
            set_access_token(data["accessToken"])
            print("HDFC Sky access token obtained successfully")
            return RedirectResponse(FRONTEND_URL)

        print(f"Failed to get access token: {data}")
        return JSONResponse(
            {"status": "error", "message": "Failed to get access token", "data": data},
            status_code=401,
        )
    except Exception as err:
        print(f"Auth callback error: {err}")
        return JSONResponse({"status": "error", "message": str(err)}, status_code=500)


@router.get("/exchange")
async def exchange(token: str | None = Query(default=None)):
    if not token:
        return JSONResponse(
            {
                "status": "error",
                "message": "Usage: /auth/exchange?token=YOUR_REQUEST_TOKEN",
                "hint": "Copy the requestToken value from the cbamoon.com redirect URL",
            },
            status_code=400,
        )

    try:
        data = await exchange_token(token)
        if data.get("accessToken"):
            set_access_token(data["accessToken"])
            print("HDFC Sky access token obtained via manual exchange")
            return {"status": "success", "message": "Connected to HDFC Sky!", "connected": True}

        return JSONResponse({"status": "error", "message": "Token exchange failed", "data": data}, status_code=401)
    except Exception as err:
        return JSONResponse({"status": "error", "message": str(err)}, status_code=500)


@router.post("/api/init")
async def api_init():
    try:
        data = await get_token_id()
        return {"status": "success", "data": data}
    except Exception as err:
        return JSONResponse({"status": "error", "message": str(err)}, status_code=500)


@router.post("/api/login")
async def api_login(payload: dict[str, Any] | None = Body(default=None)):
    try:
        username = (payload or {}).get("username")
        if not username:
            return JSONResponse({"status": "error", "message": "username required"}, status_code=400)
        data = await login_validate(username)
        return {"status": "success", "data": data}
    except Exception as err:
        return JSONResponse({"status": "error", "message": str(err)}, status_code=500)


@router.post("/api/otp")
async def api_otp(payload: dict[str, Any] | None = Body(default=None)):
    try:
        otp = (payload or {}).get("otp")
        if not otp:
            return JSONResponse({"status": "error", "message": "otp required"}, status_code=400)
        data = await validate_otp(otp)
        return {"status": "success", "data": data}
    except Exception as err:
        return JSONResponse({"status": "error", "message": str(err)}, status_code=500)


@router.post("/api/pin")
async def api_pin(payload: dict[str, Any] | None = Body(default=None)):
    try:
        pin = (payload or {}).get("pin")
        if not pin:
            return JSONResponse({"status": "error", "message": "pin required"}, status_code=400)

        data = await validate_2fa(pin)
        if data.get("requestToken"):
            auth_data = await authorize(data["requestToken"])
            final_token = auth_data.get("requestToken") or data["requestToken"]
            token_data = await exchange_token(final_token)

            if token_data.get("accessToken"):
                set_access_token(token_data["accessToken"])
                print("HDFC Sky connected via API login flow")
                return {"status": "success", "connected": True, "message": "Connected to HDFC Sky!"}
            return {"status": "partial", "data": token_data, "message": "Token exchange step - check data"}

        return {"status": "success", "data": data}
    except Exception as err:
        return JSONResponse({"status": "error", "message": str(err)}, status_code=500)


async def status_payload():
    connected = auth_model.is_connected() or (fyers_model._access_token is not None) or (zerodha_model._access_token is not None)
    
    broker = "HDFC Sky"
    if fyers_model._access_token:
        broker = "Fyers"
    elif zerodha_model._access_token:
        broker = "Zerodha"
        
    return {
        "status": "success",
        "connected": connected,
        "broker": broker if connected else None,
        "fyersConnected": fyers_model._access_token is not None,
        "zerodhaConnected": zerodha_model._access_token is not None,
        "hdfcConnected": auth_model.is_connected(),
        "tokenId": "active" if auth_model.get_token_id_value() else None,
    }


@router.get("/status")
async def status():
    return await status_payload()


@router.post("/credentials")
async def update_credentials(payload: dict[str, Any] = Body(...)):
    broker = payload.get("brokerName")
    api_key = payload.get("brokerApiKey", "")
    api_secret = payload.get("brokerSecret", "")
    
    updates = {}
    if broker == "Fyers":
        updates = {
            "FYERS_CLIENT_ID": api_key,
            "FYERS_SECRET_KEY": api_secret
        }
    elif broker == "Zerodha":
        updates = {
            "ZERODHA_API_KEY": api_key,
            "ZERODHA_API_SECRET": api_secret
        }
    elif broker == "HDFC Sky":
        updates = {
            "HDFC_API_KEY": api_key,
            "HDFC_API_SECRET": api_secret
        }
        
    if updates:
        from app.config import update_env_file
        update_env_file(updates)
        return {"status": "success", "message": f"{broker} credentials updated!"}
    
    return JSONResponse({"status": "error", "message": "Invalid broker name"}, status_code=400)
