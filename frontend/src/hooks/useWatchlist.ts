import { useCallback, useEffect, useState } from 'react'
import { watchlistApi } from '../api/watchlist'
import type { WatchlistItem } from '../types'

const DEFAULT_STOCKS: WatchlistItem[] = [
  { id: -1,  symbol: 'AAPL',  name: 'Apple',           market: 'US', added_at: '' },
  { id: -2,  symbol: 'MSFT',  name: 'Microsoft',       market: 'US', added_at: '' },
  { id: -3,  symbol: 'NVDA',  name: 'NVIDIA',          market: 'US', added_at: '' },
  { id: -4,  symbol: 'AMZN',  name: 'Amazon',          market: 'US', added_at: '' },
  { id: -5,  symbol: 'META',  name: 'Meta',            market: 'US', added_at: '' },
  { id: -6,  symbol: 'TSLA',  name: 'Tesla',           market: 'US', added_at: '' },
  { id: -7,  symbol: 'GOOGL', name: 'Alphabet A',      market: 'US', added_at: '' },
  { id: -8,  symbol: 'AVGO',  name: 'Broadcom',        market: 'US', added_at: '' },
  { id: -9,  symbol: 'COST',  name: 'Costco',          market: 'US', added_at: '' },
  { id: -10, symbol: 'NFLX',  name: 'Netflix',         market: 'US', added_at: '' },
  { id: -11, symbol: 'ADBE',  name: 'Adobe',           market: 'US', added_at: '' },
  { id: -12, symbol: 'AMD',   name: 'AMD',             market: 'US', added_at: '' },
  { id: -13, symbol: 'QCOM',  name: 'Qualcomm',        market: 'US', added_at: '' },
  { id: -14, symbol: 'CSCO',  name: 'Cisco',           market: 'US', added_at: '' },
  { id: -15, symbol: 'TMUS',  name: 'T-Mobile',        market: 'US', added_at: '' },
  { id: -16, symbol: 'INTU',  name: 'Intuit',          market: 'US', added_at: '' },
  { id: -17, symbol: 'AMGN',  name: 'Amgen',           market: 'US', added_at: '' },
  { id: -18, symbol: 'TXN',   name: 'Texas Instruments', market: 'US', added_at: '' },
  { id: -19, symbol: 'ISRG',  name: 'Intuitive Surgical', market: 'US', added_at: '' },
  { id: -20, symbol: 'GOOG',  name: 'Alphabet C',      market: 'US', added_at: '' },
]

export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>(DEFAULT_STOCKS)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const data = await watchlistApi.getAll()
      // Merge: backend items first, then defaults not already saved
      const savedSymbols = new Set(data.map((d) => d.symbol))
      const merged = [
        ...data,
        ...DEFAULT_STOCKS.filter((d) => !savedSymbols.has(d.symbol)),
      ]
      setItems(merged)
    } catch {
      // Backend unavailable — use defaults
      setItems(DEFAULT_STOCKS)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const add = useCallback(async (symbol: string, name: string | null, market: string) => {
    await watchlistApi.add(symbol, name, market)
    await load()
  }, [load])

  const remove = useCallback(async (symbol: string) => {
    await watchlistApi.remove(symbol)
    setItems((prev) => prev.filter((i) => i.symbol !== symbol))
  }, [])

  return { items, loading, add, remove, reload: load }
}
