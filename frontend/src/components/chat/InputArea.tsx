import React, { useState, useRef, useEffect } from 'react'

interface InputAreaProps {
  onSendMessage: (message: string) => void
  isLoading: boolean
  placeholder?: string
}

export function InputArea({ onSendMessage, isLoading, placeholder = "Type your message..." }: InputAreaProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSendMessage(message)
      setMessage('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="border-t border-chat-border-light dark:border-chat-border-dark bg-chat-bg-light dark:bg-chat-bg-dark">
      <div className="max-w-4xl mx-auto p-4">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex items-end space-x-3">
            {/* Textarea */}
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                disabled={isLoading}
                rows={1}
                className="w-full resize-none rounded-lg border border-chat-border-light dark:border-chat-border-dark bg-chat-surface-light dark:bg-chat-surface-dark px-4 py-3 pr-12 text-chat-text-primary-light dark:text-chat-text-primary-dark placeholder-chat-text-secondary-light dark:placeholder-chat-text-secondary-dark focus:outline-none focus:ring-2 focus:ring-chat-accent disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ minHeight: '48px', maxHeight: '200px' }}
              />
              
              {/* Character counter for longer messages */}
              {message.length > 100 && (
                <div className="absolute bottom-1 right-14 text-xs text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                  {message.length}/2000
                </div>
              )}
            </div>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!message.trim() || isLoading}
              className="p-3 bg-chat-accent hover:bg-chat-accent-hover disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center justify-center"
              aria-label="Send message"
            >
              {isLoading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
          
          {/* Helper text */}
          <div className="mt-2 text-xs text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
            Press Enter to send, Shift+Enter for new line
          </div>
        </form>
      </div>
    </div>
  )
}
