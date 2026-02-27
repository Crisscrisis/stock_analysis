"""Data fetcher — routes to akshare (A股/港股/ETF) or yfinance (美股).

All external I/O (akshare / yfinance) is synchronous blocking code.
We wrap every call with asyncio.to_thread() so uvicorn's event loop is never blocked.

Symbol convention at API boundary:
  A股:  600519.SH  /  000001.SZ
  港股:  00700.HK
  美股:  AAPL
"""
from __future__ import annotations

import asyncio
import re
import time
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Symbol helpers
# ---------------------------------------------------------------------------

def _market(symbol: str) -> str:
    upper = symbol.upper()
    if upper.endswith(".SH") or upper.endswith(".SZ"):
        return "A"
    if upper.endswith(".HK"):
        return "HK"
    return "US"


def _to_akshare_a(symbol: str) -> str:
    """'600519.SH' → 'sh600519'"""
    code, exchange = symbol.upper().rsplit(".", 1)
    return exchange.lower() + code


def _validate_symbol(symbol: str) -> None:
    if not re.match(r"^[A-Za-z0-9.\-]+$", symbol):
        raise ValueError(f"Invalid symbol: {symbol!r}")


def _date_range(period: str) -> tuple[str, str]:
    from datetime import date, timedelta
    today = date.today()
    days = {
        "1W": 7, "1M": 30, "3M": 90, "6M": 180,
        "1Y": 365, "3Y": 365 * 3, "5Y": 365 * 5,
    }.get(period.upper(), 30)
    start = today - timedelta(days=days)
    return start.strftime("%Y%m%d"), today.strftime("%Y%m%d")


def _df_to_bars(df: pd.DataFrame, date_col: str, o: str, h: str, lo: str, c: str, v: str) -> list[dict]:
    bars = []
    for _, row in df.iterrows():
        ts = int(pd.Timestamp(row[date_col]).timestamp())
        bars.append({
            "timestamp": ts,
            "open": float(row[o]),
            "high": float(row[h]),
            "low": float(row[lo]),
            "close": float(row[c]),
            "volume": float(row[v]),
        })
    return bars


# ---------------------------------------------------------------------------
# Sync implementations (run these in thread pool via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _sync_ohlcv_yfinance(symbol: str, period: str, interval: str) -> list[dict]:
    import yfinance as yf
    period_map = {
        "1W": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo",
        "1Y": "1y", "3Y": "3y", "5Y": "5y",
    }
    yf_period = period_map.get(period.upper(), "1mo")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=yf_period, interval=interval)
    df = df.reset_index()
    bars = []
    for _, row in df.iterrows():
        dt = row["Date"]
        ts = int(pd.Timestamp(dt).timestamp())
        bars.append({
            "timestamp": ts,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]),
        })
    return bars


def _sync_ohlcv_akshare_a(symbol: str, period: str, interval: str) -> list[dict]:
    import akshare as ak
    code = symbol.upper().split(".")[0]
    start, end = _date_range(period)
    period_map = {"1d": "daily", "1w": "weekly", "1mo": "monthly"}
    ak_period = period_map.get(interval, "daily")
    df = ak.stock_zh_a_hist(symbol=code, period=ak_period, start_date=start, end_date=end, adjust="qfq")
    return _df_to_bars(df, date_col="日期", o="开盘", h="最高", lo="最低", c="收盘", v="成交量")


def _sync_ohlcv_akshare_hk(symbol: str, period: str, interval: str) -> list[dict]:
    import akshare as ak
    code = symbol.upper().replace(".HK", "")
    start, end = _date_range(period)
    df = ak.stock_hk_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="qfq")
    return _df_to_bars(df, date_col="日期", o="开盘", h="最高", lo="最低", c="收盘", v="成交量")


def _sync_quote_yfinance(symbol: str) -> dict:
    import yfinance as yf
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    price = float(info.last_price)
    prev_close = float(info.previous_close or price)
    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0.0
    return {
        "symbol": symbol,
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "volume": float(info.three_month_average_volume or 0),
        "timestamp": int(time.time()),
    }


def _sync_quote_akshare_a(symbol: str) -> dict:
    import akshare as ak
    code = symbol.upper().split(".")[0]
    df = ak.stock_zh_a_spot_em()
    row = df[df["代码"] == code]
    if row.empty:
        raise ValueError(f"Symbol not found: {symbol}")
    row = row.iloc[0]
    return {
        "symbol": symbol,
        "price": float(row["最新价"]),
        "change": float(row["涨跌额"]),
        "change_pct": float(row["涨跌幅"]),
        "volume": float(row["成交量"]),
        "timestamp": int(time.time()),
    }


def _sync_quote_akshare_hk(symbol: str) -> dict:
    import akshare as ak
    code = symbol.upper().replace(".HK", "")
    df = ak.stock_hk_spot_em()
    row = df[df["代码"] == code]
    if row.empty:
        raise ValueError(f"Symbol not found: {symbol}")
    row = row.iloc[0]
    return {
        "symbol": symbol,
        "price": float(row["最新价"]),
        "change": float(row["涨跌额"]),
        "change_pct": float(row["涨跌幅"]),
        "volume": None,
        "timestamp": int(time.time()),
    }


def _sync_search_akshare(q: str) -> list[dict]:
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    mask = df["名称"].str.contains(q, na=False) | df["代码"].str.contains(q, na=False)
    results = []
    for _, row in df[mask].head(20).iterrows():
        code = row["代码"]
        exchange = "SH" if code.startswith(("6", "5")) else "SZ"
        results.append({"symbol": f"{code}.{exchange}", "name": row["名称"], "market": "A"})
    return results


def _sync_fundamentals_yfinance(symbol: str) -> dict:
    import yfinance as yf
    info = yf.Ticker(symbol).info
    return {
        "symbol": symbol,
        "pe_ttm": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "market_cap": info.get("marketCap"),
        "revenue_ttm": info.get("totalRevenue"),
        "net_profit_ttm": info.get("netIncomeToCommon"),
        "dividend_yield": info.get("dividendYield"),
    }


def _sync_fundamentals_akshare_a(symbol: str) -> dict:
    import akshare as ak
    code = symbol.upper().split(".")[0]
    try:
        df = ak.stock_a_lg_indicator(symbol=code)
        row = df.iloc[-1] if not df.empty else None
    except Exception:
        row = None
    return {
        "symbol": symbol,
        "pe_ttm": float(row["pe_ttm"]) if row is not None and "pe_ttm" in row else None,
        "pb": float(row["pb"]) if row is not None and "pb" in row else None,
        "market_cap": None,
        "revenue_ttm": None,
        "net_profit_ttm": None,
        "dividend_yield": None,
    }


def _sync_capital_flow_akshare(symbol: str) -> dict:
    import akshare as ak
    code = symbol.upper().split(".")[0]
    market_suffix = "sh" if symbol.upper().endswith(".SH") else "sz"
    result: dict[str, Any] = {"symbol": symbol, "northbound_net": None}

    try:
        df = ak.stock_individual_fund_flow(stock=code, market=market_suffix)
        if not df.empty:
            row = df.iloc[-1]
            result["main_force_net"] = float(row.get("主力净流入-净额", 0))
        else:
            result["main_force_net"] = None
    except Exception:
        result["main_force_net"] = None

    try:
        df_top = ak.stock_lhb_detail_em(symbol=code, start_date="20240101", end_date="20241231")
        result["top_list"] = df_top.head(5).to_dict("records") if not df_top.empty else []
    except Exception:
        result["top_list"] = []

    return result


# ---------------------------------------------------------------------------
# Async public API — all sync work offloaded to thread pool
# ---------------------------------------------------------------------------

async def get_ohlcv(symbol: str, period: str = "1M", interval: str = "1d") -> list[dict[str, Any]]:
    _validate_symbol(symbol)
    market = _market(symbol)
    if market == "A":
        return await asyncio.to_thread(_sync_ohlcv_akshare_a, symbol, period, interval)
    if market == "HK":
        return await asyncio.to_thread(_sync_ohlcv_akshare_hk, symbol, period, interval)
    return await asyncio.to_thread(_sync_ohlcv_yfinance, symbol, period, interval)


async def get_quote(symbol: str) -> dict[str, Any]:
    _validate_symbol(symbol)
    market = _market(symbol)
    if market == "A":
        return await asyncio.to_thread(_sync_quote_akshare_a, symbol)
    if market == "HK":
        return await asyncio.to_thread(_sync_quote_akshare_hk, symbol)
    return await asyncio.to_thread(_sync_quote_yfinance, symbol)


async def search_stocks(q: str) -> list[dict[str, Any]]:
    if not q or len(q) > 50:
        return []
    try:
        return await asyncio.to_thread(_sync_search_akshare, q)
    except Exception:
        return []


async def get_fundamentals(symbol: str) -> dict[str, Any]:
    _validate_symbol(symbol)
    market = _market(symbol)
    if market == "US":
        return await asyncio.to_thread(_sync_fundamentals_yfinance, symbol)
    if market == "A":
        return await asyncio.to_thread(_sync_fundamentals_akshare_a, symbol)
    return {"symbol": symbol, "pe_ttm": None, "pb": None, "market_cap": None,
            "revenue_ttm": None, "net_profit_ttm": None, "dividend_yield": None}


async def get_capital_flow(symbol: str) -> dict[str, Any]:
    _validate_symbol(symbol)
    if _market(symbol) != "A":
        raise ValueError("Capital flow data is only available for A-share stocks")
    return await asyncio.to_thread(_sync_capital_flow_akshare, symbol)
