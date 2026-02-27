import { useState, useCallback } from 'react'
import { CapitalFlowPanel } from './components/CapitalFlowPanel'
import { ChartPanel } from './components/ChartPanel'
import { FundamentalsPanel } from './components/FundamentalsPanel'
import { TopBar } from './components/TopBar'
import { WatchlistSidebar } from './components/WatchlistSidebar'
import { useWebSocket } from './hooks/useWebSocket'
import { useWatchlist } from './hooks/useWatchlist'
import type { SearchResult, WsPrice } from './types'

export default function App() {
  const [selected, setSelected] = useState<string>('AAPL')
  const { items, add, remove } = useWatchlist()

  // Real-time price for the currently selected symbol
  const { price: livePrice } = useWebSocket(selected)

  // Accumulated live prices for sidebar display
  const [prices, setPrices] = useState<Record<string, WsPrice>>({})

  // Update accumulated prices when live price updates
  const onLivePrice = useCallback((p: WsPrice) => {
    setPrices((prev) => ({ ...prev, [p.symbol]: p }))
  }, [])

  // Keep sidebar prices in sync with the active WS feed
  if (livePrice && (!prices[livePrice.symbol] || prices[livePrice.symbol].timestamp !== livePrice.timestamp)) {
    onLivePrice(livePrice)
  }

  const handleSearch = (result: SearchResult) => {
    setSelected(result.symbol)
    // Auto-add to watchlist if not already present
    const alreadyIn = items.some((i) => i.symbol === result.symbol)
    if (!alreadyIn) {
      add(result.symbol, result.name, result.market).catch(() => {})
    }
  }

  const sidebarPrices: Record<string, { price: number; change_pct: number }> = {}
  Object.entries(prices).forEach(([sym, p]) => {
    sidebarPrices[sym] = { price: p.price, change_pct: p.change_pct }
  })

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-bg-primary">
      <TopBar symbol={selected} livePrice={livePrice} onSearch={handleSearch} />

      <div className="flex flex-1 overflow-hidden">
        <WatchlistSidebar
          items={items}
          selected={selected}
          prices={sidebarPrices}
          onSelect={setSelected}
          onRemove={remove}
        />

        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Chart — takes most vertical space */}
          <div className="flex-1 overflow-hidden border-b border-border">
            <ChartPanel symbol={selected} />
          </div>

          {/* Bottom panels */}
          <div className="h-52 flex gap-3 p-3 overflow-auto flex-shrink-0">
            <div className="flex-1 min-w-0">
              <FundamentalsPanel symbol={selected} />
            </div>
            <div className="flex-1 min-w-0">
              <CapitalFlowPanel symbol={selected} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
