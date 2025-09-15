"""
Encryption utilities for secure API key storage
Provides AES-256 encryption for sensitive data like LLM provider API keys
"""

import os
import base64
import secrets
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data like API keys
    Uses AES-256 encryption with PBKDF2 key derivation
    """
    
    def __init__(self):
        """Initialize the encryption service"""
        self._master_key = self._get_or_create_master_key()
        self._fernet = Fernet(self._master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """
        Get or create the master encryption key
        
        Returns:
            bytes: Base64-encoded Fernet key
        """
        # Try to get key from environment
        env_key = os.getenv('ENCRYPTION_MASTER_KEY')
        if env_key:
            try:
                return env_key.encode('utf-8')
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # For development, use a derived key from settings
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
            return self._derive_key_from_secret(settings.SECRET_KEY)
        
        # Fallback: generate a new key (not recommended for production)
        logger.warning("No encryption key found, generating new key. This should not happen in production!")
        return Fernet.generate_key()
    
    def _derive_key_from_secret(self, secret: str) -> bytes:
        """
        Derive an encryption key from the application secret
        
        Args:
            secret: Application secret key
            
        Returns:
            bytes: Derived Fernet key
        """
        # Use a fixed salt for consistency (in production, use environment variable)
        salt = b'fantasy_recap_salt_v1'  # 22 bytes
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode('utf-8')))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            str: Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted_text: Base64-encoded encrypted string
            
        Returns:
            str: Decrypted plaintext string
        """
        if not encrypted_text:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")
    
    def encrypt_api_key(self, api_key: str, provider: str) -> Tuple[str, str]:
        """
        Encrypt an API key with additional metadata
        
        Args:
            api_key: API key to encrypt
            provider: Provider name for metadata
            
        Returns:
            Tuple[str, str]: (encrypted_key, key_hash) for storage and validation
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
        
        # Encrypt the full API key
        encrypted_key = self.encrypt(api_key)
        
        # Create a hash of the last 8 characters for validation/display
        suffix = api_key[-8:] if len(api_key) >= 8 else api_key
        key_hash = self._create_key_hash(suffix, provider)
        
        return encrypted_key, key_hash
    
    def _create_key_hash(self, suffix: str, provider: str) -> str:
        """
        Create a hash for API key validation/display
        
        Args:
            suffix: Last few characters of the API key
            provider: Provider name
            
        Returns:
            str: Hash for validation
        """
        import hashlib
        
        combined = f"{provider}:{suffix}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # First 16 characters
    
    def validate_encryption_key(self) -> bool:
        """
        Validate that encryption/decryption is working correctly
        
        Returns:
            bool: True if encryption is working
        """
        try:
            test_data = "test_encryption_" + secrets.token_hex(8)
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            return test_data == decrypted
        except Exception as e:
            logger.error(f"Encryption validation failed: {e}")
            return False


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail"""
    pass


# Global encryption service instance
encryption_service = EncryptionService()
