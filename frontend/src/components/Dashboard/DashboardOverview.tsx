import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import LeagueOverview from './LeagueOverview'
import RecapsOverview from './RecapsOverview'
import QuickActions from './QuickActions'

type DashboardTab = 'overview' | 'leagues' | 'recaps'

const DashboardOverview: React.FC = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview')

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '🏠' },
    { id: 'leagues' as const, label: 'Leagues', icon: '🏈' },
    { id: 'recaps' as const, label: 'Recaps', icon: '📝' },
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
        </div>
      </div>
    </div>
  )
}

export default DashboardOverview