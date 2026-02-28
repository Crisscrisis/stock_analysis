"""Tests for indicators router — stock_data service and calculator are mocked."""
from unittest.mock import AsyncMock, patch

FAKE_BARS = [
    {"timestamp": 1700000000 + i * 86400,
     "open": 100.0 + i, "high": 105.0 + i, "low": 99.0 + i,
     "close": 103.0 + i, "volume": 1000.0}
    for i in range(30)
]


class TestIndicators:
    async def test_ma_returned(self, client):
        with (
            patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)),
        ):
            resp = await client.get("/api/indicators/AAPL?types=MA")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["ma"] is not None
        assert body["data"]["symbol"] == "AAPL"

    async def test_macd_returned(self, client):
        with patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)):
            resp = await client.get("/api/indicators/AAPL?types=MACD")
        assert resp.json()["data"]["macd"] is not None

    async def test_rsi_returned(self, client):
        with patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)):
            resp = await client.get("/api/indicators/AAPL?types=RSI")
        assert resp.json()["data"]["rsi"] is not None

    async def test_bollinger_returned(self, client):
        with patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)):
            resp = await client.get("/api/indicators/AAPL?types=BOLLINGER")
        assert resp.json()["data"]["bollinger"] is not None

    async def test_multiple_types(self, client):
        with patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)):
            resp = await client.get("/api/indicators/AAPL?types=MA,RSI")
        data = resp.json()["data"]
        assert data["ma"] is not None
        assert data["rsi"] is not None
        assert data["macd"] is None

    async def test_timestamps_match_bars(self, client):
        with patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(return_value=FAKE_BARS)):
            resp = await client.get("/api/indicators/AAPL?types=MA")
        timestamps = resp.json()["data"]["timestamps"]
        assert len(timestamps) == len(FAKE_BARS)
        assert timestamps[0] == FAKE_BARS[0]["timestamp"]

    async def test_fetcher_error_returns_500(self, client):
        with patch("routers.indicators.stock_data.get_ohlcv", new=AsyncMock(side_effect=Exception("err"))):
            resp = await client.get("/api/indicators/AAPL?types=MA")
        assert resp.json()["code"] == 500
