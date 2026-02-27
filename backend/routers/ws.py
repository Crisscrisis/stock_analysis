"""WebSocket endpoint — real-time price push every 3 seconds."""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services import fetcher
from services.cache import quote_cache

logger = logging.getLogger(__name__)
router = APIRouter()

PUSH_INTERVAL = 3  # seconds


@router.websocket("/ws/price/{symbol}")
async def ws_price(websocket: WebSocket, symbol: str) -> None:
    await websocket.accept()
    try:
        while True:
            # Try cache first
            cached = quote_cache.get(symbol)
            if cached is not None:
                quote = cached
            else:
                try:
                    quote = await fetcher.get_quote(symbol)
                    quote_cache.set(symbol, quote)
                except Exception as exc:
                    logger.warning("WS quote fetch failed for %s: %s", symbol, exc)
                    await websocket.send_text(
                        json.dumps({"error": "Failed to fetch quote", "symbol": symbol})
                    )
                    await asyncio.sleep(PUSH_INTERVAL)
                    continue

            payload = {
                "symbol": quote["symbol"],
                "price": quote["price"],
                "change_pct": quote["change_pct"],
                "timestamp": quote["timestamp"],
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(PUSH_INTERVAL)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for %s", symbol)
