from pydantic import BaseModel


class OHLCVBar(BaseModel):
    timestamp: int      # Unix seconds
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCVResponse(BaseModel):
    symbol: str
    interval: str
    bars: list[OHLCVBar]


class QuoteResponse(BaseModel):
    symbol: str
    price: float
    change: float
    change_pct: float
    volume: float | None = None
    timestamp: int


class SearchResult(BaseModel):
    symbol: str
    name: str
    market: str


class MAResult(BaseModel):
    period: int
    values: list[float | None]


class MACDResult(BaseModel):
    macd: list[float | None]
    signal: list[float | None]
    histogram: list[float | None]


class RSIResult(BaseModel):
    period: int
    values: list[float | None]


class BollingerResult(BaseModel):
    upper: list[float | None]
    middle: list[float | None]
    lower: list[float | None]


class IndicatorsResponse(BaseModel):
    symbol: str
    timestamps: list[int]
    ma: list[MAResult] | None = None
    macd: MACDResult | None = None
    rsi: RSIResult | None = None
    bollinger: BollingerResult | None = None


class FundamentalsResponse(BaseModel):
    symbol: str
    pe_ttm: float | None = None
    pb: float | None = None
    market_cap: float | None = None   # in CNY / USD
    revenue_ttm: float | None = None
    net_profit_ttm: float | None = None
    dividend_yield: float | None = None


class CapitalFlowResponse(BaseModel):
    symbol: str
    northbound_net: float | None = None    # 北向资金净流入（万元）
    main_force_net: float | None = None    # 主力净流入
    top_list: list[dict] | None = None     # 龙虎榜
