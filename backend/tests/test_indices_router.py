"""Integration tests for indices API endpoints."""
import time

import pytest
from sqlalchemy import insert

from models.index_constituent import IndexConstituent


async def _seed_constituents(db_session):
    """Insert sample constituents for testing."""
    now = time.time()
    rows = [
        {"index_name": "NASDAQ100", "symbol": "AAPL", "name": "Apple Inc.", "market": "US", "is_active": True, "added_at": now},
        {"index_name": "NASDAQ100", "symbol": "MSFT", "name": "Microsoft Corp.", "market": "US", "is_active": True, "added_at": now},
        {"index_name": "NASDAQ100", "symbol": "INTC", "name": "Intel Corp.", "market": "US", "is_active": False, "added_at": now, "removed_at": now},
        {"index_name": "HSI", "symbol": "00700.HK", "name": "Tencent", "market": "HK", "is_active": True, "added_at": now},
    ]
    await db_session.execute(insert(IndexConstituent), rows)
    await db_session.commit()


class TestListIndices:
    async def test_empty(self, client):
        resp = await client.get("/api/indices")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"] == []

    async def test_returns_indices_with_active_count(self, client, db_session):
        await _seed_constituents(db_session)
        resp = await client.get("/api/indices")
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        assert len(data) == 2
        by_name = {d["name"]: d for d in data}
        assert by_name["HSI"]["active_count"] == 1
        assert by_name["HSI"]["market"] == "HK"
        # NASDAQ100 has 2 active out of 3 total
        assert by_name["NASDAQ100"]["active_count"] == 2
        assert by_name["NASDAQ100"]["market"] == "US"


class TestGetConstituents:
    async def test_unknown_index(self, client):
        resp = await client.get("/api/indices/UNKNOWN/constituents")
        body = resp.json()
        assert body["code"] == 404
        assert body["data"] is None

    async def test_returns_constituents(self, client, db_session):
        await _seed_constituents(db_session)
        resp = await client.get("/api/indices/NASDAQ100/constituents")
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        assert len(data) == 3
        symbols = [c["symbol"] for c in data]
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "INTC" in symbols
        # Check inactive flag
        intc = next(c for c in data if c["symbol"] == "INTC")
        assert intc["is_active"] is False

    async def test_hsi_constituents(self, client, db_session):
        await _seed_constituents(db_session)
        resp = await client.get("/api/indices/HSI/constituents")
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]) == 1
        assert body["data"][0]["symbol"] == "00700.HK"
