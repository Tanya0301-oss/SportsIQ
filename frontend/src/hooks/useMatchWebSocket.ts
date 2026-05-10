/**
 * useMatchWebSocket — manages a live WebSocket connection to a match.
 *
 * Features:
 *  - Auto-reconnect with exponential backoff (up to 30s)
 *  - Heartbeat handling
 *  - Tracks connection status
 *  - Cleanup on unmount
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import type { Prediction } from '../api/client'
import { wsUrl } from '../api/client'

interface UseMatchWebSocketResult {
  prediction: Prediction | null
  isConnected: boolean
  reconnectCount: number
}

export function useMatchWebSocket(matchId: number | null): UseMatchWebSocketResult {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectCount, setReconnectCount] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reconnectDelay = useRef(1000)
  const unmounted = useRef(false)

  const connect = useCallback(() => {
    if (!matchId || unmounted.current) return

    const url = wsUrl(matchId)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (unmounted.current) return
      setIsConnected(true)
      reconnectDelay.current = 1000   // reset backoff on success
    }

    ws.onmessage = (event) => {
      if (unmounted.current) return
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'heartbeat') return
        setPrediction(data as Prediction)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      if (unmounted.current) return
      setIsConnected(false)
      // Exponential backoff: 1s → 2s → 4s … up to 30s
      const delay = Math.min(reconnectDelay.current, 30_000)
      reconnectDelay.current = delay * 2
      reconnectTimer.current = setTimeout(() => {
        if (!unmounted.current) {
          setReconnectCount(c => c + 1)
          connect()
        }
      }, delay)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [matchId])

  useEffect(() => {
    unmounted.current = false
    reconnectDelay.current = 1000
    connect()

    return () => {
      unmounted.current = true
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { prediction, isConnected, reconnectCount }
}
