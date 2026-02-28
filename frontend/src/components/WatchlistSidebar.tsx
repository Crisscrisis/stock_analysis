import type { WatchlistItem } from '../types'

const MARKET_BADGE: Record<string, string> = {
  A: 'bg-red-500/20 text-red-400',
  US: 'bg-blue-500/20 text-blue-400',
  HK: 'bg-orange-500/20 text-orange-400',
}

function getMarket(symbol: string): string {
  const upper = symbol.toUpperCase()
  if (upper.endsWith('.SH') || upper.endsWith('.SZ')) return 'A'
  if (upper.endsWith('.HK')) return 'HK'
  return 'US'
}

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
              className={`group px-2 py-2 cursor-pointer border-b border-border/50 flex items-center gap-1
                ${isActive
                  ? 'bg-blue-500/10 border-l-4 border-l-blue-400'
                  : 'border-l-4 border-l-transparent hover:bg-bg-hover'
                }`}
            >
              {/* 股票信息 */}
              <div className="flex-1 min-w-0">
                <div className={`font-mono text-xs truncate flex items-center gap-1 ${isActive ? 'text-white font-bold' : 'text-slate-300'}`}>
                  <span className={`${MARKET_BADGE[getMarket(item.symbol)] ?? 'bg-gray-500/20 text-gray-400'} text-[9px] font-semibold px-1 py-0.5 rounded leading-none`}>
                    {getMarket(item.symbol)}
                  </span>
                  {item.symbol}
                </div>
                <div className={`text-xs truncate ${isActive ? 'text-slate-300' : 'text-accent-gray'}`}>
                  {item.name ?? ''}
                </div>
              </div>

              {/* 价格区 */}
              <div className="text-right flex-shrink-0">
                {live ? (
                  <>
                    <div className="font-mono text-xs text-slate-200">{live.price.toFixed(2)}</div>
                    <div className={`font-mono text-xs ${pctColor}`}>
                      {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                    </div>
                  </>
                ) : (
                  <div className="text-slate-600 text-xs">—</div>
                )}
              </div>

              {/* 删除按钮：始终可见，hover 变红 */}
              <button
                onClick={(e) => { e.stopPropagation(); onRemove(item.symbol) }}
                title="从自选股移除"
                className="flex-shrink-0 w-4 text-center text-slate-600 hover:text-red-400 text-sm leading-none transition-colors"
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
