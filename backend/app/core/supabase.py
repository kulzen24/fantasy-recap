"""
Supabase client configuration and initialization
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance
    
    Returns:
        Client: Configured Supabase client
        
    Raises:
        ValueError: If required environment variables are not set
    """
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        try:
            _supabase_client = create_client(url, key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    return _supabase_client


def get_supabase_client_safe() -> Optional[Client]:
    """
    Get Supabase client without raising exceptions
    
    Returns:
        Client or None: Supabase client if available, None otherwise
    """
    try:
        return get_supabase_client()
    except Exception as e:
        logger.warning(f"Supabase client not available: {e}")
        return None


def get_supabase_service_client() -> Client:
    """
    Get Supabase client with service role key for bypassing RLS.
    Used for authenticated backend operations.
    
    Returns:
        Client: Configured Supabase client with service role
        
    Raises:
        ValueError: If required environment variables are not set
    """
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    
    try:
        client = create_client(url, service_key)
        logger.info("Supabase service client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase service client: {e}")
        raise


def get_supabase_service_client_safe() -> Optional[Client]:
    """
    Get Supabase service client without raising exceptions
    
    Returns:
        Client or None: Supabase service client if available, None otherwise
    """
    try:
        return get_supabase_service_client()
    except Exception as e:
        logger.warning(f"Supabase service client not available: {e}")
        return None


def reset_supabase_client():
    """Reset the global Supabase client (useful for testing)"""
    global _supabase_client
    _supabase_client = None


# Create wrapper class for compatibility
class SupabaseClientWrapper:
    """Wrapper to maintain compatibility with existing code"""
    
    def __init__(self):
        self._client = None
    
    @property 
    def client(self):
        """Get the Supabase client"""
        if self._client is None:
            self._client = get_supabase_client_safe()
        return self._client

# Global instances for compatibility
supabase_client = SupabaseClientWrapper()
supabase = get_supabase_client_safe()