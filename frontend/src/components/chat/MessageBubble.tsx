import React from 'react'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  isTyping?: boolean
}

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-3xl rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-chat-accent text-white ml-12'
            : 'bg-chat-surface-light dark:bg-chat-surface-dark text-chat-text-primary-light dark:text-chat-text-primary-dark mr-12'
        }`}
      >
        {/* Message Content */}
        <div className={`${isUser ? 'text-white' : ''}`}>
          {message.isTyping ? (
            <div className="flex items-center space-x-1">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-current rounded-full animate-pulse" />
                <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-75" />
                <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-150" />
              </div>
              <span className="ml-2 text-sm opacity-70">Generating response...</span>
            </div>
          ) : isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                components={{
                  // Custom styling for markdown elements
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold mb-3 text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold mb-2 text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-semibold mb-2 text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-3 leading-relaxed text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="mb-3 space-y-1 text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="mb-3 space-y-1 text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{children}</span>
                    </li>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark">
                      {children}
                    </strong>
                  ),
                  code: ({ children }) => (
                    <code className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-sm font-mono">
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="bg-gray-100 dark:bg-gray-800 rounded-md p-3 overflow-x-auto">
                      {children}
                    </pre>
                  )
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={`text-xs mt-2 ${
            isUser
              ? 'text-white/70'
              : 'text-chat-text-secondary-light dark:text-chat-text-secondary-dark'
          }`}
        >
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  )
}
