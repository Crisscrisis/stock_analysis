"""Tests for crawler collectors: ohlcv, fundamentals, earnings, dividends."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from models.ohlcv import OHLCVBar
from models.fundamentals import FundamentalsCache
from models.earnings import Earnings
from models.dividend import Dividend


# ---------------------------------------------------------------------------
# T-23: collect_ohlcv
# ---------------------------------------------------------------------------


class TestCollectOhlcv:
    async def test_backfill_empty_db(self, db_session):
        from crawler.collectors import collect_ohlcv

        fake_bars = [
            {"timestamp": 1704067200, "open": 185.0, "high": 186.5,
             "low": 184.0, "close": 185.5, "volume": 50000000},
            {"timestamp": 1704153600, "open": 185.5, "high": 187.0,
             "low": 185.0, "close": 186.0, "volume": 48000000},
        ]
        with patch("crawler.collectors.fetcher.get_ohlcv", AsyncMock(return_value=fake_bars)):
            result = await collect_ohlcv(db_session, "AAPL", "US")

        assert result is True
        rows = (await db_session.execute(
            select(OHLCVBar).where(OHLCVBar.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 2

    async def test_incremental_with_existing_data(self, db_session):
        from crawler.collectors import collect_ohlcv

        # Pre-populate
        db_session.add(OHLCVBar(
            symbol="AAPL", interval="1d", timestamp=1704067200,
            open=185.0, high=186.5, low=184.0, close=185.5, volume=50000000,
        ))
        await db_session.commit()

        new_bars = [
            {"timestamp": 1704153600, "open": 185.5, "high": 187.0,
             "low": 185.0, "close": 186.0, "volume": 48000000},
        ]
        with patch("crawler.collectors.fetcher.get_ohlcv", AsyncMock(return_value=new_bars)):
            result = await collect_ohlcv(db_session, "AAPL", "US")

        assert result is True
        rows = (await db_session.execute(
            select(OHLCVBar).where(OHLCVBar.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 2

    async def test_backfill_flag(self, db_session):
        from crawler.collectors import collect_ohlcv

        # Pre-populate
        db_session.add(OHLCVBar(
            symbol="AAPL", interval="1d", timestamp=1704067200,
            open=185.0, high=186.5, low=184.0, close=185.5, volume=50000000,
        ))
        await db_session.commit()

        mock_get = AsyncMock(return_value=[])
        with patch("crawler.collectors.fetcher.get_ohlcv", mock_get):
            await collect_ohlcv(db_session, "AAPL", "US", backfill=True)

        # Should use 1Y period when backfill is True
        mock_get.assert_called_once_with("AAPL", "1Y", "1d")

    async def test_on_conflict_dedup(self, db_session):
        from crawler.collectors import collect_ohlcv

        fake_bars = [
            {"timestamp": 1704067200, "open": 185.0, "high": 186.5,
             "low": 184.0, "close": 185.5, "volume": 50000000},
        ]
        with patch("crawler.collectors.fetcher.get_ohlcv", AsyncMock(return_value=fake_bars)):
            await collect_ohlcv(db_session, "AAPL", "US")
            # Run again — should not duplicate
            await collect_ohlcv(db_session, "AAPL", "US", backfill=True)

        rows = (await db_session.execute(
            select(OHLCVBar).where(OHLCVBar.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# T-25: collect_fundamentals
# ---------------------------------------------------------------------------


class TestCollectFundamentals:
    async def test_insert_new(self, db_session):
        from crawler.collectors import collect_fundamentals

        fake_data = {
            "symbol": "AAPL", "pe_ttm": 28.5, "pb": 45.2,
            "market_cap": 2800000000000, "revenue_ttm": 383000000000,
            "net_profit_ttm": 97000000000, "dividend_yield": 0.55,
        }
        with patch("crawler.collectors.fetcher.get_fundamentals", AsyncMock(return_value=fake_data)):
            result = await collect_fundamentals(db_session, "AAPL", "US")

        assert result is True
        row = (await db_session.execute(
            select(FundamentalsCache).where(FundamentalsCache.symbol == "AAPL")
        )).scalar_one()
        assert row.pe_ttm == 28.5

    async def test_update_existing(self, db_session):
        from crawler.collectors import collect_fundamentals

        db_session.add(FundamentalsCache(
            symbol="AAPL", pe_ttm=25.0, pb=40.0, market_cap=2500000000000,
            revenue_ttm=None, net_profit_ttm=None, dividend_yield=None,
            updated_ts=1000000,
        ))
        await db_session.commit()

        fake_data = {
            "symbol": "AAPL", "pe_ttm": 28.5, "pb": 45.2,
            "market_cap": 2800000000000, "revenue_ttm": 383000000000,
            "net_profit_ttm": 97000000000, "dividend_yield": 0.55,
        }
        with patch("crawler.collectors.fetcher.get_fundamentals", AsyncMock(return_value=fake_data)):
            result = await collect_fundamentals(db_session, "AAPL", "US")

        assert result is True
        row = (await db_session.execute(
            select(FundamentalsCache).where(FundamentalsCache.symbol == "AAPL")
        )).scalar_one()
        assert row.pe_ttm == 28.5
        assert row.updated_ts > 1000000


# ---------------------------------------------------------------------------
# T-27: collect_earnings
# ---------------------------------------------------------------------------


class TestCollectEarnings:
    async def test_insert(self, db_session):
        from crawler.collectors import collect_earnings

        fake_earnings = [
            {"period_end": "2025-03-31", "period_type": "quarterly",
             "revenue": 94836000000, "net_income": 23636000000,
             "eps": 1.53, "gross_profit": 43000000000, "operating_income": 30000000000},
        ]
        with patch("crawler.collectors.fetcher.get_earnings", AsyncMock(return_value=fake_earnings)):
            result = await collect_earnings(db_session, "AAPL", "US")

        assert result is True
        rows = (await db_session.execute(
            select(Earnings).where(Earnings.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 1
        assert rows[0].revenue == 94836000000

    async def test_dedup(self, db_session):
        from crawler.collectors import collect_earnings

        fake_earnings = [
            {"period_end": "2025-03-31", "period_type": "quarterly",
             "revenue": 94836000000, "net_income": 23636000000,
             "eps": 1.53, "gross_profit": None, "operating_income": None},
        ]
        with patch("crawler.collectors.fetcher.get_earnings", AsyncMock(return_value=fake_earnings)):
            await collect_earnings(db_session, "AAPL", "US")
            await collect_earnings(db_session, "AAPL", "US")

        rows = (await db_session.execute(
            select(Earnings).where(Earnings.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 1

    async def test_empty_returns_true(self, db_session):
        from crawler.collectors import collect_earnings

        with patch("crawler.collectors.fetcher.get_earnings", AsyncMock(return_value=[])):
            result = await collect_earnings(db_session, "AAPL", "US")
        assert result is True


# ---------------------------------------------------------------------------
# T-29: collect_dividends
# ---------------------------------------------------------------------------


class TestCollectDividends:
    async def test_insert(self, db_session):
        from crawler.collectors import collect_dividends

        fake_divs = [
            {"ex_date": "2025-02-07", "amount": 0.25, "currency": "USD"},
        ]
        with patch("crawler.collectors.fetcher.get_dividends", AsyncMock(return_value=fake_divs)):
            result = await collect_dividends(db_session, "AAPL", "US")

        assert result is True
        rows = (await db_session.execute(
            select(Dividend).where(Dividend.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 1
        assert rows[0].amount == 0.25

    async def test_dedup(self, db_session):
        from crawler.collectors import collect_dividends

        fake_divs = [
            {"ex_date": "2025-02-07", "amount": 0.25, "currency": "USD"},
        ]
        with patch("crawler.collectors.fetcher.get_dividends", AsyncMock(return_value=fake_divs)):
            await collect_dividends(db_session, "AAPL", "US")
            await collect_dividends(db_session, "AAPL", "US")

        rows = (await db_session.execute(
            select(Dividend).where(Dividend.symbol == "AAPL")
        )).scalars().all()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# T-31: collect_all_for_stock
# ---------------------------------------------------------------------------


class TestCollectAllForStock:
    async def test_all_succeed(self, db_session):
        from crawler.collectors import collect_all_for_stock

        with (
            patch("crawler.collectors.collect_ohlcv", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_fundamentals", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_earnings", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_dividends", AsyncMock(return_value=True)),
        ):
            result = await collect_all_for_stock(db_session, "AAPL", "US")

        assert result == {
            "ohlcv": True,
            "fundamentals": True,
            "earnings": True,
            "dividends": True,
        }

    async def test_partial_failure(self, db_session):
        from crawler.collectors import collect_all_for_stock

        with (
            patch("crawler.collectors.collect_ohlcv", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_fundamentals", AsyncMock(side_effect=Exception("timeout"))),
            patch("crawler.collectors.collect_earnings", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_dividends", AsyncMock(return_value=True)),
        ):
            result = await collect_all_for_stock(db_session, "AAPL", "US")

        assert result["ohlcv"] is True
        assert result["fundamentals"] is False
        assert result["earnings"] is True
        assert result["dividends"] is True

    async def test_backfill_passed_through(self, db_session):
        from crawler.collectors import collect_all_for_stock

        mock_ohlcv = AsyncMock(return_value=True)
        with (
            patch("crawler.collectors.collect_ohlcv", mock_ohlcv),
            patch("crawler.collectors.collect_fundamentals", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_earnings", AsyncMock(return_value=True)),
            patch("crawler.collectors.collect_dividends", AsyncMock(return_value=True)),
        ):
            await collect_all_for_stock(db_session, "AAPL", "US", backfill=True)

        mock_ohlcv.assert_called_once_with(db_session, "AAPL", "US", backfill=True)
