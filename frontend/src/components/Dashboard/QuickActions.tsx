import React, { useState } from 'react'
import { useLeagues, useRecaps, useProviderPreferences, useApiKeys } from '../../hooks/useDashboardData'
import GenerateRecapModal from './GenerateRecapModal'

const QuickActions: React.FC = () => {
  const [showGenerateModal, setShowGenerateModal] = useState(false)
  
  const { data: leaguesData, refetch: refetchLeagues } = useLeagues()
  const { data: recapsData, refetch: refetchRecaps } = useRecaps({ page_size: 1 })
  const { data: providerPrefs } = useProviderPreferences()
  const { data: apiKeys } = useApiKeys()

  const leagues = leaguesData?.data || []
  const hasLeagues = leagues.length > 0
  const hasRecaps = (recapsData?.count || 0) > 0
  const hasProviderSetup = providerPrefs?.primary_provider && (apiKeys?.length || 0) > 0
  const recentRecap = recapsData?.data?.[0]

  const handleConnectLeague = () => {
    // TODO: Implement league connection modal/flow
    console.log('Connect league clicked')
  }

  const handleSetupProvider = () => {
    // TODO: Implement provider setup modal/flow
    console.log('Setup LLM provider clicked')
  }

  const handleViewRecap = () => {
    if (recentRecap) {
      // TODO: Navigate to recap view
      console.log('View recent recap:', recentRecap.id)
    }
  }

  const handleGenerateSuccess = () => {
    refetchRecaps()
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
      
      <div className="space-y-3">
        {/* Generate Recap - Primary action */}
        {hasLeagues && hasProviderSetup && (
          <button
            onClick={() => setShowGenerateModal(true)}
            className="w-full inline-flex items-center justify-center px-4 py-3 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Generate New Recap
          </button>
        )}

        {/* Setup steps when prerequisites aren't met */}
        {!hasLeagues && (
          <button
            onClick={handleConnectLeague}
            className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Connect Your First League
          </button>
        )}

        {hasLeagues && !hasProviderSetup && (
          <button
            onClick={handleSetupProvider}
            className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Setup LLM Provider
          </button>
        )}

        {/* View recent recap */}
        {hasRecaps && recentRecap && (
          <button
            onClick={handleViewRecap}
            className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            View Recent Recap
            <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
              ({recentRecap.league_name}, Week {recentRecap.week})
            </span>
          </button>
        )}

        {/* Sync all leagues */}
        {hasLeagues && (
          <button
            onClick={() => {
              // TODO: Implement sync all leagues
              refetchLeagues()
            }}
            className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Sync All Leagues
          </button>
        )}
      </div>

      {/* Setup progress indicator */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Setup Progress</span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {[hasLeagues, hasProviderSetup].filter(Boolean).length}/2 complete
          </span>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
          <div 
            className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
            style={{ 
              width: `${([hasLeagues, hasProviderSetup].filter(Boolean).length / 2) * 100}%` 
            }}
          ></div>
        </div>
        
        <div className="mt-2 space-y-1">
          <div className="flex items-center text-sm">
            <div className={`w-2 h-2 rounded-full mr-2 ${hasLeagues ? 'bg-green-400' : 'bg-gray-300 dark:bg-gray-500'}`}></div>
            <span className={hasLeagues ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
              Connect fantasy leagues
            </span>
          </div>
          <div className="flex items-center text-sm">
            <div className={`w-2 h-2 rounded-full mr-2 ${hasProviderSetup ? 'bg-green-400' : 'bg-gray-300 dark:bg-gray-500'}`}></div>
            <span className={hasProviderSetup ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'}>
              Setup LLM provider
            </span>
          </div>
        </div>
      </div>

      {/* Generate Recap Modal */}
      <GenerateRecapModal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        onSuccess={handleGenerateSuccess}
      />
    </div>
  )
}

export default QuickActions