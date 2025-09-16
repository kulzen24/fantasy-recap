import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_CONFIG } from '../config';

interface League {
  id: string; // Database ID for deletion
  league_id: string;
  league_name: string;
  season: number;
  is_active: boolean;
  platform: string;
}

export function YahooLeagueConnection() {
  const { user, session } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectingYahoo, setConnectingYahoo] = useState(false);
  const [showManualAuth, setShowManualAuth] = useState(false);
  const [callbackUrl, setCallbackUrl] = useState('');
  const [processedCodes, setProcessedCodes] = useState<Set<string>>(new Set());

  // Fetch user's connected leagues
  const fetchLeagues = useCallback(async () => {
    if (!session?.access_token) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/leagues/`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setLeagues(data.leagues || data.data || []);
        setError(null);
      } else {
        setError('Failed to fetch leagues');
      }
    } catch (err) {
      setError('Error fetching leagues');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  // Import leagues from Yahoo after successful OAuth
  const importYahooLeagues = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First, connect the Yahoo leagues to our system
      const connectResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/leagues/connect/yahoo`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          platform: 'yahoo',
          season: 2024
        }),
      });
      
      if (connectResponse.ok) {
        const connectData = await connectResponse.json();
        if (connectData.success) {
          // Refresh the leagues list
          await fetchLeagues();
          setError(null);
        } else {
          setError(`Failed to import Yahoo leagues: ${connectData.error || 'Unknown error'}`);
        }
      } else {
        const errorData = await connectResponse.json();
        setError(`Failed to import Yahoo leagues: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Error importing Yahoo leagues');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token, fetchLeagues]);

  // Handle Yahoo OAuth callback from popup
  const handleYahooCallback = useCallback(async (code: string, state: string | null) => {
    // Prevent processing the same code twice
    if (processedCodes.has(code)) {
      console.log('Code already processed, skipping:', code.substring(0, 10) + '...');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Mark code as being processed
      setProcessedCodes(prev => new Set(prev).add(code));
      
      // Clear processed code after 5 minutes to prevent memory leaks
      setTimeout(() => {
        setProcessedCodes(prev => {
          const newSet = new Set(prev);
          newSet.delete(code);
          return newSet;
        });
      }, 300000);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/fantasy/yahoo/callback`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, state }),
      });

      const result = await response.json();
      
      if (response.ok && result.success) {
        console.log('Yahoo OAuth successful:', result.message);
        // Refresh leagues after successful connection
        await importYahooLeagues();
      } else {
        const errorMessage = result.detail || result.message || 'Yahoo authentication failed';
        if (errorMessage.includes('Authorization code expired') || errorMessage.includes('invalid_grant')) {
          setError('Authorization code expired. Please try connecting to Yahoo again - codes expire quickly!');
        } else {
          setError(errorMessage);
        }
      }
    } catch (err) {
      setError('Failed to process Yahoo authentication');
      console.error('Yahoo callback error:', err);
    } finally {
      setLoading(false);
      setConnectingYahoo(false);
    }
  }, [session?.access_token, importYahooLeagues, processedCodes]);

  // Listen for popup messages
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'yahoo_auth_success' && event.data.success) {
        console.log('Received Yahoo auth success message:', event.data);
        setShowManualAuth(false);
        setConnectingYahoo(false);
        // Token exchange already completed in backend, just refresh leagues
        importYahooLeagues();
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [importYahooLeagues]);

  // Delete a league
  const deleteLeague = async (leagueId: string) => {
    if (!window.confirm('Are you sure you want to remove this league?')) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/leagues/${leagueId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Refresh the leagues list
        await fetchLeagues();
        setError(null);
      } else {
        const errorData = await response.json();
        setError(`Failed to delete league: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Error deleting league');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Connect Yahoo account with popup flow
  const connectYahoo = async () => {
    try {
      setConnectingYahoo(true);
      setError(null);
      
      // Get Yahoo OAuth URL
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/fantasy/yahoo/auth-url`);
      const data = await response.json();
      
      if (data.success) {
        // Open popup window
        const popup = window.open(
          data.auth_url,
          'yahoo-oauth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );
        
        if (!popup) {
          setError('Popup blocked. Please allow popups for this site and try again.');
          setConnectingYahoo(false);
          return;
        }

        // Poll for popup closure
        const pollTimer = setInterval(() => {
          if (popup.closed) {
            clearInterval(pollTimer);
            setConnectingYahoo(false);
            // If popup was closed without message, show manual instructions
            setShowManualAuth(true);
          }
        }, 1000);

        // Cleanup timer when component unmounts or popup closes
        const cleanup = () => {
          clearInterval(pollTimer);
          setConnectingYahoo(false);
        };

        // Fallback: close popup after 5 minutes
        setTimeout(() => {
          cleanup();
          if (!popup.closed) {
            popup.close();
          }
          setShowManualAuth(true);
        }, 300000);
      } else {
        setError('Failed to get Yahoo authorization URL');
        setConnectingYahoo(false);
      }
    } catch (err) {
      setError('Error connecting to Yahoo');
      console.error('Error:', err);
      setConnectingYahoo(false);
    }
  };

  // Process manual callback URL
  const processManualCallback = async () => {
    if (!callbackUrl.trim()) {
      setError('Please enter the callback URL');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Extract code from URL
      const url = new URL(callbackUrl);
      const code = url.searchParams.get('code');
      const state = url.searchParams.get('state');

      if (!code) {
        setError('No authorization code found in URL. Make sure you copied the complete URL.');
        return;
      }

      await handleYahooCallback(code, state);
      setShowManualAuth(false);
      setCallbackUrl('');
    } catch (err) {
      setError('Invalid URL format. Please copy the complete URL from the browser address bar.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };



  // Refresh leagues after Yahoo OAuth callback
  useEffect(() => {
    if (user) {
      fetchLeagues();
    }
  }, [user, session, fetchLeagues]);

  // Handle Yahoo OAuth callback (you'll need to set up a route for this)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    
    if (code && session?.access_token) {
      handleYahooCallback(code, state);
    }
  }, [session, handleYahooCallback]);

  if (!user) {
    return (
      <div className="p-6 bg-chat-surface-light dark:bg-chat-surface-dark rounded-lg">
        <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
          Please sign in to connect your Yahoo Fantasy leagues.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-chat-surface-light dark:bg-chat-surface-dark rounded-lg p-6">
        <h3 className="text-lg font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-4">
          Yahoo Fantasy Leagues
        </h3>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-md">
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        )}

        {leagues.length === 0 ? (
          <div className="py-8">
            {!showManualAuth ? (
              <div className="text-center">
                <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark mb-4">
                  No Yahoo Fantasy leagues connected yet.
                </p>
                <button
                  onClick={connectYahoo}
                  disabled={connectingYahoo}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors font-medium"
                >
                  {connectingYahoo ? 'Connecting...' : 'Connect Yahoo Fantasy'}
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                    Complete Yahoo Authorization
                  </h4>
                  <ol className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-decimal list-inside">
                    <li>Sign in to Yahoo and approve the app in the new tab</li>
                    <li>After approval, you'll be redirected to a page (might show an error)</li>
                    <li>Copy the complete URL from your browser's address bar</li>
                    <li>Paste it below and click "Complete Connection"</li>
                  </ol>
                </div>
                
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-chat-text-primary-light dark:text-chat-text-primary-dark">
                    Paste the callback URL here:
                  </label>
                  <textarea
                    value={callbackUrl}
                    onChange={(e) => setCallbackUrl(e.target.value)}
                    placeholder={`${API_CONFIG.BASE_URL}/api/v1/fantasy/yahoo/callback?code=...`}
                    className="w-full p-3 border border-chat-border-light dark:border-chat-border-dark rounded-lg bg-white dark:bg-gray-800 text-chat-text-primary-light dark:text-chat-text-primary-dark text-sm"
                    rows={3}
                  />
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={processManualCallback}
                      disabled={loading || !callbackUrl.trim()}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors font-medium"
                    >
                      {loading ? 'Processing...' : 'Complete Connection'}
                    </button>
                    <button
                      onClick={() => {
                        setShowManualAuth(false);
                        setCallbackUrl('');
                        setError(null);
                      }}
                      className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-medium text-chat-text-primary-light dark:text-chat-text-primary-dark">
                Connected Leagues ({leagues.length})
              </h4>
              <div className="flex space-x-2">
                <button
                  onClick={importYahooLeagues}
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
                >
                  {loading ? 'Importing...' : 'Import Leagues'}
                </button>
                <button
                  onClick={connectYahoo}
                  disabled={connectingYahoo}
                  className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors text-sm"
                >
                  Add More Leagues
                </button>
              </div>
            </div>
            
            {loading ? (
              <div className="text-center py-4">
                <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                  Loading leagues...
                </p>
              </div>
            ) : (
              <div className="grid gap-3">
                {leagues.map((league) => (
                  <div
                    key={`${league.league_id}-${league.season}`}
                    className="p-4 border border-chat-border-light dark:border-chat-border-dark rounded-lg"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h5 className="font-medium text-chat-text-primary-light dark:text-chat-text-primary-dark">
                          {league.league_name}
                        </h5>
                        <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                          {league.season} Season • Yahoo Fantasy
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          league.is_active 
                            ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300' 
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                        }`}>
                          {league.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <button
                          onClick={() => deleteLeague(league.id)}
                          disabled={loading}
                          className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded disabled:opacity-50 transition-colors"
                          title="Remove league"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
