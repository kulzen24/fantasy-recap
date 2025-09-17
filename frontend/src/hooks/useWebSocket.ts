import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

interface UseWebSocketOptions {
  enabled?: boolean
  reconnectAttempts?: number
  reconnectInterval?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const { user } = useAuth()
  const {
    enabled = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = () => {
    if (!enabled || !user || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        reconnectCountRef.current = 0
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        
        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++
          console.log(`Attempting reconnection ${reconnectCountRef.current}/${reconnectAttempts}`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('WebSocket connection error')
      }
    } catch (err) {
      setError(`Failed to create WebSocket connection: ${err}`)
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User initiated disconnect')
      wsRef.current = null
    }
    
    setIsConnected(false)
    setLastMessage(null)
    setError(null)
    reconnectCountRef.current = 0
  }

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
      return true
    }
    return false
  }

  useEffect(() => {
    if (enabled && user) {
      connect()
    }

    return disconnect
  }, [enabled, user, url])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [])

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    connect,
    disconnect
  }
}

// Specific hook for league sync status updates
export function useLeagueSyncWebSocket() {
  const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/league-sync'
  
  const { lastMessage, isConnected, sendMessage } = useWebSocket(wsUrl, {
    enabled: true,
    reconnectAttempts: 3,
    reconnectInterval: 5000
  })

  const [syncStatuses, setSyncStatuses] = useState<Map<string, any>>(new Map())

  useEffect(() => {
    if (lastMessage?.type === 'league_sync_update') {
      setSyncStatuses(prev => {
        const newMap = new Map(prev)
        newMap.set(lastMessage.data.league_id, lastMessage.data)
        return newMap
      })
    }
  }, [lastMessage])

  const subscribeTo = (leagueId: string) => {
    return sendMessage({
      type: 'subscribe',
      league_id: leagueId
    })
  }

  const unsubscribeFrom = (leagueId: string) => {
    return sendMessage({
      type: 'unsubscribe',
      league_id: leagueId
    })
  }

  return {
    isConnected,
    syncStatuses,
    subscribeTo,
    unsubscribeFrom
  }
}