from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.stock import IndicatorsResponse, MAResult, MACDResult, RSIResult, BollingerResult
from services import calculator, stock_data

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("/{symbol}")
async def get_indicators(
    symbol: str,
    types: str = Query("MA,MACD,RSI,BOLLINGER"),
    period: str = Query("6M"),
    interval: str = Query("1d"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    requested = {t.strip().upper() for t in types.split(",")}
    try:
        bars = await stock_data.get_ohlcv(db, symbol, period, interval)
    except Exception:
        return _err(500, "Failed to fetch price data")

    closes = [b["close"] for b in bars]
    timestamps = [b["timestamp"] for b in bars]

    ma_result = None
    if "MA" in requested:
        raw = calculator.calc_ma(closes, [5, 10, 20, 60])
        ma_result = [MAResult(period=int(k.split("_")[1]), values=v) for k, v in raw.items()]

    macd_result = None
    if "MACD" in requested:
        raw = calculator.calc_macd(closes)
        macd_result = MACDResult(**raw)

    rsi_result = None
    if "RSI" in requested:
        values = calculator.calc_rsi(closes, 14)
        rsi_result = RSIResult(period=14, values=values)

    bollinger_result = None
    if "BOLLINGER" in requested:
        raw = calculator.calc_bollinger(closes, 20)
        bollinger_result = BollingerResult(**raw)

    return _ok(IndicatorsResponse(
        symbol=symbol,
        timestamps=timestamps,
        ma=ma_result,
        macd=macd_result,
        rsi=rsi_result,
        bollinger=bollinger_result,
    ).model_dump())
