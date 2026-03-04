#!/usr/bin/env python3
"""CLI tool for viewing stock analysis database contents (read-only)."""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone


DEFAULT_DB = "./stock_analysis.db"


def fmt_float(value: object, decimals: int = 2) -> str:
    """Format a float value, return '-' for None."""
    if value is None:
        return "-"
    return f"{float(value):,.{decimals}f}"


def fmt_ts(ts: object) -> str:
    """Format a Unix timestamp to readable date string."""
    if ts is None:
        return "-"
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")


def fmt_datetime(dt_str: object) -> str:
    """Format a datetime string to readable format."""
    if dt_str is None:
        return "-"
    s = str(dt_str)
    # Trim microseconds if present
    if "." in s:
        s = s.split(".")[0]
    return s


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print an aligned text table."""
    if not rows:
        print("(no data)")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Header
    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("  ".join("-" * w for w in widths))

    # Rows
    for row in rows:
        line = "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(line)


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open a read-only SQLite connection."""
    if not os.path.exists(db_path):
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def cmd_stats(args: argparse.Namespace) -> None:
    """Show database overview: file size, row counts, date ranges."""
    db_path = args.db
    if not os.path.exists(db_path):
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)
    size_bytes = os.path.getsize(db_path)
    if size_bytes < 1024:
        size_str = f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

    print(f"Database: {db_path}")
    print(f"Size:     {size_str}")
    print()

    conn = get_connection(db_path)
    cur = conn.cursor()

    # Table row counts
    tables = [
        ("ohlcv_bar", "timestamp"),
        ("fundamentals_cache", "updated_ts"),
        ("watchlist", None),
    ]

    for table_name, ts_col in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")  # noqa: S608
            count = cur.fetchone()[0]
        except sqlite3.OperationalError:
            count = 0

        line = f"  {table_name}: {count} rows"

        if ts_col and count > 0:
            cur.execute(
                f"SELECT MIN({ts_col}), MAX({ts_col}) FROM {table_name}"  # noqa: S608
            )
            min_ts, max_ts = cur.fetchone()
            line += f"  ({fmt_ts(min_ts)} ~ {fmt_ts(max_ts)})"

        print(line)

    conn.close()


def cmd_watchlist(args: argparse.Namespace) -> None:
    """List all watchlist entries."""
    conn = get_connection(args.db)
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT symbol, name, market, added_at FROM watchlist ORDER BY added_at"
        )
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        print("(watchlist table not found)")
        conn.close()
        return

    headers = ["Symbol", "Name", "Market", "Added At"]
    formatted = [
        [r[0], r[1] or "-", r[2], fmt_datetime(r[3])]
        for r in rows
    ]
    print_table(headers, formatted)
    conn.close()


def cmd_ohlcv(args: argparse.Namespace) -> None:
    """List OHLCV symbols or show data for a specific symbol."""
    conn = get_connection(args.db)
    cur = conn.cursor()

    if args.list:
        # List all symbols with row counts
        try:
            cur.execute(
                "SELECT symbol, interval, COUNT(*), MIN(timestamp), MAX(timestamp) "
                "FROM ohlcv_bar GROUP BY symbol, interval "
                "ORDER BY symbol, interval"
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            print("(ohlcv_bar table not found)")
            conn.close()
            return

        headers = ["Symbol", "Interval", "Bars", "From", "To"]
        formatted = [
            [r[0], r[1], str(r[2]), fmt_ts(r[3]), fmt_ts(r[4])]
            for r in rows
        ]
        print_table(headers, formatted)
    elif args.symbol:
        # Show data for a specific symbol
        symbol = args.symbol
        interval = args.interval
        limit = args.limit

        try:
            cur.execute(
                "SELECT timestamp, open, high, low, close, volume "
                "FROM ohlcv_bar "
                "WHERE symbol = ? AND interval = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (symbol, interval, limit),
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            print("(ohlcv_bar table not found)")
            conn.close()
            return

        if not rows:
            print(f"No OHLCV data for {symbol} (interval={interval})")
            conn.close()
            return

        # Reverse to show oldest first
        rows = rows[::-1]

        print(f"{symbol}  interval={interval}  ({len(rows)} bars)")
        print()
        headers = ["Date", "Open", "High", "Low", "Close", "Volume"]
        formatted = [
            [
                fmt_ts(r[0]),
                fmt_float(r[1]),
                fmt_float(r[2]),
                fmt_float(r[3]),
                fmt_float(r[4]),
                fmt_float(r[5], 0),
            ]
            for r in rows
        ]
        print_table(headers, formatted)
    else:
        print("Usage: cli.py ohlcv --list  OR  cli.py ohlcv <SYMBOL>")

    conn.close()


def cmd_fundamentals(args: argparse.Namespace) -> None:
    """List all fundamentals or show data for a specific symbol."""
    conn = get_connection(args.db)
    cur = conn.cursor()

    if args.symbol:
        # Show detail for one symbol
        try:
            cur.execute(
                "SELECT symbol, pe_ttm, pb, market_cap, revenue_ttm, "
                "net_profit_ttm, dividend_yield, updated_ts "
                "FROM fundamentals_cache WHERE symbol = ?",
                (args.symbol,),
            )
            row = cur.fetchone()
        except sqlite3.OperationalError:
            print("(fundamentals_cache table not found)")
            conn.close()
            return

        if not row:
            print(f"No fundamentals data for {args.symbol}")
            conn.close()
            return

        labels = [
            ("Symbol", row[0]),
            ("PE (TTM)", fmt_float(row[1])),
            ("PB", fmt_float(row[2])),
            ("Market Cap", fmt_float(row[3])),
            ("Revenue (TTM)", fmt_float(row[4])),
            ("Net Profit (TTM)", fmt_float(row[5])),
            ("Dividend Yield", fmt_float(row[6])),
            ("Updated", fmt_ts(row[7])),
        ]
        max_label = max(len(l[0]) for l in labels)
        for label, value in labels:
            print(f"  {label.ljust(max_label)}  {value}")
    else:
        # List all
        try:
            cur.execute(
                "SELECT symbol, pe_ttm, pb, market_cap, updated_ts "
                "FROM fundamentals_cache ORDER BY symbol"
            )
            rows = cur.fetchall()
        except sqlite3.OperationalError:
            print("(fundamentals_cache table not found)")
            conn.close()
            return

        headers = ["Symbol", "PE(TTM)", "PB", "Market Cap", "Updated"]
        formatted = [
            [
                r[0],
                fmt_float(r[1]),
                fmt_float(r[2]),
                fmt_float(r[3]),
                fmt_ts(r[4]),
            ]
            for r in rows
        ]
        print_table(headers, formatted)

    conn.close()


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        description="Stock Analysis DB Viewer (read-only)"
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB, help="Path to SQLite database file"
    )

    sub = parser.add_subparsers(dest="command")

    # stats
    sub.add_parser("stats", help="Show database overview")

    # watchlist
    sub.add_parser("watchlist", help="List watchlist entries")

    # ohlcv
    ohlcv_parser = sub.add_parser("ohlcv", help="View OHLCV price data")
    ohlcv_parser.add_argument("symbol", nargs="?", help="Stock symbol (e.g. AAPL)")
    ohlcv_parser.add_argument(
        "--list", action="store_true", help="List all symbols with data"
    )
    ohlcv_parser.add_argument(
        "--limit", type=int, default=20, help="Number of bars to show (default: 20)"
    )
    ohlcv_parser.add_argument(
        "--interval", default="1d", help="Bar interval (default: 1d)"
    )

    # fundamentals
    fund_parser = sub.add_parser("fundamentals", help="View fundamentals data")
    fund_parser.add_argument(
        "symbol", nargs="?", help="Stock symbol (e.g. AAPL)"
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return

    commands = {
        "stats": cmd_stats,
        "watchlist": cmd_watchlist,
        "ohlcv": cmd_ohlcv,
        "fundamentals": cmd_fundamentals,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
