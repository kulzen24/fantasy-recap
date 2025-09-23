import { test, expect } from '@playwright/test';

test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page title is correct
    await expect(page).toHaveTitle(/StatChat/);
    
    // Check that main content loads
    await expect(page.locator('body')).toBeVisible();
  });

  test('navigation elements are present', async ({ page }) => {
    await page.goto('/');
    
    // Wait for React to load
    await page.waitForLoadState('networkidle');
    
    // Check for auth button (login/logout)
    await expect(page.locator('button')).toBeVisible();
  });

  test('app handles 404 gracefully', async ({ page }) => {
    await page.goto('/non-existent-page');
    
    // Should still load the React app, not show browser 404
    await expect(page.locator('body')).toBeVisible();
  });
});
