/**
 * Batch Winner Assignment Component
 * Allows users to assign multiple award winners at once for efficiency
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
import { useBulkAwardOperations } from '../../hooks/useAwards'

interface BatchWinnerAssignmentProps {
  awards: Award[]
  league?: League
  week: number
  season: number
  teams?: Team[]
  onSuccess?: (winners: AwardWinner[]) => void
  onCancel?: () => void
  className?: string
}

interface AssignmentEntry {
  awardId: string
  winnerId?: string
  winnerName?: string
  winnerType?: 'team' | 'player'
  platform?: string
  reason?: string
}

export function BatchWinnerAssignment({
  awards,
  league,
  week,
  season,
  teams = [],
  onSuccess,
  onCancel,
  className = ''
}: BatchWinnerAssignmentProps) {
  const { bulkAssignWinners, isLoading, error } = useBulkAwardOperations()
  
  const [assignments, setAssignments] = useState<AssignmentEntry[]>([])
  const [globalReason, setGlobalReason] = useState('')
  const [useGlobalReason, setUseGlobalReason] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  
  // Initialize assignments for each award
  useEffect(() => {
    setAssignments(
      awards.map(award => ({
        awardId: award.id,
        reason: ''
      }))
    )
  }, [awards])
  
  // Generate candidate options
  const getCandidatesForAward = (award: Award) => {
    const candidates: Array<{ id: string; name: string; type: 'team' | 'player'; platform: string; teamName?: string; position?: string }> = []
    
    // Add teams for team-based awards
    if (award.criteria.type === 'team_performance' || award.criteria.type === 'matchup_based' || award.criteria.type === 'custom') {
      teams.forEach(team => {
        candidates.push({
          id: team.id,
          name: team.name,
          type: 'team',
          platform: team.platform
        })
      })
    }
    
    // Add players for player-based awards
    if (award.criteria.type === 'player_performance' || award.criteria.type === 'custom') {
      teams.forEach(team => {
        team.roster.forEach(player => {
          candidates.push({
            id: player.id,
            name: player.name,
            type: 'player',
            platform: player.platform,
            teamName: team.name,
            position: player.position
          })
        })
      })
    }
    
    return candidates
  }
  
  // Update assignment
  const updateAssignment = (awardId: string, updates: Partial<AssignmentEntry>) => {
    setAssignments(prev => 
      prev.map(assignment => 
        assignment.awardId === awardId 
          ? { ...assignment, ...updates }
          : assignment
      )
    )
  }
  
  // Handle winner selection
  const handleWinnerSelect = (awardId: string, candidateId: string) => {
    const award = awards.find(a => a.id === awardId)
    if (!award) return
    
    const candidates = getCandidatesForAward(award)
    const candidate = candidates.find(c => c.id === candidateId)
    
    if (candidate) {
      updateAssignment(awardId, {
        winnerId: candidate.id,
        winnerName: candidate.name,
        winnerType: candidate.type,
        platform: candidate.platform
      })
    }
  }
  
  // Apply global reason to all assignments
  const applyGlobalReason = () => {
    if (globalReason.trim()) {
      setAssignments(prev => 
        prev.map(assignment => ({
          ...assignment,
          reason: globalReason.trim()
        }))
      )
    }
  }
  
  // Validate assignments
  const validateAssignments = (): boolean => {
    const newErrors: Record<string, string> = {}
    
    assignments.forEach((assignment, index) => {
      const award = awards.find(a => a.id === assignment.awardId)
      if (!award) return
      
      if (!assignment.winnerId) {
        newErrors[`winner_${assignment.awardId}`] = 'Please select a winner'
      }
      
      if (!assignment.reason?.trim()) {
        newErrors[`reason_${assignment.awardId}`] = 'Please provide a reason'
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateAssignments()) return
    
    try {
      const assignmentRequests = assignments
        .filter(assignment => assignment.winnerId)
        .map(assignment => ({
          awardId: assignment.awardId,
          data: {
            week,
            season,
            winner_type: assignment.winnerType!,
            winner_id: assignment.winnerId!,
            winner_name: assignment.winnerName!,
            platform: assignment.platform!,
            reason: assignment.reason!,
            stats: {}
          } as AwardWinnerAssignRequest
        }))
      
      await bulkAssignWinners(assignmentRequests)
      onSuccess?.([]) // Would need to return actual winners from bulk operation
    } catch (error) {
      setErrors({
        general: error instanceof Error ? error.message : 'Failed to assign winners'
      })
    }
  }
  
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Batch Award Assignment
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Assign winners to multiple awards for Week {week}, {season}
        </p>
        {league && (
          <p className="text-sm text-gray-500 dark:text-gray-500">
            League: {league.league_name}
          </p>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Global Reason */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-medium text-blue-900 dark:text-blue-100">
              Global Settings
            </h3>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={useGlobalReason}
                onChange={(e) => setUseGlobalReason(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-blue-800 dark:text-blue-200">
                Use global reason for all awards
              </span>
            </label>
          </div>
          
          {useGlobalReason && (
            <div>
              <textarea
                value={globalReason}
                onChange={(e) => setGlobalReason(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-blue-300 dark:border-blue-600 rounded-md 
                         bg-white dark:bg-blue-800/50 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter a reason to apply to all awards..."
                maxLength={500}
              />
              <div className="flex justify-between mt-2">
                <button
                  type="button"
                  onClick={applyGlobalReason}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-500"
                >
                  Apply to All Awards
                </button>
                <span className="text-sm text-blue-700 dark:text-blue-300">
                  {globalReason.length}/500
                </span>
              </div>
            </div>
          )}
        </div>
        
        {/* Award Assignments */}
        <div className="space-y-6">
          {awards.map((award, index) => {
            const assignment = assignments.find(a => a.awardId === award.id)
            const candidates = getCandidatesForAward(award)
            
            return (
              <div key={award.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-3">{award.emoji}</span>
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">{award.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{award.description}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Winner Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Winner *
                    </label>
                    <select
                      value={assignment?.winnerId || ''}
                      onChange={(e) => handleWinnerSelect(award.id, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                               bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                               focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Select winner...</option>
                      {candidates.map(candidate => (
                        <option key={`${candidate.type}-${candidate.id}`} value={candidate.id}>
                          {candidate.name}
                          {candidate.type === 'player' && candidate.position && ` (${candidate.position})`}
                          {candidate.teamName && ` • ${candidate.teamName}`}
                          {` • ${candidate.type}`}
                        </option>
                      ))}
                    </select>
                    {errors[`winner_${award.id}`] && (
                      <p className="text-red-500 text-sm mt-1">{errors[`winner_${award.id}`]}</p>
                    )}
                  </div>
                  
                  {/* Reason */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Reason *
                    </label>
                    <textarea
                      value={assignment?.reason || ''}
                      onChange={(e) => updateAssignment(award.id, { reason: e.target.value })}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                               bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                               focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Why does this winner deserve this award?"
                      maxLength={500}
                      disabled={useGlobalReason}
                    />
                    {errors[`reason_${award.id}`] && (
                      <p className="text-red-500 text-sm mt-1">{errors[`reason_${award.id}`]}</p>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
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
            disabled={isLoading || assignments.every(a => !a.winnerId)}
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
            <span>Assign All Winners ({assignments.filter(a => a.winnerId).length})</span>
          </button>
        </div>
      </form>
    </div>
  )
}
