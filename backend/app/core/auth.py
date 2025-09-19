"""
Authentication and authorization utilities
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError

from app.core.supabase import get_supabase_client_safe, get_supabase_service_client_safe

logger = logging.getLogger(__name__)

security = HTTPBearer()
# Optional bearer that does not error when Authorization header is missing
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current user from JWT token
    
    Args:
        credentials: Authorization credentials from request header
        
    Returns:
        Dict containing user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode the JWT token without verification for now
        # In production, you'd want to verify the signature using Supabase's public key
        payload = jwt.decode(token, options={"verify_signature": False})
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Add additional user info from the token
        user_info = {
            "id": user_id,  # Use 'id' as the primary key for consistency
            "sub": user_id,
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "email_verified": payload.get("email_verified", False),
            "aud": payload.get("aud"),
            "iss": payload.get("iss"),
            "iat": payload.get("iat"),
            "exp": payload.get("exp")
        }
        
        # Note: User profile should be automatically created by Supabase Auth
        # or via database triggers when user signs up
        
        return user_info
        
    except PyJWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token (optional)
    
    Args:
        credentials: Authorization credentials from request header
        
    Returns:
        Dict containing user information or None if not authenticated
    """
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def ensure_user_profile_exists(user_info: Dict[str, Any]) -> None:
    """
    Ensure user profile exists in the database, create if it doesn't exist.
    Uses service role client to bypass RLS policies.
    
    Args:
        user_info: User information from JWT token
    """
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            logger.warning("Supabase service client not available, skipping user profile creation")
            return
        
        user_id = user_info.get("id")
        if not user_id:
            logger.warning("No user ID found in user_info, skipping profile creation")
            return
        
        # Check if user profile already exists
        existing_user = supabase.table("user_profiles").select("id").eq("id", user_id).execute()
        
        if existing_user.data:
            logger.debug(f"User profile already exists for user {user_id}")
            return
        
        # Create user profile
        profile_data = {
            "id": user_id,
            "display_name": user_info.get("name"),
            "avatar_url": user_info.get("picture"),
            "timezone": "UTC",
            "preferences": {
                "email": user_info.get("email"),
                "email_verified": user_info.get("email_verified", False)
            }
        }
        
        result = supabase.table("user_profiles").insert(profile_data).execute()
        
        if result.data:
            logger.info(f"Created user profile for user {user_id}")
        else:
            logger.error(f"Failed to create user profile for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error ensuring user profile exists: {e}")
        # Don't raise exception here - we don't want to block authentication
        # if profile creation fails


def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Dict containing decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # For development, we're not verifying the signature
        # In production, you'd fetch Supabase's public key and verify
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Basic validation
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
            
        return payload
        
    except PyJWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )