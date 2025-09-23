/**
 * Yahoo Player Selector Component
 * Queries Yahoo API to fetch player data for award assignment
 */

import React, { useState, useEffect } from 'react'
import { useYahooPlayers, useYahooTeams, useYahooMatchups } from '../../hooks/useYahooData'

interface YahooPlayerSelectorProps {
  leagueId: string
  week: number
  season: number
  onPlayerSelect: (player: SelectedPlayer) => void
  awardCriteria?: string
  className?: string
}

export interface SelectedPlayer {
  id: string
  name: string
  type: 'player' | 'team'
  platform: string
  stats?: Record<string, number>
  teamName?: string
  position?: string
  reason?: string
}

interface StatLeader {
  player: any
  stat: string
  value: number
  reason: string
}

export function YahooPlayerSelector({
  leagueId,
  week,
  season,
  onPlayerSelect,
  awardCriteria = '',
  className = ''
}: YahooPlayerSelectorProps) {
  const { players, isLoading: playersLoading, error: playersError } = useYahooPlayers(leagueId, week)
  const { teams, isLoading: teamsLoading, error: teamsError } = useYahooTeams(leagueId)
  const { matchups, isLoading: matchupsLoading, error: matchupsError } = useYahooMatchups(leagueId, week, season)
  
  const [selectedType, setSelectedType] = useState<'players' | 'teams' | 'auto'>('auto')
  const [statLeaders, setStatLeaders] = useState<StatLeader[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'points' | 'name' | 'position'>('points')

  // Calculate stat leaders automatically based on criteria
  useEffect(() => {
    if (!players.length && !teams.length) return

    const leaders: StatLeader[] = []

    // Auto-detect award type and find leaders
    const criteriaLower = awardCriteria.toLowerCase()
    
    if (players.length > 0) {
      // Player-based awards
      const playersWithStats = players.filter(p => p.points_this_week !== undefined)
      
      if (criteriaLower.includes('highest') || criteriaLower.includes('most') || criteriaLower.includes('mvp')) {
        const topPlayer = playersWithStats.reduce((max, player) => 
          (player.points_this_week || 0) > (max.points_this_week || 0) ? player : max
        )
        if (topPlayer) {
          leaders.push({
            player: topPlayer,
            stat: 'Points',
            value: topPlayer.points_this_week || 0,
            reason: `Highest scoring player with ${topPlayer.points_this_week} points`
          })
        }
      }
      
      if (criteriaLower.includes('lowest') || criteriaLower.includes('least') || criteriaLower.includes('lvp')) {
        const bottomPlayer = playersWithStats.reduce((min, player) => 
          (player.points_this_week || 0) < (min.points_this_week || 0) ? player : min
        )
        if (bottomPlayer) {
          leaders.push({
            player: bottomPlayer,
            stat: 'Points',
            value: bottomPlayer.points_this_week || 0,
            reason: `Lowest scoring player with ${bottomPlayer.points_this_week} points`
          })
        }
      }
    }

    if (teams.length > 0) {
      // Team-based awards from matchups
      if (matchups.length > 0) {
        const highestScoringTeam = matchups.reduce((max, matchup) => {
          const homeScore = matchup.home_score
          const awayScore = matchup.away_score
          
          if (homeScore > awayScore && homeScore > (max.score || 0)) {
            return { teamId: matchup.home_team_id, teamName: matchup.home_team_name, score: homeScore }
          } else if (awayScore > homeScore && awayScore > (max.score || 0)) {
            return { teamId: matchup.away_team_id, teamName: matchup.away_team_name, score: awayScore }
          }
          return max
        }, { score: 0 } as any)

        if (highestScoringTeam.teamId && (criteriaLower.includes('highest') || criteriaLower.includes('most'))) {
          leaders.push({
            player: { 
              id: highestScoringTeam.teamId,
              name: highestScoringTeam.teamName,
              type: 'team'
            },
            stat: 'Team Score',
            value: highestScoringTeam.score,
            reason: `Highest scoring team with ${highestScoringTeam.score} points`
          })
        }

        const lowestScoringTeam = matchups.reduce((min, matchup) => {
          const homeScore = matchup.home_score
          const awayScore = matchup.away_score
          
          if (homeScore < awayScore && homeScore < (min.score || Infinity)) {
            return { teamId: matchup.home_team_id, teamName: matchup.home_team_name, score: homeScore }
          } else if (awayScore < homeScore && awayScore < (min.score || Infinity)) {
            return { teamId: matchup.away_team_id, teamName: matchup.away_team_name, score: awayScore }
          }
          return min
        }, { score: Infinity } as any)

        if (lowestScoringTeam.teamId && (criteriaLower.includes('lowest') || criteriaLower.includes('least'))) {
          leaders.push({
            player: { 
              id: lowestScoringTeam.teamId,
              name: lowestScoringTeam.teamName,
              type: 'team'
            },
            stat: 'Team Score',
            value: lowestScoringTeam.score,
            reason: `Lowest scoring team with ${lowestScoringTeam.score} points`
          })
        }
      }
    }

    setStatLeaders(leaders)
  }, [players, teams, matchups, awardCriteria])

  // Filter and sort data
  const filteredPlayers = players
    .filter(player => 
      searchQuery === '' || 
      player.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      player.position.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'points':
          return (b.points_this_week || 0) - (a.points_this_week || 0)
        case 'name':
          return a.name.localeCompare(b.name)
        case 'position':
          return a.position.localeCompare(b.position)
        default:
          return 0
      }
    })

  const filteredTeams = teams
    .filter(team => 
      searchQuery === '' || 
      team.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      team.owner_name.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => b.points_for - a.points_for)

  const handleSelectPlayer = (player: any, reason?: string) => {
    const selectedPlayer: SelectedPlayer = {
      id: player.id,
      name: player.name,
      type: 'player',
      platform: 'yahoo',
      stats: {
        points_this_week: player.points_this_week || 0,
        points_season: player.points_season || 0
      },
      teamName: player.team,
      position: player.position,
      reason: reason || `Selected for award`
    }
    onPlayerSelect(selectedPlayer)
  }

  const handleSelectTeam = (team: any, reason?: string) => {
    const selectedPlayer: SelectedPlayer = {
      id: team.id,
      name: team.name,
      type: 'team',
      platform: 'yahoo',
      stats: {
        points_for: team.points_for,
        points_against: team.points_against,
        wins: team.wins,
        losses: team.losses
      },
      reason: reason || `Selected for award`
    }
    onPlayerSelect(selectedPlayer)
  }

  const isLoading = playersLoading || teamsLoading || matchupsLoading
  const hasError = playersError || teamsError || matchupsError

  if (hasError) {
    return (
      <div className={`p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg ${className}`}>
        <h4 className="font-medium text-red-900 dark:text-red-100 mb-2">
          Error Loading Yahoo Data
        </h4>
        <p className="text-sm text-red-700 dark:text-red-300">
          {playersError || teamsError || matchupsError}
        </p>
        <p className="text-xs text-red-600 dark:text-red-400 mt-2">
          Make sure your Yahoo league is connected in Settings.
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`p-6 text-center ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading Yahoo league data...</p>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Award Criteria & Auto-Suggestions */}
      {awardCriteria && statLeaders.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
            🎯 Suggested Winners (Based on "{awardCriteria}")
          </h4>
          <div className="space-y-2">
            {statLeaders.map((leader, index) => (
              <div key={index} className="flex items-center justify-between bg-white dark:bg-gray-800 rounded p-3">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {leader.player.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {leader.reason}
                  </p>
                </div>
                <button
                  onClick={() => 
                    leader.player.type === 'team' 
                      ? handleSelectTeam(leader.player, leader.reason)
                      : handleSelectPlayer(leader.player, leader.reason)
                  }
                  className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition-colors"
                >
                  Select
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search players or teams..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        
        <div className="flex gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as 'players' | 'teams' | 'auto')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="auto">Auto</option>
            <option value="players">Players</option>
            <option value="teams">Teams</option>
          </select>
          
          {(selectedType === 'players' || selectedType === 'auto') && (
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'points' | 'name' | 'position')}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="points">Points</option>
              <option value="name">Name</option>
              <option value="position">Position</option>
            </select>
          )}
        </div>
      </div>

      {/* Players List */}
      {(selectedType === 'players' || selectedType === 'auto') && filteredPlayers.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 dark:text-white mb-3">
            Players (Week {week})
          </h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {filteredPlayers.map((player) => (
              <div
                key={player.id}
                className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {player.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {player.position} • {player.team}
                    {player.points_this_week !== undefined && (
                      <> • {player.points_this_week} pts this week</>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => handleSelectPlayer(player)}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                >
                  Select
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Teams List */}
      {(selectedType === 'teams' || selectedType === 'auto') && filteredTeams.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-900 dark:text-white mb-3">
            Teams
          </h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {filteredTeams.map((team) => (
              <div
                key={team.id}
                className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {team.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Owner: {team.owner_name} • {team.wins}-{team.losses} • {team.points_for.toFixed(1)} PF
                  </p>
                </div>
                <button
                  onClick={() => handleSelectTeam(team)}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                >
                  Select
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Data Message */}
      {!isLoading && filteredPlayers.length === 0 && filteredTeams.length === 0 && (
        <div className="text-center py-8">
          <div className="text-4xl mb-4">🏈</div>
          <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No Data Found
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            {searchQuery 
              ? `No results found for "${searchQuery}"`
              : 'No player or team data available for this league and week.'
            }
          </p>
        </div>
      )}
    </div>
  )
}
