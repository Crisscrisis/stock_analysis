import type { CapitalFlow, Fundamentals, IndicatorsData, OHLCVData, Quote, SearchResult } from '../types'
import { api } from './client'

export const stocksApi = {
  getOHLCV: (symbol: string, period = '1M', interval = '1d') =>
    api.get<OHLCVData>(`/stocks/${encodeURIComponent(symbol)}/ohlcv?period=${period}&interval=${interval}`),

  getQuote: (symbol: string) =>
    api.get<Quote>(`/stocks/${encodeURIComponent(symbol)}/quote`),

  search: (q: string) =>
    api.get<SearchResult[]>(`/stocks/search?q=${encodeURIComponent(q)}`),

  getIndicators: (symbol: string, types = 'MA,MACD,RSI,BOLLINGER', period = '6M') =>
    api.get<IndicatorsData>(
      `/indicators/${encodeURIComponent(symbol)}?types=${types}&period=${period}`
    ),

  getFundamentals: (symbol: string) =>
    api.get<Fundamentals>(`/fundamentals/${encodeURIComponent(symbol)}`),

  getCapitalFlow: (symbol: string) =>
    api.get<CapitalFlow>(`/capital-flow/${encodeURIComponent(symbol)}`),
}
