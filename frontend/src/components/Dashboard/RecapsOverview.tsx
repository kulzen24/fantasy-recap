import React, { useState } from 'react'
import { useRecaps, useRecapStats, useDeleteRecap, useRegenerateRecap } from '../../hooks/useDashboardData'
import { Recap } from '../../types/api'
import RecapCard from './RecapCard'

const RecapsOverview: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedRecap, setSelectedRecap] = useState<Recap | null>(null)
  const [deletingRecapId, setDeletingRecapId] = useState<string | null>(null)
  const [regeneratingRecapId, setRegeneratingRecapId] = useState<string | null>(null)
  
  const pageSize = 6
  const { 
    data: recapsResponse, 
    loading: recapsLoading, 
    error: recapsError, 
    refetch: refetchRecaps 
  } = useRecaps({ 
    page: currentPage, 
    page_size: pageSize
  })
  
  const { data: stats, loading: statsLoading } = useRecapStats()
  const { mutate: deleteRecap } = useDeleteRecap()
  const { mutate: regenerateRecap } = useRegenerateRecap()

  const recaps = recapsResponse?.data || []
  const totalRecaps = recapsResponse?.count || 0
  const hasMore = (currentPage * pageSize) < totalRecaps

  const handleViewRecap = (recap: Recap) => {
    setSelectedRecap(recap)
    // TODO: Implement modal or navigation to full recap view
    console.log('View recap:', recap.id)
  }

  const handleDeleteRecap = async (recapId: string) => {
    if (!confirm('Are you sure you want to delete this recap? This action cannot be undone.')) {
      return
    }

    setDeletingRecapId(recapId)
    try {
      await deleteRecap(`/recaps/${recapId}`)
      await refetchRecaps()
    } catch (error) {
      console.error('Failed to delete recap:', error)
    } finally {
      setDeletingRecapId(null)
    }
  }

  const handleRegenerateRecap = async (recapId: string) => {
    setRegeneratingRecapId(recapId)
    try {
      await regenerateRecap(`/recaps/${recapId}/regenerate`)
      await refetchRecaps()
    } catch (error) {
      console.error('Failed to regenerate recap:', error)
    } finally {
      setRegeneratingRecapId(null)
    }
  }

  const handleGenerateRecap = () => {
    // TODO: Implement generate recap modal
    console.log('Generate recap clicked')
  }

  if (recapsLoading && currentPage === 1) {
    return (
      <div className="space-y-6" aria-live="polite" aria-label="Loading recaps">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-6"></div>
          <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/6"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (recapsError) {
    return (
      <div role="alert" className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
              Error loading recaps
            </h3>
            <p className="mt-1 text-sm text-red-700 dark:text-red-300">{recapsError}</p>
            <button
              onClick={refetchRecaps}
              aria-label="Retry loading recaps"
              className="mt-2 text-sm font-medium text-red-800 dark:text-red-200 hover:text-red-700 dark:hover:text-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded px-2 py-1 min-h-[44px]"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <main className="space-y-6">
      {/* Header with stats */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">History</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {totalRecaps} {totalRecaps === 1 ? 'recap' : 'recaps'} generated
            {stats && !statsLoading && (
              <span className="ml-2">
                • Avg quality: <span aria-label={`Quality score ${stats.avg_quality_score.toFixed(1)} out of 5 stars`}>{stats.avg_quality_score.toFixed(1)}⭐</span>
              </span>
            )}
          </p>
        </div>
        <button
          onClick={handleGenerateRecap}
          aria-label="Generate a new fantasy football recap"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-500 dark:hover:bg-indigo-600 min-h-[44px]"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Generate Recap
        </button>
      </div>

      {/* Stats cards */}
      {stats && !statsLoading && (
        <section aria-labelledby="stats-heading">
          <h2 id="stats-heading" className="sr-only">Statistics Overview</h2>
          <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center">
                <div className="flex-1">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Recaps</dt>
                  <dd className="text-lg sm:text-2xl font-semibold text-gray-900 dark:text-white">{stats.total_recaps}</dd>
                </div>
                <div className="p-3 bg-indigo-100 dark:bg-indigo-900 rounded-full" aria-hidden="true">
                  <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
            </div>
            
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center">
                <div className="flex-1">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg Quality</dt>
                  <dd className="text-lg sm:text-2xl font-semibold text-gray-900 dark:text-white">
                    <span aria-label={`Average quality score ${stats.avg_quality_score.toFixed(1)} out of 5 stars`}>
                      {stats.avg_quality_score.toFixed(1)}⭐
                    </span>
                  </dd>
                </div>
                <div className="p-3 bg-yellow-100 dark:bg-yellow-900 rounded-full" aria-hidden="true">
                  <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center">
                <div className="flex-1">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Recent</dt>
                  <dd className="text-lg sm:text-2xl font-semibold text-gray-900 dark:text-white">{stats.recent_recaps}</dd>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900 rounded-full" aria-hidden="true">
                  <svg className="w-6 h-6 text-green-600 dark:text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center">
                <div className="flex-1">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Favorite Tone</dt>
                  <dd className="text-sm sm:text-lg font-semibold text-gray-900 dark:text-white capitalize">{stats.favorite_tone}</dd>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900 rounded-full" aria-hidden="true">
                  <svg className="w-6 h-6 text-purple-600 dark:text-purple-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m0 0V1a1 1 0 011-1h2a1 1 0 011 1v3M7 4H5a1 1 0 00-1 1v16a1 1 0 001 1h14a1 1 0 001-1V5a1 1 0 00-1-1h-2M7 4h10M9 9h6m-6 4h6m-3 4h3" />
                  </svg>
                </div>
              </div>
            </div>
          </dl>
        </section>
      )}

      {/* Empty state */}
      {totalRecaps === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No recaps generated yet</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Get started by generating your first fantasy football recap.
          </p>
          <div className="mt-6">
            <button
              onClick={handleGenerateRecap}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-500 dark:hover:bg-indigo-600"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Generate Your First Recap
            </button>
          </div>
        </div>
      )}

      {/* Recaps grid */}
      {totalRecaps > 0 && (
        <>
          <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {recaps.map((recap) => (
              <RecapCard
                key={recap.id}
                recap={recap}
                onView={handleViewRecap}
                onDelete={handleDeleteRecap}
                onRegenerate={handleRegenerateRecap}
                isDeleting={deletingRecapId === recap.id}
                isRegenerating={regeneratingRecapId === recap.id}
              />
            ))}
          </div>

          {/* Pagination */}
          {(currentPage > 1 || hasMore) && (
            <nav aria-label="Recaps pagination" className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1 || recapsLoading}
                aria-label="Go to previous page"
                aria-disabled={currentPage === 1 || recapsLoading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 min-h-[44px]"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Previous
              </button>
              
              <span className="text-sm text-gray-500 dark:text-gray-400" aria-live="polite">
                Page {currentPage} of {Math.ceil(totalRecaps / pageSize)} • {totalRecaps} total recaps
              </span>
              
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={!hasMore || recapsLoading}
                aria-label="Go to next page"
                aria-disabled={!hasMore || recapsLoading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 min-h-[44px]"
              >
                Next
                <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </nav>
          )}
        </>
      )}
    </main>
  )
}

export default RecapsOverview