/**
 * React hooks for Natural Language Query operations
 * Integrates with backend NLQ API endpoints
 */

import { useApi, useApiMutation } from './useApi'
import { useAuth } from '../contexts/AuthContext'

// NLQ Types based on backend models
export interface NLQRequest {
  query: string
  league_id: string
  context?: Record<string, any>
  include_visualizations?: boolean
  max_response_length?: number
}

export interface QueryEntity {
  entity_type: 'player' | 'team' | 'league' | 'week' | 'season' | 'stat' | 'position'
  value: string
  confidence: number
  original_text: string
  start_pos?: number
  end_pos?: number
}

export interface ParsedQuery {
  original_query: string
  query_type: string
  intent: string
  entities: QueryEntity[]
  confidence: number
  target_player_ids: string[]
  target_team_ids: string[]
  target_leagues: string[]
  week_range?: [number, number]
  season?: number
  aggregation?: 'sum' | 'avg' | 'max' | 'min' | 'median'
  comparison_type?: 'vs' | 'against' | 'better_than' | 'worse_than'
  time_period?: 'this_week' | 'last_week' | 'season' | 'recent'
}

export interface QueryResponse {
  query_id: string
  original_query: string
  parsed_query: ParsedQuery
  answer: string
  supporting_data: Record<string, any>
  visualizations: Array<Record<string, any>>
  confidence: number
  response_time_ms: number
  data_sources: string[]
  league_id: string
  user_id: string
  timestamp: string
}

export interface NLQResponse {
  success: boolean
  query_response?: QueryResponse
  error?: string
  suggestions: string[]
}

export interface QueryExamples {
  success: boolean
  examples: string[]
  categories: {
    player_stats: string[]
    team_performance: string[]
    league_analysis: string[]
    trends: string[]
  }
}

export interface QueryAnalytics {
  success: boolean
  league_id: string
  analytics: {
    total_queries: number
    avg_response_time_ms: number
    avg_confidence: number
    popular_query_types: Array<{
      type: string
      count: number
      percentage: number
    }>
    user_satisfaction: number
    most_common_queries: string[]
  }
}

export interface QueryFeedback {
  query_id: string
  rating: number
  feedback_type: string
  feedback_text?: string
}

/**
 * Hook to submit a natural language query
 */
export function useNLQQuery() {
  const { mutate, loading, error } = useApiMutation<NLQResponse, NLQRequest>()
  
  const submitQuery = async (request: NLQRequest): Promise<NLQResponse> => {
    const response = await mutate('/nlq/query', request, 'POST')
    if (!response) {
      throw new Error('Failed to submit query')
    }
    return response
  }
  
  return {
    submitQuery,
    isLoading: loading,
    error
  }
}

/**
 * Hook to get query examples
 */
export function useNLQExamples() {
  const { user } = useAuth()
  
  const apiResult = useApi<QueryExamples>('/nlq/examples', {
    immediate: !!user,
    deps: [user]
  })
  
  return {
    data: apiResult.data,
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to get NLQ health status
 */
export function useNLQHealth() {
  const apiResult = useApi<{
    success: boolean
    health: {
      status: string
      components: Record<string, string>
    }
    timestamp: string
  }>('/nlq/health', {
    immediate: true,
    deps: []
  })
  
  return {
    data: apiResult.data,
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to submit batch queries
 */
export function useNLQBatch() {
  const { mutate, loading, error } = useApiMutation<{
    success: boolean
    total_queries: number
    successful_responses: number
    failed_responses: number
    responses: Array<{
      query: string
      response: NLQResponse
    }>
  }, NLQRequest[]>()
  
  const submitBatch = async (queries: NLQRequest[]) => {
    const response = await mutate('/nlq/query/batch', queries, 'POST')
    if (!response) {
      throw new Error('Failed to submit batch queries')
    }
    return response
  }
  
  return {
    submitBatch,
    isLoading: loading,
    error
  }
}

/**
 * Hook to get query analytics for a league
 */
export function useNLQAnalytics(leagueId?: string) {
  const { user } = useAuth()
  
  const apiResult = useApi<QueryAnalytics>(
    leagueId ? `/nlq/analytics/${leagueId}` : '',
    {
      immediate: !!user && !!leagueId,
      deps: [user, leagueId]
    }
  )
  
  return {
    data: apiResult.data,
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to submit query feedback
 */
export function useNLQFeedback() {
  const { mutate, loading, error } = useApiMutation<{
    success: boolean
    message: string
    query_id: string
  }, QueryFeedback>()
  
  const submitFeedback = async (feedback: QueryFeedback) => {
    const response = await mutate('/nlq/feedback', feedback, 'POST')
    if (!response) {
      throw new Error('Failed to submit feedback')
    }
    return response
  }
  
  return {
    submitFeedback,
    isLoading: loading,
    error
  }
}
