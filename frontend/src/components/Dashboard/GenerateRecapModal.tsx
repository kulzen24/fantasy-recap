import React, { useState, useEffect } from 'react'
import { useLeagues, useGenerateRecap } from '../../hooks/useDashboardData'
import { RecapGenerationRequest } from '../../types/api'

interface GenerateRecapModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const GenerateRecapModal: React.FC<GenerateRecapModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { data: leaguesResponse } = useLeagues()
  const { mutate: generateRecap, loading, error } = useGenerateRecap()
  
  const [formData, setFormData] = useState<RecapGenerationRequest>({
    league_id: '',
    week: getCurrentWeek(),
    season: new Date().getFullYear(),
    tone: 'humorous',
    length: 'medium',
    include_awards: true,
    include_predictions: true,
    focus_on_user_team: false
  })

  const leagues = leaguesResponse?.data || []

  // Helper function to estimate current NFL week
  function getCurrentWeek(): number {
    const now = new Date()
    const nflSeasonStart = new Date(now.getFullYear(), 8, 5) // Roughly September 5th
    
    if (now < nflSeasonStart) {
      return 1
    }
    
    const diffTime = now.getTime() - nflSeasonStart.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    const week = Math.ceil(diffDays / 7)
    
    return Math.min(Math.max(week, 1), 18)
  }

  // Close modal on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  // Set default league if only one available
  useEffect(() => {
    if (leagues.length === 1 && !formData.league_id) {
      setFormData(prev => ({ ...prev, league_id: leagues[0].id }))
    }
  }, [leagues, formData.league_id])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const result = await generateRecap('/recaps/generate', formData)
      if (result) {
        onSuccess()
        onClose()
        // Reset form for next use
        setFormData(prev => ({ 
          ...prev, 
          league_id: leagues.length === 1 ? leagues[0].id : '',
          week: getCurrentWeek()
        }))
      }
    } catch (error) {
      console.error('Failed to generate recap:', error)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  if (!isOpen) return null

  const selectedLeague = leagues.find(l => l.id === formData.league_id)

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75"
          onClick={onClose}
        ></div>

        {/* Modal */}
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-indigo-100 dark:bg-indigo-900 sm:mx-0 sm:h-10 sm:w-10">
              <svg className="h-6 w-6 text-indigo-600 dark:text-indigo-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
              <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                Generate Fantasy Recap
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Create a personalized recap for your fantasy league week.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-6">
            <div className="space-y-4">
              {/* League Selection */}
              <div>
                <label htmlFor="league_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  League
                </label>
                <select
                  id="league_id"
                  name="league_id"
                  value={formData.league_id}
                  onChange={handleInputChange}
                  required
                  className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white focus:border-indigo-500 focus:ring-indigo-500"
                >
                  <option value="">Select a league...</option>
                  {leagues.map((league) => (
                    <option key={league.id} value={league.id}>
                      {league.league_name} ({league.platform.toUpperCase()})
                    </option>
                  ))}
                </select>
              </div>

              {/* Week and Season */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="week" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Week
                  </label>
                  <input
                    type="number"
                    id="week"
                    name="week"
                    min="1"
                    max="18"
                    value={formData.week}
                    onChange={handleInputChange}
                    required
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label htmlFor="season" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Season
                  </label>
                  <input
                    type="number"
                    id="season"
                    name="season"
                    min="2020"
                    max="2030"
                    value={formData.season}
                    onChange={handleInputChange}
                    required
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Current week indicator */}
              {selectedLeague && (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  League is currently on Week {selectedLeague.league_data.current_week}
                </div>
              )}

              {/* Tone and Length */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="tone" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Tone
                  </label>
                  <select
                    id="tone"
                    name="tone"
                    value={formData.tone}
                    onChange={handleInputChange}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white focus:border-indigo-500 focus:ring-indigo-500"
                  >
                    <option value="humorous">Humorous</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="dramatic">Dramatic</option>
                    <option value="analytical">Analytical</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="length" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Length
                  </label>
                  <select
                    id="length"
                    name="length"
                    value={formData.length}
                    onChange={handleInputChange}
                    className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white focus:border-indigo-500 focus:ring-indigo-500"
                  >
                    <option value="short">Short (~200 words)</option>
                    <option value="medium">Medium (~500 words)</option>
                    <option value="long">Long (~1000 words)</option>
                  </select>
                </div>
              </div>

              {/* Options */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Options</h4>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="include_awards"
                    checked={formData.include_awards}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Include weekly awards</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="include_predictions"
                    checked={formData.include_predictions}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Include next week predictions</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="focus_on_user_team"
                    checked={formData.focus_on_user_team}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Focus on my team</span>
                </label>
              </div>

              {/* Error display */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 rounded-md p-3">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-3 space-y-3 space-y-reverse sm:space-y-0">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="inline-flex w-full justify-center rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-2 text-base font-medium text-gray-700 dark:text-gray-200 shadow-sm hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !formData.league_id}
                className="inline-flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-base font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                    Generating...
                  </>
                ) : (
                  'Generate Recap'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default GenerateRecapModal