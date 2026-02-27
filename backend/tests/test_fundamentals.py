"""Tests for fundamentals router."""
from unittest.mock import AsyncMock, patch

FAKE_FUNDAMENTALS = {
    "symbol": "AAPL",
    "pe_ttm": 28.5,
    "pb": 45.2,
    "market_cap": 2_800_000_000_000,
    "revenue_ttm": 394_000_000_000,
    "net_profit_ttm": 100_000_000_000,
    "dividend_yield": 0.005,
}


class TestFundamentals:
    async def test_returns_data(self, client):
        with patch("routers.fundamentals.fetcher.get_fundamentals", new=AsyncMock(return_value=FAKE_FUNDAMENTALS)):
            resp = await client.get("/api/fundamentals/AAPL")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["pe_ttm"] == 28.5
        assert body["data"]["symbol"] == "AAPL"

    async def test_fetcher_error_returns_500(self, client):
        with patch("routers.fundamentals.fetcher.get_fundamentals", new=AsyncMock(side_effect=Exception("err"))):
            resp = await client.get("/api/fundamentals/AAPL")
        assert resp.json()["code"] == 500

    async def test_nullable_fields_allowed(self, client):
        sparse = {"symbol": "TST", "pe_ttm": None, "pb": None,
                  "market_cap": None, "revenue_ttm": None,
                  "net_profit_ttm": None, "dividend_yield": None}
        with patch("routers.fundamentals.fetcher.get_fundamentals", new=AsyncMock(return_value=sparse)):
            resp = await client.get("/api/fundamentals/TST")
        assert resp.json()["code"] == 200
