"""Tests for index registry and constituent fetchers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from crawler.registry import IndexConfig, INDICES, get_index, all_indices


# ---------------------------------------------------------------------------
# T-10: Index registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_index_config_structure(self):
        cfg = INDICES["NASDAQ100"]
        assert isinstance(cfg, IndexConfig)
        assert cfg.name == "NASDAQ100"
        assert cfg.market == "US"
        assert callable(cfg.fetch_constituents)

    def test_all_three_indices(self):
        assert "NASDAQ100" in INDICES
        assert "HSI" in INDICES
        assert "HSTECH" in INDICES

    def test_get_index(self):
        cfg = get_index("HSI")
        assert cfg.market == "HK"

    def test_get_index_unknown(self):
        with pytest.raises(KeyError):
            get_index("SP500")

    def test_all_indices(self):
        result = all_indices()
        assert len(result) == 3
        names = [c.name for c in result]
        assert "NASDAQ100" in names


# ---------------------------------------------------------------------------
# T-12: NASDAQ-100 constituent fetcher
# ---------------------------------------------------------------------------


class TestFetchNasdaq100:
    async def test_returns_correct_format(self):
        from crawler.constituents import fetch_nasdaq100

        fake_df = pd.DataFrame({
            "Ticker": ["AAPL", "MSFT", "GOOG"],
            "Company": ["Apple Inc.", "Microsoft Corp.", "Alphabet Inc."],
        })
        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        mock_resp.raise_for_status = MagicMock()
        with patch("crawler.constituents.requests.get", return_value=mock_resp):
            with patch("crawler.constituents.pd.read_html", return_value=[fake_df]):
                result = await fetch_nasdaq100()

        assert len(result) == 3
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["name"] == "Apple Inc."

    async def test_symbol_no_prefix(self):
        from crawler.constituents import fetch_nasdaq100

        fake_df = pd.DataFrame({
            "Ticker": ["  AAPL  ", "MSFT"],
            "Company": ["Apple", "Microsoft"],
        })
        mock_resp = MagicMock()
        mock_resp.text = "<html></html>"
        mock_resp.raise_for_status = MagicMock()
        with patch("crawler.constituents.requests.get", return_value=mock_resp):
            with patch("crawler.constituents.pd.read_html", return_value=[fake_df]):
                result = await fetch_nasdaq100()

        assert result[0]["symbol"] == "AAPL"  # stripped

    async def test_exception_returns_empty(self):
        from crawler.constituents import fetch_nasdaq100

        with patch("crawler.constituents.requests.get", side_effect=Exception("network")):
            result = await fetch_nasdaq100()

        assert result == []


# ---------------------------------------------------------------------------
# T-14: HSI / HSTECH constituent fetchers (HSI official JSON API)
# ---------------------------------------------------------------------------


def _mock_hsi_api_response(constituents: list[dict]) -> MagicMock:
    """Build a mock requests.Response mimicking the HSI API JSON."""
    content = [{"code": c["code"], "constituentName": c["name"]} for c in constituents]
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "indexSeriesList": [{
            "indexList": [{
                "constituentContent": content,
            }],
        }],
    }
    return mock_resp


class TestFetchHSI:
    async def test_returns_correct_format(self):
        from crawler.constituents import fetch_hsi

        mock_resp = _mock_hsi_api_response([
            {"code": "700", "name": "TENCENT"},
            {"code": "9988", "name": "ALIBABA-SW"},
            {"code": "1810", "name": "XIAOMI-W"},
        ])
        with patch("crawler.constituents.requests.get", return_value=mock_resp):
            result = await fetch_hsi()

        assert len(result) == 3
        assert result[0]["symbol"] == "00700.HK"
        assert result[0]["name"] == "TENCENT"
        # Code should be zero-padded to 5 digits
        assert result[1]["symbol"] == "09988.HK"

    async def test_exception_returns_empty(self):
        from crawler.constituents import fetch_hsi

        with patch("crawler.constituents.requests.get", side_effect=Exception("err")):
            result = await fetch_hsi()
        assert result == []


class TestFetchHSTECH:
    async def test_returns_correct_format(self):
        from crawler.constituents import fetch_hstech

        mock_resp = _mock_hsi_api_response([
            {"code": "700", "name": "TENCENT"},
            {"code": "3690", "name": "MEITUAN-W"},
        ])
        with patch("crawler.constituents.requests.get", return_value=mock_resp):
            result = await fetch_hstech()

        assert len(result) == 2
        assert result[0]["symbol"] == "00700.HK"

    async def test_exception_returns_empty(self):
        from crawler.constituents import fetch_hstech

        with patch("crawler.constituents.requests.get", side_effect=Exception("err")):
            result = await fetch_hstech()
        assert result == []
