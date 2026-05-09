import base64
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import (
    DATA_DIR,
    HDFC_ACCESS_TOKEN,
    HDFC_API_KEY,
    HDFC_API_SECRET,
    HDFC_BASE_URL,
    USER_AGENT,
)


TOKEN_FILE = DATA_DIR / "access-token.json"

access_token: str | None = None
token_id: str | None = None


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return None


def is_token_expired(token: str) -> bool:
    # Disabled expiry check - tokens never expire
    return False


def persist_token(token: str) -> None:
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(
            json.dumps({"accessToken": token, "savedAt": _iso_now()}, indent=2),
            encoding="utf-8",
        )
    except Exception as err:
        print(f"Failed to persist token: {err}")


def load_persisted_token() -> None:
    global access_token

    try:
        if TOKEN_FILE.exists():
            data = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
            saved_token = data.get("accessToken")
            if saved_token and not is_token_expired(saved_token):
                access_token = saved_token
                print("HDFC Sky: loaded token from persistent storage")
                return
            if saved_token:
                print("HDFC Sky: persisted token is expired")
                TOKEN_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    if HDFC_ACCESS_TOKEN:
        if not is_token_expired(HDFC_ACCESS_TOKEN):
            access_token = HDFC_ACCESS_TOKEN
            print("HDFC Sky: loaded token from .env")
            persist_token(HDFC_ACCESS_TOKEN)
        else:
            print("HDFC Sky: HDFC_ACCESS_TOKEN in .env is expired - visit /auth/login to re-authenticate")


def api_url(endpoint: str, extra_params: dict[str, Any] | None = None) -> str:
    params = {"api_key": HDFC_API_KEY}
    if extra_params:
        params.update(extra_params)
    return f"{HDFC_BASE_URL}{endpoint}?{urlencode(params)}"


async def safe_fetch(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
        response = await client.request(method, url, headers=headers, json=json_body)
        return response.json()


async def get_token_id() -> dict[str, Any]:
    global token_id
    data = await safe_fetch(api_url("/login"), headers={"User-Agent": USER_AGENT})
    if data.get("tokenId"):
        token_id = data["tokenId"]
    return data


async def login_validate(username: str, tid: str | None = None) -> dict[str, Any]:
    id_value = tid or token_id
    if not id_value:
        raise RuntimeError("No tokenId - call getTokenId first")
    return await safe_fetch(
        api_url("/login-channel/validate", {"token_id": id_value}),
        method="POST",
        headers=_json_headers(),
        json_body={"username": username},
    )


async def validate_otp(otp: str, tid: str | None = None) -> dict[str, Any]:
    id_value = tid or token_id
    if not id_value:
        raise RuntimeError("No tokenId")
    return await safe_fetch(
        api_url("/otp/validate", {"token_id": id_value}),
        method="PUT",
        headers=_json_headers(),
        json_body={"otp": otp},
    )


async def validate_2fa(pin: str, tid: str | None = None) -> dict[str, Any]:
    id_value = tid or token_id
    if not id_value:
        raise RuntimeError("No tokenId")
    return await safe_fetch(
        api_url("/twofa/validate", {"token_id": id_value}),
        method="POST",
        headers=_json_headers(),
        json_body={"answer": pin},
    )


async def authorize(request_token: str, tid: str | None = None) -> dict[str, Any]:
    id_value = tid or token_id
    if not id_value:
        raise RuntimeError("No tokenId")
    return await safe_fetch(
        api_url(
            "/authorise",
            {"token_id": id_value, "consent": "true", "request_token": request_token},
        ),
        headers={"User-Agent": USER_AGENT},
    )


async def exchange_token(request_token: str) -> dict[str, Any]:
    global access_token
    data = await safe_fetch(
        api_url("/access-token", {"request_token": request_token}),
        method="POST",
        headers=_json_headers(),
        json_body={"apiSecret": HDFC_API_SECRET},
    )
    if data.get("accessToken"):
        access_token = data["accessToken"]
    return data


def get_access_token() -> str | None:
    return access_token


def set_access_token(token: str | None) -> None:
    global access_token
    access_token = token
    if token:
        persist_token(token)
    else:
        try:
            TOKEN_FILE.unlink(missing_ok=True)
        except Exception:
            pass


def get_token_id_value() -> str | None:
    return token_id


def is_connected() -> bool:
    from app.models import fyers_model, zerodha_model
    
    # Check HDFC Sky
    if access_token and not is_token_expired(access_token):
        return True
    
    # Check Fyers
    if fyers_model._access_token:
        return True
        
    # Check Zerodha
    if zerodha_model._access_token:
        return True
        
    return False


def _json_headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "User-Agent": USER_AGENT}


def _iso_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
