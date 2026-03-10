"""APScheduler integration for scheduled crawling."""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from crawler.orchestrator import crawl_index

logger = logging.getLogger(__name__)


def init_scheduler(session_factory: async_sessionmaker) -> AsyncIOScheduler:
    """Create and configure the scheduler with cron jobs."""
    scheduler = AsyncIOScheduler()

    async def _crawl_hk() -> None:
        logger.info("Scheduled crawl starting: HSI + HSTECH")
        for name in ("HSI", "HSTECH"):
            try:
                report = await crawl_index(session_factory, name)
                report.print_summary()
            except Exception:
                logger.exception("Scheduled crawl failed for %s", name)

    async def _crawl_us() -> None:
        logger.info("Scheduled crawl starting: NASDAQ100")
        try:
            report = await crawl_index(session_factory, "NASDAQ100")
            report.print_summary()
        except Exception:
            logger.exception("Scheduled crawl failed for NASDAQ100")

    # HK market: 16:30 HKT = 08:30 UTC, mon-fri
    scheduler.add_job(
        _crawl_hk,
        "cron",
        id="crawl_hk",
        hour=8,
        minute=30,
        day_of_week="mon-fri",
    )

    # US market: 17:00 ET ≈ 22:00 UTC, mon-fri
    scheduler.add_job(
        _crawl_us,
        "cron",
        id="crawl_us",
        hour=22,
        minute=0,
        day_of_week="mon-fri",
    )

    return scheduler


async def start_scheduler(session_factory: async_sessionmaker) -> AsyncIOScheduler:
    """Initialize and start the scheduler."""
    scheduler = init_scheduler(session_factory)
    scheduler.start()
    logger.info("Crawler scheduler started")
    return scheduler


async def shutdown_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Crawler scheduler stopped")
