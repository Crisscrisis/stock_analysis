"""Tests for capital_flow router."""
from unittest.mock import AsyncMock, patch

FAKE_FLOW = {
    "symbol": "600519.SH",
    "northbound_net": 12345.0,
    "main_force_net": -5000.0,
    "top_list": [{"机构": "某券商", "买入金额": 10000}],
}


class TestCapitalFlow:
    async def test_returns_data(self, client):
        with patch("routers.capital_flow.fetcher.get_capital_flow", new=AsyncMock(return_value=FAKE_FLOW)):
            resp = await client.get("/api/capital-flow/600519.SH")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["northbound_net"] == 12345.0
        assert body["data"]["symbol"] == "600519.SH"

    async def test_us_stock_returns_error(self, client):
        with patch(
            "routers.capital_flow.fetcher.get_capital_flow",
            new=AsyncMock(side_effect=ValueError("A-share only")),
        ):
            resp = await client.get("/api/capital-flow/AAPL")
        assert resp.json()["code"] == 400

    async def test_fetcher_error_returns_500(self, client):
        with patch("routers.capital_flow.fetcher.get_capital_flow", new=AsyncMock(side_effect=Exception("err"))):
            resp = await client.get("/api/capital-flow/600519.SH")
        assert resp.json()["code"] == 500
