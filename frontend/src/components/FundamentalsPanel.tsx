import { useEffect, useState } from 'react'
import { stocksApi } from '../api/stocks'
import type { Fundamentals } from '../types'

function fmt(v: number | null, digits = 2): string {
  if (v === null || v === undefined) return '—'
  return v.toFixed(digits)
}

function fmtBig(v: number | null): string {
  if (v === null || v === undefined) return '—'
  if (Math.abs(v) >= 1e12) return (v / 1e12).toFixed(2) + 'T'
  if (Math.abs(v) >= 1e9)  return (v / 1e9).toFixed(2) + 'B'
  if (Math.abs(v) >= 1e6)  return (v / 1e6).toFixed(2) + 'M'
  return v.toFixed(0)
}

interface Row { label: string; value: string }

interface Props { symbol: string }

export function FundamentalsPanel({ symbol }: Props) {
  const [data, setData] = useState<Fundamentals | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!symbol) return
    setLoading(true)
    setData(null)
    stocksApi.getFundamentals(symbol)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [symbol])

  const rows: Row[] = data
    ? [
        { label: 'PE (TTM)',   value: fmt(data.pe_ttm) },
        { label: 'PB',         value: fmt(data.pb) },
        { label: '市值',       value: fmtBig(data.market_cap) },
        { label: '营收 (TTM)', value: fmtBig(data.revenue_ttm) },
        { label: '净利润',     value: fmtBig(data.net_profit_ttm) },
        { label: '股息率',     value: data.dividend_yield !== null ? fmt(data.dividend_yield * 100) + '%' : '—' },
      ]
    : []

  return (
    <div className="bg-bg-panel border border-border rounded p-3 flex flex-col gap-2">
      <div className="text-xs font-semibold text-accent-gray uppercase tracking-wider mb-1">基本面</div>
      {loading && <div className="text-accent-gray text-xs animate-pulse">加载中…</div>}
      {!loading && rows.length === 0 && <div className="text-accent-gray text-xs">暂无数据</div>}
      {rows.map((r) => (
        <div key={r.label} className="flex justify-between items-center">
          <span className="text-accent-gray text-xs">{r.label}</span>
          <span className="font-mono text-xs text-slate-200">{r.value}</span>
        </div>
      ))}
    </div>
  )
}
