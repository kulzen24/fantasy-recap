import { test, expect } from '@playwright/test';

test.describe('Health Checks', () => {
  test('backend health endpoint is accessible', async ({ request }) => {
    // Test the health endpoint
    const response = await request.get('http://localhost:8000/api/v1/health');
    
    expect(response.status()).toBe(200);
    
    const health = await response.json();
    expect(health).toHaveProperty('status', 'healthy');
    expect(health).toHaveProperty('timestamp');
  });

  test('public API info endpoint is accessible', async ({ request }) => {
    // Test the public info endpoint
    const response = await request.get('http://localhost:8000/api/v1/public');
    
    expect(response.status()).toBe(200);
    
    const info = await response.json();
    expect(info).toHaveProperty('version');
    expect(info).toHaveProperty('name');
  });

  test('dashboard loads without authentication errors', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Should redirect to auth or show login, not crash
    await page.waitForLoadState('networkidle');
    
    // Check that page loaded successfully (no network errors)
    const errors = [];
    page.on('pageerror', (err) => errors.push(err));
    
    await page.waitForTimeout(1000);
    expect(errors.length).toBe(0);
  });
});
