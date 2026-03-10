"""Data collectors — fetch and persist data for a single stock."""
from __future__ import annotations

import logging
import time

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.dividend import Dividend
from models.earnings import Earnings
from models.fundamentals import FundamentalsCache
from models.ohlcv import OHLCVBar
from services import fetcher

logger = logging.getLogger(__name__)


async def collect_ohlcv(
    db: AsyncSession,
    symbol: str,
    market: str,
    backfill: bool = False,
) -> bool:
    """Fetch OHLCV bars and persist. Returns True on success."""
    # Determine period based on existing data
    if backfill:
        period = "1Y"
    else:
        result = await db.execute(
            select(func.count()).where(OHLCVBar.symbol == symbol)
        )
        count = result.scalar()
        period = "1Y" if count == 0 else "1M"

    bars = await fetcher.get_ohlcv(symbol, period, "1d")

    if bars:
        rows = [
            {
                "symbol": symbol,
                "interval": "1d",
                "timestamp": bar["timestamp"],
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
            }
            for bar in bars
        ]
        stmt = sqlite_insert(OHLCVBar).values(rows).on_conflict_do_nothing(
            index_elements=["symbol", "interval", "timestamp"],
        )
        await db.execute(stmt)
    await db.commit()
    return True


async def collect_fundamentals(
    db: AsyncSession,
    symbol: str,
    market: str,
) -> bool:
    """Fetch fundamentals and persist/update."""
    data = await fetcher.get_fundamentals(symbol)
    now_ts = int(time.time())

    existing = (await db.execute(
        select(FundamentalsCache).where(FundamentalsCache.symbol == symbol)
    )).scalar_one_or_none()

    if existing:
        existing.pe_ttm = data.get("pe_ttm")
        existing.pb = data.get("pb")
        existing.market_cap = data.get("market_cap")
        existing.revenue_ttm = data.get("revenue_ttm")
        existing.net_profit_ttm = data.get("net_profit_ttm")
        existing.dividend_yield = data.get("dividend_yield")
        existing.updated_ts = now_ts
    else:
        db.add(FundamentalsCache(
            symbol=symbol,
            pe_ttm=data.get("pe_ttm"),
            pb=data.get("pb"),
            market_cap=data.get("market_cap"),
            revenue_ttm=data.get("revenue_ttm"),
            net_profit_ttm=data.get("net_profit_ttm"),
            dividend_yield=data.get("dividend_yield"),
            updated_ts=now_ts,
        ))
    await db.commit()
    return True


async def collect_earnings(
    db: AsyncSession,
    symbol: str,
    market: str,
) -> bool:
    """Fetch earnings and persist. Skips if no data available."""
    records = await fetcher.get_earnings(symbol)
    if not records:
        return True  # skip, not a failure

    now_ts = int(time.time())
    rows = [
        {
            "symbol": symbol,
            "period_end": rec["period_end"],
            "period_type": rec["period_type"],
            "revenue": rec.get("revenue"),
            "net_income": rec.get("net_income"),
            "eps": rec.get("eps"),
            "gross_profit": rec.get("gross_profit"),
            "operating_income": rec.get("operating_income"),
            "updated_ts": now_ts,
        }
        for rec in records
    ]
    stmt = sqlite_insert(Earnings).values(rows).on_conflict_do_nothing(
        index_elements=["symbol", "period_end", "period_type"],
    )
    await db.execute(stmt)
    await db.commit()
    return True


async def collect_dividends(
    db: AsyncSession,
    symbol: str,
    market: str,
) -> bool:
    """Fetch dividends and persist."""
    records = await fetcher.get_dividends(symbol)
    if not records:
        return True

    now_ts = int(time.time())
    rows = [
        {
            "symbol": symbol,
            "ex_date": rec["ex_date"],
            "amount": rec["amount"],
            "currency": rec.get("currency", "USD"),
            "updated_ts": now_ts,
        }
        for rec in records
    ]
    stmt = sqlite_insert(Dividend).values(rows).on_conflict_do_nothing(
        index_elements=["symbol", "ex_date"],
    )
    await db.execute(stmt)
    await db.commit()
    return True


async def collect_all_for_stock(
    db: AsyncSession,
    symbol: str,
    market: str,
    backfill: bool = False,
) -> dict[str, bool]:
    """Run all collectors for one stock. Individual failures are isolated."""
    results: dict[str, bool] = {}

    collectors = [
        ("ohlcv", collect_ohlcv(db, symbol, market, backfill=backfill)),
        ("fundamentals", collect_fundamentals(db, symbol, market)),
        ("earnings", collect_earnings(db, symbol, market)),
        ("dividends", collect_dividends(db, symbol, market)),
    ]

    for name, coro in collectors:
        try:
            results[name] = await coro
        except Exception:
            logger.exception("Collector %s failed for %s", name, symbol)
            results[name] = False

    return results
