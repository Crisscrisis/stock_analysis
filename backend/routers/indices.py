from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.index_constituent import IndexConstituent

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("")
async def list_indices(db: AsyncSession = Depends(get_db)) -> dict:
    """Return all indices with their active constituent count."""
    stmt = (
        select(
            IndexConstituent.index_name,
            IndexConstituent.market,
            func.count().filter(IndexConstituent.is_active.is_(True)).label("active_count"),
        )
        .group_by(IndexConstituent.index_name, IndexConstituent.market)
        .order_by(IndexConstituent.index_name)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return _ok([
        {"name": row.index_name, "market": row.market, "active_count": row.active_count}
        for row in rows
    ])


@router.get("/{name}/constituents")
async def get_constituents(name: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Return constituents for a given index name."""
    stmt = (
        select(IndexConstituent)
        .where(IndexConstituent.index_name == name)
        .order_by(IndexConstituent.symbol)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    if not items:
        return _err(404, f"Index '{name}' not found or has no constituents")
    return _ok([
        {
            "symbol": c.symbol,
            "name": c.name,
            "market": c.market,
            "is_active": c.is_active,
        }
        for c in items
    ])
