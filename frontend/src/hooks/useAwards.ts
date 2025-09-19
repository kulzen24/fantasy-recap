/**
 * React hooks for Award CRUD operations
 * Integrates with backend award API endpoints
 */

import { useApi, useApiMutation } from './useApi'
import { useAuth } from '../contexts/AuthContext'
import { 
  Award,
  AwardCreateRequest,
  AwardUpdateRequest,
  AwardListResponse,
  AwardResponse,
  AwardWinner,
  AwardWinnerAssignRequest,
  AwardWinnerListResponse,
  AwardWinnerResponse,
  AwardTemplate,
  AwardTemplateResponse
} from '../types/award'

// API Keys for React Query
export const AWARD_QUERY_KEYS = {
  awards: ['awards'] as const,
  award: (id: string) => ['awards', id] as const,
  userAwards: (userId?: string) => ['awards', 'user', userId] as const,
  leagueAwards: (leagueId: string) => ['awards', 'league', leagueId] as const,
  winners: ['award-winners'] as const,
  winner: (id: string) => ['award-winners', id] as const,
  awardWinners: (awardId: string) => ['award-winners', 'award', awardId] as const,
  weekWinners: (week: number, season: number) => ['award-winners', 'week', week, season] as const,
  templates: ['award-templates'] as const,
}

/**
 * Hook to fetch user's awards
 */
export function useAwards(leagueId?: string) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (leagueId) queryParams.set('league_id', leagueId)
  
  const endpoint = `/awards${queryParams.toString() ? `?${queryParams}` : ''}`
  
  const apiResult = useApi<AwardListResponse>(endpoint, {
    immediate: !!user,
    deps: [user, leagueId]
  })
  
  return {
    data: apiResult.data?.data || [],
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to fetch a specific award by ID
 */
export function useAward(awardId: string) {
  const { user } = useAuth()
  
  const apiResult = useApi<AwardResponse>(`/awards/${awardId}`, {
    immediate: !!user && !!awardId,
    deps: [user, awardId]
  })
  
  return {
    data: apiResult.data?.data,
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to create a new award
 */
export function useCreateAward() {
  const { mutate, loading, error } = useApiMutation<AwardResponse, AwardCreateRequest>()
  
  const createAward = async (data: AwardCreateRequest): Promise<Award> => {
    const response = await mutate('/awards', data, 'POST')
    if (!response?.data) {
      throw new Error(response?.error || 'Failed to create award')
    }
    return response.data
  }
  
  return {
    mutateAsync: createAward,
    isPending: loading,
    error
  }
}

/**
 * Hook to update an existing award
 */
export function useUpdateAward() {
  const { mutate, loading, error } = useApiMutation<AwardResponse, AwardUpdateRequest>()
  
  const updateAward = async ({ id, data }: { id: string; data: AwardUpdateRequest }): Promise<Award> => {
    const response = await mutate(`/awards/${id}`, data, 'PUT')
    if (!response?.data) {
      throw new Error(response?.error || 'Failed to update award')
    }
    return response.data
  }
  
  return {
    mutateAsync: updateAward,
    isPending: loading,
    error
  }
}

/**
 * Hook to delete an award
 */
export function useDeleteAward() {
  const { mutate, loading, error } = useApiMutation()
  
  const deleteAward = async (awardId: string): Promise<void> => {
    const response = await mutate(`/awards/${awardId}`, undefined, 'DELETE')
    if (!response) {
      throw new Error('Failed to delete award')
    }
  }
  
  return {
    mutateAsync: deleteAward,
    isPending: loading,
    error
  }
}

/**
 * Hook to fetch award winners
 */
export function useAwardWinners(awardId?: string, week?: number, season?: number) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (awardId) queryParams.set('award_id', awardId)
  if (week) queryParams.set('week', week.toString())
  if (season) queryParams.set('season', season.toString())
  
  const endpoint = `/awards/winners${queryParams.toString() ? `?${queryParams}` : ''}`
  
  const apiResult = useApi<AwardWinnerListResponse>(endpoint, {
    immediate: !!user,
    deps: [user, awardId, week, season]
  })
  
  return {
    data: apiResult.data?.data || [],
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to assign an award winner
 */
export function useAssignAwardWinner() {
  const { mutate, loading, error } = useApiMutation<AwardWinnerResponse, AwardWinnerAssignRequest>()
  
  const assignWinner = async ({ awardId, data }: { 
    awardId: string; 
    data: AwardWinnerAssignRequest 
  }): Promise<AwardWinner> => {
    const response = await mutate(`/awards/${awardId}/winners`, data, 'POST')
    if (!response?.data) {
      throw new Error(response?.error || 'Failed to assign award winner')
    }
    return response.data
  }
  
  return {
    mutateAsync: assignWinner,
    isPending: loading,
    error
  }
}

/**
 * Hook to remove an award winner
 */
export function useRemoveAwardWinner() {
  const { mutate, loading, error } = useApiMutation()
  
  const removeWinner = async (winnerId: string): Promise<void> => {
    const response = await mutate(`/awards/winners/${winnerId}`, undefined, 'DELETE')
    if (!response) {
      throw new Error('Failed to remove award winner')
    }
  }
  
  return {
    mutateAsync: removeWinner,
    isPending: loading,
    error
  }
}

/**
 * Hook to fetch award templates
 */
export function useAwardTemplates() {
  const { user } = useAuth()
  
  const apiResult = useApi<AwardTemplateResponse>('/awards/templates', {
    immediate: !!user,
    deps: [user]
  })
  
  return {
    data: {
      templates: apiResult.data?.data || [],
      categories: apiResult.data?.categories || []
    },
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to get award statistics
 */
export function useAwardStats(leagueId?: string) {
  const { data: awards } = useAwards(leagueId)
  const { data: winners } = useAwardWinners()
  
  const stats = {
    totalAwards: awards?.length || 0,
    activeAwards: awards?.filter(award => award.status === 'active').length || 0,
    totalWinners: winners?.length || 0,
    weeklyAwards: awards?.filter(award => award.frequency === 'weekly').length || 0,
    seasonAwards: awards?.filter(award => award.frequency === 'season').length || 0,
    autoAssignAwards: awards?.filter(award => award.auto_assign).length || 0,
  }
  
  return {
    data: stats,
    isLoading: false, // Derived from other queries
  }
}

/**
 * Hook for bulk award operations
 */
export function useBulkAwardOperations() {
  const { mutate, loading, error } = useApiMutation()
  
  const bulkAssignWinners = async (assignments: Array<{ awardId: string; data: AwardWinnerAssignRequest }>) => {
    const promises = assignments.map(({ awardId, data }) =>
      mutate(`/awards/${awardId}/winners`, data, 'POST')
    )
    return Promise.all(promises)
  }
  
  const bulkUpdateStatus = async ({ awardIds, status }: { awardIds: string[]; status: string }) => {
    const promises = awardIds.map(id =>
      mutate(`/awards/${id}`, { status }, 'PUT')
    )
    return Promise.all(promises)
  }
  
  return {
    bulkAssignWinners,
    bulkUpdateStatus,
    isLoading: loading,
    error
  }
}
