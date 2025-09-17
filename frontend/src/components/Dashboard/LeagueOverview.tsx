import React, { useState } from 'react'
import { useLeagues, useLeagueStats, useSyncLeague } from '../../hooks/useDashboardData'
import { PaginatedResponse, League, LeagueStats } from '../../types/api'
import LeagueCard from './LeagueCard'

const LeagueOverview: React.FC = () => {
  const { data: leaguesResponse, loading: leaguesLoading, error: leaguesError, refetch: refetchLeagues } = useLeagues()
  const { data: stats, loading: statsLoading } = useLeagueStats()
  const { mutate: syncLeague, loading: syncingLeague } = useSyncLeague()
  
  const [syncingLeagueId, setSyncingLeagueId] = useState<string | null>(null)

  // Handle the response structure from the API
  const leagues = leaguesResponse?.data || []
  const totalLeagues = leaguesResponse?.count || 0

  const handleSyncLeague = async (leagueId: string) => {
    setSyncingLeagueId(leagueId)
    try {
      await syncLeague(`/leagues/${leagueId}/sync`)
      await refetchLeagues()
    } catch (error) {
      console.error('Failed to sync league:', error)
    } finally {
      setSyncingLeagueId(null)
    }
  }

  const handleViewInsights = (leagueId: string) => {
    // TODO: Implement navigation to insights view
    console.log('View insights for league:', leagueId)
  }

  const handleConnectLeague = () => {
    // TODO: Implement connect league modal
    console.log('Connect league clicked')
  }

  if (leaguesLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-6"></div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (leaguesError) {
    return (
      <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
              Error loading leagues
            </h3>
            <p className="mt-1 text-sm text-red-700 dark:text-red-300">{leaguesError}</p>
            <button
              onClick={refetchLeagues}
              className="mt-2 text-sm font-medium text-red-800 dark:text-red-200 hover:text-red-700 dark:hover:text-red-100"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Fantasy Leagues</h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {totalLeagues} {totalLeagues === 1 ? 'league' : 'leagues'} connected
            {stats && !statsLoading && (
              <span className="ml-2">
                • {stats.active_leagues} active
              </span>
            )}
          </p>
        </div>
        <button
          onClick={handleConnectLeague}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-500 dark:hover:bg-indigo-600"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Connect League
        </button>
      </div>

      {/* Platform stats */}
      {stats && !statsLoading && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Leagues</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.total_leagues}</p>
              </div>
              <div className="p-3 bg-indigo-100 dark:bg-indigo-900 rounded-full">
                <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Yahoo</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.platforms.yahoo}</p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-full">
                <span className="text-purple-600 dark:text-purple-300 font-semibold text-sm">Y!</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">ESPN</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.platforms.espn}</p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900 rounded-full">
                <span className="text-red-600 dark:text-red-300 font-semibold text-sm">ESPN</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Sleeper</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">{stats.platforms.sleeper}</p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-full">
                <span className="text-blue-600 dark:text-blue-300 font-semibold text-sm">SLP</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {totalLeagues === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No leagues connected</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Get started by connecting your first fantasy league.
          </p>
          <div className="mt-6">
            <button
              onClick={handleConnectLeague}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-500 dark:hover:bg-indigo-600"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Connect Your First League
            </button>
          </div>
        </div>
      )}

      {/* Leagues grid */}
      {totalLeagues > 0 && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {leagues.map((league) => (
            <LeagueCard
              key={league.id}
              league={league}
              onSync={handleSyncLeague}
              onViewInsights={handleViewInsights}
              isLoading={syncingLeagueId === league.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default LeagueOverview