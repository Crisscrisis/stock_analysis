import { useEffect, useState } from 'react'
import { stocksApi } from '../api/stocks'
import type { CapitalFlow } from '../types'

function fmtFlow(v: number | null): string {
  if (v === null || v === undefined) return '—'
  const sign = v >= 0 ? '+' : ''
  if (Math.abs(v) >= 10000) return sign + (v / 10000).toFixed(2) + '亿'
  return sign + v.toFixed(0) + '万'
}

interface Props { symbol: string }

export function CapitalFlowPanel({ symbol }: Props) {
  const [data, setData] = useState<CapitalFlow | null>(null)
  const [loading, setLoading] = useState(false)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    if (!symbol) return
    setLoading(true)
    setData(null)
    setUnavailable(false)
    stocksApi.getCapitalFlow(symbol)
      .then(setData)
      .catch(() => setUnavailable(true))
      .finally(() => setLoading(false))
  }, [symbol])

  const northColor = data?.northbound_net != null
    ? data.northbound_net >= 0 ? 'text-accent-green' : 'text-accent-red'
    : 'text-accent-gray'

  const mainColor = data?.main_force_net != null
    ? data.main_force_net >= 0 ? 'text-accent-green' : 'text-accent-red'
    : 'text-accent-gray'

  return (
    <div className="bg-bg-panel border border-border rounded p-3 flex flex-col gap-2">
      <div className="text-xs font-semibold text-accent-gray uppercase tracking-wider mb-1">资金流向</div>

      {loading && <div className="text-accent-gray text-xs animate-pulse">加载中…</div>}

      {unavailable && (
        <div className="text-accent-gray text-xs">仅支持 A 股资金流向数据</div>
      )}

      {data && !unavailable && (
        <>
          <div className="flex justify-between">
            <span className="text-accent-gray text-xs">北向资金</span>
            <span className={`font-mono text-xs ${northColor}`}>{fmtFlow(data.northbound_net)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-accent-gray text-xs">主力净流入</span>
            <span className={`font-mono text-xs ${mainColor}`}>{fmtFlow(data.main_force_net)}</span>
          </div>

          {data.top_list && data.top_list.length > 0 && (
            <div className="mt-2">
              <div className="text-accent-gray text-xs mb-1">龙虎榜</div>
              <div className="space-y-1">
                {data.top_list.slice(0, 3).map((row, i) => (
                  <div key={i} className="flex justify-between text-xs text-slate-400">
                    <span className="truncate max-w-[8rem]">{String(row['机构'] ?? row['营业部名称'] ?? '—')}</span>
                    <span className="font-mono ml-2">{String(row['买入金额'] ?? '—')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(!data.top_list || data.top_list.length === 0) && (
            <div className="text-accent-gray text-xs">暂无龙虎榜数据</div>
          )}
        </>
      )}
    </div>
  )
}
