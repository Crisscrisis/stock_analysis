import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type CandlestickData,
  type LineData,
  type HistogramData,
  type Time,
} from 'lightweight-charts'
import { useEffect, useRef, useState } from 'react'
import { stocksApi } from '../api/stocks'
import type { IndicatorsData, OHLCVBar } from '../types'

const PERIODS = ['1M', '3M', '6M', '1Y', '3Y'] as const
type Period = typeof PERIODS[number]

const INDICATOR_TYPES = ['MA', 'MACD', 'RSI', 'BOLLINGER'] as const
type IndicatorType = typeof INDICATOR_TYPES[number]

const MA_COLORS: Record<number, string> = {
  5:  '#f59e0b',
  10: '#3b82f6',
  20: '#a855f7',
  60: '#06b6d4',
}

interface Props {
  symbol: string
}

export function ChartPanel({ symbol }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const [period, setPeriod] = useState<Period>('3M')
  const [activeIndicators, setActiveIndicators] = useState<Set<IndicatorType>>(
    new Set(['MA'])
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleIndicator = (type: IndicatorType) => {
    setActiveIndicators((prev) => {
      const next = new Set(prev)
      if (next.has(type)) next.delete(type)
      else next.add(type)
      return next
    })
  }

  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f1117' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e2130' },
        horzLines: { color: '#1e2130' },
      },
      crosshair: { vertLine: { color: '#3b82f6' }, horzLine: { color: '#3b82f6' } },
      rightPriceScale: { borderColor: '#2a2d3e' },
      timeScale: { borderColor: '#2a2d3e', timeVisible: true },
      width: containerRef.current.clientWidth,
      height: containerRef.current.clientHeight,
    })
    chartRef.current = chart

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        })
      }
    })
    ro.observe(containerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!chartRef.current || !symbol) return

    const chart = chartRef.current
    // Remove all existing series by recreating via removeSeries pattern:
    // lightweight-charts v5 — we track series ourselves and remove them
    const addedSeries: ISeriesApi<'Candlestick' | 'Line' | 'Histogram'>[] = []

    setLoading(true)
    setError(null)

    const indicatorTypes = Array.from(activeIndicators).join(',')

    Promise.all([
      stocksApi.getOHLCV(symbol, period),
      stocksApi.getIndicators(symbol, indicatorTypes, period),
    ])
      .then(([ohlcvData, indicData]) => {
        // Candlestick series
        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#22c55e',
          downColor: '#ef4444',
          borderUpColor: '#22c55e',
          borderDownColor: '#ef4444',
          wickUpColor: '#22c55e',
          wickDownColor: '#ef4444',
        })
        addedSeries.push(candleSeries)

        const candles: CandlestickData[] = ohlcvData.bars.map((b: OHLCVBar) => ({
          time: b.timestamp as Time,
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
        }))
        candleSeries.setData(candles)

        drawIndicators(chart, addedSeries, indicData)

        chart.timeScale().fitContent()
      })
      .catch(() => setError('加载数据失败'))
      .finally(() => setLoading(false))

    return () => {
      addedSeries.forEach((s) => {
        try { chart.removeSeries(s) } catch { /* already removed */ }
      })
    }
  }, [symbol, period, activeIndicators])

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-3 py-2 border-b border-border flex-shrink-0">
        <div className="flex gap-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-2 py-0.5 rounded text-xs font-mono
                ${period === p
                  ? 'bg-accent-blue text-white'
                  : 'text-accent-gray hover:text-slate-200 hover:bg-bg-hover'}`}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="w-px h-4 bg-border" />
        <div className="flex gap-1">
          {INDICATOR_TYPES.map((ind) => (
            <button
              key={ind}
              onClick={() => toggleIndicator(ind)}
              className={`px-2 py-0.5 rounded text-xs
                ${activeIndicators.has(ind)
                  ? 'bg-bg-hover text-slate-200 border border-accent-blue'
                  : 'text-accent-gray hover:text-slate-200 hover:bg-bg-hover'}`}
            >
              {ind}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="relative flex-1">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center text-accent-gray text-sm z-10">
            加载中…
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center text-accent-red text-sm z-10">
            {error}
          </div>
        )}
        <div ref={containerRef} className="w-full h-full" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Indicator drawing helpers
// ---------------------------------------------------------------------------

function toLineData(timestamps: number[], values: (number | null)[]): LineData[] {
  const data: LineData[] = []
  timestamps.forEach((ts, i) => {
    const v = values[i]
    if (v !== null && v !== undefined) {
      data.push({ time: ts as Time, value: v })
    }
  })
  return data
}

function drawIndicators(
  chart: IChartApi,
  addedSeries: ISeriesApi<'Candlestick' | 'Line' | 'Histogram'>[],
  data: IndicatorsData
) {
  const ts = data.timestamps

  // MA lines
  if (data.ma) {
    for (const ma of data.ma) {
      const s = chart.addSeries(LineSeries, {
        color: MA_COLORS[ma.period] ?? '#94a3b8',
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      })
      s.setData(toLineData(ts, ma.values))
      addedSeries.push(s)
    }
  }

  // Bollinger Bands
  if (data.bollinger) {
    const bandStyle = { lineWidth: 1, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false } as const
    const upper = chart.addSeries(LineSeries, { ...bandStyle, color: '#475569' })
    const middle = chart.addSeries(LineSeries, { ...bandStyle, color: '#64748b' })
    const lower = chart.addSeries(LineSeries, { ...bandStyle, color: '#475569' })
    upper.setData(toLineData(ts, data.bollinger.upper))
    middle.setData(toLineData(ts, data.bollinger.middle))
    lower.setData(toLineData(ts, data.bollinger.lower))
    addedSeries.push(upper, middle, lower)
  }

  // MACD (histogram overlaid on price axis — simplified)
  if (data.macd) {
    const histData: HistogramData[] = []
    ts.forEach((t, i) => {
      const v = data.macd!.histogram[i]
      if (v !== null && v !== undefined) {
        histData.push({ time: t as Time, value: v, color: v >= 0 ? '#22c55e55' : '#ef444455' })
      }
    })
    const histSeries = chart.addSeries(HistogramSeries, { priceScaleId: 'macd', priceLineVisible: false })
    histSeries.setData(histData)
    addedSeries.push(histSeries)

    const macdLine = chart.addSeries(LineSeries, { color: '#3b82f6', lineWidth: 1, priceScaleId: 'macd', priceLineVisible: false, lastValueVisible: false })
    macdLine.setData(toLineData(ts, data.macd.macd))
    addedSeries.push(macdLine)

    const signalLine = chart.addSeries(LineSeries, { color: '#f59e0b', lineWidth: 1, priceScaleId: 'macd', priceLineVisible: false, lastValueVisible: false })
    signalLine.setData(toLineData(ts, data.macd.signal))
    addedSeries.push(signalLine)
  }

  // RSI
  if (data.rsi) {
    const rsiSeries = chart.addSeries(LineSeries, {
      color: '#a855f7',
      lineWidth: 1,
      priceScaleId: 'rsi',
      priceLineVisible: false,
      lastValueVisible: false,
    })
    rsiSeries.setData(toLineData(ts, data.rsi.values))
    addedSeries.push(rsiSeries)
  }
}
