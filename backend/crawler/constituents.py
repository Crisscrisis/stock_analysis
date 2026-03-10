"""Constituent list fetchers for each index."""
from __future__ import annotations

import asyncio
import logging
import re
from io import StringIO

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

NASDAQ100_WIKI_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"

# Hang Seng Indexes official JSON API
_HSI_API = "https://www.hsi.com.hk/data/eng/rt/index-series/{series}/constituents.do"


# ---------------------------------------------------------------------------
# NASDAQ-100 — Wikipedia
# ---------------------------------------------------------------------------

def _sync_fetch_nasdaq100() -> list[dict[str, str]]:
    resp = requests.get(NASDAQ100_WIKI_URL, headers=_HTTP_HEADERS, timeout=15)
    resp.raise_for_status()
    tables = pd.read_html(StringIO(resp.text))
    for t in tables:
        if "Ticker" in t.columns:
            result = []
            for _, row in t.iterrows():
                symbol = str(row["Ticker"]).strip()
                name = str(row.get("Company", "")).strip()
                result.append({"symbol": symbol, "name": name})
            return result
    return []


async def fetch_nasdaq100() -> list[dict[str, str]]:
    """Fetch NASDAQ-100 constituents from Wikipedia."""
    try:
        return await asyncio.to_thread(_sync_fetch_nasdaq100)
    except Exception:
        logger.exception("Failed to fetch NASDAQ-100 constituents")
        return []


# ---------------------------------------------------------------------------
# HSI / HSTECH — Hang Seng Indexes official API
# ---------------------------------------------------------------------------

def _sync_fetch_hsi_api(series: str) -> list[dict[str, str]]:
    """Fetch constituents from HSI official JSON API."""
    url = _HSI_API.format(series=series)
    resp = requests.get(url, headers=_HTTP_HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    result = []
    for idx_series in data.get("indexSeriesList", []):
        for idx in idx_series.get("indexList", []):
            for c in idx.get("constituentContent", []):
                code = str(c.get("code", "")).strip()
                name = str(c.get("constituentName", "")).strip()
                if code:
                    # Pad to 5 digits: "5" -> "00005"
                    code = code.zfill(5)
                    result.append({"symbol": f"{code}.HK", "name": name})
    return result


async def fetch_hsi() -> list[dict[str, str]]:
    """Fetch Hang Seng Index constituents from official API."""
    try:
        return await asyncio.to_thread(_sync_fetch_hsi_api, "hsi")
    except Exception:
        logger.exception("Failed to fetch HSI constituents")
        return []


async def fetch_hstech() -> list[dict[str, str]]:
    """Fetch Hang Seng TECH Index constituents from official API."""
    try:
        return await asyncio.to_thread(_sync_fetch_hsi_api, "hstech")
    except Exception:
        logger.exception("Failed to fetch HSTECH constituents")
        return []
