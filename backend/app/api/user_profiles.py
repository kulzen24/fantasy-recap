"""
User Profile API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from app.core.auth import get_current_user
from app.services.user_profile_service import UserProfileService
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/profile", tags=["user-profiles"])

# Initialize the service
user_profile_service = UserProfileService()


@router.get("/me")
async def get_my_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> UserProfile:
    """Get current user's profile"""
    try:
        user_id = current_user["sub"]
        profile = await user_profile_service.get_profile(user_id)
        
        if not profile:
            # Auto-create profile if it doesn't exist
            profile_data = UserProfileCreate(
                id=user_id,
                display_name=current_user.get("name") or current_user.get("email", "").split("@")[0],
                avatar_url=current_user.get("picture"),
                timezone="UTC"
            )
            profile = await user_profile_service.create_profile(profile_data)
            
        return profile
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")


@router.post("/")
async def create_profile(
    profile_data: UserProfileCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfile:
    """Create user profile"""
    try:
        user_id = current_user["sub"]
        
        # Ensure the profile is created for the current user
        profile_data.id = user_id
        
        profile = await user_profile_service.create_profile(profile_data)
        return profile
        
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user profile")


@router.put("/")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserProfile:
    """Update user profile"""
    try:
        user_id = current_user["sub"]
        
        profile = await user_profile_service.update_profile(user_id, profile_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")


@router.delete("/")
async def delete_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete user profile"""
    try:
        user_id = current_user["sub"]
        
        success = await user_profile_service.delete_profile(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        return {"message": "Profile deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user profile")
