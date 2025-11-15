from fastapi import APIRouter, HTTPException, Query
import httpx
from ..config import settings

router = APIRouter(prefix="/api/v1/bot", tags=["bot-proxy"])

def _bot_url(method: str) -> str:
    base = settings.max_api_base.rstrip("/")
    token = settings.max_bot_token.strip()
    if not token:
        raise HTTPException(500, "MAX bot token is not configured")
    return f"{base}/bot{token}/{method}"

@router.get("/updates")
async def get_updates(offset: int | None = Query(None), timeout: int = Query(25, ge=1, le=60)):
    params = {}
    if offset is not None:
        params["offset"] = offset
    params["timeout"] = timeout
    url = _bot_url("getUpdates")
    async with httpx.AsyncClient(timeout=timeout + 5) as cl:
        r = await cl.get(url, params=params)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)
        return r.json()

@router.post("/send")
async def send_message(payload: dict):
    url = _bot_url("sendMessage")
    async with httpx.AsyncClient(timeout=10) as cl:
        r = await cl.post(url, json=payload)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)
        return r.json()
