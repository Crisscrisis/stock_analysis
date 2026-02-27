from fastapi import APIRouter

from schemas.stock import CapitalFlowResponse
from services import fetcher

router = APIRouter()


def _ok(data) -> dict:
    return {"data": data, "code": 200, "message": "ok"}


def _err(code: int, message: str) -> dict:
    return {"data": None, "code": code, "message": message}


@router.get("/{symbol}")
async def get_capital_flow(symbol: str) -> dict:
    try:
        data = await fetcher.get_capital_flow(symbol)
    except ValueError as e:
        return _err(400, str(e))
    except Exception:
        return _err(500, "Failed to fetch capital flow data")
    return _ok(CapitalFlowResponse(**data).model_dump())
