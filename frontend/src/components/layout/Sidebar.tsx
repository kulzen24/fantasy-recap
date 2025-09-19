import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
  currentConversation: string | null
  onConversationSelect: (id: string | null) => void
  'aria-expanded'?: boolean
}

// Mock data for now - will be replaced with real data from API
const mockConversations = [
  { id: '1', title: 'Week 1 Recap - My League', date: '2024-01-15', preview: 'Generated recap for week 1...' },
  { id: '2', title: 'Trade Analysis', date: '2024-01-14', preview: 'Should I trade my RB1 for...' },
  { id: '3', title: 'Waiver Wire Priorities', date: '2024-01-13', preview: 'Best waiver pickups this week...' },
  { id: '4', title: 'Season Outlook', date: '2024-01-12', preview: 'How does my team look for playoffs...' },
]

export function Sidebar({ isOpen, onToggle, currentConversation, onConversationSelect, ...ariaProps }: SidebarProps) {
  const { user } = useAuth()
  const location = useLocation()
  const [searchTerm, setSearchTerm] = useState('')

  const filteredConversations = mockConversations.filter(conv =>
    conv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conv.preview.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (!isOpen) {
    return null
  }

  return (
    <>
      {/* Mobile Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
        onClick={onToggle}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <nav 
        role="navigation" 
        aria-label="Conversation history"
        className="fixed inset-y-0 left-0 z-50 w-64 sm:w-80 bg-chat-sidebar-light dark:bg-chat-sidebar-dark border-r border-chat-border-light dark:border-chat-border-dark flex flex-col lg:relative lg:z-0 animate-slide-in lg:animate-none"
        {...ariaProps}
      >
        {/* Sidebar Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 border-b border-chat-border-light dark:border-chat-border-dark">
          <h2 className="text-base sm:text-lg font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark">
            History
          </h2>
          <button
            onClick={() => onConversationSelect(null)}
            aria-label="Create new recap"
            className="px-3 py-2 text-sm bg-chat-accent hover:bg-chat-accent-hover text-white rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-chat-accent min-h-[44px]"
          >
            New Recap
          </button>
        </div>

        {/* Navigation */}
        <div className="px-4 py-2 border-b border-chat-border-light dark:border-chat-border-dark">
          <nav className="space-y-1">
            <Link
              to="/dashboard"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                location.pathname === '/dashboard'
                  ? 'bg-chat-accent text-white'
                  : 'text-chat-text-primary-light dark:text-chat-text-primary-dark hover:bg-chat-surface-light dark:hover:bg-chat-surface-dark'
              }`}
            >
              <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v0M8 5a2 2 0 012-2h4a2 2 0 012 2v0" />
              </svg>
              Dashboard
            </Link>
            <Link
              to="/"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                location.pathname === '/'
                  ? 'bg-chat-accent text-white'
                  : 'text-chat-text-primary-light dark:text-chat-text-primary-dark hover:bg-chat-surface-light dark:hover:bg-chat-surface-dark'
              }`}
            >
              <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Chat
            </Link>
          </nav>
        </div>

        {/* Search */}
        <div className="p-4">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-chat-text-secondary-light dark:text-chat-text-secondary-dark"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <label htmlFor="search-recaps" className="sr-only">Search recaps</label>
            <input
              id="search-recaps"
              type="text"
              placeholder="Search recaps..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-3 text-base sm:text-sm bg-chat-surface-light dark:bg-chat-surface-dark border border-chat-border-light dark:border-chat-border-dark rounded-md text-chat-text-primary-light dark:text-chat-text-primary-dark placeholder-chat-text-secondary-light dark:placeholder-chat-text-secondary-dark focus:outline-none focus:ring-2 focus:ring-chat-accent min-h-[48px]"
            />
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto px-2" role="list" aria-label="Recap history">
          {filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-chat-text-secondary-light dark:text-chat-text-secondary-dark" aria-live="polite">
              {searchTerm ? 'No matching recaps found' : 'No recaps yet'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredConversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => onConversationSelect(conversation.id)}
                  aria-current={currentConversation === conversation.id ? 'page' : undefined}
                  aria-label={`${conversation.title} - ${conversation.preview}`}
                  className={`w-full text-left p-3 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-chat-accent focus:ring-offset-2 min-h-[48px] ${
                    currentConversation === conversation.id
                      ? 'bg-chat-accent text-white'
                      : 'hover:bg-chat-surface-light dark:hover:bg-chat-surface-dark text-chat-text-primary-light dark:text-chat-text-primary-dark'
                  }`}
                  role="listitem"
                >
                  <div className="font-medium text-sm truncate">
                    {conversation.title}
                  </div>
                  <div className={`text-xs mt-1 truncate ${
                    currentConversation === conversation.id
                      ? 'text-white/80'
                      : 'text-chat-text-secondary-light dark:text-chat-text-secondary-dark'
                  }`}>
                    {conversation.preview}
                  </div>
                  <time 
                    dateTime={conversation.date}
                    className={`text-xs mt-1 block ${
                      currentConversation === conversation.id
                        ? 'text-white/60'
                        : 'text-chat-text-secondary-light dark:text-chat-text-secondary-dark'
                    }`}
                  >
                    {new Date(conversation.date).toLocaleDateString()}
                  </time>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <footer className="p-4 border-t border-chat-border-light dark:border-chat-border-dark">
          <div className="flex items-center space-x-3">
            {user?.user_metadata?.avatar_url && (
              <img
                src={user.user_metadata.avatar_url}
                alt={`${user?.user_metadata?.full_name || user?.email} profile picture`}
                className="w-8 h-8 rounded-full"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-chat-text-primary-light dark:text-chat-text-primary-dark truncate">
                {user?.user_metadata?.full_name || user?.email}
              </div>
              <div className="text-xs text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                Signed in
              </div>
            </div>
          </div>
        </footer>
      </nav>
    </>
  )
}
