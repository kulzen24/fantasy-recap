"""
Authentication API routes
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from supabase import create_client

from app.core.config import settings
from app.core.auth import get_current_user

router = APIRouter()

# Pydantic models for request/response
class UserProfile(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    preferences: dict = {}


class UserProfileResponse(BaseModel):
    id: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    preferences: dict
    created_at: datetime
    updated_at: datetime


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[dict] = None
    message: str


def get_supabase_client():
    """Get Supabase client for database operations"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration missing"
        )
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(current_user: dict = Depends(get_current_user)):
    """Get current authentication status"""
    return AuthStatusResponse(
        authenticated=True,
        user=current_user,
        message="User is authenticated"
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile information"""
    supabase = get_supabase_client()
    user_id = current_user["id"]
    
    try:
        # Get user profile from database
        result = supabase.table('user_profiles').select('*').eq('id', user_id).execute()
        
        if not result.data:
            # Create default profile if doesn't exist
            default_profile = {
                "id": user_id,
                "display_name": current_user.get("email", "").split("@")[0],
                "timezone": "UTC",
                "preferences": {}
            }
            
            create_result = supabase.table('user_profiles').insert(default_profile).execute()
            profile = create_result.data[0] if create_result.data else default_profile
        else:
            profile = result.data[0]
        
        return UserProfileResponse(**profile)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfile,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile information"""
    supabase = get_supabase_client()
    user_id = current_user["id"]
    
    try:
        # Prepare update data
        update_data = profile_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update profile in database
        result = supabase.table('user_profiles').update(update_data).eq('id', user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return UserProfileResponse(**result.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete("/profile")
async def delete_user_profile(current_user: dict = Depends(get_current_user)):
    """Delete current user's profile and all associated data"""
    supabase = get_supabase_client()
    user_id = current_user["id"]
    
    try:
        # Delete all user data (cascading delete should handle most)
        supabase.table('user_profiles').delete().eq('id', user_id).execute()
        
        return {
            "message": "Profile and associated data deleted successfully",
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


@router.get("/providers")
async def get_oauth_providers(current_user: dict = Depends(get_current_user)):
    """Get user's connected OAuth providers"""
    supabase = get_supabase_client()
    user_id = current_user["id"]
    
    try:
        result = supabase.table('user_oauth_providers').select('provider,created_at').eq('user_id', user_id).execute()
        
        return {
            "providers": result.data or [],
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve providers: {str(e)}"
        )


@router.get("/logout")
async def logout_info():
    """Information about logout (handled by frontend with Supabase)"""
    return {
        "message": "Logout should be handled by the frontend using supabase.auth.signOut()",
        "instructions": [
            "Call supabase.auth.signOut() in your frontend",
            "Clear any local state/storage",
            "Redirect to login page"
        ]
    }
