"""Tests for fetcher extensions: earnings, dividends, HK fundamentals."""

from unittest.mock import MagicMock, patch

import pandas as pd

from services.fetcher import get_dividends, get_earnings, get_fundamentals


# ---------------------------------------------------------------------------
# T-17: Earnings
# ---------------------------------------------------------------------------


class TestGetEarningsYfinance:
    async def test_quarterly(self):
        # Mock yfinance Ticker with quarterly income statement
        mock_ticker = MagicMock()
        mock_ticker.quarterly_income_stmt = pd.DataFrame(
            {
                pd.Timestamp("2025-03-31"): {
                    "Total Revenue": 94836000000,
                    "Net Income": 23636000000,
                    "Basic EPS": 1.53,
                    "Gross Profit": 43000000000,
                    "Operating Income": 30000000000,
                },
                pd.Timestamp("2024-12-31"): {
                    "Total Revenue": 88000000000,
                    "Net Income": 20000000000,
                    "Basic EPS": 1.30,
                    "Gross Profit": 40000000000,
                    "Operating Income": 28000000000,
                },
            }
        )
        mock_ticker.income_stmt = pd.DataFrame(
            {
                pd.Timestamp("2024-12-31"): {
                    "Total Revenue": 350000000000,
                    "Net Income": 90000000000,
                    "Basic EPS": 5.80,
                    "Gross Profit": 160000000000,
                    "Operating Income": 120000000000,
                },
            }
        )
        with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_earnings("AAPL")

        assert len(result) == 3
        quarterly = [r for r in result if r["period_type"] == "quarterly"]
        annual = [r for r in result if r["period_type"] == "annual"]
        assert len(quarterly) == 2
        assert len(annual) == 1
        assert quarterly[0]["revenue"] == 94836000000
        assert quarterly[0]["period_end"] == "2025-03-31"

    async def test_empty_data(self):
        mock_ticker = MagicMock()
        mock_ticker.quarterly_income_stmt = pd.DataFrame()
        mock_ticker.income_stmt = pd.DataFrame()
        with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_earnings("AAPL")
        assert result == []


class TestGetEarningsHK:
    async def test_hk_earnings(self):
        fake_df = pd.DataFrame({
            "REPORT_DATE": ["2025-03-31", "2024-12-31"],
            "TOTAL_OPERATE_INCOME": [150000000000, 140000000000],
            "NETPROFIT": [40000000000, 38000000000],
            "BASIC_EPS": [4.2, 4.0],
            "TOTAL_PROFIT": [50000000000, 48000000000],
            "OPERATE_PROFIT": [45000000000, 43000000000],
        })
        with patch("akshare.stock_financial_hk_report_em", return_value=fake_df):
            result = await get_earnings("00700.HK")

        assert len(result) == 2
        assert result[0]["period_end"] == "2025-03-31"
        assert result[0]["revenue"] == 150000000000
        assert result[0]["period_type"] == "annual"


# ---------------------------------------------------------------------------
# T-19: Dividends
# ---------------------------------------------------------------------------


class TestGetDividendsYfinance:
    async def test_normal(self):
        mock_ticker = MagicMock()
        mock_ticker.dividends = pd.Series(
            [0.24, 0.25],
            index=pd.DatetimeIndex(["2025-02-07", "2025-05-09"]),
        )
        with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_dividends("AAPL")

        assert len(result) == 2
        assert result[0]["ex_date"] == "2025-02-07"
        assert result[0]["amount"] == 0.24
        assert result[0]["currency"] == "USD"

    async def test_empty(self):
        mock_ticker = MagicMock()
        mock_ticker.dividends = pd.Series([], dtype=float)
        with patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_dividends("AAPL")
        assert result == []


class TestGetDividendsHK:
    async def test_hk_dividends(self):
        fake_df = pd.DataFrame({
            "除净日": ["2025-05-16", "2024-05-17"],
            "分红方案": ["每股派港币4.5元", "每股派港币3.4元"],
            "分配类型": ["年度分配", "年度分配"],
        })
        with patch("akshare.stock_hk_dividend_payout_em", return_value=fake_df):
            result = await get_dividends("00700.HK")

        assert len(result) == 2
        assert result[0]["ex_date"] == "2025-05-16"
        assert result[0]["amount"] == 4.5
        assert result[0]["currency"] == "HKD"


# ---------------------------------------------------------------------------
# T-21: HK Fundamentals
# ---------------------------------------------------------------------------


class TestGetFundamentalsHK:
    async def test_hk_fundamentals(self):
        fake_df = pd.DataFrame({
            "代码": ["00700"],
            "最新价": [380.0],
            "市盈率(动态)": [25.3],
            "市净率": [5.1],
            "总市值": [3600000000000],
        })
        with patch("akshare.stock_hk_spot_em", return_value=fake_df):
            result = await get_fundamentals("00700.HK")

        assert result["symbol"] == "00700.HK"
        assert result["pe_ttm"] == 25.3
        assert result["pb"] == 5.1
        assert result["market_cap"] == 3600000000000

    async def test_hk_fundamentals_fallback_on_akshare_failure(self):
        """When akshare raises, yfinance fallback should provide data."""
        yf_info = {
            "trailingPE": 20.5, "priceToBook": 3.2, "marketCap": 3000000000000,
            "totalRevenue": 600000000000, "netIncomeToCommon": 150000000000,
            "dividendYield": 0.008,
        }
        mock_ticker = MagicMock()
        mock_ticker.info = yf_info
        with patch("akshare.stock_hk_spot_em", side_effect=Exception("network error")), \
             patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_fundamentals("00700.HK")

        assert result["pe_ttm"] == 20.5
        assert result["market_cap"] == 3000000000000
        assert result["revenue_ttm"] == 600000000000

    async def test_hk_fundamentals_fallback_on_not_found(self):
        """When akshare returns empty df, yfinance fallback should kick in."""
        empty_df = pd.DataFrame({"代码": [], "市盈率(动态)": [], "市净率": [], "总市值": []})
        yf_info = {"trailingPE": 10.0, "priceToBook": 1.5, "marketCap": 500000000000}
        mock_ticker = MagicMock()
        mock_ticker.info = yf_info
        with patch("akshare.stock_hk_spot_em", return_value=empty_df), \
             patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_fundamentals("00001.HK")

        assert result["pe_ttm"] == 10.0
        assert result["pb"] == 1.5


class TestHKEarningsFallback:
    async def test_earnings_fallback_on_akshare_failure(self):
        """When akshare earnings fails, yfinance should provide data."""
        mock_ticker = MagicMock()
        mock_ticker.quarterly_income_stmt = pd.DataFrame()
        mock_ticker.income_stmt = pd.DataFrame({
            pd.Timestamp("2024-12-31"): {
                "Total Revenue": 100000000000,
                "Net Income": 25000000000,
                "Basic EPS": 2.5,
                "Gross Profit": 50000000000,
                "Operating Income": 35000000000,
            },
        })
        with patch("akshare.stock_financial_hk_report_em", side_effect=Exception("fail")), \
             patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_earnings("00700.HK")

        assert len(result) == 1
        assert result[0]["revenue"] == 100000000000


class TestHKDividendsFallback:
    async def test_dividends_fallback_on_akshare_failure(self):
        """When akshare dividends fails, yfinance should provide data."""
        mock_ticker = MagicMock()
        mock_ticker.dividends = pd.Series(
            [1.5], index=pd.DatetimeIndex(["2025-06-01"]),
        )
        with patch("akshare.stock_hk_dividend_payout_em", side_effect=Exception("fail")), \
             patch("services.fetcher.yf.Ticker", return_value=mock_ticker):
            result = await get_dividends("00700.HK")

        assert len(result) == 1
        assert result[0]["amount"] == 1.5
