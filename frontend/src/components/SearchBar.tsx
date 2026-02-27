import { useEffect, useRef, useState } from 'react'
import { stocksApi } from '../api/stocks'
import type { SearchResult } from '../types'

interface Props {
  onSelect: (result: SearchResult) => void
}

export function SearchBar({ onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [open, setOpen] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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

  const handleSelect = (r: SearchResult) => {
    onSelect(r)
    setQuery('')
    setResults([])
    setOpen(false)
  }

  return (
    <div className="relative w-72">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索股票代码或名称…"
        className="w-full bg-bg-secondary border border-border rounded px-3 py-1.5 text-sm
                   text-slate-200 placeholder-accent-gray focus:outline-none focus:border-accent-blue"
      />
      {open && results.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-bg-panel border border-border rounded shadow-xl max-h-60 overflow-auto">
          {results.map((r) => (
            <li
              key={r.symbol}
              onClick={() => handleSelect(r)}
              className="px-3 py-2 cursor-pointer hover:bg-bg-hover flex justify-between"
            >
              <span className="text-slate-200 font-mono">{r.symbol}</span>
              <span className="text-accent-gray ml-4 truncate">{r.name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
