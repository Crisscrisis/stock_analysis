from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.stock import OHLCVResponse, OHLCVBar, QuoteResponse, SearchResult
from services import fetcher, stock_data

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    period: str = Query("1M"),
    interval: str = Query("1d"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        bars = await stock_data.get_ohlcv(db, symbol, period, interval)
    except ValueError as e:
        return _err(404, str(e))
    except Exception:
        return _err(500, "Failed to fetch OHLCV data")
    return _ok(OHLCVResponse(
        symbol=symbol,
        interval=interval,
        bars=[OHLCVBar(**b) for b in bars],
    ).model_dump())


@router.get("/search")
async def search_stocks(q: str = Query(..., min_length=1)) -> dict:
    try:
        results = await fetcher.search_stocks(q)
    except Exception:
        return _err(500, "Search failed")
    return _ok([SearchResult(**r).model_dump() for r in results])


@router.get("/{symbol}/quote")
async def get_quote(symbol: str) -> dict:
    try:
        quote = await fetcher.get_quote(symbol)
    except ValueError as e:
        return _err(404, str(e))
    except Exception:
        return _err(500, "Failed to fetch quote")
    return _ok(QuoteResponse(**quote).model_dump())
