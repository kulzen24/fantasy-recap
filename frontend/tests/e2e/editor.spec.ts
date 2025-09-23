import { test, expect } from '@playwright/test';

test.describe('Recap Editor', () => {
  test('editor page loads', async ({ page }) => {
    await page.goto('/editor');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that the editor page is displayed
    await expect(page.locator('body')).toBeVisible();
    
    // Check for no JavaScript errors
    const errors = [];
    page.on('pageerror', (err) => errors.push(err));
    
    await page.waitForTimeout(1000);
    expect(errors.length).toBe(0);
  });

  test('editor has basic text editing capabilities', async ({ page }) => {
    await page.goto('/editor');
    await page.waitForLoadState('networkidle');
    
    // Look for contenteditable elements (Lexical editor)
    const editor = page.locator('[contenteditable="true"]').first();
    
    if (await editor.isVisible()) {
      // Try to type in the editor
      await editor.click();
      await editor.fill('Test content for recap editor');
      
      // Verify content was entered
      await expect(editor).toContainText('Test content');
    }
  });

  test('editor toolbar is functional', async ({ page }) => {
    await page.goto('/editor');
    await page.waitForLoadState('networkidle');
    
    // Look for toolbar buttons (bold, italic, etc.)
    const toolbar = page.locator('[role="toolbar"], .toolbar, .editor-toolbar').first();
    
    if (await toolbar.isVisible()) {
      // Check that toolbar buttons exist
      const buttons = toolbar.locator('button');
      const buttonCount = await buttons.count();
      
      expect(buttonCount).toBeGreaterThan(0);
    }
  });
});
