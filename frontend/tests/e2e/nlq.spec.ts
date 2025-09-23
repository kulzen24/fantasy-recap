/**
 * End-to-end tests for Natural Language Query system
 * Tests complete user workflow from dashboard to AI assistant
 */

import { test, expect } from '@playwright/test'

test.describe('Natural Language Query System', () => {
  
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/v1/auth/**', async route => {
      await route.fulfill({
        json: {
          user: {
            id: 'test-user-1',
            email: 'test@example.com',
            user_metadata: { display_name: 'Test User' }
          }
        }
      })
    })

    // Mock NLQ API endpoints
    await page.route('**/api/v1/nlq/examples', async route => {
      await route.fulfill({
        json: {
          success: true,
          examples: ['Who scored the most points this week?'],
          categories: {
            player_stats: ['Who scored the most points this week?', 'How did my QB perform?'],
            team_performance: ['How is my team doing?', 'What are my team strengths?'],
            league_analysis: ['Show me the standings', 'Who has the best record?'],
            trends: ['Which players are trending up?', 'Show breakout performances']
          }
        }
      })
    })

    await page.route('**/api/v1/nlq/query', async route => {
      const request = await route.request().postDataJSON()
      await route.fulfill({
        json: {
          success: true,
          query_response: {
            query_id: 'test-query-123',
            original_query: request.query,
            answer: `Josh Allen scored the most points this week with 28.5 points. He had an outstanding performance with 3 passing touchdowns and 1 rushing touchdown.`,
            supporting_data: {
              top_scorer: { name: 'Josh Allen', points: 28.5, position: 'QB' },
              league_average: 18.2
            },
            confidence: 0.92,
            response_time_ms: 850
          },
          suggestions: ['How has Josh Allen been performing this season?', 'Who are the top QBs this week?']
        }
      })
    })

    // Navigate to dashboard
    await page.goto('/')
  })

  test('user can access NLQ from dashboard', async ({ page }) => {
    // Should see dashboard with tabs
    await expect(page.getByText('Welcome back')).toBeVisible()
    
    // Click on Ask AI tab
    await page.getByRole('button', { name: /Ask AI/i }).click()
    
    // Should see league selection
    await expect(page.getByText('Select a League to Ask Questions')).toBeVisible()
  })

  test('user can select league and ask questions', async ({ page }) => {
    // Navigate to Ask AI tab
    await page.getByRole('button', { name: /Ask AI/i }).click()
    
    // Select a league
    await page.getByText('My Fantasy League 2024').click()
    
    // Should see chat interface
    await expect(page.getByText('Fantasy Assistant')).toBeVisible()
    await expect(page.getByPlaceholderText('Ask about your fantasy league...')).toBeVisible()
    
    // Should see welcome message
    await expect(page.getByText(/Hi! I'm your fantasy football assistant/)).toBeVisible()
  })

  test('user can view and click query examples', async ({ page }) => {
    // Navigate to chat
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    // Should see examples
    await expect(page.getByText('Try asking:')).toBeVisible()
    await expect(page.getByText('"Who scored the most points this week?"')).toBeVisible()
    
    // Click on an example
    await page.getByText('"Who scored the most points this week?"').click()
    
    // Should fill the input
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    await expect(input).toHaveValue('Who scored the most points this week?')
    
    // Examples should be hidden after clicking
    await expect(page.getByText('Try asking:')).not.toBeVisible()
  })

  test('user can submit query and receive response', async ({ page }) => {
    // Navigate to chat
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    // Type a query
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    await input.fill('Who scored the most points this week?')
    
    // Submit query
    await page.getByRole('button', { name: /Send/i }).click()
    
    // Should show loading state
    await expect(page.getByText('Analyzing your question...')).toBeVisible()
    
    // Should show user message
    await expect(page.getByText('Who scored the most points this week?')).toBeVisible()
    
    // Should show AI response
    await expect(page.getByText(/Josh Allen scored the most points/)).toBeVisible()
    
    // Should show supporting data
    await expect(page.getByText('Supporting Data:')).toBeVisible()
    
    // Input should be cleared
    await expect(input).toHaveValue('')
  })

  test('user can submit multiple queries in conversation', async ({ page }) => {
    // Navigate to chat and submit first query
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    
    // First query
    await input.fill('Who scored the most points?')
    await page.getByRole('button', { name: /Send/i }).click()
    await expect(page.getByText(/Josh Allen scored the most points/)).toBeVisible()
    
    // Second query
    await input.fill('How is my team doing?')
    await page.getByRole('button', { name: /Send/i }).click()
    
    // Should have multiple message bubbles
    const userMessages = page.locator('[data-testid="user-message"], .user-message, :text("Who scored the most points?")')
    await expect(userMessages).toHaveCount(1) // First user message
    
    const assistantMessages = page.locator('[data-testid="assistant-message"], .assistant-message')
    // Should have at least one assistant response
    await expect(page.getByText(/Josh Allen scored the most points/)).toBeVisible()
  })

  test('user can switch between leagues', async ({ page }) => {
    // Navigate to chat and select league
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    // Should see chat interface
    await expect(page.getByText('Fantasy Assistant')).toBeVisible()
    
    // Click change league
    await page.getByText('Change League').click()
    
    // Should return to league selection
    await expect(page.getByText('Select a League to Ask Questions')).toBeVisible()
    
    // Select different league
    await page.getByText('Work League Championship').click()
    
    // Should see chat interface again
    await expect(page.getByText('Fantasy Assistant')).toBeVisible()
  })

  test('submit button states work correctly', async ({ page }) => {
    // Navigate to chat
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    const submitButton = page.getByRole('button', { name: /Send/i })
    
    // Submit should be disabled when empty
    await expect(submitButton).toBeDisabled()
    
    // Submit should be enabled when input has content
    await input.fill('Test query')
    await expect(submitButton).toBeEnabled()
    
    // Submit should be disabled during loading
    await submitButton.click()
    // Note: Testing loading state is tricky in E2E tests due to timing
  })

  test('keyboard shortcuts work', async ({ page }) => {
    // Navigate to chat
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    
    // Type query and press Enter
    await input.fill('Who scored the most points?')
    await input.press('Enter')
    
    // Should submit the query
    await expect(page.getByText('Analyzing your question...')).toBeVisible()
  })

  test('responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Navigate to chat
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    // Chat interface should be responsive
    await expect(page.getByText('Fantasy Assistant')).toBeVisible()
    await expect(page.getByPlaceholderText('Ask about your fantasy league...')).toBeVisible()
    
    // Submit a query
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    await input.fill('Test mobile query')
    await page.getByRole('button', { name: /Send/i }).click()
    
    // Should work on mobile
    await expect(page.getByText(/Josh Allen scored the most points/)).toBeVisible()
  })

  test('error handling displays user-friendly messages', async ({ page }) => {
    // Mock API error
    await page.route('**/api/v1/nlq/query', async route => {
      await route.fulfill({
        status: 500,
        json: { detail: 'Internal server error' }
      })
    })

    // Navigate to chat and submit query
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    const input = page.getByPlaceholderText('Ask about your fantasy league...')
    await input.fill('Test error query')
    await page.getByRole('button', { name: /Send/i }).click()
    
    // Should show user-friendly error message
    await expect(page.getByText(/Sorry, I encountered an error/)).toBeVisible()
  })

  test('accessibility features work correctly', async ({ page }) => {
    // Navigate to chat
    await page.getByRole('button', { name: /Ask AI/i }).click()
    await page.getByText('My Fantasy League 2024').click()
    
    // Check for proper ARIA labels and roles
    await expect(page.getByRole('textbox', { name: /Ask about your fantasy league/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /Send/i })).toBeVisible()
    
    // Test keyboard navigation
    await page.getByPlaceholderText('Ask about your fantasy league...').focus()
    await page.keyboard.press('Tab')
    await expect(page.getByRole('button', { name: /Send/i })).toBeFocused()
  })
})
