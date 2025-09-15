"""
LLM API Key Management Service
Handles secure storage, validation, and management of user LLM provider API keys
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from app.core.supabase import get_supabase_client
from app.core.encryption import encryption_service, EncryptionError
from app.models.llm import LLMProvider, ProviderError, AuthenticationError

logger = logging.getLogger(__name__)


@dataclass
class StoredAPIKey:
    """Represents a stored API key with metadata"""
    id: str
    user_id: str
    provider: LLMProvider
    key_hash: str
    encrypted_key: str
    is_valid: bool
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict = None


class APIKeyService:
    """
    Service for managing user LLM provider API keys
    
    Handles encryption, storage, validation, and retrieval of API keys
    """
    
    def __init__(self):
        """Initialize the API key service"""
        self.table_name = "user_llm_api_keys"
        
        # Validate encryption is working
        if not encryption_service.validate_encryption_key():
            raise EncryptionError("Encryption service validation failed")
    
    async def store_api_key(
        self,
        user_id: str,
        provider: LLMProvider,
        api_key: str,
        validate_key: bool = True
    ) -> bool:
        """
        Store an encrypted API key for a user
        
        Args:
            user_id: User ID
            provider: LLM provider
            api_key: Raw API key to store
            validate_key: Whether to validate the key before storing
            
        Returns:
            bool: True if stored successfully
            
        Raises:
            EncryptionError: If encryption fails
            ProviderError: If validation fails
        """
        try:
            # Encrypt the API key
            encrypted_key, key_hash = encryption_service.encrypt_api_key(api_key, provider.value)
            
            # Validate the key if requested
            is_valid = False
            if validate_key:
                is_valid = await self._validate_api_key_with_provider(api_key, provider)
                if not is_valid:
                    raise AuthenticationError(
                        provider,
                        "API key validation failed - key appears to be invalid"
                    )
            
            supabase = get_supabase_client()
            
            # Check if key already exists for this user/provider
            existing_query = supabase.table(self.table_name).select("id").eq(
                "user_id", user_id
            ).eq("provider", provider.value)
            
            existing_response = existing_query.execute()
            
            current_time = datetime.utcnow().isoformat()
            
            key_data = {
                "user_id": user_id,
                "provider": provider.value,
                "encrypted_api_key": encrypted_key,
                "key_hash": key_hash,
                "is_valid": is_valid,
                "last_validated": current_time if is_valid else None,
                "updated_at": current_time,
                "metadata": {
                    "key_length": len(api_key),
                    "validation_attempted": validate_key,
                    "storage_method": "fernet_encryption"
                }
            }
            
            if existing_response.data:
                # Update existing key
                update_response = supabase.table(self.table_name).update(key_data).eq(
                    "id", existing_response.data[0]["id"]
                ).execute()
                
                if not update_response.data:
                    logger.error(f"Failed to update API key for user {user_id}, provider {provider.value}")
                    return False
                
                logger.info(f"Updated API key for user {user_id}, provider {provider.value}")
            else:
                # Insert new key
                key_data["created_at"] = current_time
                
                insert_response = supabase.table(self.table_name).insert(key_data).execute()
                
                if not insert_response.data:
                    logger.error(f"Failed to store API key for user {user_id}, provider {provider.value}")
                    return False
                
                logger.info(f"Stored new API key for user {user_id}, provider {provider.value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            raise
    
    async def get_api_key(self, user_id: str, provider: LLMProvider) -> Optional[str]:
        """
        Retrieve and decrypt an API key for a user
        
        Args:
            user_id: User ID
            provider: LLM provider
            
        Returns:
            Optional[str]: Decrypted API key or None if not found
        """
        try:
            supabase = get_supabase_client()
            
            query = supabase.table(self.table_name).select("*").eq(
                "user_id", user_id
            ).eq("provider", provider.value)
            
            response = query.execute()
            
            if not response.data:
                return None
            
            key_record = response.data[0]
            encrypted_key = key_record["encrypted_api_key"]
            
            # Decrypt the API key
            decrypted_key = encryption_service.decrypt(encrypted_key)
            
            logger.debug(f"Retrieved API key for user {user_id}, provider {provider.value}")
            return decrypted_key
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key: {e}")
            return None
    
    async def get_stored_api_key_info(self, user_id: str, provider: LLMProvider) -> Optional[StoredAPIKey]:
        """
        Get API key metadata without decrypting the actual key
        
        Args:
            user_id: User ID
            provider: LLM provider
            
        Returns:
            Optional[StoredAPIKey]: Key metadata or None if not found
        """
        try:
            supabase = get_supabase_client()
            
            query = supabase.table(self.table_name).select("*").eq(
                "user_id", user_id
            ).eq("provider", provider.value)
            
            response = query.execute()
            
            if not response.data:
                return None
            
            data = response.data[0]
            
            return StoredAPIKey(
                id=data["id"],
                user_id=data["user_id"],
                provider=LLMProvider(data["provider"]),
                key_hash=data["key_hash"],
                encrypted_key=data["encrypted_api_key"],
                is_valid=data.get("is_valid", False),
                last_validated=datetime.fromisoformat(data["last_validated"]) if data.get("last_validated") else None,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                metadata=data.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to get API key info: {e}")
            return None
    
    async def list_user_api_keys(self, user_id: str) -> List[StoredAPIKey]:
        """
        List all API keys for a user (without decrypting them)
        
        Args:
            user_id: User ID
            
        Returns:
            List[StoredAPIKey]: List of stored API key metadata
        """
        try:
            supabase = get_supabase_client()
            
            query = supabase.table(self.table_name).select("*").eq("user_id", user_id)
            response = query.execute()
            
            keys = []
            for data in response.data or []:
                try:
                    stored_key = StoredAPIKey(
                        id=data["id"],
                        user_id=data["user_id"],
                        provider=LLMProvider(data["provider"]),
                        key_hash=data["key_hash"],
                        encrypted_key=data["encrypted_api_key"],
                        is_valid=data.get("is_valid", False),
                        last_validated=datetime.fromisoformat(data["last_validated"]) if data.get("last_validated") else None,
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        metadata=data.get("metadata", {})
                    )
                    keys.append(stored_key)
                except Exception as e:
                    logger.error(f"Failed to parse API key record: {e}")
                    continue
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list user API keys: {e}")
            return []
    
    async def delete_api_key(self, user_id: str, provider: LLMProvider) -> bool:
        """
        Delete an API key for a user
        
        Args:
            user_id: User ID
            provider: LLM provider
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            supabase = get_supabase_client()
            
            delete_response = supabase.table(self.table_name).delete().eq(
                "user_id", user_id
            ).eq("provider", provider.value).execute()
            
            success = bool(delete_response.data)
            if success:
                logger.info(f"Deleted API key for user {user_id}, provider {provider.value}")
            else:
                logger.warning(f"No API key found to delete for user {user_id}, provider {provider.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False
    
    async def validate_stored_key(self, user_id: str, provider: LLMProvider) -> bool:
        """
        Validate a stored API key and update its status
        
        Args:
            user_id: User ID
            provider: LLM provider
            
        Returns:
            bool: True if key is valid
        """
        try:
            # Get the stored key
            api_key = await self.get_api_key(user_id, provider)
            if not api_key:
                return False
            
            # Validate with provider
            is_valid = await self._validate_api_key_with_provider(api_key, provider)
            
            # Update validation status
            supabase = get_supabase_client()
            update_data = {
                "is_valid": is_valid,
                "last_validated": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase.table(self.table_name).update(update_data).eq(
                "user_id", user_id
            ).eq("provider", provider.value).execute()
            
            logger.info(f"Validated API key for user {user_id}, provider {provider.value}: {'valid' if is_valid else 'invalid'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Failed to validate stored key: {e}")
            return False
    
    async def _validate_api_key_with_provider(self, api_key: str, provider: LLMProvider) -> bool:
        """
        Validate an API key directly with the provider
        
        Args:
            api_key: API key to validate
            provider: Provider to validate against
            
        Returns:
            bool: True if key is valid
        """
        try:
            # Import provider classes to avoid circular imports
            if provider == LLMProvider.OPENAI:
                return await self._validate_openai_key(api_key)
            elif provider == LLMProvider.ANTHROPIC:
                return await self._validate_anthropic_key(api_key)
            elif provider == LLMProvider.GOOGLE:
                return await self._validate_google_key(api_key)
            else:
                logger.warning(f"No validation method for provider: {provider.value}")
                return False
                
        except Exception as e:
            logger.error(f"Provider validation failed for {provider.value}: {e}")
            return False
    
    async def _validate_openai_key(self, api_key: str) -> bool:
        """Validate OpenAI API key"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=api_key)
            
            # Make a minimal request to validate the key
            response = await client.models.list()
            return len(response.data) > 0
            
        except Exception:
            return False
    
    async def _validate_anthropic_key(self, api_key: str) -> bool:
        """Validate Anthropic API key"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=api_key)
            
            # Make a minimal request to validate the key
            response = await client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return bool(response.content)
            
        except Exception:
            return False
    
    async def _validate_google_key(self, api_key: str) -> bool:
        """Validate Google API key"""
        try:
            # This would need to be implemented based on Google's Gemini API
            # For now, return False as placeholder
            logger.warning("Google API key validation not yet implemented")
            return False
            
        except Exception:
            return False


# Global API key service instance
api_key_service = APIKeyService()
