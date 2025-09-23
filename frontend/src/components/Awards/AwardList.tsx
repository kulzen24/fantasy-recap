/**
 * Award List and Management Component
 * Displays awards with filtering, editing, and management capabilities
 */

import React, { useState } from 'react'
import { Award, AwardStatus, AwardFrequency } from '../../types/award'
import { useAwards, useDeleteAward, useAwardStats } from '../../hooks/useAwards'
import { AwardForm } from './AwardForm'
import { AwardWinnersList } from './AwardWinnersList'

interface AwardListProps {
  leagueId?: string
  onEditAward?: (award: Award) => void
  onCreateAward?: () => void
  className?: string
}

interface FilterState {
  status: 'all' | AwardStatus
  frequency: 'all' | AwardFrequency
  search: string
}

export function AwardList({ leagueId, onEditAward, onCreateAward, className = '' }: AwardListProps) {
  const { data: awards = [], isLoading, error, refetch } = useAwards(leagueId)
  const { data: stats } = useAwardStats(leagueId)
  const deleteAward = useDeleteAward()
  
  const [filters, setFilters] = useState<FilterState>({
    status: 'all',
    frequency: 'all',
    search: ''
  })
  
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingAward, setEditingAward] = useState<Award | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [managingWinnersAward, setManagingWinnersAward] = useState<Award | null>(null)
  
  // Filter awards
  const filteredAwards = awards.filter(award => {
    const matchesStatus = filters.status === 'all' || award.status === filters.status
    const matchesFrequency = filters.frequency === 'all' || award.frequency === filters.frequency
    const matchesSearch = !filters.search || 
      award.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      award.description?.toLowerCase().includes(filters.search.toLowerCase())
    
    return matchesStatus && matchesFrequency && matchesSearch
  })
  
  // Handle delete
  const handleDelete = async (awardId: string) => {
    try {
      await deleteAward.mutateAsync(awardId)
      setConfirmDelete(null)
    } catch (error) {
      console.error('Failed to delete award:', error)
    }
  }
  
  // Handle edit
  const handleEdit = (award: Award) => {
    setEditingAward(award)
    onEditAward?.(award)
  }
  
  // Handle create success
  const handleCreateSuccess = (award: Award) => {
    setShowCreateForm(false)
    refetch()
  }
  
  // Handle edit success
  const handleEditSuccess = (award: Award) => {
    setEditingAward(null)
    refetch()
  }
  
  if (showCreateForm) {
    return (
      <AwardForm
        leagueId={leagueId}
        onSuccess={handleCreateSuccess}
        onCancel={() => setShowCreateForm(false)}
        className={className}
      />
    )
  }
  
  if (editingAward) {
    return (
      <AwardForm
        award={editingAward}
        onSuccess={handleEditSuccess}
        onCancel={() => setEditingAward(null)}
        className={className}
      />
    )
  }

  if (managingWinnersAward) {
    return (
      <AwardWinnersList
        award={managingWinnersAward}
        onCancel={() => setManagingWinnersAward(null)}
        className={className}
      />
    )
  }
  
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Custom Awards
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Manage your league's custom weekly awards
            </p>
          </div>
          
          <button
            onClick={() => {
              setShowCreateForm(true)
              onCreateAward?.()
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                     flex items-center space-x-2"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Create Award</span>
          </button>
        </div>
        
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.totalAwards}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Awards</div>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {stats.activeAwards}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Active</div>
            </div>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {stats.weeklyAwards}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Weekly</div>
            </div>
            
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {stats.autoAssignAwards}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Auto-Assign</div>
            </div>
          </div>
        )}
      </div>
      
      {/* Filters */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Search
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              placeholder="Search awards..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Frequency
            </label>
            <select
              value={filters.frequency}
              onChange={(e) => setFilters(prev => ({ ...prev, frequency: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                       focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Frequencies</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="season">Season</option>
              <option value="playoff">Playoff</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ status: 'all', frequency: 'all', search: '' })}
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
          <p className="text-gray-600 dark:text-gray-400 mt-2">Loading awards...</p>
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="p-8 text-center">
          <div className="text-red-600 dark:text-red-400 mb-2">Failed to load awards</div>
          <button
            onClick={() => refetch()}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Try again
          </button>
        </div>
      )}
      
      {/* Empty State */}
      {!isLoading && !error && filteredAwards.length === 0 && (
        <div className="p-8 text-center">
          {awards.length === 0 ? (
            <div>
              <div className="text-6xl mb-4">🏆</div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Custom Awards Yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Create your first custom award to get started!
              </p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Create Your First Award
              </button>
            </div>
          ) : (
            <div>
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                No Awards Found
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Try adjusting your filters or search terms.
              </p>
            </div>
          )}
        </div>
      )}
      
      {/* Awards Grid */}
      {!isLoading && !error && filteredAwards.length > 0 && (
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAwards.map((award) => (
              <AwardCard
                key={award.id}
                award={award}
                onEdit={() => handleEdit(award)}
                onDelete={() => setConfirmDelete(award.id)}
                onManageWinners={() => setManagingWinnersAward(award)}
                isDeleting={deleteAward.isPending}
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Delete Award
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Are you sure you want to delete this award? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 
                         bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                         rounded-md hover:bg-gray-50 dark:hover:bg-gray-600"
                disabled={deleteAward.isPending}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDelete)}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 
                         border border-transparent rounded-md hover:bg-red-700
                         disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={deleteAward.isPending}
              >
                {deleteAward.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Individual Award Card Component
interface AwardCardProps {
  award: Award
  onEdit: () => void
  onDelete: () => void
  onManageWinners: () => void
  isDeleting: boolean
}

function AwardCard({ award, onEdit, onDelete, onManageWinners, isDeleting }: AwardCardProps) {
  const getStatusColor = (status: AwardStatus) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
      case 'inactive': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
      case 'archived': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    }
  }
  
  const getFrequencyIcon = (frequency: AwardFrequency) => {
    switch (frequency) {
      case 'weekly': return '📅'
      case 'monthly': return '🗓️'
      case 'season': return '🏁'
      case 'playoff': return '🏆'
      default: return '⭐'
    }
  }
  
  return (
    <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{award.emoji}</span>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">{award.name}</h3>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(award.status)}`}>
                {award.status}
              </span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {getFrequencyIcon(award.frequency)} {award.frequency}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            onClick={onEdit}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            title="Edit award"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
            title="Delete award"
            disabled={isDeleting}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Description */}
      {award.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {award.description}
        </p>
      )}
      
      {/* Criteria Summary */}
      <div className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        <strong>Criteria:</strong> {award.criteria.type.replace('_', ' ')}
        {award.criteria.stat_category && ` • ${award.criteria.stat_category}`}
        {award.criteria.comparison && ` • ${award.criteria.comparison}`}
      </div>
      
      {/* Stats */}
      <div className="flex items-center justify-between text-sm mb-4">
        <div className="text-gray-500 dark:text-gray-400">
          Awarded {award.times_awarded} times
        </div>
        <div className="flex items-center space-x-2">
          {award.is_public && (
            <span className="text-blue-500" title="Public award">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
              </svg>
            </span>
          )}
          {award.auto_assign && (
            <span className="text-green-500" title="Auto-assign">
              <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </span>
          )}
        </div>
      </div>
      
      {/* Action Button */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-600">
        <button
          onClick={onManageWinners}
          className="w-full px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 
                   bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 
                   rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                   transition-colors flex items-center justify-center space-x-2"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
          <span>Manage Winners</span>
        </button>
      </div>
    </div>
  )
}
