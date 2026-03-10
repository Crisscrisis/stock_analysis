export interface OHLCVBar {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface OHLCVData {
  symbol: string
  interval: string
  bars: OHLCVBar[]
}

export interface Quote {
  symbol: string
  price: number
  change: number
  change_pct: number
  volume: number | null
  timestamp: number
}

export interface SearchResult {
  symbol: string
  name: string
  market: string
}

export interface MAResult {
  period: number
  values: (number | null)[]
}

export interface MACDResult {
  macd: (number | null)[]
  signal: (number | null)[]
  histogram: (number | null)[]
}

export interface RSIResult {
  period: number
  values: (number | null)[]
}

export interface BollingerResult {
  upper: (number | null)[]
  middle: (number | null)[]
  lower: (number | null)[]
}

export interface IndicatorsData {
  symbol: string
  timestamps: number[]
  ma: MAResult[] | null
  macd: MACDResult | null
  rsi: RSIResult | null
  bollinger: BollingerResult | null
}

export interface Fundamentals {
  symbol: string
  pe_ttm: number | null
  pb: number | null
  market_cap: number | null
  revenue_ttm: number | null
  net_profit_ttm: number | null
  dividend_yield: number | null
}

export interface CapitalFlow {
  symbol: string
  northbound_net: number | null
  main_force_net: number | null
  top_list: Record<string, unknown>[] | null
}

export interface WatchlistItem {
  id: number
  symbol: string
  name: string | null
  market: string
  added_at: string
}

export interface WsPrice {
  symbol: string
  price: number
  change_pct: number
  timestamp: number
}

export interface IndexInfo {
  name: string
  market: string
  active_count: number
}

export interface IndexConstituent {
  symbol: string
  name: string
  market: string
  is_active: boolean
}
