"""
Authentication utilities for Supabase JWT validation
"""

import jwt
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

# Security scheme for FastAPI
security = HTTPBearer()


class AuthenticationError(Exception):
    """Authentication-related errors"""
    pass


def verify_supabase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify Supabase JWT token and return user payload
    
    Args:
        credentials: HTTP Authorization credentials containing the Bearer token
        
    Returns:
        Dict containing user information from JWT payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )
    
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
        
        # Extract user ID (required)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def get_current_user(token_payload: Dict[str, Any] = Depends(verify_supabase_token)) -> Dict[str, Any]:
    """
    Extract current user information from verified JWT token
    
    Args:
        token_payload: Verified JWT payload from verify_supabase_token
        
    Returns:
        Dict containing user information
    """
    return {
        "id": token_payload.get("sub"),
        "email": token_payload.get("email"),
        "role": token_payload.get("role", "authenticated"),
        "aud": token_payload.get("aud"),
        "exp": token_payload.get("exp"),
        "iat": token_payload.get("iat"),
    }


def get_current_user_id(token_payload: Dict[str, Any] = Depends(verify_supabase_token)) -> str:
    """
    Extract current user ID from verified JWT token
    
    Args:
        token_payload: Verified JWT payload from verify_supabase_token
        
    Returns:
        User ID string
    """
    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    return user_id


def require_authentication(token_payload: Dict[str, Any] = Depends(verify_supabase_token)) -> Dict[str, Any]:
    """
    Require authentication for protected endpoints
    
    Args:
        token_payload: Verified JWT payload from verify_supabase_token
        
    Returns:
        Dict containing user information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    role = token_payload.get("role")
    if role != "authenticated":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return get_current_user(token_payload)


# Optional dependency for endpoints that can work with or without auth
def optional_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication for endpoints that work with or without auth
    
    Args:
        credentials: Optional HTTP Authorization credentials
        
    Returns:
        User information dict if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return verify_supabase_token(credentials)
    except HTTPException:
        return None
