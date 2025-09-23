/**
 * React hooks for Yahoo Fantasy Data
 * Integrates with backend Yahoo Fantasy API endpoints
 */

import { useApi } from './useApi'
import { useAuth } from '../contexts/AuthContext'

export interface YahooPlayer {
  id: string
  name: string
  position: string
  team: string
  points_this_week?: number
  points_season?: number
  is_available: boolean
}

export interface YahooTeam {
  id: string
  name: string
  owner_name: string
  wins: number
  losses: number
  points_for: number
  points_against: number
}

export interface YahooMatchup {
  id: string
  week: number
  season: number
  home_team_id: string
  away_team_id: string
  home_team_name: string
  away_team_name: string
  home_score: number
  away_score: number
  status: string
}

export interface YahooLeagueInfo {
  id: string
  name: string
  season: number
  current_week: number
  total_teams: number
  scoring_type: string
}

/**
 * Hook to fetch Yahoo league information
 */
export function useYahooLeague(leagueId?: string) {
  const { user } = useAuth()
  
  const apiResult = useApi<{ success: boolean; data: YahooLeagueInfo }>(
    leagueId ? `/fantasy/yahoo/leagues/${leagueId}` : '',
    {
      immediate: !!user && !!leagueId,
      deps: [user, leagueId]
    }
  )
  
  return {
    league: apiResult.data?.data,
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to fetch Yahoo league teams
 */
export function useYahooTeams(leagueId?: string) {
  const { user } = useAuth()
  
  const apiResult = useApi<{ success: boolean; data: YahooTeam[] }>(
    leagueId ? `/fantasy/yahoo/leagues/${leagueId}/teams` : '',
    {
      immediate: !!user && !!leagueId,
      deps: [user, leagueId]
    }
  )
  
  return {
    teams: apiResult.data?.data || [],
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to fetch Yahoo league players
 */
export function useYahooPlayers(leagueId?: string, week?: number) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (week) queryParams.set('week', week.toString())
  
  const endpoint = leagueId 
    ? `/fantasy/yahoo/leagues/${leagueId}/players${queryParams.toString() ? `?${queryParams}` : ''}`
    : ''
  
  const apiResult = useApi<{ success: boolean; data: YahooPlayer[] }>(endpoint, {
    immediate: !!user && !!leagueId,
    deps: [user, leagueId, week]
  })
  
  return {
    players: apiResult.data?.data || [],
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to fetch Yahoo league matchups
 */
export function useYahooMatchups(leagueId?: string, week?: number, year?: number) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (week) queryParams.set('week', week.toString())
  if (year) queryParams.set('year', year.toString())
  
  const endpoint = leagueId 
    ? `/fantasy/yahoo/leagues/${leagueId}/matchups${queryParams.toString() ? `?${queryParams}` : ''}`
    : ''
  
  const apiResult = useApi<{ success: boolean; data: YahooMatchup[] }>(endpoint, {
    immediate: !!user && !!leagueId && !!week,
    deps: [user, leagueId, week, year]
  })
  
  return {
    matchups: apiResult.data?.data || [],
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}

/**
 * Hook to fetch team roster
 */
export function useYahooTeamRoster(leagueId?: string, teamId?: string, week?: number) {
  const { user } = useAuth()
  
  const queryParams = new URLSearchParams()
  if (week) queryParams.set('week', week.toString())
  
  const endpoint = leagueId && teamId
    ? `/fantasy/yahoo/leagues/${leagueId}/teams/${teamId}/roster${queryParams.toString() ? `?${queryParams}` : ''}`
    : ''
  
  const apiResult = useApi<{ success: boolean; data: YahooPlayer[] }>(endpoint, {
    immediate: !!user && !!leagueId && !!teamId,
    deps: [user, leagueId, teamId, week]
  })
  
  return {
    roster: apiResult.data?.data || [],
    isLoading: apiResult.loading,
    error: apiResult.error,
    refetch: apiResult.refetch
  }
}
