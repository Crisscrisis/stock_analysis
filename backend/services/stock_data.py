"""OHLCV data service — DB-first with incremental fetching.

Reads from local DB first. If data is missing or stale, fetches from
the upstream source (via fetcher), persists new bars, and returns
the merged result.
"""
from __future__ import annotations

import time
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.ohlcv import OHLCVBar
from services import fetcher

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PERIOD_DAYS: dict[str, int] = {
    "1W": 7, "1M": 30, "3M": 90, "6M": 180,
    "1Y": 365, "3Y": 365 * 3, "5Y": 365 * 5,
}

_ONE_DAY = 86400


def _period_start_ts(period: str) -> int:
    days = _PERIOD_DAYS.get(period.upper(), 30)
    start = date.today() - timedelta(days=days)
    return int(time.mktime(start.timetuple()))


def _yesterday_ts() -> int:
    yesterday = date.today() - timedelta(days=1)
    return int(time.mktime(yesterday.timetuple()))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_ohlcv(
    db: AsyncSession,
    symbol: str,
    period: str = "1M",
    interval: str = "1d",
) -> list[dict]:
    """Return OHLCV bars, using local DB as cache with incremental updates."""
    period_start = _period_start_ts(period)

    # 1. Query existing bars from DB
    stmt = (
        select(OHLCVBar)
        .where(
            OHLCVBar.symbol == symbol,
            OHLCVBar.interval == interval,
            OHLCVBar.timestamp >= period_start,
        )
        .order_by(OHLCVBar.timestamp)
    )
    result = await db.execute(stmt)
    existing = result.scalars().all()

    if existing:
        latest_ts = existing[-1].timestamp
        # Data is fresh enough — return directly
        if latest_ts >= _yesterday_ts():
            return [_bar_to_dict(b) for b in existing]

        # Data exists but is stale — incremental fetch (1M window)
        new_bars = await fetcher.get_ohlcv(symbol, "1M", interval)
        # Keep only bars newer than what we already have
        new_bars = [b for b in new_bars if b["timestamp"] > latest_ts]
    else:
        # No data at all — full fetch
        new_bars = await fetcher.get_ohlcv(symbol, period, interval)

    # 2. Persist new bars (skip duplicates via ON CONFLICT DO NOTHING)
    if new_bars:
        await _upsert_bars(db, symbol, interval, new_bars)

    # 3. Re-query DB for the complete result set
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_bar_to_dict(b) for b in rows]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _bar_to_dict(bar: OHLCVBar) -> dict:
    return {
        "timestamp": bar.timestamp,
        "open": bar.open,
        "high": bar.high,
        "low": bar.low,
        "close": bar.close,
        "volume": bar.volume,
    }


async def _upsert_bars(
    db: AsyncSession,
    symbol: str,
    interval: str,
    bars: list[dict],
) -> None:
    for bar in bars:
        stmt = sqlite_insert(OHLCVBar).values(
            symbol=symbol,
            interval=interval,
            timestamp=bar["timestamp"],
            open=bar["open"],
            high=bar["high"],
            low=bar["low"],
            close=bar["close"],
            volume=bar["volume"],
        ).on_conflict_do_nothing(
            index_elements=["symbol", "interval", "timestamp"],
        )
        await db.execute(stmt)
    await db.commit()
