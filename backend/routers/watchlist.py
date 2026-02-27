from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.watchlist import Watchlist
from schemas.watchlist import WatchlistCreate, WatchlistItem

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("")
async def get_watchlist(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Watchlist).order_by(Watchlist.added_at))
    items = result.scalars().all()
    return _ok([WatchlistItem.model_validate(i).model_dump() for i in items])


@router.post("")
async def add_to_watchlist(
    payload: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    item = Watchlist(
        symbol=payload.symbol,
        name=payload.name,
        market=payload.market,
    )
    db.add(item)
    try:
        await db.commit()
        await db.refresh(item)
    except IntegrityError:
        await db.rollback()
        return _err(409, f"symbol '{payload.symbol}' already exists in watchlist")
    return _ok(WatchlistItem.model_validate(item).model_dump())


@router.delete("/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    symbol = symbol.upper()
    result = await db.execute(delete(Watchlist).where(Watchlist.symbol == symbol))
    await db.commit()
    if result.rowcount == 0:
        return _err(404, f"symbol '{symbol}' not found in watchlist")
    return _ok({"symbol": symbol})
