import { useApi, useApiMutation } from './useApi'
import { useAuth } from '../contexts/AuthContext'
import { 
  League, 
  LeagueStats, 
  Recap, 
  RecapStats, 
  RecapGenerationRequest,
  ProviderPreferences, 
  APIKeyInfo,
  Template,
  TemplateStats,
  APIResponse,
  PaginatedResponse 
} from '../types/api'

// League Hooks
export function useLeagues(filters?: { season?: number; platform?: string; active_only?: boolean }) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (filters?.season) queryParams.set('season', filters.season.toString())
  if (filters?.platform) queryParams.set('platform', filters.platform)
  if (filters?.active_only !== undefined) queryParams.set('active_only', filters.active_only.toString())
  
  const endpoint = `/leagues${queryParams.toString() ? `?${queryParams}` : ''}`
  
  return useApi<PaginatedResponse<League>>(endpoint, { 
    immediate: !!user,
    deps: [user, filters]
  })
}

export function useLeagueStats() {
  const { user } = useAuth()
  
  return useApi<LeagueStats>('/leagues/stats', { 
    immediate: !!user,
    deps: [user]
  })
}

export function useLeague(leagueId: string) {
  const { user } = useAuth()
  
  return useApi<League>(`/leagues/${leagueId}`, {
    immediate: !!user && !!leagueId,
    deps: [user, leagueId]
  })
}

// League Mutations
export function useConnectLeague() {
  return useApiMutation<APIResponse<League>, { platform: string; oauth_code?: string }>()
}

export function useSyncLeague() {
  return useApiMutation<APIResponse<League>, {}>()
}

export function useUpdateLeague() {
  return useApiMutation<APIResponse<League>, Partial<League>>()
}

export function useDeleteLeague() {
  return useApiMutation<APIResponse<void>, {}>()
}

// Recap Hooks
export function useRecaps(params?: { 
  page?: number
  page_size?: number 
  league_id?: string
  week?: number
  season?: number
}) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.set('page', params.page.toString())
  if (params?.page_size) queryParams.set('page_size', params.page_size.toString())
  if (params?.league_id) queryParams.set('league_id', params.league_id)
  if (params?.week) queryParams.set('week', params.week.toString())
  if (params?.season) queryParams.set('season', params.season.toString())
  
  const endpoint = `/recaps${queryParams.toString() ? `?${queryParams}` : ''}`
  
  return useApi<PaginatedResponse<Recap>>(endpoint, { 
    immediate: !!user,
    deps: [user, params]
  })
}

export function useRecap(recapId: string) {
  const { user } = useAuth()
  
  return useApi<Recap>(`/recaps/${recapId}`, {
    immediate: !!user && !!recapId,
    deps: [user, recapId]
  })
}

export function useRecapStats() {
  const { user } = useAuth()
  
  return useApi<RecapStats>('/recaps/stats/summary', { 
    immediate: !!user,
    deps: [user]
  })
}

export function useLeagueInsights(leagueId: string, week?: number, season?: number) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (week) queryParams.set('week', week.toString())
  if (season) queryParams.set('season', season.toString())
  
  const endpoint = `/recaps/insights/${leagueId}${queryParams.toString() ? `?${queryParams}` : ''}`
  
  return useApi<any>(endpoint, {
    immediate: !!user && !!leagueId,
    deps: [user, leagueId, week, season]
  })
}

// Recap Mutations
export function useGenerateRecap() {
  return useApiMutation<APIResponse<Recap>, RecapGenerationRequest>()
}

export function useDeleteRecap() {
  return useApiMutation<APIResponse<void>, {}>()
}

export function useRegenerateRecap() {
  return useApiMutation<APIResponse<Recap>, Partial<RecapGenerationRequest>>()
}

export function useSubmitRecapFeedback() {
  return useApiMutation<APIResponse<void>, {
    rating: number
    style_accuracy: number
    content_quality: number
    feedback_text?: string
    improvement_suggestions?: string
  }>()
}

// Provider and API Key Hooks
export function useProviderPreferences() {
  const { user } = useAuth()
  
  return useApi<ProviderPreferences>('/provider-preferences/preferences', { 
    immediate: !!user,
    deps: [user]
  })
}

export function useApiKeys() {
  const { user } = useAuth()
  
  return useApi<APIKeyInfo[]>('/llm-keys', { 
    immediate: !!user,
    deps: [user]
  })
}

export function useAvailableProviders() {
  const { user } = useAuth()
  
  return useApi<{ providers: string[] }>('/provider-preferences/available-providers', { 
    immediate: !!user,
    deps: [user]
  })
}

// Provider Mutations
export function useSetProviderPreferences() {
  return useApiMutation<APIResponse<ProviderPreferences>, Partial<ProviderPreferences>>()
}

export function useStoreApiKey() {
  return useApiMutation<APIResponse<APIKeyInfo>, { provider: string; api_key: string }>()
}

export function useValidateApiKey() {
  return useApiMutation<{ is_valid: boolean; error?: string }, {}>()
}

export function useDeleteApiKey() {
  return useApiMutation<APIResponse<void>, {}>()
}

// Template Hooks
export function useTemplates(params?: { 
  page?: number
  page_size?: number 
  status_filter?: string
}) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.set('page', params.page.toString())
  if (params?.page_size) queryParams.set('page_size', params.page_size.toString())
  if (params?.status_filter) queryParams.set('status_filter', params.status_filter)
  
  const endpoint = `/templates${queryParams.toString() ? `?${queryParams}` : ''}`
  
  return useApi<PaginatedResponse<Template>>(endpoint, { 
    immediate: !!user,
    deps: [user, params]
  })
}

export function useTemplate(templateId: string) {
  const { user } = useAuth()
  
  return useApi<Template>(`/templates/${templateId}`, {
    immediate: !!user && !!templateId,
    deps: [user, templateId]
  })
}

export function useTemplateStats() {
  const { user } = useAuth()
  
  return useApi<TemplateStats>('/templates/stats/summary', { 
    immediate: !!user,
    deps: [user]
  })
}

export function useActivePromptTemplate() {
  const { user } = useAuth()
  
  return useApi<Template | null>('/templates/prompts/active', { 
    immediate: !!user,
    deps: [user]
  })
}

// Template Mutations
export function useUploadTemplate() {
  return useApiMutation<APIResponse<Template>, FormData>()
}

export function useAnalyzeTemplate() {
  return useApiMutation<APIResponse<Template>, { force_reanalysis?: boolean }>()
}

export function useSetDefaultTemplate() {
  return useApiMutation<APIResponse<void>, {}>()
}

export function useDeleteTemplate() {
  return useApiMutation<APIResponse<void>, {}>()
}

// Recap editing hooks
export function useUpdateRecap() {
  return useApiMutation<Recap>()
}

export function useCreateRecap() {
  return useApiMutation<Recap>()
}

export function useGetRecap(recapId: string) {
  return useApi<Recap>(`/recaps/${recapId}`, {
    immediate: !!recapId,
    deps: [recapId]
  })
}