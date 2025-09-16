"""
User Provider Configuration Service
Handles user-specific LLM provider preferences and routing
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from app.models.llm import LLMProvider, ProviderConfig
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


@dataclass
class UserProviderPreference:
    """User's provider preference configuration"""
    user_id: str
    preferred_provider: LLMProvider
    fallback_providers: List[LLMProvider]
    cost_optimization: bool = False  # Whether to prefer cheaper providers
    quality_preference: str = "balanced"  # "speed", "balanced", "quality"
    created_at: datetime = None
    updated_at: datetime = None


class UserProviderConfigService:
    """Service for managing user-specific provider configurations"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_user_preferences(self, user_id: str) -> Optional[UserProviderPreference]:
        """
        Get user's provider preferences from database
        
        Args:
            user_id: User ID
            
        Returns:
            UserProviderPreference or None if not found
        """
        try:
            response = self.supabase.table("user_provider_preferences").select("*").eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                data = response.data[0]
                return UserProviderPreference(
                    user_id=data["user_id"],
                    preferred_provider=LLMProvider(data["preferred_provider"]),
                    fallback_providers=[LLMProvider(p) for p in data.get("fallback_providers", [])],
                    cost_optimization=data.get("cost_optimization", False),
                    quality_preference=data.get("quality_preference", "balanced"),
                    created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
                    updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return None
    
    async def save_user_preferences(self, preferences: UserProviderPreference) -> bool:
        """
        Save user's provider preferences to database
        
        Args:
            preferences: User preferences to save
            
        Returns:
            bool: True if saved successfully
        """
        try:
            data = {
                "user_id": preferences.user_id,
                "preferred_provider": preferences.preferred_provider.value,
                "fallback_providers": [p.value for p in preferences.fallback_providers],
                "cost_optimization": preferences.cost_optimization,
                "quality_preference": preferences.quality_preference,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upsert (insert or update)
            response = self.supabase.table("user_provider_preferences").upsert(data).execute()
            
            if response.data:
                logger.info(f"Saved provider preferences for user {preferences.user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
            return False
    
    async def get_available_providers_for_user(self, user_id: str) -> List[LLMProvider]:
        """
        Get list of providers that the user has API keys for
        
        Args:
            user_id: User ID
            
        Returns:
            List[LLMProvider]: Available providers for user
        """
        try:
            # Query user's API keys
            response = self.supabase.table("user_llm_api_keys").select("provider").eq("user_id", user_id).eq("is_valid", True).execute()
            
            if response.data:
                return [LLMProvider(row["provider"]) for row in response.data]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get available providers for user {user_id}: {e}")
            return []
    
    def get_default_preferences(self, user_id: str, available_providers: List[LLMProvider]) -> UserProviderPreference:
        """
        Generate default preferences for a user
        
        Args:
            user_id: User ID
            available_providers: List of providers user has keys for
            
        Returns:
            UserProviderPreference: Default preferences
        """
        # Default provider preference order (can be customized)
        preferred_order = [
            LLMProvider.ANTHROPIC,  # Often best for creative writing
            LLMProvider.OPENAI,     # Good general purpose
            LLMProvider.GOOGLE      # Most cost-effective
        ]
        
        # Find first available provider from preferred order
        preferred = None
        for provider in preferred_order:
            if provider in available_providers:
                preferred = provider
                break
        
        # If no preferred provider found, use first available
        if not preferred and available_providers:
            preferred = available_providers[0]
        
        # Set fallback order (other available providers)
        fallbacks = [p for p in available_providers if p != preferred]
        
        return UserProviderPreference(
            user_id=user_id,
            preferred_provider=preferred or LLMProvider.OPENAI,  # Default fallback
            fallback_providers=fallbacks,
            cost_optimization=False,
            quality_preference="balanced"
        )
    
    async def get_provider_selection_for_user(
        self, 
        user_id: str, 
        request_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Get provider selection strategy for a user based on their preferences
        
        Args:
            user_id: User ID
            request_type: Type of request ("recap", "query", "general")
            
        Returns:
            Dict with provider selection info
        """
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            available_providers = await self.get_available_providers_for_user(user_id)
            
            # Use defaults if no preferences set
            if not preferences:
                preferences = self.get_default_preferences(user_id, available_providers)
            
            # Filter preferences by available providers
            preferred_provider = preferences.preferred_provider if preferences.preferred_provider in available_providers else None
            fallback_providers = [p for p in preferences.fallback_providers if p in available_providers]
            
            # Adjust selection based on request type and quality preference
            if request_type == "recap" and preferences.quality_preference == "quality":
                # For high-quality recaps, prefer Anthropic or OpenAI
                quality_providers = [LLMProvider.ANTHROPIC, LLMProvider.OPENAI]
                for provider in quality_providers:
                    if provider in available_providers:
                        preferred_provider = provider
                        break
            
            elif request_type == "query" and preferences.cost_optimization:
                # For cost-optimized queries, prefer Google
                if LLMProvider.GOOGLE in available_providers:
                    preferred_provider = LLMProvider.GOOGLE
            
            return {
                "preferred_provider": preferred_provider,
                "fallback_providers": fallback_providers,
                "available_providers": available_providers,
                "cost_optimization": preferences.cost_optimization,
                "quality_preference": preferences.quality_preference,
                "has_preferences": preferences is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to get provider selection for user {user_id}: {e}")
            return {
                "preferred_provider": LLMProvider.OPENAI,
                "fallback_providers": [],
                "available_providers": [],
                "cost_optimization": False,
                "quality_preference": "balanced",
                "has_preferences": False
            }
    
    async def update_user_provider_preference(
        self, 
        user_id: str, 
        preferred_provider: LLMProvider,
        fallback_providers: Optional[List[LLMProvider]] = None,
        cost_optimization: Optional[bool] = None,
        quality_preference: Optional[str] = None
    ) -> bool:
        """
        Update specific user preference fields
        
        Args:
            user_id: User ID
            preferred_provider: New preferred provider
            fallback_providers: New fallback provider list
            cost_optimization: Whether to optimize for cost
            quality_preference: Quality preference level
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Get existing preferences or create new
            existing = await self.get_user_preferences(user_id)
            available_providers = await self.get_available_providers_for_user(user_id)
            
            if not existing:
                existing = self.get_default_preferences(user_id, available_providers)
            
            # Update fields if provided
            if preferred_provider:
                existing.preferred_provider = preferred_provider
            if fallback_providers is not None:
                existing.fallback_providers = fallback_providers
            if cost_optimization is not None:
                existing.cost_optimization = cost_optimization
            if quality_preference is not None:
                existing.quality_preference = quality_preference
            
            return await self.save_user_preferences(existing)
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False


# Global service instance
user_provider_service = UserProviderConfigService()
