from datetime import datetime

from pydantic import BaseModel, field_validator


VALID_MARKETS = {"A", "US", "HK", "ETF"}


class WatchlistCreate(BaseModel):
    symbol: str
    name: str | None = None
    market: str

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 20:
            raise ValueError("symbol must be 1-20 characters")
        # Basic injection guard — only allow alphanumeric + . -
        import re
        if not re.match(r"^[A-Za-z0-9.\-]+$", v):
            raise ValueError("symbol contains invalid characters")
        return v.upper()

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_MARKETS:
            raise ValueError(f"market must be one of {VALID_MARKETS}")
        return v


class WatchlistItem(BaseModel):
    id: int
    symbol: str
    name: str | None
    market: str
    added_at: datetime

    model_config = {"from_attributes": True}
