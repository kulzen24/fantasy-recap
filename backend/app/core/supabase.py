"""
Supabase client configuration and utilities
"""

import os
from typing import Optional
from supabase import create_client, Client
from .config import settings


class SupabaseClient:
    """Supabase client wrapper with additional utilities"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get standard Supabase client with anon key"""
        if self._client is None:
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Get Supabase client with service role key for admin operations"""
        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY must be set for admin operations")
        
        if self._service_client is None:
            self._service_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
        return self._service_client
    
    async def encrypt_api_key(self, api_key: str, encryption_key: str) -> bytes:
        """Encrypt an API key using the database encryption function"""
        try:
            # Set the encryption key for this session
            await self.service_client.rpc(
                'set_config',
                {
                    'setting_name': 'app.encryption_key',
                    'new_value': encryption_key,
                    'is_local': True
                }
            )
            
            # Encrypt the API key
            result = await self.service_client.rpc(
                'encrypt_sensitive_data',
                {'data': api_key}
            )
            
            return result.data
        except Exception as e:
            raise ValueError(f"Failed to encrypt API key: {str(e)}")
    
    async def decrypt_api_key(self, encrypted_data: bytes, encryption_key: str) -> str:
        """Decrypt an API key using the database decryption function"""
        try:
            # Set the encryption key for this session
            await self.service_client.rpc(
                'set_config',
                {
                    'setting_name': 'app.encryption_key',
                    'new_value': encryption_key,
                    'is_local': True
                }
            )
            
            # Decrypt the API key
            result = await self.service_client.rpc(
                'decrypt_sensitive_data',
                {'encrypted_data': encrypted_data}
            )
            
            return result.data
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    async def get_user_profile(self, user_id: str) -> Optional[dict]:
        """Get user profile by ID"""
        try:
            result = self.client.table('user_profiles').select('*').eq('id', user_id).single().execute()
            return result.data
        except Exception:
            return None
    
    async def create_user_profile(self, user_id: str, **profile_data) -> dict:
        """Create a new user profile"""
        profile_data['id'] = user_id
        result = self.client.table('user_profiles').insert(profile_data).execute()
        return result.data[0] if result.data else {}
    
    async def get_user_api_keys(self, user_id: str) -> list:
        """Get all API keys for a user (encrypted)"""
        result = self.client.table('user_api_keys').select('*').eq('user_id', user_id).eq('is_active', True).execute()
        return result.data or []
    
    async def get_user_fantasy_leagues(self, user_id: str) -> list:
        """Get all fantasy leagues for a user"""
        result = self.client.table('fantasy_leagues').select('*').eq('user_id', user_id).eq('is_active', True).execute()
        return result.data or []
    
    async def get_league_recaps(self, league_id: str, season: Optional[int] = None) -> list:
        """Get recaps for a specific league"""
        query = self.client.table('generated_recaps').select('*').eq('league_id', league_id)
        
        if season:
            query = query.eq('season', season)
        
        result = query.order('week', desc=True).execute()
        return result.data or []


# Global Supabase client instance
supabase_client = SupabaseClient()
