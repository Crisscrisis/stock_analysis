"""Tests for services/fundamentals_data — DB cache for fundamentals."""
import time
from unittest.mock import AsyncMock, patch

from models.fundamentals import FundamentalsCache
from services import fundamentals_data

SYMBOL = "AAPL"
FAKE_DATA = {
    "symbol": SYMBOL,
    "pe_ttm": 28.5,
    "pb": 45.2,
    "market_cap": 2_800_000_000_000,
    "revenue_ttm": 394_000_000_000,
    "net_profit_ttm": 100_000_000_000,
    "dividend_yield": 0.005,
}


class TestEmptyCache:
    """No cached data — should call fetcher and persist."""

    async def test_calls_fetcher_and_returns(self, db_session):
        with patch.object(fundamentals_data.fetcher, "get_fundamentals", new=AsyncMock(return_value=FAKE_DATA)) as mock:
            result = await fundamentals_data.get_fundamentals(db_session, SYMBOL)
        mock.assert_called_once_with(SYMBOL)
        assert result["pe_ttm"] == 28.5
        assert result["symbol"] == SYMBOL

    async def test_persists_to_db(self, db_session):
        with patch.object(fundamentals_data.fetcher, "get_fundamentals", new=AsyncMock(return_value=FAKE_DATA)):
            await fundamentals_data.get_fundamentals(db_session, SYMBOL)

        from sqlalchemy import select
        result = await db_session.execute(select(FundamentalsCache).where(FundamentalsCache.symbol == SYMBOL))
        row = result.scalar_one()
        assert row.pe_ttm == 28.5


class TestFreshCache:
    """Cache is recent — should NOT call fetcher."""

    async def test_no_fetcher_call(self, db_session):
        with patch.object(fundamentals_data.fetcher, "get_fundamentals", new=AsyncMock(return_value=FAKE_DATA)):
            await fundamentals_data.get_fundamentals(db_session, SYMBOL)

        with patch.object(fundamentals_data.fetcher, "get_fundamentals", new=AsyncMock()) as mock:
            result = await fundamentals_data.get_fundamentals(db_session, SYMBOL)
        mock.assert_not_called()
        assert result["pe_ttm"] == 28.5


class TestStaleCache:
    """Cache is older than 1 day — should refresh from fetcher."""

    async def test_refreshes_stale_data(self, db_session):
        # Insert stale cache manually
        stale = FundamentalsCache(
            symbol=SYMBOL,
            pe_ttm=20.0,
            pb=30.0,
            market_cap=None,
            revenue_ttm=None,
            net_profit_ttm=None,
            dividend_yield=None,
            updated_ts=int(time.time()) - 200_000,  # ~2 days ago
        )
        db_session.add(stale)
        await db_session.commit()

        with patch.object(fundamentals_data.fetcher, "get_fundamentals", new=AsyncMock(return_value=FAKE_DATA)) as mock:
            result = await fundamentals_data.get_fundamentals(db_session, SYMBOL)
        mock.assert_called_once()
        assert result["pe_ttm"] == 28.5  # updated value


class TestNullableFields:
    """All fields except symbol can be None."""

    async def test_all_none(self, db_session):
        sparse = {
            "symbol": "TST",
            "pe_ttm": None, "pb": None, "market_cap": None,
            "revenue_ttm": None, "net_profit_ttm": None, "dividend_yield": None,
        }
        with patch.object(fundamentals_data.fetcher, "get_fundamentals", new=AsyncMock(return_value=sparse)):
            result = await fundamentals_data.get_fundamentals(db_session, "TST")
        assert result["pe_ttm"] is None
        assert result["symbol"] == "TST"
