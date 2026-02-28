from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.stock import FundamentalsResponse
from services import fundamentals_data

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("/{symbol}")
async def get_fundamentals(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        data = await fundamentals_data.get_fundamentals(db, symbol)
    except Exception:
        return _err(500, "Failed to fetch fundamentals")
    return _ok(FundamentalsResponse(**data).model_dump())
