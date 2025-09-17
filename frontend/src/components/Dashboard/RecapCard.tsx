import React from 'react'
import { Recap } from '../../types/api'

interface RecapCardProps {
  recap: Recap
  onView: (recap: Recap) => void
  onEdit?: (recap: Recap) => void
  onDelete: (recapId: string) => void
  onRegenerate: (recapId: string) => void
  isDeleting?: boolean
  isRegenerating?: boolean
}

const RecapCard: React.FC<RecapCardProps> = ({ 
  recap, 
  onView, 
  onEdit,
  onDelete, 
  onRegenerate,
  isDeleting = false,
  isRegenerating = false
}) => {
  const toneColors = {
    humorous: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    professional: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    casual: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    dramatic: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    analytical: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
  }

  const statusColors = {
    pending: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
    generating: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  }

  const getQualityColor = (score?: number) => {
    if (!score) return 'text-gray-500 dark:text-gray-400'
    if (score >= 8) return 'text-green-600 dark:text-green-400'
    if (score >= 6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const truncateContent = (content: string, maxLength: number = 150) => {
    if (content.length <= maxLength) return content
    return content.substring(0, maxLength).trim() + '...'
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 dark:text-white text-lg mb-2">
            {recap.title}
          </h3>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${toneColors[recap.tone as keyof typeof toneColors] || toneColors.casual}`}>
              {recap.tone}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
              {recap.length}
            </span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[recap.status]}`}>
              {recap.status}
            </span>
            {recap.quality_score && (
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getQualityColor(recap.quality_score)}`}>
                ⭐ {recap.quality_score.toFixed(1)}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Meta info */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <p className="text-gray-500 dark:text-gray-400">League</p>
          <p className="font-medium text-gray-900 dark:text-white">{recap.league_name || 'Unknown League'}</p>
        </div>
        <div>
          <p className="text-gray-500 dark:text-gray-400">Week</p>
          <p className="font-medium text-gray-900 dark:text-white">Week {recap.week}, {recap.season}</p>
        </div>
      </div>

      {/* Content preview */}
      <div className="mb-4">
        <p className="text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
          {truncateContent(recap.content)}
        </p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-600">
        <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {formatDate(recap.created_at)}
        </div>
        
        <div className="flex items-center gap-2">
          {recap.status === 'completed' && (
            <>
              <button
                onClick={() => onRegenerate(recap.id)}
                disabled={isRegenerating}
                className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isRegenerating ? (
                  <>
                    <div className="animate-spin -ml-1 mr-1 h-3 w-3 border border-gray-300 rounded-full border-t-transparent"></div>
                    Regenerating...
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Regenerate
                  </>
                )}
              </button>
              
              {onEdit && (
                <button
                  onClick={() => onEdit(recap)}
                  className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900 border border-indigo-200 dark:border-indigo-700 rounded hover:bg-indigo-100 dark:hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Edit
                </button>
              )}

              <button
                onClick={() => onView(recap)}
                className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 border border-transparent rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-500 dark:hover:bg-indigo-600"
              >
                View Full
                <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </>
          )}

          {recap.status === 'generating' && (
            <div className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded">
              <div className="animate-spin -ml-1 mr-1 h-3 w-3 border border-blue-300 rounded-full border-t-transparent"></div>
              Generating...
            </div>
          )}

          {recap.status === 'failed' && (
            <button
              onClick={() => onRegenerate(recap.id)}
              disabled={isRegenerating}
              className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded hover:bg-red-100 dark:hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Retry
            </button>
          )}
          
          <button
            onClick={() => onDelete(recap.id)}
            disabled={isDeleting}
            className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-red-700 dark:text-red-300 bg-white dark:bg-gray-700 border border-red-300 dark:border-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
          >
            {isDeleting ? (
              <>
                <div className="animate-spin -ml-1 mr-1 h-3 w-3 border border-red-300 rounded-full border-t-transparent"></div>
                Deleting...
              </>
            ) : (
              <>
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default RecapCard