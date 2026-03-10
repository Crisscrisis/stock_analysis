"""Tests for the CLI database viewer tool."""

import os
import sqlite3
import tempfile

import pytest

from cli import (
    build_parser,
    cmd_fundamentals,
    cmd_ohlcv,
    cmd_stats,
    cmd_watchlist,
    fmt_datetime,
    fmt_float,
    fmt_ts,
    main,
    print_table,
)


@pytest.fixture()
def tmp_db(tmp_path):
    """Create a temporary SQLite database with test data."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables matching the ORM models
    cur.execute("""
        CREATE TABLE ohlcv_bar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            UNIQUE(symbol, interval, timestamp)
        )
    """)

    cur.execute("""
        CREATE TABLE fundamentals_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            pe_ttm REAL,
            pb REAL,
            market_cap REAL,
            revenue_ttm REAL,
            net_profit_ttm REAL,
            dividend_yield REAL,
            updated_ts INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            name TEXT,
            market TEXT NOT NULL,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert test data
    # OHLCV: 3 bars for AAPL, 2 bars for MSFT
    ohlcv_data = [
        ("AAPL", "1d", 1704067200, 185.0, 186.5, 184.0, 185.5, 50000000),  # 2024-01-01
        ("AAPL", "1d", 1704153600, 185.5, 187.0, 185.0, 186.0, 48000000),  # 2024-01-02
        ("AAPL", "1d", 1704240000, 186.0, 188.0, 185.5, 187.5, 52000000),  # 2024-01-03
        ("MSFT", "1d", 1704067200, 370.0, 372.0, 369.0, 371.0, 30000000),  # 2024-01-01
        ("MSFT", "1d", 1704153600, 371.0, 373.0, 370.0, 372.5, 28000000),  # 2024-01-02
    ]
    cur.executemany(
        "INSERT INTO ohlcv_bar (symbol, interval, timestamp, open, high, low, close, volume) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ohlcv_data,
    )

    # Fundamentals
    fund_data = [
        ("AAPL", 28.5, 45.2, 2800000000000, 383000000000, 97000000000, 0.55, 1704067200),
        ("MSFT", 35.1, 12.8, 2700000000000, 211000000000, 72000000000, 0.82, 1704067200),
    ]
    cur.executemany(
        "INSERT INTO fundamentals_cache "
        "(symbol, pe_ttm, pb, market_cap, revenue_ttm, net_profit_ttm, dividend_yield, updated_ts) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        fund_data,
    )

    # Watchlist
    cur.execute(
        "INSERT INTO watchlist (symbol, name, market, added_at) VALUES (?, ?, ?, ?)",
        ("AAPL", "Apple Inc.", "US", "2024-01-01 10:00:00"),
    )
    cur.execute(
        "INSERT INTO watchlist (symbol, name, market, added_at) VALUES (?, ?, ?, ?)",
        ("00700.HK", "Tencent", "HK", "2024-01-02 12:00:00"),
    )

    conn.commit()
    conn.close()
    return db_path


# --- Unit tests for helper functions ---


class TestFmtFloat:
    def test_normal(self):
        assert fmt_float(123.456) == "123.46"

    def test_none(self):
        assert fmt_float(None) == "-"

    def test_zero_decimals(self):
        assert fmt_float(50000000, 0) == "50,000,000"

    def test_large_number(self):
        assert fmt_float(2800000000000.0) == "2,800,000,000,000.00"


class TestFmtTs:
    def test_normal(self):
        assert fmt_ts(1704067200) == "2024-01-01"

    def test_none(self):
        assert fmt_ts(None) == "-"


class TestFmtDatetime:
    def test_normal(self):
        assert fmt_datetime("2024-01-01 10:00:00") == "2024-01-01 10:00:00"

    def test_with_microseconds(self):
        assert fmt_datetime("2024-01-01 10:00:00.123456") == "2024-01-01 10:00:00"

    def test_none(self):
        assert fmt_datetime(None) == "-"


class TestPrintTable:
    def test_normal(self, capsys):
        print_table(["A", "B"], [["1", "22"], ["333", "4"]])
        out = capsys.readouterr().out
        lines = out.strip().split("\n")
        assert len(lines) == 4  # header + separator + 2 rows
        assert "A" in lines[0]
        assert "---" in lines[1]

    def test_empty(self, capsys):
        print_table(["A"], [])
        out = capsys.readouterr().out
        assert "(no data)" in out


# --- Integration tests for commands ---


class TestCmdStats:
    def test_stats(self, tmp_db, capsys):
        main(["--db", tmp_db, "stats"])
        out = capsys.readouterr().out
        assert "ohlcv_bar: 5 rows" in out
        assert "fundamentals_cache: 2 rows" in out
        assert "watchlist: 2 rows" in out
        assert "2024-01-01" in out


class TestCmdWatchlist:
    def test_list(self, tmp_db, capsys):
        main(["--db", tmp_db, "watchlist"])
        out = capsys.readouterr().out
        assert "AAPL" in out
        assert "Apple Inc." in out
        assert "00700.HK" in out
        assert "Tencent" in out
        assert "US" in out
        assert "HK" in out


class TestCmdOhlcv:
    def test_list(self, tmp_db, capsys):
        main(["--db", tmp_db, "ohlcv", "--list"])
        out = capsys.readouterr().out
        assert "AAPL" in out
        assert "MSFT" in out
        assert "3" in out  # AAPL has 3 bars
        assert "2" in out  # MSFT has 2 bars

    def test_symbol(self, tmp_db, capsys):
        main(["--db", tmp_db, "ohlcv", "AAPL"])
        out = capsys.readouterr().out
        assert "AAPL" in out
        assert "interval=1d" in out
        assert "185.00" in out
        assert "2024-01-01" in out

    def test_symbol_with_limit(self, tmp_db, capsys):
        main(["--db", tmp_db, "ohlcv", "AAPL", "--limit", "2"])
        out = capsys.readouterr().out
        lines = [l for l in out.strip().split("\n") if l.strip() and "---" not in l]
        # Header line (AAPL info) + empty + column header + 2 data rows = 5
        data_rows = [l for l in lines if "2024-01" in l]
        assert len(data_rows) == 2

    def test_no_data(self, tmp_db, capsys):
        main(["--db", tmp_db, "ohlcv", "GOOG"])
        out = capsys.readouterr().out
        assert "No OHLCV data" in out

    def test_no_args(self, tmp_db, capsys):
        main(["--db", tmp_db, "ohlcv"])
        out = capsys.readouterr().out
        assert "Usage" in out


class TestCmdFundamentals:
    def test_list(self, tmp_db, capsys):
        main(["--db", tmp_db, "fundamentals"])
        out = capsys.readouterr().out
        assert "AAPL" in out
        assert "MSFT" in out
        assert "28.50" in out  # AAPL PE
        assert "35.10" in out  # MSFT PE

    def test_symbol_detail(self, tmp_db, capsys):
        main(["--db", tmp_db, "fundamentals", "AAPL"])
        out = capsys.readouterr().out
        assert "AAPL" in out
        assert "28.50" in out
        assert "45.20" in out
        assert "Dividend Yield" in out

    def test_no_data(self, tmp_db, capsys):
        main(["--db", tmp_db, "fundamentals", "GOOG"])
        out = capsys.readouterr().out
        assert "No fundamentals data" in out


class TestMainNoCommand:
    def test_no_command_shows_help(self, capsys):
        """When no command is given, print help without error."""
        main([])
        out = capsys.readouterr().out
        assert "usage" in out.lower() or "Stock Analysis" in out


class TestDbNotFound:
    def test_missing_db(self):
        with pytest.raises(SystemExit):
            main(["--db", "/nonexistent/path.db", "stats"])


# --- T-39: CLI crawl subcommand ---


class TestCmdCrawl:
    def test_crawl_all(self, capsys):
        from unittest.mock import patch, AsyncMock
        from crawler.report import CollectionReport

        fake_reports = [
            CollectionReport(
                index_name="NASDAQ100", total=3, succeeded=3,
                failed=0, skipped=0, elapsed_seconds=10.0,
            ),
        ]
        with patch("cli.crawl_all", AsyncMock(return_value=fake_reports)):
            main(["crawl"])
        out = capsys.readouterr().out
        assert "NASDAQ100" in out

    def test_crawl_single_index(self, capsys):
        from unittest.mock import patch, AsyncMock
        from crawler.report import CollectionReport

        fake_report = CollectionReport(
            index_name="NASDAQ100", total=3, succeeded=3,
            failed=0, skipped=0, elapsed_seconds=5.0,
        )
        with patch("cli.crawl_index", AsyncMock(return_value=fake_report)):
            main(["crawl", "NASDAQ100"])
        out = capsys.readouterr().out
        assert "NASDAQ100" in out

    def test_crawl_backfill(self, capsys):
        from unittest.mock import patch, AsyncMock
        from crawler.report import CollectionReport

        fake_reports = [
            CollectionReport(
                index_name="TEST", total=1, succeeded=1,
                failed=0, skipped=0, elapsed_seconds=1.0,
            ),
        ]
        mock_crawl_all = AsyncMock(return_value=fake_reports)
        with patch("cli.crawl_all", mock_crawl_all):
            main(["crawl", "--backfill"])
        # Verify backfill was passed
        mock_crawl_all.assert_called_once()
        _, kwargs = mock_crawl_all.call_args
        assert kwargs.get("backfill") is True

    def test_crawl_invalid_index(self, capsys):
        main(["crawl", "INVALID_INDEX"])
        out = capsys.readouterr().out
        assert "Unknown index" in out or "unknown" in out.lower() or "error" in out.lower()
