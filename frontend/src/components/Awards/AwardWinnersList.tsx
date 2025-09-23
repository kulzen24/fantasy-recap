/**
 * Award Winners List Component
 * Displays award winners with history and management capabilities
 */

import React, { useState } from 'react'
import { 
  Award,
  AwardWinner,
  League
} from '../../types/api'
import { useAwardWinners, useRemoveAwardWinner } from '../../hooks/useAwards'
import { AwardWinnerForm } from './AwardWinnerForm'

interface AwardWinnersListProps {
  award?: Award
  league?: League
  week?: number
  season?: number
  onCancel?: () => void
  className?: string
}

interface FilterState {
  week: string
  season: string
  winnerType: 'all' | 'team' | 'player'
  search: string
}

export function AwardWinnersList({ 
  award, 
  league, 
  week, 
  season, 
  onCancel,
  className = '' 
}: AwardWinnersListProps) {
  const { data: winners = [], isLoading, error, refetch } = useAwardWinners(
    award?.id, 
    week, 
    season
  )
  const removeWinner = useRemoveAwardWinner()
  
  const [filters, setFilters] = useState<FilterState>({
    week: week?.toString() || '',
    season: season?.toString() || new Date().getFullYear().toString(),
    winnerType: 'all',
    search: ''
  })
  
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [editingWinner, setEditingWinner] = useState<AwardWinner | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  
  // Filter winners
  const filteredWinners = winners.filter(winner => {
    const matchesWeek = !filters.week || winner.week.toString() === filters.week
    const matchesSeason = !filters.season || winner.season.toString() === filters.season
    const matchesType = filters.winnerType === 'all' || winner.winner_type === filters.winnerType
    const matchesSearch = !filters.search || 
      winner.winner_name.toLowerCase().includes(filters.search.toLowerCase()) ||
      winner.reason?.toLowerCase().includes(filters.search.toLowerCase())
    
    return matchesWeek && matchesSeason && matchesType && matchesSearch
  })
  
  // Group winners by week for better organization
  const winnersByWeek = filteredWinners.reduce((acc, winner) => {
    const key = `${winner.season}-W${winner.week}`
    if (!acc[key]) {
      acc[key] = []
    }
    acc[key].push(winner)
    return acc
  }, {} as Record<string, AwardWinner[]>)
  
  // Handle delete
  const handleDelete = async (winnerId: string) => {
    try {
      await removeWinner.mutateAsync(winnerId)
      setConfirmDelete(null)
      refetch()
    } catch (error) {
      console.error('Failed to remove award winner:', error)
    }
  }
  
  // Handle assign success
  const handleAssignSuccess = () => {
    setShowAssignForm(false)
    setEditingWinner(null)
    refetch()
  }
  
  // Get unique weeks and seasons for filters
  const availableWeeks = Array.from(new Set(winners.map(w => w.week))).sort((a, b) => b - a)
  const availableSeasons = Array.from(new Set(winners.map(w => w.season))).sort((a, b) => b - a)
  
  if (showAssignForm || editingWinner) {
    return (
      <AwardWinnerForm
        award={award!}
        league={league}
        week={editingWinner?.week || week || 1}
        season={editingWinner?.season || season || new Date().getFullYear()}
        existingWinner={editingWinner || undefined}
        onSuccess={handleAssignSuccess}
        onCancel={() => {
          setShowAssignForm(false)
          setEditingWinner(null)
        }}
        className={className}
      />
    )
  }
  
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {onCancel && (
              <button
                onClick={onCancel}
                className="mr-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 
                         rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                title="Back to awards"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {award ? (
                  <span className="flex items-center">
                    <span className="text-2xl mr-2">{award.emoji}</span>
                    {award.name} Winners
                  </span>
                ) : (
                  'Award Winners'
                )}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {award 
                  ? `View and manage winners for this ${award.frequency} award`
                  : 'View all award winners across your league'
                }
              </p>
            </div>
          </div>
          
          {award && (
            <button
              onClick={() => setShowAssignForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                       flex items-center space-x-2"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Assign Winner</span>
            </button>
          )}
        </div>
        
        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {winners.length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Total Winners</div>
          </div>
          
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {winners.filter(w => w.winner_type === 'team').length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Teams</div>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {winners.filter(w => w.winner_type === 'player').length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Players</div>
          </div>
          
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {availableWeeks.length}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Weeks</div>
          </div>
        </div>
      </div>
      
      {/* Filters */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Search
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              placeholder="Search winners..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Season
            </label>
            <select
              value={filters.season}
              onChange={(e) => setFilters(prev => ({ ...prev, season: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Seasons</option>
              {availableSeasons.map(season => (
                <option key={season} value={season}>{season}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Week
            </label>
            <select
              value={filters.week}
              onChange={(e) => setFilters(prev => ({ ...prev, week: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Weeks</option>
              {availableWeeks.map(week => (
                <option key={week} value={week}>Week {week}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type
            </label>
            <select
              value={filters.winnerType}
              onChange={(e) => setFilters(prev => ({ ...prev, winnerType: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              <option value="team">Teams</option>
              <option value="player">Players</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ week: '', season: '', winnerType: 'all', search: '' })}
              className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>
      
      {/* Loading State */}
      {isLoading && (
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">Loading winners...</p>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="p-8 text-center">
          <div className="text-red-600 dark:text-red-400 mb-2">Failed to load winners</div>
          <button
            onClick={() => refetch()}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Try again
          </button>
        </div>
      )}
      
      {/* Empty State */}
      {!isLoading && !error && filteredWinners.length === 0 && (
        <div className="p-8 text-center">
          {winners.length === 0 ? (
            <div>
              <div className="text-6xl mb-4">🏆</div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Winners Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {award 
                  ? 'No winners have been assigned to this award yet.'
                  : 'No award winners found for your league.'
                }
              </p>
              {award && (
                <button
                  onClick={() => setShowAssignForm(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Assign First Winner
                </button>
              )}
            </div>
          ) : (
            <div>
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Winners Found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Try adjusting your filters or search terms.
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Winners List */}
      {!isLoading && !error && filteredWinners.length > 0 && (
        <div className="p-6">
          {Object.entries(winnersByWeek)
            .sort(([a], [b]) => b.localeCompare(a))
            .map(([weekKey, weekWinners]) => (
              <div key={weekKey} className="mb-8 last:mb-0">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {weekKey}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {weekWinners.map((winner) => (
                    <WinnerCard
                      key={winner.id}
                      winner={winner}
                      award={award}
                      onEdit={() => setEditingWinner(winner)}
                      onDelete={() => setConfirmDelete(winner.id)}
                      isDeleting={removeWinner.isPending}
                    />
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Remove Award Winner
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to remove this award winner? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 
                         bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                         rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                disabled={removeWinner.isPending}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 
                         border border-transparent rounded-md hover:bg-red-700
                         disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={removeWinner.isPending}
              >
                {removeWinner.isPending ? 'Removing...' : 'Remove'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Individual Winner Card Component
interface WinnerCardProps {
  winner: AwardWinner
  award?: Award
  onEdit: () => void
  onDelete: () => void
  isDeleting: boolean
}

function WinnerCard({ winner, award, onEdit, onDelete, isDeleting }: WinnerCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }
  
  return (
    <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            winner.winner_type === 'team' 
              ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
              : 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
          }`}>
            {winner.winner_type === 'team' ? 'Team' : 'Player'}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {winner.platform}
          </span>
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            onClick={onEdit}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            title="Edit winner"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
            title="Remove winner"
            disabled={isDeleting}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Winner Name */}
      <div className="font-medium text-gray-900 dark:text-white mb-2">
        {winner.winner_name}
      </div>
      
      {/* Reason */}
      {winner.reason && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {winner.reason}
        </p>
      )}
      
      {/* Highlight Message */}
      {winner.highlight_message && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-2 mb-3">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            💬 {winner.highlight_message}
          </p>
        </div>
      )}
      
      {/* Stats */}
      {winner.stats && Object.keys(winner.stats).length > 0 && (
        <div className="mb-3">
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Stats:</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(winner.stats).map(([key, value]) => (
              <span key={key} className="text-xs bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded">
                {key}: {typeof value === 'number' ? value.toFixed(1) : value}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Footer */}
      <div className="text-xs text-gray-500 dark:text-gray-400 flex justify-between items-center">
        <span>Awarded {formatDate(winner.awarded_at)}</span>
        {winner.awarded_by && (
          <span>by {winner.awarded_by}</span>
        )}
      </div>
    </div>
  )
}
