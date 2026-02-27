import type { WatchlistItem } from '../types'
import { api } from './client'

export const watchlistApi = {
  getAll: () => api.get<WatchlistItem[]>('/watchlist'),

  add: (symbol: string, name: string | null, market: string) =>
    api.post<WatchlistItem>('/watchlist', { symbol, name, market }),

  remove: (symbol: string) =>
    api.delete<{ symbol: string }>(`/watchlist/${encodeURIComponent(symbol)}`),
}
