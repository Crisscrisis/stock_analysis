from fastapi import APIRouter

from schemas.stock import FundamentalsResponse
from services import fetcher

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("/{symbol}")
async def get_fundamentals(symbol: str) -> dict:
    try:
        data = await fetcher.get_fundamentals(symbol)
    except Exception:
        return _err(500, "Failed to fetch fundamentals")
    return _ok(FundamentalsResponse(**data).model_dump())
