"""
User Profile Service
Handles user profile creation, updates, and management
"""

import logging
from typing import Optional
from datetime import datetime

from app.core.supabase import get_supabase_client_safe
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for managing user profiles"""
    
    def __init__(self):
        self.supabase = get_supabase_client_safe()
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile or None if not found
        """
        if not self.supabase:
            logger.warning("Supabase client not available, returning None for user profile")
            return None
            
        try:
            response = self.supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                data = response.data[0]
                return UserProfile(
                    id=data["id"],
                    display_name=data.get("display_name"),
                    avatar_url=data.get("avatar_url"),
                    timezone=data.get("timezone", "UTC"),
                    preferences=data.get("preferences", {}),
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {e}")
            return None
    
    async def create_profile(self, profile_data: UserProfileCreate) -> Optional[UserProfile]:
        """
        Create a new user profile
        
        Args:
            profile_data: Profile creation data
            
        Returns:
            UserProfile or None if creation failed
        """
        if not self.supabase:
            logger.warning("Supabase client not available, cannot create user profile")
            return None
            
        try:
            now = datetime.utcnow().isoformat()
            data = {
                "id": profile_data.id,
                "display_name": profile_data.display_name,
                "avatar_url": profile_data.avatar_url,
                "timezone": profile_data.timezone,
                "preferences": profile_data.preferences,
                "created_at": now,
                "updated_at": now
            }
            
            response = self.supabase.table("user_profiles").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                created_data = response.data[0]
                logger.info(f"Created user profile for {profile_data.id}")
                return UserProfile(
                    id=created_data["id"],
                    display_name=created_data.get("display_name"),
                    avatar_url=created_data.get("avatar_url"),
                    timezone=created_data.get("timezone", "UTC"),
                    preferences=created_data.get("preferences", {}),
                    created_at=datetime.fromisoformat(created_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(created_data["updated_at"].replace("Z", "+00:00"))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create user profile for {profile_data.id}: {e}")
            return None
    
    async def update_profile(self, user_id: str, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_data: Profile update data
            
        Returns:
            UserProfile or None if update failed
        """
        if not self.supabase:
            logger.warning("Supabase client not available, cannot update user profile")
            return None
            
        try:
            # Build update data, only including non-None values
            update_data = {"updated_at": datetime.utcnow().isoformat()}
            
            if profile_data.display_name is not None:
                update_data["display_name"] = profile_data.display_name
            if profile_data.avatar_url is not None:
                update_data["avatar_url"] = profile_data.avatar_url
            if profile_data.timezone is not None:
                update_data["timezone"] = profile_data.timezone
            if profile_data.preferences is not None:
                update_data["preferences"] = profile_data.preferences
            
            response = self.supabase.table("user_profiles").update(update_data).eq("id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                updated_data = response.data[0]
                logger.info(f"Updated user profile for {user_id}")
                return UserProfile(
                    id=updated_data["id"],
                    display_name=updated_data.get("display_name"),
                    avatar_url=updated_data.get("avatar_url"),
                    timezone=updated_data.get("timezone", "UTC"),
                    preferences=updated_data.get("preferences", {}),
                    created_at=datetime.fromisoformat(updated_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(updated_data["updated_at"].replace("Z", "+00:00"))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to update user profile for {user_id}: {e}")
            return None
    
    async def delete_profile(self, user_id: str) -> bool:
        """
        Delete user profile
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if deleted successfully
        """
        if not self.supabase:
            logger.warning("Supabase client not available, cannot delete user profile")
            return False
            
        try:
            response = self.supabase.table("user_profiles").delete().eq("id", user_id).execute()
            
            if response.data is not None:
                logger.info(f"Deleted user profile for {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete user profile for {user_id}: {e}")
            return False
