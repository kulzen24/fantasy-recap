import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardOverview from '../components/Dashboard/DashboardOverview';
import { AuthContext } from '../contexts/AuthContext';

// Mock the API hooks
jest.mock('../hooks/useDashboardData', () => ({
  useLeagues: () => ({
    data: {
      data: [
        {
          id: '1',
          name: 'Test League',
          platform: 'yahoo',
          league_id: 'test-123',
          total_teams: 10,
          current_week: 1,
          season: 2024,
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
  useRecaps: () => ({
    data: {
      data: [
        {
          id: '1',
          title: 'Week 1 Recap',
          content: 'Test recap content',
          league_id: '1',
          week: 1,
          season: 2024,
          status: 'completed',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
  useDashboardStats: () => ({
    data: {
      total_leagues: 1,
      total_recaps: 1,
      recent_activity: [],
    },
    isLoading: false,
    error: null,
  }),
}));

const mockAuthContext = {
  user: {
    id: '123',
    email: 'test@example.com',
    user_metadata: { full_name: 'Test User' },
  },
  signIn: jest.fn(),
  signOut: jest.fn(),
  loading: false,
};

const DashboardWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthContext.Provider value={mockAuthContext}>
      {children}
    </AuthContext.Provider>
  </BrowserRouter>
);

describe('DashboardOverview', () => {
  test('renders dashboard sections', () => {
    render(
      <DashboardWrapper>
        <DashboardOverview />
      </DashboardWrapper>
    );

    // Check for main dashboard sections
    expect(screen.getByText(/leagues/i)).toBeInTheDocument();
    expect(screen.getByText(/recaps/i)).toBeInTheDocument();
  });

  test('displays league information', () => {
    render(
      <DashboardWrapper>
        <DashboardOverview />
      </DashboardWrapper>
    );

    expect(screen.getByText('Test League')).toBeInTheDocument();
  });

  test('displays recap information', () => {
    render(
      <DashboardWrapper>
        <DashboardOverview />
      </DashboardWrapper>
    );

    expect(screen.getByText('Week 1 Recap')).toBeInTheDocument();
  });
});
