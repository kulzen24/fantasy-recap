import React from 'react'
import { League } from '../../types/api'

interface LeagueCardProps {
  league: League
  onSync: (leagueId: string) => void
  onViewInsights: (leagueId: string) => void
  isLoading?: boolean
}

const LeagueCard: React.FC<LeagueCardProps> = ({ 
  league, 
  onSync, 
  onViewInsights, 
  isLoading = false 
}) => {
  const platformColors = {
    yahoo: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    espn: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    sleeper: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
  }

  const formatLastSync = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-white text-lg mb-2">
            {league.league_name}
          </h3>
          <div className="flex items-center gap-2 mb-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${platformColors[league.platform]}`}>
              {league.platform.toUpperCase()}
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              league.is_active 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
            }`}>
              {league.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <button
            onClick={() => onSync(league.id)}
            disabled={isLoading}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 shadow-sm text-xs font-medium rounded text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <div className="animate-spin -ml-1 mr-2 h-3 w-3 border border-gray-300 rounded-full border-t-transparent"></div>
                Syncing...
              </>
            ) : (
              <>
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync
              </>
            )}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Season</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{league.season}</p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Teams</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{league.league_data.total_teams}</p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Current Week</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">Week {league.league_data.current_week}</p>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Scoring</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{league.league_data.scoring_type.toUpperCase()}</p>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-600">
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Last sync: {formatLastSync(league.league_data.last_sync)}
        </div>
        <button
          onClick={() => onViewInsights(league.id)}
          className="inline-flex items-center text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300"
        >
          View Insights
          <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default LeagueCard