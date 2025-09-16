import React, { useState } from 'react';
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

export function TestYahooConnection() {
  const { user, session } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Test function to add mock leagues
  const addTestLeague = async () => {
    if (!session?.access_token) {
      setError('Please sign in first');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Create a mock league for testing
      const mockLeague = {
        platform: 'yahoo',
        league_id: `test_${Date.now()}`,
        league_name: `Test League ${leagues.length + 1}`,
        season: 2024,
        is_active: true,
        league_data: {
          teams: 12,
          scoring: 'PPR',
          created_for: 'testing'
        }
      };

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/leagues/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mockLeague),
      });

      if (response.ok) {
        await fetchLeagues(); // Refresh the list
      } else {
        const errorData = await response.json();
        setError(`Failed to add test league: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Error adding test league');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Delete a league
  const deleteLeague = async (leagueId: string) => {
    if (!session?.access_token) {
      setError('Please sign in first');
      return;
    }

    if (!window.confirm('Are you sure you want to remove this league?')) {
      return;
    }

    try {
      setDeletingId(leagueId);
      setError(null);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/leagues/${leagueId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        await fetchLeagues(); // Refresh the list
      } else {
        const errorData = await response.json();
        setError(`Failed to remove league: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Error removing league');
      console.error('Error:', err);
    } finally {
      setDeletingId(null);
    }
  };

  // Fetch user's leagues
  const fetchLeagues = React.useCallback(async () => {
    if (!session?.access_token) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/leagues/`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setLeagues(data.leagues || []);
      } else {
        const errorData = await response.json();
        setError(`Failed to fetch leagues: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Error fetching leagues');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  React.useEffect(() => {
    if (user && session?.access_token) {
      fetchLeagues();
    }
  }, [user, session?.access_token, fetchLeagues]);

  if (!user) {
    return (
      <div className="p-6 bg-chat-surface-light dark:bg-chat-surface-dark rounded-lg">
        <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
          Please sign in to test league connections.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-chat-surface-light dark:bg-chat-surface-dark rounded-lg p-6">
        <h3 className="text-lg font-semibold text-chat-text-primary-light dark:text-chat-text-primary-dark mb-4">
          🧪 Test League Connection
        </h3>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-md">
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        )}

        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h4 className="font-medium text-chat-text-primary-light dark:text-chat-text-primary-dark">
                Connected Leagues ({leagues.length})
              </h4>
              <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                Test your league connection functionality
              </p>
            </div>
            <button
              onClick={addTestLeague}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm"
            >
              {loading ? 'Adding...' : 'Add Test League'}
            </button>
          </div>
          
          {loading && leagues.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                Loading leagues...
              </p>
            </div>
          ) : leagues.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-chat-text-secondary-light dark:text-chat-text-secondary-dark mb-4">
                No leagues connected yet.
              </p>
              <p className="text-xs text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                Click "Add Test League" to test the functionality
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
                    <div className="flex-1">
                      <h5 className="font-medium text-chat-text-primary-light dark:text-chat-text-primary-dark">
                        {league.league_name}
                      </h5>
                      <p className="text-sm text-chat-text-secondary-light dark:text-chat-text-secondary-dark">
                        {league.season} Season • {league.platform.charAt(0).toUpperCase() + league.platform.slice(1)} Fantasy
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        league.is_active 
                          ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300' 
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                      }`}>
                        {league.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <button
                        onClick={() => deleteLeague(league.id)}
                        disabled={deletingId === league.id}
                        className="p-1 text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50 transition-colors"
                        title="Remove league"
                      >
                        {deletingId === league.id ? (
                          <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
