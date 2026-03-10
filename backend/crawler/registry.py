"""Index registry — defines which indices to crawl and how."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Awaitable

from crawler.constituents import fetch_nasdaq100, fetch_hsi, fetch_hstech


@dataclass(frozen=True)
class IndexConfig:
    name: str
    market: str
    expected_count: tuple[int, int]
    cron_hour: int
    cron_minute: int
    fetch_constituents: Callable[[], Awaitable[list[dict[str, str]]]]


INDICES: dict[str, IndexConfig] = {
    "NASDAQ100": IndexConfig(
        name="NASDAQ100",
        market="US",
        expected_count=(90, 110),
        cron_hour=22,
        cron_minute=0,
        fetch_constituents=fetch_nasdaq100,
    ),
    "HSI": IndexConfig(
        name="HSI",
        market="HK",
        expected_count=(50, 90),
        cron_hour=8,
        cron_minute=30,
        fetch_constituents=fetch_hsi,
    ),
    "HSTECH": IndexConfig(
        name="HSTECH",
        market="HK",
        expected_count=(20, 40),
        cron_hour=8,
        cron_minute=30,
        fetch_constituents=fetch_hstech,
    ),
}


def get_index(name: str) -> IndexConfig:
    return INDICES[name]


def all_indices() -> list[IndexConfig]:
    return list(INDICES.values())
