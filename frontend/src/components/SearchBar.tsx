import { useEffect, useRef, useState } from 'react'
import { stocksApi } from '../api/stocks'
import type { SearchResult } from '../types'

interface Props {
  onSelect: (result: SearchResult) => void
}

const MARKET_BADGE: Record<string, string> = {
  A: 'bg-red-500/20 text-red-400',
  US: 'bg-blue-500/20 text-blue-400',
  HK: 'bg-orange-500/20 text-orange-400',
}

function MarketBadge({ market }: { market: string }) {
  const cls = MARKET_BADGE[market] ?? 'bg-gray-500/20 text-gray-400'
  return (
    <span className={`${cls} text-[10px] font-semibold px-1.5 py-0.5 rounded`}>
      {market}
    </span>
  )
}

export function SearchBar({ onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [open, setOpen] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // 搜索防抖
  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return }
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      try {
        const data = await stocksApi.search(query)
        setResults(data)
        setOpen(true)
      } catch {
        setResults([])
      }
    }, 300)
  }, [query])

  // 点击外部关闭下拉
  useEffect(() => {
    const handleMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleMouseDown)
    return () => document.removeEventListener('mousedown', handleMouseDown)
  }, [])

  const handleSelect = (r: SearchResult) => {
    onSelect(r)
    setQuery('')
    setResults([])
    setOpen(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key !== 'Enter') return
    e.preventDefault()
    if (results.length > 0) {
      handleSelect(results[0])
    } else if (query.trim()) {
      handleSelect({ symbol: query.trim().toUpperCase(), name: '', market: '' })
    }
  }

  return (
    <div ref={containerRef} className="relative w-72">
      <div className="relative">
        <svg
          className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-accent-gray pointer-events-none"
          fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" strokeLinecap="round" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="搜索股票代码或名称…"
          className="w-full bg-bg-secondary border border-border rounded pl-8 pr-3 py-1.5 text-sm
                     text-slate-200 placeholder-accent-gray focus:outline-none focus:border-accent-blue"
        />
      </div>
      {open && results.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-bg-panel border border-border rounded shadow-xl max-h-60 overflow-auto">
          {results.map((r) => (
            <li
              key={r.symbol}
              onClick={() => handleSelect(r)}
              className="px-3 py-2 cursor-pointer hover:bg-bg-hover flex items-center gap-2"
            >
              <MarketBadge market={r.market} />
              <span className="text-slate-200 font-mono text-xs">{r.symbol}</span>
              <span className="text-accent-gray text-xs ml-auto truncate">{r.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
