import { useEffect, useState } from 'react'
import { stocksApi } from '../api/stocks'
import type { IndexConstituent, IndexInfo } from '../types'

const MARKET_BADGE: Record<string, string> = {
  A: 'bg-red-500/20 text-red-400',
  US: 'bg-blue-500/20 text-blue-400',
  HK: 'bg-orange-500/20 text-orange-400',
}

interface Props {
  onSelect: (symbol: string, name: string | null, market: string) => void
}

export function IndexBrowser({ onSelect }: Props) {
  const [indices, setIndices] = useState<IndexInfo[]>([])
  const [selected, setSelected] = useState<string>('')
  const [constituents, setConstituents] = useState<IndexConstituent[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    stocksApi.getIndices().then((data) => {
      setIndices(data)
      if (data.length > 0 && !selected) {
        setSelected(data[0].name)
      }
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    stocksApi.getConstituents(selected).then((data) => {
      setConstituents(data)
    }).catch(() => {
      setConstituents([])
    }).finally(() => setLoading(false))
  }, [selected])

  return (
    <div className="flex flex-col h-full">
      <div className="px-2 py-2 border-b border-border">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full bg-bg-primary text-slate-200 text-xs border border-border rounded px-2 py-1 focus:outline-none focus:border-blue-500"
        >
          {indices.map((idx) => (
            <option key={idx.name} value={idx.name}>
              {idx.name} ({idx.active_count})
            </option>
          ))}
        </select>
      </div>

      <ul className="flex-1 overflow-y-auto">
        {loading && (
          <li className="px-3 py-4 text-xs text-accent-gray text-center">加载中...</li>
        )}
        {!loading && constituents.filter(c => c.is_active).length === 0 && (
          <li className="px-3 py-4 text-xs text-accent-gray text-center">暂无数据</li>
        )}
        {!loading && constituents.filter(c => c.is_active).map((c) => (
          <li
            key={c.symbol}
            onClick={() => onSelect(c.symbol, c.name, c.market)}
            className="px-2 py-2 cursor-pointer border-b border-border/50 border-l-4 border-l-transparent hover:bg-bg-hover flex items-center gap-1"
          >
            <div className="flex-1 min-w-0">
              {c.market === 'HK' ? (
                <>
                  <div className="text-xs truncate flex items-center gap-1 text-slate-300">
                    <span className={`${MARKET_BADGE.HK} text-[9px] font-semibold px-1 py-0.5 rounded leading-none`}>
                      HK
                    </span>
                    {c.name ?? c.symbol}
                  </div>
                  <div className="font-mono text-[10px] truncate text-accent-gray ml-5">
                    {c.symbol.replace(/\.(SH|SZ|HK)$/i, '')}
                  </div>
                </>
              ) : (
                <>
                  <div className="font-mono text-xs truncate flex items-center gap-1 text-slate-300">
                    <span className={`${MARKET_BADGE[c.market] ?? 'bg-gray-500/20 text-gray-400'} text-[9px] font-semibold px-1 py-0.5 rounded leading-none`}>
                      {c.market}
                    </span>
                    {c.symbol}
                  </div>
                  <div className="text-xs truncate text-accent-gray">
                    {c.name ?? ''}
                  </div>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
