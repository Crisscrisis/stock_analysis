import type { WatchlistItem } from '../types'

interface Props {
  items: WatchlistItem[]
  selected: string | null
  prices: Record<string, { price: number; change_pct: number }>
  onSelect: (symbol: string) => void
  onRemove: (symbol: string) => void
}

export function WatchlistSidebar({ items, selected, prices, onSelect, onRemove }: Props) {
  return (
    <aside className="w-48 flex-shrink-0 bg-bg-secondary border-r border-border flex flex-col overflow-hidden">
      <div className="px-3 py-2 border-b border-border text-xs font-semibold text-accent-gray uppercase tracking-wider">
        自选股
      </div>
      <ul className="flex-1 overflow-y-auto">
        {items.map((item) => {
          const live = prices[item.symbol]
          const pct = live?.change_pct ?? 0
          const isActive = item.symbol === selected
          const pctColor = pct > 0 ? 'text-accent-green' : pct < 0 ? 'text-accent-red' : 'text-accent-gray'

          return (
            <li
              key={item.symbol}
              onClick={() => onSelect(item.symbol)}
              className={`group px-3 py-2 cursor-pointer border-b border-border/50 flex items-center justify-between
                ${isActive ? 'bg-bg-hover border-l-2 border-l-accent-blue' : 'hover:bg-bg-hover'}`}
            >
              <div className="flex-1 min-w-0">
                <div className="font-mono text-xs text-slate-200 truncate">{item.symbol}</div>
                <div className="text-accent-gray text-xs truncate">{item.name ?? ''}</div>
              </div>
              <div className="ml-2 text-right flex-shrink-0">
                {live ? (
                  <>
                    <div className="font-mono text-xs text-slate-200">{live.price.toFixed(2)}</div>
                    <div className={`font-mono text-xs ${pctColor}`}>
                      {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                    </div>
                  </>
                ) : (
                  <div className="text-accent-gray text-xs">—</div>
                )}
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); onRemove(item.symbol) }}
                className="ml-1 opacity-0 group-hover:opacity-100 text-accent-gray hover:text-accent-red text-xs px-1"
                title="删除"
              >
                ✕
              </button>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
