import React, { useState, useRef, useEffect } from 'react'
import { MessageBubble } from '../chat/MessageBubble'
import { InputArea } from '../chat/InputArea'
import { LeaguesSetup } from '../LeaguesSetup'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  isTyping?: boolean
}

interface ConversationViewProps {
  conversationId: string | null
  className?: string
}

// Mock data for demonstration
const mockMessages: Record<string, Message[]> = {
  '1': [
    {
      id: '1',
      content: 'Can you generate a recap for week 1 of my fantasy league?',
      role: 'user',
      timestamp: new Date('2024-01-15T10:00:00')
    },
    {
      id: '2',
      content: `# Week 1 Fantasy Recap: League Championship

## 🏆 Top Performers
**Highest Scorer:** Your Team Name (142.5 pts)
- **QB:** Josh Allen - 28.4 pts (spectacular performance!)
- **RB:** Christian McCaffrey - 24.8 pts
- **WR:** Tyreek Hill - 21.2 pts

## 📈 Key Highlights
- **Upset of the Week:** Team Underdog defeated the defending champ 118.2 to 103.4
- **Closest Matchup:** Only 2.1 points separated victory from defeat
- **Waiver Wire Hero:** Gabe Davis (picked up by 3 teams) scored 18.6 points

## 🔥 What to Watch
Looking ahead to Week 2, keep an eye on:
- Weather conditions for outdoor games
- Injury reports for key players
- Emerging waiver wire targets

Great start to the season! Your team is looking strong with that balanced scoring attack.`,
      role: 'assistant',
      timestamp: new Date('2024-01-15T10:01:00')
    }
  ],
  '2': [
    {
      id: '3',
      content: 'Should I trade my RB1 for a top WR? I have depth at RB but thin at WR.',
      role: 'user',
      timestamp: new Date('2024-01-14T15:30:00')
    },
    {
      id: '4',
      content: `That's a strategic question that depends on several factors. Let me break this down:

## ✅ Reasons to Consider the Trade:
- **Positional scarcity:** Top WRs can be harder to find on waivers
- **Consistency:** Elite WRs often have more predictable target shares
- **Your depth:** If you have quality RB2/RB3 options, this could work

## ❌ Reasons to be Cautious:
- **RB1 value:** Top RBs typically score more points per game
- **Injury risk:** WRs can be more boom/bust week to week
- **League scoring:** Check if your league favors RBs (standard) or WRs (PPR)

## 🔍 Questions to Ask:
1. Who specifically are you targeting?
2. What's your current RB depth chart?
3. Is this PPR or standard scoring?

Share those details and I can give you a more specific recommendation!`,
      role: 'assistant',
      timestamp: new Date('2024-01-14T15:31:00')
    }
  ]
}

export function ConversationView({ conversationId, className = '' }: ConversationViewProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showLeaguesSetup, setShowLeaguesSetup] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Load messages for the current conversation
    if (conversationId && mockMessages[conversationId]) {
      setMessages(mockMessages[conversationId])
    } else {
      setMessages([])
    }
  }, [conversationId])

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: content.trim(),
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    // Simulate AI response delay
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I'm a demo response! In the real app, this would be an AI-generated recap or analysis based on your fantasy league data.",
        role: 'assistant',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1500)
  }

  if (!conversationId) {
    if (showLeaguesSetup) {
      return (
        <div className={`flex flex-col ${className}`}>
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 border-b border-chat-border-light dark:border-chat-border-dark">
              <button
                onClick={() => setShowLeaguesSetup(false)}
                className="flex items-center text-chat-text-secondary-light dark:text-chat-text-secondary-dark hover:text-chat-text-primary-light dark:hover:text-chat-text-primary-dark transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Home
              </button>
            </div>
            <LeaguesSetup />
          </div>
        </div>
      )
    }

    return (
      <div className={`flex flex-col ${className}`}>
        {/* Welcome Screen */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-2xl">
            <div className="w-16 h-16 mx-auto mb-6">
              <img 
                src="/official-logo.png" 
                alt="StatChat Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            <h2 className="text-3xl font-bold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-4">
              Welcome to StatChat
            </h2>
            <p className="text-lg text-chat-text-secondary-light dark:text-chat-text-secondary-dark mb-8">
              Generate AI-powered recaps, trade analysis, and insights for your fantasy leagues. 
              Ask me anything about your team or start a new conversation!
            </p>
            
            {/* Get Started Button */}
            <div className="mb-8">
              <button
                onClick={() => setShowLeaguesSetup(true)}
                className="px-6 py-3 bg-chat-accent text-white rounded-lg hover:bg-chat-accent-hover transition-colors font-medium"
              >
                🔗 Connect Your Leagues
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              <div className="p-4 border border-chat-border-light dark:border-chat-border-dark rounded-lg">
                <h3 className="font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-2">
                  📊 Weekly Recaps
                </h3>
                <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                  Get detailed analysis of your league's performance, top players, and key moments
                </p>
              </div>
              <div className="p-4 border border-chat-border-light dark:border-chat-border-dark rounded-lg">
                <h3 className="font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-2">
                  🔄 Trade Analysis
                </h3>
                <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                  Evaluate potential trades and get recommendations based on your roster needs
                </p>
              </div>
              <div className="p-4 border border-chat-border-light dark:border-chat-border-dark rounded-lg">
                <h3 className="font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-2">
                  📈 Waiver Wire
                </h3>
                <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                  Discover the best available players and prioritize your waiver claims
                </p>
              </div>
              <div className="p-4 border border-chat-border-light dark:border-chat-border-dark rounded-lg">
                <h3 className="font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-2">
                  🎯 Strategy Tips
                </h3>
                <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                  Get personalized advice for lineup decisions and season-long planning
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Input Area */}
        <InputArea 
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          placeholder="Ask me about your fantasy league..."
        />
      </div>
    )
  }

  return (
    <div className={`flex flex-col ${className}`}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <MessageBubble
            message={{
              id: 'typing',
              content: 'Thinking...',
              role: 'assistant',
              timestamp: new Date(),
              isTyping: true
            }}
          />
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <InputArea 
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        placeholder="Ask a follow-up question..."
      />
    </div>
  )
}
