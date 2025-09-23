import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthButton } from '../components/AuthButton';
import { AuthContext } from '../contexts/AuthContext';

// Mock the AuthContext
const mockAuthContext = {
  user: null,
  signIn: jest.fn(),
  signOut: jest.fn(),
  loading: false,
};

const AuthButtonWrapper = ({ children, contextValue = mockAuthContext }) => (
  <BrowserRouter>
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  </BrowserRouter>
);

describe('AuthButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders sign in button when user is not authenticated', () => {
    render(
      <AuthButtonWrapper>
        <AuthButton />
      </AuthButtonWrapper>
    );

    const signInButton = screen.getByText(/sign in/i);
    expect(signInButton).toBeInTheDocument();
  });

  test('renders user info and sign out when user is authenticated', () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      user_metadata: { full_name: 'Test User' },
    };

    render(
      <AuthButtonWrapper contextValue={{ ...mockAuthContext, user: mockUser }}>
        <AuthButton />
      </AuthButtonWrapper>
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText(/sign out/i)).toBeInTheDocument();
  });

  test('calls signIn when sign in button is clicked', () => {
    render(
      <AuthButtonWrapper>
        <AuthButton />
      </AuthButtonWrapper>
    );

    const signInButton = screen.getByText(/sign in/i);
    fireEvent.click(signInButton);

    expect(mockAuthContext.signIn).toHaveBeenCalledTimes(1);
  });

  test('calls signOut when sign out button is clicked', () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      user_metadata: { full_name: 'Test User' },
    };

    render(
      <AuthButtonWrapper contextValue={{ ...mockAuthContext, user: mockUser }}>
        <AuthButton />
      </AuthButtonWrapper>
    );

    const signOutButton = screen.getByText(/sign out/i);
    fireEvent.click(signOutButton);

    expect(mockAuthContext.signOut).toHaveBeenCalledTimes(1);
  });

  test('shows loading state', () => {
    render(
      <AuthButtonWrapper contextValue={{ ...mockAuthContext, loading: true }}>
        <AuthButton />
      </AuthButtonWrapper>
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
