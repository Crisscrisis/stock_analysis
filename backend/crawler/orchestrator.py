"""Orchestrator — coordinates crawling for an index or all indices."""
from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from crawler.collectors import collect_all_for_stock
from crawler.registry import all_indices, get_index
from crawler.report import CollectionReport, StockResult
from models.index_constituent import IndexConstituent

logger = logging.getLogger(__name__)

_SEMAPHORE_LIMIT = 5


async def _reconcile_constituents(
    db: AsyncSession,
    index_name: str,
    market: str,
    fresh_list: list[dict[str, str]],
) -> tuple[list[str], list[str]]:
    """Compare fresh constituent list with DB, return (added, removed)."""
    # Load existing constituents from DB
    result = await db.execute(
        select(IndexConstituent).where(
            IndexConstituent.index_name == index_name,
        )
    )
    existing = {row.symbol: row for row in result.scalars().all()}
    fresh_symbols = {item["symbol"] for item in fresh_list}
    fresh_by_symbol = {item["symbol"]: item for item in fresh_list}

    added: list[str] = []
    removed: list[str] = []
    now = time.time()

    # Handle new or rejoining constituents
    for symbol in fresh_symbols:
        if symbol in existing:
            row = existing[symbol]
            if not row.is_active:
                # Rejoin
                row.is_active = True
                row.removed_at = None
                added.append(symbol)
        else:
            # Brand new
            db.add(IndexConstituent(
                index_name=index_name,
                symbol=symbol,
                name=fresh_by_symbol[symbol].get("name"),
                market=market,
                is_active=True,
                added_at=now,
            ))
            added.append(symbol)

    # Handle removals
    for symbol, row in existing.items():
        if symbol not in fresh_symbols and row.is_active:
            row.is_active = False
            row.removed_at = now
            removed.append(symbol)

    await db.commit()
    return added, removed


async def crawl_index(
    session_factory: async_sessionmaker,
    index_name: str,
    already_collected: set[str] | None = None,
    backfill: bool = False,
) -> CollectionReport:
    """Crawl all active constituents of an index."""
    start = time.time()
    config = get_index(index_name)

    if already_collected is None:
        already_collected = set()

    # 1. Fetch fresh constituent list
    fresh_list = await config.fetch_constituents()

    async with session_factory() as db:
        # 2. Validate count
        min_count, max_count = config.expected_count
        if fresh_list and not (min_count <= len(fresh_list) <= max_count):
            logger.warning(
                "%s: abnormal constituent count %d (expected %d-%d), using DB list",
                index_name, len(fresh_list), min_count, max_count,
            )
            fresh_list = []  # Will fallback to DB

        # 3. If empty, fallback to existing DB list
        if not fresh_list:
            result = await db.execute(
                select(IndexConstituent).where(
                    IndexConstituent.index_name == index_name,
                    IndexConstituent.is_active == True,  # noqa: E712
                )
            )
            db_constituents = result.scalars().all()
            active_symbols = [
                {"symbol": r.symbol, "name": r.name or ""}
                for r in db_constituents
            ]
            added, removed = [], []
        else:
            # 4. Reconcile
            added, removed = await _reconcile_constituents(
                db, index_name, config.market, fresh_list
            )
            active_symbols = fresh_list

    # 5. Collect data for each active constituent
    sem = asyncio.Semaphore(_SEMAPHORE_LIMIT)
    succeeded = 0
    failed = 0
    skipped = 0
    failures: list[StockResult] = []

    async def _collect_one(symbol_info: dict[str, str]) -> None:
        nonlocal succeeded, failed, skipped
        symbol = symbol_info["symbol"]
        name = symbol_info.get("name", "")

        if symbol in already_collected:
            skipped += 1
            return

        async with sem:
            async with session_factory() as db:
                try:
                    result = await collect_all_for_stock(
                        db, symbol, config.market, backfill=backfill,
                    )
                    already_collected.add(symbol)
                    if all(result.values()):
                        succeeded += 1
                    else:
                        failed += 1
                        failures.append(StockResult(
                            symbol=symbol,
                            name=name,
                            success=result,
                            error_message="partial failure",
                        ))
                except Exception as e:
                    failed += 1
                    already_collected.add(symbol)
                    failures.append(StockResult(
                        symbol=symbol,
                        name=name,
                        success={},
                        error_message=str(e),
                    ))

    tasks = [_collect_one(s) for s in active_symbols]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start
    return CollectionReport(
        index_name=index_name,
        total=len(active_symbols),
        succeeded=succeeded,
        failed=failed,
        skipped=skipped,
        added=added,
        removed=removed,
        failures=failures,
        elapsed_seconds=elapsed,
    )


async def crawl_all(
    session_factory: async_sessionmaker,
    backfill: bool = False,
) -> list[CollectionReport]:
    """Crawl all registered indices sequentially, deduplicating across indices."""
    collected: set[str] = set()
    reports: list[CollectionReport] = []

    for idx_config in all_indices():
        report = await crawl_index(
            session_factory, idx_config.name,
            already_collected=collected, backfill=backfill,
        )
        reports.append(report)

    return reports
