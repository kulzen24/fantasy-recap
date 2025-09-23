# Testing Documentation

## Overview

This project uses a comprehensive testing stack including:

- **React Testing Library** for unit and integration tests
- **Playwright** for end-to-end testing
- **Axe** for accessibility testing
- **MSW** for API mocking (not yet configured)

## Test Structure

```
tests/
├── e2e/                    # Playwright E2E tests
│   ├── smoke.spec.ts       # Basic smoke tests
│   ├── health.spec.ts      # API health checks
│   ├── editor.spec.ts      # Recap editor functionality
│   └── accessibility.spec.ts # Accessibility tests
├── integration/            # Integration tests (future)
└── README.md              # This file

src/
├── __tests__/              # Unit tests (React Testing Library)
│   ├── AuthButton.test.tsx
│   └── Dashboard.test.tsx
└── setupTests.ts           # Test configuration
```

## Available Scripts

### Unit Tests
```bash
npm test                    # Run unit tests in watch mode
npm run test:unit          # Run unit tests once
```

### E2E Tests
```bash
npm run test:e2e           # Run all Playwright tests
npm run test:e2e:ui        # Run Playwright with UI
npm run test:smoke         # Run smoke tests only
npm run test:accessibility # Run accessibility tests only
```

### All Tests
```bash
npm run test:all           # Run unit tests + E2E tests
```

## Prerequisites for E2E Tests

Before running E2E tests, ensure:

1. **Frontend is running**: `npm start` (port 3000)
2. **Backend is running**: Backend server should be running on port 8000
3. **Database is available**: Supabase or local database should be accessible

## Test Configuration

### Playwright Configuration
- **Config file**: `playwright.config.ts`
- **Base URL**: http://localhost:3000
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Auto server start**: Automatically starts `npm start` before tests

### React Testing Library
- **Setup file**: `src/setupTests.ts`
- **Mock environment variables** for testing
- **Mock browser APIs** (matchMedia, IntersectionObserver)

## Writing Tests

### Unit Tests (React Testing Library)
```typescript
import { render, screen } from '@testing-library/react';
import MyComponent from '../MyComponent';

test('renders component', () => {
  render(<MyComponent />);
  expect(screen.getByText('Hello')).toBeInTheDocument();
});
```

### E2E Tests (Playwright)
```typescript
import { test, expect } from '@playwright/test';

test('user can navigate to dashboard', async ({ page }) => {
  await page.goto('/');
  await page.click('text=Dashboard');
  await expect(page).toHaveURL('/dashboard');
});
```

### Accessibility Tests
```typescript
import AxeBuilder from '@axe-core/playwright';

test('page has no accessibility violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

## Known Issues

1. **React Router v7**: Some compatibility issues with older test setups
2. **Unit test mocking**: May need additional mocking for complex components
3. **Backend dependency**: E2E tests require running backend server

## Next Steps

1. Fix React Router compatibility in unit tests
2. Add MSW for API mocking in tests
3. Expand test coverage for all components
4. Add visual regression testing
5. Set up CI/CD test pipeline
