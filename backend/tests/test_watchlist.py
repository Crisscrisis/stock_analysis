"""Integration tests for watchlist CRUD endpoints."""
import pytest


class TestGetWatchlist:
    async def test_empty_list(self, client):
        resp = await client.get("/api/watchlist")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"] == []

    async def test_returns_added_items(self, client):
        await client.post("/api/watchlist", json={"symbol": "AAPL", "market": "US"})
        resp = await client.get("/api/watchlist")
        symbols = [item["symbol"] for item in resp.json()["data"]]
        assert "AAPL" in symbols


class TestAddWatchlist:
    async def test_add_success(self, client):
        resp = await client.post(
            "/api/watchlist",
            json={"symbol": "600519.SH", "name": "贵州茅台", "market": "A"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        item = body["data"]
        assert item["symbol"] == "600519.SH"
        assert item["name"] == "贵州茅台"
        assert item["market"] == "A"
        assert "id" in item
        assert "added_at" in item

    async def test_add_normalises_symbol_to_uppercase(self, client):
        resp = await client.post(
            "/api/watchlist", json={"symbol": "aapl", "market": "US"}
        )
        assert resp.json()["data"]["symbol"] == "AAPL"

    async def test_add_duplicate_returns_error(self, client):
        await client.post("/api/watchlist", json={"symbol": "TSLA", "market": "US"})
        resp = await client.post(
            "/api/watchlist", json={"symbol": "TSLA", "market": "US"}
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 409

    async def test_invalid_market_returns_422(self, client):
        resp = await client.post(
            "/api/watchlist", json={"symbol": "AAPL", "market": "INVALID"}
        )
        assert resp.status_code == 422

    async def test_invalid_symbol_chars_returns_422(self, client):
        resp = await client.post(
            "/api/watchlist", json={"symbol": "../../etc", "market": "US"}
        )
        assert resp.status_code == 422

    async def test_symbol_too_long_returns_422(self, client):
        resp = await client.post(
            "/api/watchlist", json={"symbol": "A" * 21, "market": "US"}
        )
        assert resp.status_code == 422


class TestDeleteWatchlist:
    async def test_delete_existing(self, client):
        await client.post("/api/watchlist", json={"symbol": "MSFT", "market": "US"})
        resp = await client.delete("/api/watchlist/MSFT")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        # Confirm gone
        get_resp = await client.get("/api/watchlist")
        symbols = [i["symbol"] for i in get_resp.json()["data"]]
        assert "MSFT" not in symbols

    async def test_delete_nonexistent_returns_404(self, client):
        resp = await client.delete("/api/watchlist/NONEXISTENT")
        assert resp.status_code == 200
        assert resp.json()["code"] == 404
