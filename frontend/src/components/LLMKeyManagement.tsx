import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { API_CONFIG } from '../config';

interface APIKey {
  provider: string;
  key_hash: string;
  is_valid: boolean;
  last_validated: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

interface LLMProvider {
  id: string;
  name: string;
  description: string;
  icon: string;
  keyFormat: string;
  helpUrl: string;
}

const SUPPORTED_PROVIDERS: LLMProvider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4, GPT-3.5, and other OpenAI models',
    icon: '🤖',
    keyFormat: 'sk-...',
    helpUrl: 'https://platform.openai.com/api-keys'
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    description: 'Claude 3 and other Anthropic models',
    icon: '🧠',
    keyFormat: 'sk-ant-...',
    helpUrl: 'https://console.anthropic.com/account/keys'
  },
  {
    id: 'google',
    name: 'Google AI',
    description: 'Gemini and other Google AI models',
    icon: '🌟',
    keyFormat: 'AI...',
    helpUrl: 'https://aistudio.google.com/app/apikey'
  }
];

export function LLMKeyManagement() {
  const { user, session } = useAuth();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [addingProvider, setAddingProvider] = useState<string | null>(null);
  const [newKeyValue, setNewKeyValue] = useState('');
  const [validatingKey, setValidatingKey] = useState<string | null>(null);

  // Fetch existing API keys
  const fetchAPIKeys = async () => {
    if (!session?.access_token) return;

    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/llm-keys/`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.data || []);
        setError(null);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to fetch API keys');
      }
    } catch (err) {
      setError('Error fetching API keys');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Add new API key
  const addAPIKey = async (provider: string, apiKey: string) => {
    if (!session?.access_token) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/llm-keys/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: provider,
          api_key: apiKey,
          validate_key: true
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(`${provider.toUpperCase()} API key added successfully!`);
        setAddingProvider(null);
        setNewKeyValue('');
        await fetchAPIKeys();
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(data.detail || 'Failed to add API key');
      }
    } catch (err) {
      setError('Error adding API key');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Validate existing API key
  const validateAPIKey = async (provider: string) => {
    if (!session?.access_token) return;

    try {
      setValidatingKey(provider);
      setError(null);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/llm-keys/${provider}/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(`${provider.toUpperCase()} API key validated successfully!`);
        await fetchAPIKeys();
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(data.detail || 'Failed to validate API key');
      }
    } catch (err) {
      setError('Error validating API key');
      console.error('Error:', err);
    } finally {
      setValidatingKey(null);
    }
  };

  // Delete API key
  const deleteAPIKey = async (provider: string) => {
    if (!session?.access_token) return;
    
    if (!window.confirm(`Are you sure you want to remove the ${provider.toUpperCase()} API key?`)) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/llm-keys/${provider}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setSuccess(`${provider.toUpperCase()} API key removed successfully!`);
        await fetchAPIKeys();
        
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to delete API key');
      }
    } catch (err) {
      setError('Error deleting API key');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent, provider: string) => {
    e.preventDefault();
    if (!newKeyValue.trim()) {
      setError('Please enter an API key');
      return;
    }
    addAPIKey(provider, newKeyValue.trim());
  };

  // Get provider info
  const getProviderInfo = (providerId: string) => {
    return SUPPORTED_PROVIDERS.find(p => p.id === providerId);
  };

  // Check if provider has existing key
  const hasExistingKey = (providerId: string) => {
    return apiKeys.some(key => key.provider === providerId);
  };

  useEffect(() => {
    if (user) {
      fetchAPIKeys();
    }
  }, [user, fetchAPIKeys]);

  if (!user) {
    return (
      <div className="p-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-gray-600 dark:text-gray-400">
          Please sign in to manage your LLM API keys.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          LLM API Key Management
        </h3>
        
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
            🔐 API Key Security
          </h4>
          <p className="text-sm text-blue-800 dark:text-blue-200">
            Your API keys are encrypted and stored securely. We only store a hash of your keys for validation. 
            Keys are never logged or exposed in responses.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-md">
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-100 dark:bg-green-900/20 border border-green-300 dark:border-green-700 rounded-md">
            <p className="text-green-700 dark:text-green-300 text-sm">{success}</p>
          </div>
        )}

        <div className="space-y-4">
          {SUPPORTED_PROVIDERS.map((provider) => {
            const existingKey = apiKeys.find(key => key.provider === provider.id);
            const isAdding = addingProvider === provider.id;
            
            return (
              <div key={provider.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="text-2xl">{provider.icon}</div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {provider.name}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {provider.description}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                        Key format: {provider.keyFormat}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {existingKey ? (
                      <>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            existingKey.is_valid 
                              ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300' 
                              : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                          }`}>
                            {existingKey.is_valid ? 'Valid' : 'Invalid'}
                          </span>
                          
                          <button
                            onClick={() => validateAPIKey(provider.id)}
                            disabled={validatingKey === provider.id}
                            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                          >
                            {validatingKey === provider.id ? 'Validating...' : 'Validate'}
                          </button>
                          
                          <button
                            onClick={() => deleteAPIKey(provider.id)}
                            disabled={loading}
                            className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 transition-colors"
                          >
                            Remove
                          </button>
                        </div>
                      </>
                    ) : (
                      <button
                        onClick={() => setAddingProvider(isAdding ? null : provider.id)}
                        className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors text-sm"
                      >
                        {isAdding ? 'Cancel' : 'Add Key'}
                      </button>
                    )}
                  </div>
                </div>

                {isAdding && (
                  <form onSubmit={(e) => handleSubmit(e, provider.id)} className="mt-4 space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        {provider.name} API Key
                      </label>
                      <input
                        type="password"
                        value={newKeyValue}
                        onChange={(e) => setNewKeyValue(e.target.value)}
                        placeholder={`Enter your ${provider.name} API key`}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <a
                        href={provider.helpUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 underline"
                      >
                        Get {provider.name} API Key →
                      </a>
                      
                      <div className="flex space-x-2">
                        <button
                          type="button"
                          onClick={() => {
                            setAddingProvider(null);
                            setNewKeyValue('');
                            setError(null);
                          }}
                          className="px-3 py-2 text-sm bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={loading || !newKeyValue.trim()}
                          className="px-3 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
                        >
                          {loading ? 'Adding...' : 'Add Key'}
                        </button>
                      </div>
                    </div>
                  </form>
                )}

                {existingKey && (
                  <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                    Added: {new Date(existingKey.created_at).toLocaleDateString()}
                    {existingKey.last_validated && (
                      <> • Last validated: {new Date(existingKey.last_validated).toLocaleDateString()}</>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {apiKeys.length === 0 && !loading && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🔑</div>
            <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No API Keys Added Yet
            </h4>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Add LLM API keys to enable AI-powered features like natural language queries and recap generation.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
