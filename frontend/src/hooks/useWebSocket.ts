import { useEffect, useRef, useState } from 'react'
import type { WsPrice } from '../types'

type WsStatus = 'connecting' | 'open' | 'closed' | 'error'

export function useWebSocket(symbol: string | null) {
  const [price, setPrice] = useState<WsPrice | null>(null)
  const [status, setStatus] = useState<WsStatus>('closed')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!symbol) return

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws/price/${symbol}`)
    wsRef.current = ws
    setStatus('connecting')

    ws.onopen = () => setStatus('open')
    ws.onmessage = (e) => {
      try {
        const data: WsPrice = JSON.parse(e.data)
        if (!('error' in data)) setPrice(data)
      } catch {
        // ignore malformed messages
      }
    }
    ws.onerror = () => setStatus('error')
    ws.onclose = () => setStatus('closed')

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [symbol])

  return { price, status }
}
