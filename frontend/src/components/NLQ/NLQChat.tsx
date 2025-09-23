/**
 * Natural Language Query Chat Interface
 * StatMuse-like chat interface for asking questions about fantasy leagues
 */

import React, { useState, useRef, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { 
  useNLQQuery, 
  useNLQExamples, 
  useNLQFeedback,
  NLQRequest,
  QueryResponse,
  QueryFeedback
} from '../../hooks/useNLQ'

interface NLQChatProps {
  leagueId?: string
  className?: string
}

interface ChatMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  queryResponse?: QueryResponse
  isLoading?: boolean
  error?: string
}

export function NLQChat({ leagueId, className = '' }: NLQChatProps) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [showExamples, setShowExamples] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const { submitQuery, isLoading } = useNLQQuery()
  const { data: examples } = useNLQExamples()
  const { submitFeedback } = useNLQFeedback()
  
  // Scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  // Add welcome message on first load
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        type: 'assistant',
        content: "Hi! I'm your fantasy football assistant. Ask me anything about your league, players, or stats. For example, you could ask \"Who scored the most points this week?\" or \"How is my team performing?\"",
        timestamp: new Date()
      }])
    }
  }, [messages.length])
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!inputValue.trim() || !leagueId) return
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    }
    
    const loadingMessage: ChatMessage = {
      id: `loading-${Date.now()}`,
      type: 'assistant',
      content: 'Analyzing your question...',
      timestamp: new Date(),
      isLoading: true
    }
    
    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInputValue('')
    setShowExamples(false)
    
    try {
      const request: NLQRequest = {
        query: inputValue.trim(),
        league_id: leagueId,
        include_visualizations: true
      }
      
      const response = await submitQuery(request)
      
      // Remove loading message and add response
      setMessages(prev => {
        const withoutLoading = prev.filter(m => m.id !== loadingMessage.id)
        
        if (response.success && response.query_response) {
          return [...withoutLoading, {
            id: response.query_response.query_id,
            type: 'assistant',
            content: response.query_response.answer,
            timestamp: new Date(),
            queryResponse: response.query_response
          }]
        } else {
          return [...withoutLoading, {
            id: `error-${Date.now()}`,
            type: 'assistant',
            content: response.error || 'I had trouble understanding your question. Could you try rephrasing it?',
            timestamp: new Date(),
            error: response.error
          }]
        }
      })
      
    } catch (error) {
      // Remove loading message and show error
      setMessages(prev => {
        const withoutLoading = prev.filter(m => m.id !== loadingMessage.id)
        return [...withoutLoading, {
          id: `error-${Date.now()}`,
          type: 'assistant',
          content: 'Sorry, I encountered an error while processing your question. Please try again.',
          timestamp: new Date(),
          error: error instanceof Error ? error.message : 'Unknown error'
        }]
      })
    }
  }
  
  const handleExampleClick = (example: string) => {
    setInputValue(example)
    setShowExamples(false)
  }
  
  const handleFeedback = async (messageId: string, rating: number) => {
    try {
      const feedback: QueryFeedback = {
        query_id: messageId,
        rating,
        feedback_type: 'rating'
      }
      await submitFeedback(feedback)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }
  
  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
  
  if (!user) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Sign in to Chat
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Please sign in to ask questions about your fantasy leagues.
          </p>
        </div>
      </div>
    )
  }
  
  if (!leagueId) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Select a League
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Choose a league to start asking questions about your fantasy team.
          </p>
        </div>
      </div>
    )
  }
  
  return (
    <div className={`flex flex-col h-full bg-white dark:bg-gray-800 rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Fantasy Assistant
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Ask me anything about your league
            </p>
          </div>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onFeedback={handleFeedback}
          />
        ))}
        
        {/* Examples */}
        {showExamples && examples && messages.length <= 1 && (
          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Try asking:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.entries(examples.categories).map(([category, categoryExamples]) => (
                <div key={category} className="space-y-1">
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                    {category.replace('_', ' ')}
                  </p>
                  {categoryExamples.slice(0, 2).map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleExampleClick(example)}
                      className="text-left w-full p-2 text-sm text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                    >
                      "{example}"
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-600">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about your fantasy league..."
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                     focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                     placeholder-gray-500 dark:placeholder-gray-400"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                     disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center space-x-2"
          >
            {isLoading ? (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
            <span>Send</span>
          </button>
        </form>
      </div>
    </div>
  )
}

// Message bubble component
interface MessageBubbleProps {
  message: ChatMessage
  onFeedback: (messageId: string, rating: number) => void
}

function MessageBubble({ message, onFeedback }: MessageBubbleProps) {
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackGiven, setFeedbackGiven] = useState(false)
  
  const handleRating = (rating: number) => {
    onFeedback(message.id, rating)
    setFeedbackGiven(true)
    setShowFeedback(false)
  }
  
  return (
    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
        message.type === 'user'
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
      }`}>
        <div className="text-sm">
          {message.isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-pulse flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              </div>
              <span>Thinking...</span>
            </div>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>
        
        {/* Supporting data visualization */}
        {message.queryResponse?.supporting_data && Object.keys(message.queryResponse.supporting_data).length > 0 && (
          <div className="mt-2 p-2 bg-gray-50 dark:bg-gray-600 rounded text-xs">
            <p className="font-medium mb-1">Supporting Data:</p>
            <pre className="text-xs overflow-x-auto">
              {JSON.stringify(message.queryResponse.supporting_data, null, 2)}
            </pre>
          </div>
        )}
        
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs opacity-75">
            {message.timestamp.toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
          
          {/* Feedback buttons for assistant messages */}
          {message.type === 'assistant' && !message.isLoading && !message.error && message.queryResponse && (
            <div className="flex items-center space-x-1">
              {!feedbackGiven && !showFeedback && (
                <button
                  onClick={() => setShowFeedback(true)}
                  className="text-xs opacity-75 hover:opacity-100 underline"
                >
                  Rate
                </button>
              )}
              
              {showFeedback && (
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => handleRating(rating)}
                      className="text-xs hover:text-yellow-500"
                    >
                      ⭐
                    </button>
                  ))}
                </div>
              )}
              
              {feedbackGiven && (
                <span className="text-xs opacity-75">Thanks!</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
