"""
User Profile data models
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class UserProfileBase(BaseModel):
    """Base user profile model"""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: str = "UTC"
    preferences: Dict[str, Any] = {}


class UserProfileCreate(UserProfileBase):
    """User profile creation model"""
    id: str  # User ID from Supabase auth


class UserProfileUpdate(UserProfileBase):
    """User profile update model"""
    pass


class UserProfile(UserProfileBase):
    """Complete user profile model"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
