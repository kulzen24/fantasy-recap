/**
 * Yahoo Recap Generator Component
 * Queries Yahoo API to generate AI-powered fantasy recaps
 */

import React, { useState } from 'react'
import { useYahooLeague, useYahooTeams, useYahooMatchups, useYahooPlayers } from '../../hooks/useYahooData'
import { useAuth } from '../../contexts/AuthContext'
import { API_CONFIG } from '../../config'

interface YahooRecapGeneratorProps {
  leagueId: string
  className?: string
}

interface RecapSettings {
  week: number
  season: number
  tone: 'professional' | 'casual' | 'humorous' | 'dramatic'
  length: 'short' | 'medium' | 'long'
  includeAwards: boolean
  includePredictions: boolean
  useTemplate: boolean
}

interface GeneratedRecap {
  id: string
  content: string
  week: number
  season: number
  league_id: string
  quality_score: number
  processing_time: number
  created_at: string
}

export function YahooRecapGenerator({ leagueId, className = '' }: YahooRecapGeneratorProps) {
  const { user, session } = useAuth()
  const { league, isLoading: leagueLoading } = useYahooLeague(leagueId)
  const [settings, setSettings] = useState<RecapSettings>({
    week: league?.current_week || 1,
    season: league?.season || new Date().getFullYear(),
    tone: 'casual',
    length: 'medium',
    includeAwards: true,
    includePredictions: true,
    useTemplate: true
  })
  
  const { teams, isLoading: teamsLoading } = useYahooTeams(leagueId)
  const { matchups, isLoading: matchupsLoading } = useYahooMatchups(leagueId, settings.week, settings.season)
  const { players, isLoading: playersLoading } = useYahooPlayers(leagueId, settings.week)
  
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedRecap, setGeneratedRecap] = useState<GeneratedRecap | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)

  // Update week when league data loads
  React.useEffect(() => {
    if (league && !settings.week) {
      setSettings(prev => ({
        ...prev,
        week: league.current_week,
        season: league.season
      }))
    }
  }, [league])

  // Generate preview of what data will be included
  React.useEffect(() => {
    if (teams.length > 0 && matchups.length > 0) {
      const preview = {
        league: league?.name || 'Unknown League',
        week: settings.week,
        season: settings.season,
        teams: teams.length,
        matchups: matchups.length,
        players: players.length,
        topTeam: teams.reduce((max, team) => team.points_for > max.points_for ? team : max, teams[0]),
        closestMatchup: matchups.reduce((closest, matchup) => {
          const margin = Math.abs(matchup.home_score - matchup.away_score)
          const closestMargin = Math.abs(closest.home_score - closest.away_score)
          return margin < closestMargin ? matchup : closest
        }, matchups[0])
      }
      setPreviewData(preview)
    }
  }, [teams, matchups, players, league, settings.week, settings.season])

  const handleGenerateRecap = async () => {
    if (!session?.access_token) {
      setError('Please sign in to generate recaps')
      return
    }

    try {
      setIsGenerating(true)
      setError(null)

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/recaps/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          league_id: leagueId,
          week: settings.week,
          season: settings.season,
          tone: settings.tone,
          length: settings.length,
          use_template: settings.useTemplate,
          include_awards: settings.includeAwards,
          include_predictions: settings.includePredictions
        })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        setGeneratedRecap({
          id: data.recap_id,
          content: data.content || 'Recap generated successfully!',
          week: settings.week,
          season: settings.season,
          league_id: leagueId,
          quality_score: data.quality_score || 0,
          processing_time: data.processing_time || 0,
          created_at: new Date().toISOString()
        })
      } else {
        setError(data.detail || data.message || 'Failed to generate recap')
      }
    } catch (err) {
      setError('Error generating recap. Please try again.')
      console.error('Recap generation error:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const isLoading = leagueLoading || teamsLoading || matchupsLoading || playersLoading
  const hasData = teams.length > 0 && matchups.length > 0

  if (!league) {
    return (
      <div className={`p-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg ${className}`}>
        <h4 className="font-medium text-yellow-900 dark:text-yellow-100 mb-2">
          League Not Found
        </h4>
        <p className="text-sm text-yellow-700 dark:text-yellow-300">
          Unable to load league data. Make sure your Yahoo league is connected in Settings.
        </p>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* League Info Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          📝 Generate Recap for {league.name}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Create an AI-powered recap using live data from your Yahoo Fantasy league.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Settings */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h4 className="font-medium text-gray-900 dark:text-white mb-4">
          Recap Settings
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Week and Season */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Week
            </label>
            <input
              type="number"
              min="1"
              max="17"
              value={settings.week}
              onChange={(e) => setSettings(prev => ({ ...prev, week: parseInt(e.target.value) || 1 }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Season
            </label>
            <input
              type="number"
              min="2020"
              max="2030"
              value={settings.season}
              onChange={(e) => setSettings(prev => ({ ...prev, season: parseInt(e.target.value) || 2024 }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Tone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tone
            </label>
            <select
              value={settings.tone}
              onChange={(e) => setSettings(prev => ({ ...prev, tone: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="humorous">Humorous</option>
              <option value="dramatic">Dramatic</option>
            </select>
          </div>

          {/* Length */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Length
            </label>
            <select
              value={settings.length}
              onChange={(e) => setSettings(prev => ({ ...prev, length: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="short">Short (~200 words)</option>
              <option value="medium">Medium (~500 words)</option>
              <option value="long">Long (~1000 words)</option>
            </select>
          </div>
        </div>

        {/* Options */}
        <div className="mt-4 space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.includeAwards}
              onChange={(e) => setSettings(prev => ({ ...prev, includeAwards: e.target.checked }))}
              className="rounded border-gray-300 dark:border-gray-600"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Include weekly awards
            </span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.includePredictions}
              onChange={(e) => setSettings(prev => ({ ...prev, includePredictions: e.target.checked }))}
              className="rounded border-gray-300 dark:border-gray-600"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Include predictions for next week
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.useTemplate}
              onChange={(e) => setSettings(prev => ({ ...prev, useTemplate: e.target.checked }))}
              className="rounded border-gray-300 dark:border-gray-600"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Use custom template (if available)
            </span>
          </label>
        </div>
      </div>

      {/* Data Preview */}
      {previewData && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
            📊 Data Preview (Week {settings.week}, {settings.season})
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-blue-700 dark:text-blue-300 font-medium">Teams:</span>
              <span className="text-blue-800 dark:text-blue-200 ml-1">{previewData.teams}</span>
            </div>
            <div>
              <span className="text-blue-700 dark:text-blue-300 font-medium">Matchups:</span>
              <span className="text-blue-800 dark:text-blue-200 ml-1">{previewData.matchups}</span>
            </div>
            <div>
              <span className="text-blue-700 dark:text-blue-300 font-medium">Players:</span>
              <span className="text-blue-800 dark:text-blue-200 ml-1">{previewData.players}</span>
            </div>
            <div>
              <span className="text-blue-700 dark:text-blue-300 font-medium">Top Team:</span>
              <span className="text-blue-800 dark:text-blue-200 ml-1">{previewData.topTeam?.name}</span>
            </div>
          </div>
          {previewData.closestMatchup && (
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
              Closest game: {previewData.closestMatchup.home_team_name} vs {previewData.closestMatchup.away_team_name}
            </p>
          )}
        </div>
      )}

      {/* Generate Button */}
      <div className="flex justify-center">
        <button
          onClick={handleGenerateRecap}
          disabled={isGenerating || !hasData || isLoading}
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium min-w-[200px]"
        >
          {isGenerating ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Generating...
            </div>
          ) : (
            '✨ Generate Recap'
          )}
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading league data from Yahoo...</p>
        </div>
      )}

      {/* Generated Recap */}
      {generatedRecap && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900 dark:text-white">
              🏆 Generated Recap
            </h4>
            <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
              <span>Quality: {((generatedRecap.quality_score || 0) * 100).toFixed(0)}%</span>
              <span>Generated in {generatedRecap.processing_time}ms</span>
            </div>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="prose prose-sm dark:prose-invert max-w-none">
              {generatedRecap.content.split('\n').map((paragraph, index) => (
                <p key={index} className="mb-3 last:mb-0">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>

          <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Week {generatedRecap.week}, {generatedRecap.season} • Generated {new Date(generatedRecap.created_at).toLocaleString()}
            </p>
            
            <div className="flex gap-2">
              <button
                onClick={() => navigator.clipboard.writeText(generatedRecap.content)}
                className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors"
              >
                Copy
              </button>
              <button
                onClick={() => setGeneratedRecap(null)}
                className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* No Data Message */}
      {!isLoading && !hasData && (
        <div className="text-center py-8">
          <div className="text-4xl mb-4">📝</div>
          <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No League Data Available
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            Unable to find matchup data for Week {settings.week}, {settings.season}. 
            Try adjusting the week or ensure your Yahoo league is properly connected.
          </p>
        </div>
      )}
    </div>
  )
}
