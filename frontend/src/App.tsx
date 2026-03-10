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

  const { price: livePrice } = useWebSocket(selected)

  const [prices, setPrices] = useState<Record<string, WsPrice>>({})

  const onLivePrice = useCallback((p: WsPrice) => {
    setPrices((prev) => ({ ...prev, [p.symbol]: p }))
  }, [])

  if (livePrice && (!prices[livePrice.symbol] || prices[livePrice.symbol].timestamp !== livePrice.timestamp)) {
    onLivePrice(livePrice)
  }

  const handleSearch = (result: SearchResult) => {
    setSelected(result.symbol)
    const alreadyIn = items.some((i) => i.symbol === result.symbol)
    if (!alreadyIn) {
      add(result.symbol, result.name, result.market).catch(() => {})
    }
  }

  const handleIndexSelect = (symbol: string, name: string | null, market: string) => {
    setSelected(symbol)
    const alreadyIn = items.some((i) => i.symbol === symbol)
    if (!alreadyIn) {
      add(symbol, name, market).catch(() => {})
    }
  }

  const sidebarPrices: Record<string, { price: number; change_pct: number }> = {}
  Object.entries(prices).forEach(([sym, p]) => {
    sidebarPrices[sym] = { price: p.price, change_pct: p.change_pct }
  })

  // 从 watchlist 中找到当前股票的名称
  const selectedName = items.find((i) => i.symbol === selected)?.name ?? null

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
          onIndexSelect={handleIndexSelect}
        />

        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-hidden border-b border-border">
            <ChartPanel symbol={selected} name={selectedName} />
          </div>

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
