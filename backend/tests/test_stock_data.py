"""Tests for services/stock_data — DB-first OHLCV caching."""
import time
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from models.ohlcv import OHLCVBar
from services import stock_data

SYMBOL = "AAPL"
INTERVAL = "1d"


def _make_bars(start_ts: int, count: int) -> list[dict]:
    return [
        {
            "timestamp": start_ts + i * 86400,
            "open": 100.0 + i,
            "high": 105.0 + i,
            "low": 99.0 + i,
            "close": 103.0 + i,
            "volume": 1000.0 + i * 100,
        }
        for i in range(count)
    ]


def _yesterday_ts() -> int:
    yesterday = date.today() - timedelta(days=1)
    return int(time.mktime(yesterday.timetuple()))


def _days_ago_ts(days: int) -> int:
    d = date.today() - timedelta(days=days)
    return int(time.mktime(d.timetuple()))


class TestEmptyDB:
    """First fetch — DB is empty, should call fetcher and persist."""

    async def test_calls_fetcher_and_returns_data(self, db_session):
        fake_bars = _make_bars(_days_ago_ts(5), 5)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=fake_bars)) as mock:
            result = await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)
        mock.assert_called_once_with(SYMBOL, "1M", INTERVAL)
        assert len(result) == 5
        assert result[0]["close"] == fake_bars[0]["close"]

    async def test_persists_to_db(self, db_session):
        fake_bars = _make_bars(_days_ago_ts(3), 3)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=fake_bars)):
            await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)

        from sqlalchemy import select
        result = await db_session.execute(select(OHLCVBar).where(OHLCVBar.symbol == SYMBOL))
        rows = result.scalars().all()
        assert len(rows) == 3


class TestFreshData:
    """DB has recent data — should NOT call fetcher."""

    async def test_no_fetcher_call(self, db_session):
        fresh_bars = _make_bars(_yesterday_ts(), 2)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=fresh_bars)):
            await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)

        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock()) as mock:
            result = await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)
        mock.assert_not_called()
        assert len(result) == 2


class TestStaleData:
    """DB has old data — should do incremental fetch."""

    async def test_incremental_fetch(self, db_session):
        old_ts = _days_ago_ts(10)
        old_bars = _make_bars(old_ts, 3)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=old_bars)):
            await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)

        # Second call — data is stale, should fetch incrementally
        newest_old_ts = old_bars[-1]["timestamp"]
        new_bars = _make_bars(newest_old_ts + 86400, 2)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=new_bars)) as mock:
            result = await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)
        mock.assert_called_once_with(SYMBOL, "1M", INTERVAL)
        assert len(result) == 5  # 3 old + 2 new


class TestDeduplication:
    """Duplicate timestamps should not produce duplicate rows."""

    async def test_no_duplicate_rows(self, db_session):
        bars = _make_bars(_days_ago_ts(3), 3)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=bars)):
            await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)
        # Insert same bars again
        await stock_data._upsert_bars(db_session, SYMBOL, INTERVAL, bars)

        from sqlalchemy import select, func
        result = await db_session.execute(
            select(func.count()).select_from(OHLCVBar).where(OHLCVBar.symbol == SYMBOL)
        )
        assert result.scalar() == 3


class TestPeriodFilter:
    """Period parameter should filter to correct date range."""

    async def test_1w_returns_only_recent(self, db_session):
        # Insert bars spanning 20 days
        bars = _make_bars(_days_ago_ts(20), 20)
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock(return_value=bars)):
            await stock_data.get_ohlcv(db_session, SYMBOL, "1M", INTERVAL)

        # Now query with 1W period — should return only ~7 days
        with patch.object(stock_data.fetcher, "get_ohlcv", new=AsyncMock()) as mock:
            result = await stock_data.get_ohlcv(db_session, SYMBOL, "1W", INTERVAL)
        # Bars from last 7 days only
        cutoff = _days_ago_ts(7)
        expected = [b for b in bars if b["timestamp"] >= cutoff]
        assert len(result) == len(expected)
