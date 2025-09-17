import React from 'react'
import { Link } from 'react-router-dom'
import { useTheme } from '../../contexts/ThemeContext'
import { AuthButton } from '../AuthButton'

interface HeaderProps {
  onSidebarToggle: () => void
  sidebarOpen: boolean
}

export function Header({ onSidebarToggle, sidebarOpen }: HeaderProps) {
  const { isDark, toggleTheme } = useTheme()

  return (
    <header className="border-b border-chat-border-light dark:border-chat-border-dark bg-chat-bg-light dark:bg-chat-bg-dark">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-3">
          {/* Sidebar Toggle */}
          <button
            onClick={onSidebarToggle}
            className="p-2 rounded-md hover:bg-chat-surface-light dark:hover:bg-chat-surface-dark transition-colors"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            <svg
              className="w-5 h-5 text-chat-text-primary-light dark:text-chat-text-primary-dark"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>

          {/* Logo and App Title */}
          <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
            <img 
              src="/official-logo.png" 
              alt="StatChat Logo" 
              className="w-8 h-8 object-contain"
            />
            <h1 className="text-xl font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark">
              StatChat
            </h1>
          </Link>
        </div>

        <div className="flex items-center space-x-3">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-md hover:bg-chat-surface-light dark:hover:bg-chat-surface-dark transition-colors"
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? (
              <svg className="w-5 h-5 text-chat-text-primary-dark" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-chat-text-primary-light" fill="currentColor" viewBox="0 0 20 20">
                <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
              </svg>
            )}
          </button>

          {/* Auth Button */}
          <AuthButton />
        </div>
      </div>
    </header>
  )
}
