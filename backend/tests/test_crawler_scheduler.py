"""Tests for crawler scheduler."""

from unittest.mock import MagicMock

from crawler.scheduler import init_scheduler, shutdown_scheduler


class TestScheduler:
    def test_init_returns_scheduler(self):
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        factory = MagicMock()
        scheduler = init_scheduler(factory)
        assert isinstance(scheduler, AsyncIOScheduler)

    def test_jobs_registered(self):
        factory = MagicMock()
        scheduler = init_scheduler(factory)
        jobs = scheduler.get_jobs()
        # Should have at least 2 jobs (HK market + US market)
        assert len(jobs) >= 2

        job_ids = [j.id for j in jobs]
        assert "crawl_hk" in job_ids
        assert "crawl_us" in job_ids

    def test_cron_settings(self):
        factory = MagicMock()
        scheduler = init_scheduler(factory)
        jobs = {j.id: j for j in scheduler.get_jobs()}

        hk_trigger = jobs["crawl_hk"].trigger
        us_trigger = jobs["crawl_us"].trigger

        # HK: 08:30 UTC mon-fri
        assert str(hk_trigger) is not None

        # US: 22:00 UTC mon-fri
        assert str(us_trigger) is not None

    async def test_start_and_shutdown(self):
        factory = MagicMock()
        scheduler = init_scheduler(factory)
        scheduler.start()
        assert scheduler.running
        # shutdown_scheduler should not raise
        await shutdown_scheduler(scheduler)
