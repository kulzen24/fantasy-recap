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
        <div className="text-center space-y-6 p-8">
          <h1 className="text-4xl font-bold text-chat-text-primary-light dark:text-chat-text-primary-dark">
            StatChat
          </h1>
          <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark text-lg max-w-md">
            Generate AI-powered recaps for your fantasy leagues
          </p>
          <div className="pt-4">
            <AuthButton />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-chat-bg-light dark:bg-chat-bg-dark flex">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        currentConversation={currentConversation}
        onConversationSelect={setCurrentConversation}
      />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
        />
        
        <ConversationView 
          conversationId={currentConversation}
          className="flex-1"
        />
      </div>
    </div>
  )
}
