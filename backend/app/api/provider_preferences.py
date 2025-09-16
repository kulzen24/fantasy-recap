"""
Provider Preferences API
Endpoints for managing user LLM provider preferences
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.models.llm import LLMProvider
from app.services.llm.user_provider_config import user_provider_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


class ProviderPreferenceRequest(BaseModel):
    """Request model for updating provider preferences"""
    preferred_provider: LLMProvider
    fallback_providers: Optional[List[LLMProvider]] = None
    cost_optimization: Optional[bool] = None
    quality_preference: Optional[str] = None


class ProviderPreferenceResponse(BaseModel):
    """Response model for provider preferences"""
    preferred_provider: Optional[LLMProvider]
    fallback_providers: List[LLMProvider]
    available_providers: List[LLMProvider]
    cost_optimization: bool
    quality_preference: str
    has_preferences: bool


@router.get("/preferences", response_model=ProviderPreferenceResponse)
async def get_user_provider_preferences(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's current LLM provider preferences
    """
    try:
        user_id = current_user["id"]
        
        selection = await user_provider_service.get_provider_selection_for_user(user_id)
        
        return ProviderPreferenceResponse(
            preferred_provider=selection.get("preferred_provider"),
            fallback_providers=selection.get("fallback_providers", []),
            available_providers=selection.get("available_providers", []),
            cost_optimization=selection.get("cost_optimization", False),
            quality_preference=selection.get("quality_preference", "balanced"),
            has_preferences=selection.get("has_preferences", False)
        )
        
    except Exception as e:
        logger.error(f"Error getting provider preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider preferences"
        )


@router.post("/preferences")
async def update_user_provider_preferences(
    request: ProviderPreferenceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user's LLM provider preferences
    """
    try:
        user_id = current_user["id"]
        
        # Validate that user has API key for preferred provider
        available_providers = await user_provider_service.get_available_providers_for_user(user_id)
        
        if request.preferred_provider not in available_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid API key found for provider: {request.preferred_provider.value}"
            )
        
        # Validate fallback providers if provided
        if request.fallback_providers:
            invalid_fallbacks = [p for p in request.fallback_providers if p not in available_providers]
            if invalid_fallbacks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No valid API keys for fallback providers: {[p.value for p in invalid_fallbacks]}"
                )
        
        # Validate quality preference
        if request.quality_preference and request.quality_preference not in ["speed", "balanced", "quality"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quality preference must be one of: speed, balanced, quality"
            )
        
        # Update preferences
        success = await user_provider_service.update_user_provider_preference(
            user_id=user_id,
            preferred_provider=request.preferred_provider,
            fallback_providers=request.fallback_providers,
            cost_optimization=request.cost_optimization,
            quality_preference=request.quality_preference
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update provider preferences"
            )
        
        return {
            "success": True,
            "message": "Provider preferences updated successfully",
            "preferred_provider": request.preferred_provider.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update provider preferences"
        )


@router.get("/available-providers")
async def get_available_providers(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """
    Get list of providers that the user has valid API keys for
    """
    try:
        user_id = current_user["id"]
        
        available_providers = await user_provider_service.get_available_providers_for_user(user_id)
        
        return {
            "success": True,
            "available_providers": [provider.value for provider in available_providers],
            "total": len(available_providers)
        }
        
    except Exception as e:
        logger.error(f"Error getting available providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available providers"
        )


@router.delete("/preferences")
async def reset_user_provider_preferences(
    current_user: dict = Depends(get_current_user)
):
    """
    Reset user's provider preferences to defaults
    """
    try:
        user_id = current_user["id"]
        
        # Get available providers and generate defaults
        available_providers = await user_provider_service.get_available_providers_for_user(user_id)
        default_preferences = user_provider_service.get_default_preferences(user_id, available_providers)
        
        success = await user_provider_service.save_user_preferences(default_preferences)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset provider preferences"
            )
        
        return {
            "success": True,
            "message": "Provider preferences reset to defaults",
            "preferred_provider": default_preferences.preferred_provider.value if default_preferences.preferred_provider else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting provider preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset provider preferences"
        )


@router.get("/recommendation")
async def get_provider_recommendation(
    request_type: str = "general",
    current_user: dict = Depends(get_current_user)
):
    """
    Get provider recommendation for a specific request type
    
    Args:
        request_type: Type of request (general, recap, query)
    """
    try:
        user_id = current_user["id"]
        
        if request_type not in ["general", "recap", "query"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request type must be one of: general, recap, query"
            )
        
        selection = await user_provider_service.get_provider_selection_for_user(user_id, request_type)
        
        return {
            "success": True,
            "request_type": request_type,
            "recommended_provider": selection.get("preferred_provider").value if selection.get("preferred_provider") else None,
            "fallback_providers": [p.value for p in selection.get("fallback_providers", [])],
            "reasoning": f"Recommended based on your {selection.get('quality_preference', 'balanced')} quality preference"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider recommendation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get provider recommendation"
        )
