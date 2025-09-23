/**
 * Unit tests for NLQ Chat Component
 * Tests user interactions, query submission, and message handling
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NLQChat } from '../components/NLQ/NLQChat'
import { AuthContext } from '../contexts/AuthContext'
import * as useNLQModule from '../hooks/useNLQ'

// Mock the useNLQ hooks
jest.mock('../hooks/useNLQ')

// Mock user context
const mockUser = {
  id: 'test-user-1',
  email: 'test@example.com',
  user_metadata: {
    display_name: 'Test User'
  }
}

const mockAuthContext = {
  user: mockUser,
  loading: false,
  signIn: jest.fn(),
  signOut: jest.fn(),
  signUp: jest.fn()
}

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={mockAuthContext}>
        {children}
      </AuthContext.Provider>
    </QueryClientProvider>
  )
}

describe('NLQChat', () => {
  // Mock implementations
  const mockSubmitQuery = jest.fn()
  const mockExamplesData = {
    success: true,
    examples: ['Example query 1', 'Example query 2'],
    categories: {
      player_stats: ['Who scored the most points this week?'],
      team_performance: ['How is my team performing?'],
      league_analysis: ['Show me the current standings'],
      trends: ['Which players are trending up?']
    }
  }

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock useNLQ hooks
    jest.spyOn(useNLQModule, 'useNLQQuery').mockReturnValue({
      submitQuery: mockSubmitQuery,
      isLoading: false,
      error: null
    })
    
    jest.spyOn(useNLQModule, 'useNLQExamples').mockReturnValue({
      data: mockExamplesData,
      isLoading: false,
      error: null,
      refetch: jest.fn()
    })
    
    jest.spyOn(useNLQModule, 'useNLQFeedback').mockReturnValue({
      submitFeedback: jest.fn(),
      isLoading: false,
      error: null
    })
  })

  test('renders without league ID - shows league selection prompt', () => {
    render(
      <TestWrapper>
        <NLQChat />
      </TestWrapper>
    )

    expect(screen.getByText('Select a League')).toBeInTheDocument()
    expect(screen.getByText('Choose a league to start asking questions about your fantasy team.')).toBeInTheDocument()
  })

  test('renders with league ID - shows chat interface', () => {
    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    expect(screen.getByText('Fantasy Assistant')).toBeInTheDocument()
    expect(screen.getByText('Ask me anything about your league')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ask about your fantasy league...')).toBeInTheDocument()
  })

  test('shows welcome message on initial load', () => {
    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    expect(screen.getByText(/Hi! I'm your fantasy football assistant/)).toBeInTheDocument()
  })

  test('displays query examples when no messages', async () => {
    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Try asking:')).toBeInTheDocument()
      expect(screen.getByText('"Who scored the most points this week?"')).toBeInTheDocument()
    })
  })

  test('handles query submission', async () => {
    const mockResponse = {
      success: true,
      query_response: {
        query_id: 'test-query-1',
        answer: 'Josh Allen scored the most points this week with 28.5 points.',
        confidence: 0.9,
        supporting_data: { top_scorer: { name: 'Josh Allen', points: 28.5 } }
      },
      suggestions: []
    }

    mockSubmitQuery.mockResolvedValueOnce(mockResponse)

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = screen.getByRole('button', { name: /send/i })

    // Type a query
    fireEvent.change(input, { target: { value: 'Who scored the most points?' } })
    fireEvent.click(submitButton)

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('Analyzing your question...')).toBeInTheDocument()
    })

    // Should show response
    await waitFor(() => {
      expect(screen.getByText('Josh Allen scored the most points this week with 28.5 points.')).toBeInTheDocument()
    })

    // Verify API call
    expect(mockSubmitQuery).toHaveBeenCalledWith({
      query: 'Who scored the most points?',
      league_id: 'test-league-1',
      include_visualizations: true
    })
  })

  test('handles query submission error', async () => {
    mockSubmitQuery.mockRejectedValueOnce(new Error('API Error'))

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = screen.getByRole('button', { name: /send/i })

    fireEvent.change(input, { target: { value: 'Test query' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument()
    })
  })

  test('handles unsuccessful API response', async () => {
    const mockResponse = {
      success: false,
      error: 'Unable to process query',
      suggestions: []
    }

    mockSubmitQuery.mockResolvedValueOnce(mockResponse)

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = screen.getByRole('button', { name: /send/i })

    fireEvent.change(input, { target: { value: 'Test query' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Unable to process query')).toBeInTheDocument()
    })
  })

  test('clicking example query fills input', () => {
    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const exampleButton = screen.getByText('"Who scored the most points this week?"')
    fireEvent.click(exampleButton)

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    expect(input).toHaveValue('Who scored the most points this week?')
  })

  test('disables submit when input is empty', () => {
    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /send/i })
    expect(submitButton).toBeDisabled()
  })

  test('enables submit when input has content', () => {
    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = screen.getByRole('button', { name: /send/i })

    fireEvent.change(input, { target: { value: 'Test query' } })
    expect(submitButton).not.toBeDisabled()
  })

  test('shows loading state during query submission', async () => {
    // Mock loading state
    jest.spyOn(useNLQModule, 'useNLQQuery').mockReturnValue({
      submitQuery: mockSubmitQuery,
      isLoading: true,
      error: null
    })

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const submitButton = screen.getByRole('button', { name: /send/i })
    expect(submitButton).toBeDisabled()
    expect(screen.getByText('Send')).toBeInTheDocument()
  })

  test('displays supporting data when available', async () => {
    const mockResponse = {
      success: true,
      query_response: {
        query_id: 'test-query-1',
        answer: 'Response with data',
        confidence: 0.9,
        supporting_data: { 
          players: [
            { name: 'Josh Allen', points: 28.5 },
            { name: 'Lamar Jackson', points: 25.2 }
          ]
        }
      },
      suggestions: []
    }

    mockSubmitQuery.mockResolvedValueOnce(mockResponse)

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = screen.getByRole('button', { name: /send/i })

    fireEvent.change(input, { target: { value: 'Test query' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Supporting Data:')).toBeInTheDocument()
    })
  })

  test('shows unauthenticated state when no user', () => {
    const unauthenticatedContext = {
      ...mockAuthContext,
      user: null
    }

    render(
      <QueryClientProvider client={new QueryClient()}>
        <AuthContext.Provider value={unauthenticatedContext}>
          <NLQChat leagueId="test-league-1" />
        </AuthContext.Provider>
      </QueryClientProvider>
    )

    expect(screen.getByText('Sign in to Chat')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to ask questions about your fantasy leagues.')).toBeInTheDocument()
  })

  test('form submission works with Enter key', async () => {
    const mockResponse = {
      success: true,
      query_response: {
        query_id: 'test-query-1',
        answer: 'Test response',
        confidence: 0.9
      },
      suggestions: []
    }

    mockSubmitQuery.mockResolvedValueOnce(mockResponse)

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    fireEvent.change(input, { target: { value: 'Test query' } })
    fireEvent.submit(input.closest('form')!)

    await waitFor(() => {
      expect(mockSubmitQuery).toHaveBeenCalled()
    })
  })

  test('clears input after successful submission', async () => {
    const mockResponse = {
      success: true,
      query_response: {
        query_id: 'test-query-1',
        answer: 'Test response',
        confidence: 0.9
      },
      suggestions: []
    }

    mockSubmitQuery.mockResolvedValueOnce(mockResponse)

    render(
      <TestWrapper>
        <NLQChat leagueId="test-league-1" />
      </TestWrapper>
    )

    const input = screen.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = screen.getByRole('button', { name: /send/i })

    fireEvent.change(input, { target: { value: 'Test query' } })
    fireEvent.click(submitButton)

    // Input should be cleared after submission
    expect(input).toHaveValue('')
  })
})
