"""Tests for stocks router — stock_data service is mocked."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

FAKE_BARS = [
    {"timestamp": 1700000000, "open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0, "volume": 1000.0},
    {"timestamp": 1700086400, "open": 103.0, "high": 108.0, "low": 102.0, "close": 107.0, "volume": 1500.0},
]
FAKE_QUOTE = {
    "symbol": "AAPL",
    "price": 180.0,
    "change": 2.5,
    "change_pct": 1.41,
    "volume": 50000000.0,
    "timestamp": 1700000000,
}
FAKE_SEARCH = [
    {"symbol": "600519.SH", "name": "贵州茅台", "market": "A"},
]


class TestOHLCV:
    async def test_returns_bars(self, client):
        with patch("routers.stocks.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)):
            resp = await client.get("/api/stocks/AAPL/ohlcv?period=1M&interval=1d")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["symbol"] == "AAPL"
        assert len(body["data"]["bars"]) == 2
        assert body["data"]["bars"][0]["close"] == 103.0

    async def test_service_called_with_correct_args(self, client):
        mock = AsyncMock(return_value=FAKE_BARS)
        with patch("routers.stocks.stock_data.get_ohlcv", new=mock):
            await client.get("/api/stocks/600519.SH/ohlcv?period=3M&interval=1d")
        # stock_data.get_ohlcv receives (db, symbol, period, interval)
        args = mock.call_args
        assert args[0][1] == "600519.SH"
        assert args[0][2] == "3M"
        assert args[0][3] == "1d"

    async def test_service_error_returns_500(self, client):
        with patch("routers.stocks.stock_data.get_ohlcv", new=AsyncMock(side_effect=Exception("network error"))):
            resp = await client.get("/api/stocks/AAPL/ohlcv")
        assert resp.status_code == 200
        assert resp.json()["code"] == 500


class TestQuote:
    async def test_returns_quote(self, client):
        with patch("routers.stocks.fetcher.get_quote", new=AsyncMock(return_value=FAKE_QUOTE)):
            resp = await client.get("/api/stocks/AAPL/quote")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["price"] == 180.0
        assert body["data"]["change_pct"] == 1.41

    async def test_not_found_returns_404(self, client):
        with patch("routers.stocks.fetcher.get_quote", new=AsyncMock(side_effect=ValueError("not found"))):
            resp = await client.get("/api/stocks/INVALID/quote")
        assert resp.json()["code"] == 404


class TestSearch:
    async def test_returns_results(self, client):
        with patch("routers.stocks.fetcher.search_stocks", new=AsyncMock(return_value=FAKE_SEARCH)):
            resp = await client.get("/api/stocks/search?q=茅台")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) == 1
        assert body["data"][0]["symbol"] == "600519.SH"

    async def test_missing_query_returns_422(self, client):
        resp = await client.get("/api/stocks/search")
        assert resp.status_code == 422


class TestMultiMarketSearch:
    """Unit tests for fetcher.search_stocks multi-market merging."""

    async def test_search_returns_multi_market(self):
        from services.fetcher import search_stocks

        a_results = [{"symbol": "600519.SH", "name": "贵州茅台", "market": "A"}]
        us_results = [{"symbol": "AAPL", "name": "Apple Inc.", "market": "US"}]
        hk_results = [{"symbol": "00700.HK", "name": "腾讯控股", "market": "HK"}]

        with patch("services.fetcher._sync_search_akshare", return_value=a_results), \
             patch("services.fetcher._sync_search_yfinance", return_value=us_results), \
             patch("services.fetcher._sync_search_akshare_hk", return_value=hk_results):
            results = await search_stocks("test")

        assert len(results) == 3
        markets = {r["market"] for r in results}
        assert markets == {"A", "US", "HK"}

    async def test_search_partial_failure(self):
        from services.fetcher import search_stocks

        a_results = [{"symbol": "600519.SH", "name": "贵州茅台", "market": "A"}]
        us_results = [{"symbol": "AAPL", "name": "Apple Inc.", "market": "US"}]

        with patch("services.fetcher._sync_search_akshare", return_value=a_results), \
             patch("services.fetcher._sync_search_yfinance", return_value=us_results), \
             patch("services.fetcher._sync_search_akshare_hk", side_effect=Exception("HK unavailable")):
            results = await search_stocks("test")

        assert len(results) == 2
        markets = {r["market"] for r in results}
        assert markets == {"A", "US"}
