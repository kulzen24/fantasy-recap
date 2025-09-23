import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import LeagueOverview from './LeagueOverview'
import RecapsOverview from './RecapsOverview'
import QuickActions from './QuickActions'
import { AwardList } from '../Awards'
import { NLQChat } from '../NLQ'
import { YahooLeagueConnection } from '../YahooLeagueConnection'
import { LLMKeyManagement } from '../LLMKeyManagement'

type DashboardTab = 'overview' | 'leagues' | 'recaps' | 'awards' | 'nlq' | 'settings'

const DashboardOverview: React.FC = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview')
  const [selectedLeagueId, setSelectedLeagueId] = useState<string>('')

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '🏠' },
    { id: 'leagues' as const, label: 'Leagues', icon: '🏈' },
    { id: 'recaps' as const, label: 'Recaps', icon: '📝' },
    { id: 'awards' as const, label: 'Awards', icon: '🏆' },
    { id: 'nlq' as const, label: 'Ask AI', icon: '🤖' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
  ]

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Please sign in to view your dashboard
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Connect your fantasy leagues and generate personalized recaps.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Welcome back, {user.user_metadata?.display_name || user.email}! 👋
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage your fantasy leagues and generate AI-powered recaps.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
              {/* Main content area */}
              <div className="lg:col-span-3 space-y-8">
                {/* Recent activity summary */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Recent Activity
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center text-sm">
                      <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                      <span className="text-gray-600 dark:text-gray-300">
                        Connected to fantasy platforms
                      </span>
                    </div>
                    <div className="flex items-center text-sm">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
                      <span className="text-gray-600 dark:text-gray-300">
                        AI recap generation ready
                      </span>
                    </div>
                    <div className="flex items-center text-sm">
                      <div className="w-2 h-2 bg-purple-400 rounded-full mr-3"></div>
                      <span className="text-gray-600 dark:text-gray-300">
                        Dashboard configured and ready
                      </span>
                    </div>
                  </div>
                </div>

                {/* Quick preview of leagues */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Your Leagues
                    </h3>
                    <button
                      onClick={() => setActiveTab('leagues')}
                      className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
                    >
                      View all →
                    </button>
                  </div>
                  <LeagueOverview />
                </div>

                {/* Quick preview of recaps */}
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Recent Recaps
                    </h3>
                    <button
                      onClick={() => setActiveTab('recaps')}
                      className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
                    >
                      View all →
                    </button>
                  </div>
                  <RecapsOverview />
                </div>
              </div>

              {/* Sidebar */}
              <div className="lg:col-span-1">
                <div className="sticky top-8 space-y-6">
                  <QuickActions />
                  
                  {/* Tips & Help */}
                  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Tips & Help
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mr-3 mt-0.5">
                          <span className="text-xs font-medium text-indigo-600 dark:text-indigo-300">1</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">Connect Leagues</p>
                          <p className="text-gray-600 dark:text-gray-400">
                            Link your Yahoo, ESPN, or Sleeper fantasy leagues
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mr-3 mt-0.5">
                          <span className="text-xs font-medium text-indigo-600 dark:text-indigo-300">2</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">Setup AI Provider</p>
                          <p className="text-gray-600 dark:text-gray-400">
                            Add your OpenAI, Anthropic, or Google AI API key
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start">
                        <div className="flex-shrink-0 w-5 h-5 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mr-3 mt-0.5">
                          <span className="text-xs font-medium text-indigo-600 dark:text-indigo-300">3</span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">Generate Recaps</p>
                          <p className="text-gray-600 dark:text-gray-400">
                            Create personalized AI-powered fantasy recaps
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'leagues' && <LeagueOverview />}
          {activeTab === 'recaps' && <RecapsOverview />}
          {activeTab === 'awards' && <AwardList />}
          {activeTab === 'nlq' && (
            <div className="space-y-6">
              {/* League Selection for NLQ */}
              {!selectedLeagueId && (
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Select a League to Ask Questions
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    Choose which league you'd like to ask questions about. You can ask about player performance, team stats, league standings, and more!
                  </p>
                  <div className="space-y-2">
                    {/* Mock league selection - in real app this would come from LeagueOverview */}
                    <button
                      onClick={() => setSelectedLeagueId('mock-league-1')}
                      className="w-full text-left p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            My Fantasy League 2024
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            12 teams • Week 12 • Yahoo Fantasy
                          </p>
                        </div>
                        <div className="text-indigo-600 dark:text-indigo-400">
                          Select →
                        </div>
                      </div>
                    </button>
                    <button
                      onClick={() => setSelectedLeagueId('mock-league-2')}
                      className="w-full text-left p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            Work League Championship
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            10 teams • Week 12 • ESPN Fantasy
                          </p>
                        </div>
                        <div className="text-indigo-600 dark:text-indigo-400">
                          Select →
                        </div>
                      </div>
                    </button>
                  </div>
                </div>
              )}
              
              {/* NLQ Chat Interface */}
              {selectedLeagueId && (
                <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="p-4 border-b border-gray-200 dark:border-gray-600">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        Fantasy Assistant
                      </h3>
                      <button
                        onClick={() => setSelectedLeagueId('')}
                        className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                      >
                        Change League
                      </button>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Ask me anything about your fantasy league!
                    </p>
                  </div>
                  <div className="h-[600px]">
                    <NLQChat leagueId={selectedLeagueId} className="h-full border-0" />
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
                  ⚙️ Account Settings
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Manage your fantasy league connections and AI provider settings.
                </p>
                
                <div className="grid gap-8 lg:grid-cols-2">
                  {/* League Management */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                      🏈 League Connections
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                      <YahooLeagueConnection />
                    </div>
                  </div>

                  {/* LLM Key Management */}
                  <div>
                    <h4 className="text-md font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                      🔑 AI Provider Keys
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                      <LLMKeyManagement />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DashboardOverview