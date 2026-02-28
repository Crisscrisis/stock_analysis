"""Fundamentals data service — DB cache with daily refresh.

Reads from local DB first. If no cached data or cache is older than 1 day,
fetches from upstream (via fetcher), persists, and returns.
"""
from __future__ import annotations

import time
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.fundamentals import FundamentalsCache
from services import fetcher

_ONE_DAY = 86400


def _yesterday_ts() -> int:
    yesterday = date.today() - timedelta(days=1)
    return int(time.mktime(yesterday.timetuple()))


async def get_fundamentals(db: AsyncSession, symbol: str) -> dict:
    """Return fundamentals, using local DB as a daily cache."""
    stmt = select(FundamentalsCache).where(FundamentalsCache.symbol == symbol)
    result = await db.execute(stmt)
    cached = result.scalar_one_or_none()

    if cached and cached.updated_ts >= _yesterday_ts():
        return _cache_to_dict(cached)

    # Fetch from upstream
    data = await fetcher.get_fundamentals(symbol)

    # Persist / update cache
    if cached:
        cached.pe_ttm = data.get("pe_ttm")
        cached.pb = data.get("pb")
        cached.market_cap = data.get("market_cap")
        cached.revenue_ttm = data.get("revenue_ttm")
        cached.net_profit_ttm = data.get("net_profit_ttm")
        cached.dividend_yield = data.get("dividend_yield")
        cached.updated_ts = int(time.time())
    else:
        cached = FundamentalsCache(
            symbol=symbol,
            pe_ttm=data.get("pe_ttm"),
            pb=data.get("pb"),
            market_cap=data.get("market_cap"),
            revenue_ttm=data.get("revenue_ttm"),
            net_profit_ttm=data.get("net_profit_ttm"),
            dividend_yield=data.get("dividend_yield"),
            updated_ts=int(time.time()),
        )
        db.add(cached)
    await db.commit()
    await db.refresh(cached)

    return _cache_to_dict(cached)


def _cache_to_dict(row: FundamentalsCache) -> dict:
    return {
        "symbol": row.symbol,
        "pe_ttm": row.pe_ttm,
        "pb": row.pb,
        "market_cap": row.market_cap,
        "revenue_ttm": row.revenue_ttm,
        "net_profit_ttm": row.net_profit_ttm,
        "dividend_yield": row.dividend_yield,
    }
