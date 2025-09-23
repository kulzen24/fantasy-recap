/**
 * Award Winner Assignment Form Component
 * Allows users to assign winners to awards for specific weeks
 */

import React, { useState, useEffect } from 'react'
import { 
  Award,
  AwardWinner,
  AwardWinnerAssignRequest,
  Team,
  Player,
  League
} from '../../types/api'
import { useAssignAwardWinner } from '../../hooks/useAwards'
import { YahooPlayerSelector, SelectedPlayer } from './YahooPlayerSelector'

interface AwardWinnerFormProps {
  award: Award
  league?: League
  week: number
  season: number
  existingWinner?: AwardWinner
  teams?: Team[]
  onSuccess?: (winner: AwardWinner) => void
  onCancel?: () => void
  className?: string
}

interface WinnerCandidate {
  id: string
  name: string
  type: 'team' | 'player'
  platform: string
  stats?: Record<string, number>
  teamName?: string
  position?: string
}

export function AwardWinnerForm({
  award,
  league,
  week,
  season,
  existingWinner,
  teams = [],
  onSuccess,
  onCancel,
  className = ''
}: AwardWinnerFormProps) {
  const assignWinner = useAssignAwardWinner()
  
  const [selectedWinner, setSelectedWinner] = useState<WinnerCandidate | null>(null)
  const [reason, setReason] = useState('')
  const [highlightMessage, setHighlightMessage] = useState('')
  const [candidates, setCandidates] = useState<WinnerCandidate[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'team' | 'player'>('all')
  const [errors, setErrors] = useState<Record<string, string>>({})
  
  // Initialize form with existing winner data
  useEffect(() => {
    if (existingWinner) {
      setSelectedWinner({
        id: existingWinner.winner_id,
        name: existingWinner.winner_name,
        type: existingWinner.winner_type as 'team' | 'player',
        platform: existingWinner.platform
      })
      setReason(existingWinner.reason || '')
      setHighlightMessage(existingWinner.highlight_message || '')
    }
  }, [existingWinner])
  
  // Generate candidates based on award criteria and available data
  useEffect(() => {
    const newCandidates: WinnerCandidate[] = []
    
    // Add teams as candidates for team-based awards
    if (award.criteria.type === 'team_performance' || award.criteria.type === 'matchup_based' || award.criteria.type === 'custom') {
      teams.forEach(team => {
        newCandidates.push({
          id: team.id,
          name: team.name,
          type: 'team',
          platform: team.platform,
          stats: {
            points_for: team.points_for,
            points_against: team.points_against,
            wins: team.wins,
            losses: team.losses
          }
        })
      })
    }
    
    // Add players as candidates for player-based awards
    if (award.criteria.type === 'player_performance' || award.criteria.type === 'custom') {
      teams.forEach(team => {
        team.roster.forEach(player => {
          newCandidates.push({
            id: player.id,
            name: player.name,
            type: 'player',
            platform: player.platform,
            teamName: team.name,
            position: player.position,
            stats: {
              projected_points: player.projected_points || 0,
              actual_points: player.actual_points || 0
            }
          })
        })
      })
    }
    
    setCandidates(newCandidates)
  }, [award.criteria.type, teams])
  
  // Filter candidates based on search and type filter
  const filteredCandidates = candidates.filter(candidate => {
    const matchesSearch = candidate.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         candidate.teamName?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === 'all' || candidate.type === filterType
    
    return matchesSearch && matchesType
  })
  
  // Validate form
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    if (!selectedWinner) {
      newErrors.winner = 'Please select a winner'
    }
    
    if (!reason.trim()) {
      newErrors.reason = 'Please provide a reason for this award'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm() || !selectedWinner) return
    
    try {
      const assignmentData: AwardWinnerAssignRequest = {
        week,
        season,
        winner_type: selectedWinner.type,
        winner_id: selectedWinner.id,
        winner_name: selectedWinner.name,
        platform: selectedWinner.platform,
        reason: reason.trim(),
        stats: selectedWinner.stats || {},
        highlight_message: highlightMessage.trim() || undefined
      }
      
      const newWinner = await assignWinner.mutateAsync({
        awardId: award.id,
        data: assignmentData
      })
      
      onSuccess?.(newWinner)
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'Failed to assign award winner'
      })
    }
  }
  
  const isLoading = assignWinner.isPending
  
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          <span className="text-2xl mr-2">{award.emoji}</span>
          Assign Winner: {award.name}
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Week {week}, {season} • {award.description}
        </p>
        {league && (
          <p className="text-sm text-gray-500 dark:text-gray-500">
            League: {league.league_name}
          </p>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Yahoo Player Selector */}
        {league?.platform === 'yahoo' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              🏈 Select from Yahoo League Data
            </label>
            <YahooPlayerSelector
              leagueId={league.league_id}
              week={week}
              season={season}
              awardCriteria={String(award.criteria || award.description || '')}
              onPlayerSelect={(player: SelectedPlayer) => {
                const winnerCandidate: WinnerCandidate = {
                  id: player.id,
                  name: player.name,
                  type: player.type,
                  platform: player.platform,
                  stats: player.stats,
                  teamName: player.teamName,
                  position: player.position
                }
                setSelectedWinner(winnerCandidate)
                if (player.reason) {
                  setReason(player.reason)
                }
              }}
              className="border border-gray-200 dark:border-gray-600 rounded-lg p-4"
            />
          </div>
        )}

        {/* Manual Winner Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Select Winner Manually *
          </label>
          
          {/* Search and Filter */}
          <div className="mb-4 flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search teams or players..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as 'all' | 'team' | 'player')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All</option>
                <option value="team">Teams</option>
                <option value="player">Players</option>
              </select>
            </div>
          </div>
          
          {/* Candidates List */}
          <div className="border border-gray-200 dark:border-gray-600 rounded-md max-h-64 overflow-y-auto">
            {filteredCandidates.length === 0 ? (
              <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                {searchTerm ? 'No candidates match your search' : 'No candidates available'}
              </div>
            ) : (
              filteredCandidates.map((candidate) => (
                <div
                  key={`${candidate.type}-${candidate.id}`}
                  onClick={() => setSelectedWinner(candidate)}
                  className={`p-3 border-b border-gray-200 dark:border-gray-600 last:border-b-0 
                           cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors
                           ${selectedWinner?.id === candidate.id ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {candidate.name}
                        {candidate.type === 'player' && candidate.position && (
                          <span className="ml-2 text-sm text-gray-500">({candidate.position})</span>
                        )}
                      </div>
                      {candidate.teamName && (
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {candidate.teamName}
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        candidate.type === 'team' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                      }`}>
                        {candidate.type === 'team' ? 'Team' : 'Player'}
                      </span>
                      {candidate.stats && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {candidate.type === 'team' 
                            ? `${candidate.stats.wins || 0}-${candidate.stats.losses || 0} • ${candidate.stats.points_for?.toFixed(1) || 0} pts`
                            : `${candidate.stats.actual_points?.toFixed(1) || 0} pts`
                          }
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          {selectedWinner && (
            <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <div className="flex items-center">
                <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Selected: {selectedWinner.name}
                  {selectedWinner.type === 'player' && selectedWinner.teamName && (
                    <span className="text-blue-700 dark:text-blue-300"> • {selectedWinner.teamName}</span>
                  )}
                </span>
              </div>
            </div>
          )}
          
          {errors.winner && <p className="text-red-500 text-sm mt-1">{errors.winner}</p>}
        </div>
        
        {/* Reason */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Reason for Award *
          </label>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Why does this person/team deserve this award? (e.g., scored the highest points this week)"
            maxLength={500}
          />
          <div className="flex justify-between mt-1">
            {errors.reason && <p className="text-red-500 text-sm">{errors.reason}</p>}
            <p className="text-sm text-gray-500 dark:text-gray-400 ml-auto">
              {reason.length}/500
            </p>
          </div>
        </div>
        
        {/* Highlight Message */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Highlight Message (Optional)
          </label>
          <input
            type="text"
            value={highlightMessage}
            onChange={(e) => setHighlightMessage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Special message to highlight with this award"
            maxLength={200}
          />
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {highlightMessage.length}/200
          </p>
        </div>
        
        {/* Error Display */}
        {errors.general && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
            <p className="text-red-600 dark:text-red-400 text-sm">{errors.general}</p>
          </div>
        )}
        
        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-600">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 
                       bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                       rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            >
              Cancel
            </button>
          )}
          
          <button
            type="submit"
            disabled={isLoading || !selectedWinner}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 
                     border border-transparent rounded-md hover:bg-blue-700 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center space-x-2"
          >
            {isLoading && (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            <span>{existingWinner ? 'Update Winner' : 'Assign Winner'}</span>
          </button>
        </div>
      </form>
    </div>
  )
}
