import { SearchBar } from './SearchBar'
import type { SearchResult, WsPrice } from '../types'

interface Props {
  symbol: string | null
  livePrice: WsPrice | null
  onSearch: (result: SearchResult) => void
}

export function TopBar({ symbol, livePrice, onSearch }: Props) {
  const pct = livePrice?.change_pct ?? 0
  const pctColor = pct > 0 ? 'text-accent-green' : pct < 0 ? 'text-accent-red' : 'text-slate-400'

  return (
    <header className="h-12 flex items-center px-4 gap-6 border-b border-border bg-bg-secondary flex-shrink-0">
      <span className="font-bold text-slate-200 text-sm tracking-wide">股票分析</span>

      <SearchBar onSelect={onSearch} />

      {symbol && (
        <div className="flex items-center gap-4 ml-2">
          <span className="font-mono text-sm font-semibold text-slate-100">{symbol}</span>
          {livePrice ? (
            <>
              <span className="font-mono text-base font-bold text-slate-100">
                {livePrice.price.toFixed(2)}
              </span>
              <span className={`font-mono text-sm font-semibold ${pctColor}`}>
                {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
              </span>
            </>
          ) : (
            <span className="text-accent-gray text-xs animate-pulse">加载中…</span>
          )}
        </div>
      )}
    </header>
  )
}
