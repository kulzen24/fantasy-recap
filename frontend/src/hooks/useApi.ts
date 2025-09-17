import { useState, useEffect, useCallback } from 'react'
import { supabase } from '../lib/supabase'

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1'

interface UseApiOptions {
  immediate?: boolean
  deps?: any[]
}

interface ApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

interface UseApiReturn<T> extends ApiState<T> {
  refetch: () => Promise<void>
}

export function useApi<T>(
  endpoint: string, 
  options: UseApiOptions = {}
): UseApiReturn<T> {
  const { immediate = true, deps = [] } = options
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: immediate,
    error: null
  })

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }))

      const { data: { session } } = await supabase.auth.getSession()
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }

      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers,
        method: 'GET'
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      setState({ data: result, loading: false, error: null })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred'
      setState({ data: null, loading: false, error: errorMessage })
    }
  }, [endpoint])

  useEffect(() => {
    if (immediate) {
      fetchData()
    }
  }, [fetchData, immediate, ...deps])

  return {
    ...state,
    refetch: fetchData
  }
}

// Mutation hook for POST/PUT/DELETE operations
export function useApiMutation<TResponse = any, TRequest = any>() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mutate = useCallback(async (
    endpoint: string,
    data?: TRequest,
    method: 'POST' | 'PUT' | 'DELETE' = 'POST'
  ): Promise<TResponse | null> => {
    try {
      setLoading(true)
      setError(null)

      const { data: { session } } = await supabase.auth.getSession()
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }

      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { mutate, loading, error }
}