"""
LLM API Key Management Endpoints
Provides secure endpoints for users to manage their LLM provider API keys
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.auth import require_authentication
from app.services.llm.api_key_service import api_key_service, StoredAPIKey
from app.models.llm import LLMProvider, ProviderError, AuthenticationError
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class APIKeyCreateRequest(BaseModel):
    provider: str = Field(..., description="LLM provider name (openai, anthropic, google)")
    api_key: str = Field(..., description="API key for the provider")
    validate_key: bool = Field(default=True, description="Whether to validate the key before storing")


class APIKeyResponse(BaseModel):
    provider: str
    key_hash: str
    is_valid: bool
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class APIKeyListResponse(BaseModel):
    success: bool
    data: List[APIKeyResponse]
    count: int


@router.get("/")
async def list_api_keys(
    current_user: dict = Depends(require_authentication)
) -> APIKeyListResponse:
    """List all stored API keys for the authenticated user"""
    try:
        user_id = current_user["id"]
        
        stored_keys = await api_key_service.list_user_api_keys(user_id)
        
        response_data = []
        for key in stored_keys:
            response_data.append(APIKeyResponse(
                provider=key.provider.value,
                key_hash=key.key_hash,
                is_valid=key.is_valid,
                last_validated=key.last_validated,
                created_at=key.created_at,
                updated_at=key.updated_at,
                metadata=key.metadata or {}
            ))
        
        logger.info(f"Listed {len(response_data)} API keys for user {user_id}")
        
        return APIKeyListResponse(
            success=True,
            data=response_data,
            count=len(response_data)
        )
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )


@router.post("/")
async def store_api_key(
    request: APIKeyCreateRequest,
    current_user: dict = Depends(require_authentication)
):
    """Store a new API key for an LLM provider"""
    try:
        user_id = current_user["id"]
        
        # Validate provider
        try:
            provider = LLMProvider(request.provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.provider}. Supported: openai, anthropic, google"
            )
        
        # Validate API key format
        if not request.api_key or len(request.api_key.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key must be at least 10 characters long"
            )
        
        # Store the API key
        success = await api_key_service.store_api_key(
            user_id=user_id,
            provider=provider,
            api_key=request.api_key.strip(),
            validate_key=request.validate_key
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store API key"
            )
        
        # Get the stored key info to return
        key_info = await api_key_service.get_stored_api_key_info(user_id, provider)
        
        logger.info(f"Stored API key for user {user_id}, provider {provider.value}")
        
        return {
            "success": True,
            "message": f"API key for {provider.value} stored successfully",
            "data": APIKeyResponse(
                provider=key_info.provider.value,
                key_hash=key_info.key_hash,
                is_valid=key_info.is_valid,
                last_validated=key_info.last_validated,
                created_at=key_info.created_at,
                updated_at=key_info.updated_at,
                metadata=key_info.metadata or {}
            ) if key_info else None
        }
        
    except AuthenticationError as e:
        logger.warning(f"API key validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key validation failed: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store API key: {str(e)}"
        )


@router.get("/{provider}")
async def get_api_key_info(
    provider: str,
    current_user: dict = Depends(require_authentication)
):
    """Get information about a stored API key (without revealing the key)"""
    try:
        user_id = current_user["id"]
        
        # Validate provider
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        key_info = await api_key_service.get_stored_api_key_info(user_id, provider_enum)
        
        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No API key found for provider: {provider}"
            )
        
        return {
            "success": True,
            "data": APIKeyResponse(
                provider=key_info.provider.value,
                key_hash=key_info.key_hash,
                is_valid=key_info.is_valid,
                last_validated=key_info.last_validated,
                created_at=key_info.created_at,
                updated_at=key_info.updated_at,
                metadata=key_info.metadata or {}
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API key info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API key info: {str(e)}"
        )


@router.post("/{provider}/validate")
async def validate_api_key(
    provider: str,
    current_user: dict = Depends(require_authentication)
):
    """Validate a stored API key against the provider"""
    try:
        user_id = current_user["id"]
        
        # Validate provider
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        # Check if key exists
        key_info = await api_key_service.get_stored_api_key_info(user_id, provider_enum)
        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No API key found for provider: {provider}"
            )
        
        # Validate the key
        is_valid = await api_key_service.validate_stored_key(user_id, provider_enum)
        
        logger.info(f"Validated API key for user {user_id}, provider {provider}: {'valid' if is_valid else 'invalid'}")
        
        return {
            "success": True,
            "provider": provider,
            "is_valid": is_valid,
            "validated_at": datetime.utcnow().isoformat(),
            "message": f"API key is {'valid' if is_valid else 'invalid'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate API key: {str(e)}"
        )


@router.delete("/{provider}")
async def delete_api_key(
    provider: str,
    current_user: dict = Depends(require_authentication)
):
    """Delete a stored API key"""
    try:
        user_id = current_user["id"]
        
        # Validate provider
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        # Delete the key
        success = await api_key_service.delete_api_key(user_id, provider_enum)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No API key found for provider: {provider}"
            )
        
        logger.info(f"Deleted API key for user {user_id}, provider {provider}")
        
        return {
            "success": True,
            "message": f"API key for {provider} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )


@router.get("/health/encryption")
async def check_encryption_health():
    """Check if encryption service is working correctly (admin endpoint)"""
    try:
        from app.core.encryption import encryption_service
        
        is_healthy = encryption_service.validate_encryption_key()
        
        return {
            "success": True,
            "encryption_healthy": is_healthy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Encryption health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption health check failed: {str(e)}"
        )
