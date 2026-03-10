"""Tests for crawler data models: IndexConstituent, Earnings, Dividend."""

import time

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models.index_constituent import IndexConstituent
from models.earnings import Earnings
from models.dividend import Dividend


# ---------------------------------------------------------------------------
# T-01: IndexConstituent
# ---------------------------------------------------------------------------


class TestIndexConstituent:
    async def test_create_table(self, db_session):
        """Table should exist after create_all."""
        result = await db_session.execute(select(IndexConstituent))
        assert result.scalars().all() == []

    async def test_insert_and_query(self, db_session):
        row = IndexConstituent(
            index_name="NASDAQ100",
            symbol="AAPL",
            name="Apple Inc.",
            market="US",
            is_active=True,
            added_at=time.time(),
        )
        db_session.add(row)
        await db_session.commit()

        result = await db_session.execute(
            select(IndexConstituent).where(IndexConstituent.symbol == "AAPL")
        )
        fetched = result.scalar_one()
        assert fetched.index_name == "NASDAQ100"
        assert fetched.market == "US"
        assert fetched.is_active is True

    async def test_unique_constraint(self, db_session):
        """(index_name, symbol) must be unique."""
        for _ in range(2):
            db_session.add(IndexConstituent(
                index_name="HSI", symbol="00700.HK", market="HK",
                is_active=True, added_at=time.time(),
            ))
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_is_active_default(self, db_session):
        row = IndexConstituent(
            index_name="NASDAQ100", symbol="MSFT", market="US",
            added_at=time.time(),
        )
        db_session.add(row)
        await db_session.commit()
        await db_session.refresh(row)
        assert row.is_active is True

    async def test_removed_at_nullable(self, db_session):
        row = IndexConstituent(
            index_name="HSI", symbol="00700.HK", market="HK",
            is_active=True, added_at=time.time(),
        )
        db_session.add(row)
        await db_session.commit()
        await db_session.refresh(row)
        assert row.removed_at is None


# ---------------------------------------------------------------------------
# T-03: Earnings
# ---------------------------------------------------------------------------


class TestEarnings:
    async def test_create_table(self, db_session):
        result = await db_session.execute(select(Earnings))
        assert result.scalars().all() == []

    async def test_insert_and_query(self, db_session):
        row = Earnings(
            symbol="AAPL",
            period_end="2025-03-31",
            period_type="quarterly",
            revenue=94836000000,
            net_income=23636000000,
            eps=1.53,
            gross_profit=43000000000,
            operating_income=30000000000,
            updated_ts=int(time.time()),
        )
        db_session.add(row)
        await db_session.commit()

        result = await db_session.execute(
            select(Earnings).where(Earnings.symbol == "AAPL")
        )
        fetched = result.scalar_one()
        assert fetched.period_type == "quarterly"
        assert fetched.revenue == 94836000000

    async def test_unique_constraint(self, db_session):
        """(symbol, period_end, period_type) must be unique."""
        for _ in range(2):
            db_session.add(Earnings(
                symbol="AAPL", period_end="2025-03-31", period_type="quarterly",
                updated_ts=int(time.time()),
            ))
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_nullable_fields(self, db_session):
        row = Earnings(
            symbol="MSFT", period_end="2025-06-30", period_type="annual",
            updated_ts=int(time.time()),
        )
        db_session.add(row)
        await db_session.commit()
        await db_session.refresh(row)
        assert row.revenue is None
        assert row.net_income is None
        assert row.eps is None


# ---------------------------------------------------------------------------
# T-05: Dividend
# ---------------------------------------------------------------------------


class TestDividend:
    async def test_create_table(self, db_session):
        result = await db_session.execute(select(Dividend))
        assert result.scalars().all() == []

    async def test_insert_and_query(self, db_session):
        row = Dividend(
            symbol="AAPL",
            ex_date="2025-02-07",
            amount=0.25,
            currency="USD",
            updated_ts=int(time.time()),
        )
        db_session.add(row)
        await db_session.commit()

        result = await db_session.execute(
            select(Dividend).where(Dividend.symbol == "AAPL")
        )
        fetched = result.scalar_one()
        assert fetched.amount == 0.25
        assert fetched.currency == "USD"

    async def test_unique_constraint(self, db_session):
        """(symbol, ex_date) must be unique."""
        for _ in range(2):
            db_session.add(Dividend(
                symbol="AAPL", ex_date="2025-02-07",
                amount=0.25, currency="USD",
                updated_ts=int(time.time()),
            ))
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_currency_default(self, db_session):
        row = Dividend(
            symbol="MSFT", ex_date="2025-03-15",
            amount=0.75, updated_ts=int(time.time()),
        )
        db_session.add(row)
        await db_session.commit()
        await db_session.refresh(row)
        assert row.currency == "USD"
