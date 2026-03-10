"""Tests for crawler orchestrator: reconcile, crawl_index, crawl_all."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from models.index_constituent import IndexConstituent
from crawler.report import CollectionReport


# ---------------------------------------------------------------------------
# T-33: _reconcile_constituents
# ---------------------------------------------------------------------------


class TestReconcileConstituents:
    async def test_fresh_index(self, db_engine):
        from crawler.orchestrator import _reconcile_constituents

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            fresh = [
                {"symbol": "AAPL", "name": "Apple Inc."},
                {"symbol": "MSFT", "name": "Microsoft Corp."},
            ]
            added, removed = await _reconcile_constituents(
                session, "NASDAQ100", "US", fresh
            )

        assert set(added) == {"AAPL", "MSFT"}
        assert removed == []

        # Verify DB state
        async with factory() as session:
            rows = (await session.execute(
                select(IndexConstituent).where(
                    IndexConstituent.index_name == "NASDAQ100"
                )
            )).scalars().all()
            assert len(rows) == 2
            assert all(r.is_active for r in rows)

    async def test_no_change(self, db_engine):
        from crawler.orchestrator import _reconcile_constituents

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        # Pre-populate
        async with factory() as session:
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="AAPL", name="Apple",
                market="US", is_active=True, added_at=time.time(),
            ))
            await session.commit()

        async with factory() as session:
            added, removed = await _reconcile_constituents(
                session, "NASDAQ100", "US",
                [{"symbol": "AAPL", "name": "Apple Inc."}],
            )
        assert added == []
        assert removed == []

    async def test_new_constituent_added(self, db_engine):
        from crawler.orchestrator import _reconcile_constituents

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="AAPL", name="Apple",
                market="US", is_active=True, added_at=time.time(),
            ))
            await session.commit()

        async with factory() as session:
            added, removed = await _reconcile_constituents(
                session, "NASDAQ100", "US",
                [
                    {"symbol": "AAPL", "name": "Apple"},
                    {"symbol": "MSFT", "name": "Microsoft"},
                ],
            )
        assert added == ["MSFT"]
        assert removed == []

    async def test_constituent_removed(self, db_engine):
        from crawler.orchestrator import _reconcile_constituents

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="AAPL", name="Apple",
                market="US", is_active=True, added_at=time.time(),
            ))
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="OLD1", name="Old Stock",
                market="US", is_active=True, added_at=time.time(),
            ))
            await session.commit()

        async with factory() as session:
            added, removed = await _reconcile_constituents(
                session, "NASDAQ100", "US",
                [{"symbol": "AAPL", "name": "Apple"}],
            )
        assert added == []
        assert removed == ["OLD1"]

        # Verify OLD1 is marked inactive
        async with factory() as session:
            row = (await session.execute(
                select(IndexConstituent).where(
                    IndexConstituent.symbol == "OLD1",
                    IndexConstituent.index_name == "NASDAQ100",
                )
            )).scalar_one()
            assert row.is_active is False
            assert row.removed_at is not None

    async def test_rejoin_after_removal(self, db_engine):
        from crawler.orchestrator import _reconcile_constituents

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="AAPL", name="Apple",
                market="US", is_active=False, added_at=time.time(),
                removed_at=time.time(),
            ))
            await session.commit()

        async with factory() as session:
            added, removed = await _reconcile_constituents(
                session, "NASDAQ100", "US",
                [{"symbol": "AAPL", "name": "Apple Inc."}],
            )
        assert added == ["AAPL"]
        assert removed == []

        async with factory() as session:
            row = (await session.execute(
                select(IndexConstituent).where(
                    IndexConstituent.symbol == "AAPL",
                    IndexConstituent.index_name == "NASDAQ100",
                )
            )).scalar_one()
            assert row.is_active is True
            assert row.removed_at is None


# ---------------------------------------------------------------------------
# T-35: crawl_index
# ---------------------------------------------------------------------------


class TestCrawlIndex:
    def _mock_config(self, constituents):
        from crawler.registry import IndexConfig
        return IndexConfig(
            name="NASDAQ100",
            market="US",
            expected_count=(2, 5),
            cron_hour=22,
            cron_minute=0,
            fetch_constituents=AsyncMock(return_value=constituents),
        )

    async def test_normal_flow(self, db_engine):
        from crawler.orchestrator import crawl_index

        config = self._mock_config([
            {"symbol": "AAPL", "name": "Apple"},
            {"symbol": "MSFT", "name": "Microsoft"},
        ])
        with patch("crawler.orchestrator.get_index", return_value=config):
            with patch("crawler.orchestrator.collect_all_for_stock", AsyncMock(
                return_value={"ohlcv": True, "fundamentals": True, "earnings": True, "dividends": True}
            )):
                factory = async_sessionmaker(db_engine, expire_on_commit=False)
                report = await crawl_index(factory, "NASDAQ100")

        assert isinstance(report, CollectionReport)
        assert report.total == 2
        assert report.succeeded == 2
        assert report.failed == 0

    async def test_already_collected_dedup(self, db_engine):
        from crawler.orchestrator import crawl_index

        config = self._mock_config([
            {"symbol": "AAPL", "name": "Apple"},
            {"symbol": "MSFT", "name": "Microsoft"},
        ])
        with patch("crawler.orchestrator.get_index", return_value=config):
            with patch("crawler.orchestrator.collect_all_for_stock", AsyncMock(
                return_value={"ohlcv": True, "fundamentals": True, "earnings": True, "dividends": True}
            )):
                factory = async_sessionmaker(db_engine, expire_on_commit=False)
                report = await crawl_index(
                    factory, "NASDAQ100", already_collected={"AAPL"}
                )

        assert report.skipped == 1
        assert report.succeeded == 1

    async def test_abnormal_count_uses_db(self, db_engine):
        from crawler.orchestrator import crawl_index

        # Pre-populate DB with existing constituents
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="AAPL", name="Apple",
                market="US", is_active=True, added_at=time.time(),
            ))
            await session.commit()

        # Config returns too few constituents (below expected_count range)
        config = self._mock_config([{"symbol": "ONLY_ONE", "name": "X"}])
        # expected_count is (2, 5), so 1 is below threshold

        with patch("crawler.orchestrator.get_index", return_value=config):
            with patch("crawler.orchestrator.collect_all_for_stock", AsyncMock(
                return_value={"ohlcv": True, "fundamentals": True, "earnings": True, "dividends": True}
            )):
                report = await crawl_index(factory, "NASDAQ100")

        # Should fallback to DB list (AAPL), not the abnormal list
        assert report.total == 1

    async def test_fetch_failure_fallback(self, db_engine):
        from crawler.orchestrator import crawl_index

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            session.add(IndexConstituent(
                index_name="NASDAQ100", symbol="AAPL", name="Apple",
                market="US", is_active=True, added_at=time.time(),
            ))
            await session.commit()

        # Config fetch fails
        from crawler.registry import IndexConfig
        config = IndexConfig(
            name="NASDAQ100", market="US", expected_count=(2, 5),
            cron_hour=22, cron_minute=0,
            fetch_constituents=AsyncMock(return_value=[]),
        )

        with patch("crawler.orchestrator.get_index", return_value=config):
            with patch("crawler.orchestrator.collect_all_for_stock", AsyncMock(
                return_value={"ohlcv": True, "fundamentals": True, "earnings": True, "dividends": True}
            )):
                report = await crawl_index(factory, "NASDAQ100")

        # Should use DB list
        assert report.total == 1


# ---------------------------------------------------------------------------
# T-37: crawl_all
# ---------------------------------------------------------------------------


class TestCrawlAll:
    async def test_calls_all_indices(self, db_engine):
        from crawler.orchestrator import crawl_all

        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        fake_report = CollectionReport(
            index_name="TEST", total=5, succeeded=5, failed=0, skipped=0,
        )
        with patch("crawler.orchestrator.crawl_index", AsyncMock(return_value=fake_report)) as mock_crawl:
            reports = await crawl_all(factory)

        assert len(reports) == 3
        # Verify all three indices were called
        called_names = [call.args[1] for call in mock_crawl.call_args_list]
        assert "NASDAQ100" in called_names
        assert "HSI" in called_names
        assert "HSTECH" in called_names

    async def test_collected_set_passed(self, db_engine):
        from crawler.orchestrator import crawl_all

        factory = async_sessionmaker(db_engine, expire_on_commit=False)

        call_args = []

        async def fake_crawl(sf, name, already_collected=None, backfill=False):
            call_args.append((name, set(already_collected) if already_collected else set()))
            # Simulate adding symbols to the collected set
            if already_collected is not None:
                already_collected.add(f"SYM_{name}")
            return CollectionReport(
                index_name=name, total=1, succeeded=1, failed=0, skipped=0,
            )

        with patch("crawler.orchestrator.crawl_index", side_effect=fake_crawl):
            with patch("crawler.orchestrator.all_indices", return_value=[
                type("IC", (), {"name": "A"})(),
                type("IC", (), {"name": "B"})(),
            ]):
                reports = await crawl_all(factory)

        assert len(reports) == 2
        # Second call should have the symbol from the first call
        assert "SYM_A" in call_args[1][1]
