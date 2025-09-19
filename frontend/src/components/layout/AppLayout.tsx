import React, { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { AuthButton } from '../AuthButton'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { ConversationView } from './ConversationView'

export function AppLayout() {
  const { user } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentConversation, setCurrentConversation] = useState<string | null>(null)

  if (!user) {
    return (
      <div className="min-h-screen bg-chat-bg-light dark:bg-chat-bg-dark flex items-center justify-center">
        <main className="text-center space-y-6 p-8">
          <h1 className="text-3xl sm:text-4xl font-bold text-chat-text-primary-light dark:text-chat-text-primary-dark">
            StatChat
          </h1>
          <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark text-base sm:text-lg max-w-md mx-auto">
            Generate AI-powered recaps for your fantasy leagues
          </p>
          <div className="pt-4">
            <AuthButton />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-chat-bg-light dark:bg-chat-bg-dark flex">
      {/* Skip navigation link */}
      <a 
        href="#main-content" 
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 bg-chat-accent text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-chat-accent"
      >
        Skip to main content
      </a>
      
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        currentConversation={currentConversation}
        onConversationSelect={setCurrentConversation}
        aria-expanded={sidebarOpen}
      />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
        />
        
        <main id="main-content" className="flex-1">
          <ConversationView 
            conversationId={currentConversation}
            className="h-full"
          />
        </main>
      </div>
    </div>
  )
}
