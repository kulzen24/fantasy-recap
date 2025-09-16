"""
Fantasy Football Recap Generator - FastAPI Backend
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.core.config import settings
from app.core.auth import get_current_user, require_authentication, optional_authentication
from app.core.security import (
    SecurityHeadersMiddleware, HTTPSRedirectMiddleware, RateLimitMiddleware, 
    InputValidationMiddleware, security_config
)
from app.api.auth import router as auth_router
from app.api.fantasy.yahoo import router as yahoo_router
from app.api.user_leagues import router as user_leagues_router
from app.api.llm_keys import router as llm_keys_router
from app.api.nlq import router as nlq_router
from app.api.provider_preferences import router as provider_preferences_router
from app.api.security import router as security_router
from app.api.templates import router as templates_router
from app.api.recaps import router as recaps_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Fantasy Football Recap Generator with Supabase Authentication",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Security Middleware (order matters - add security middleware first)
app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=security_config.enable_hsts,
    hsts_max_age=security_config.hsts_max_age
)

app.add_middleware(
    HTTPSRedirectMiddleware,
    force_https=security_config.force_https
)

app.add_middleware(
    InputValidationMiddleware,
    max_content_length=security_config.max_content_length
)

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=security_config.rate_limit_per_minute
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=security_config.trusted_hosts
)

# Configure CORS (after security middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# Mount static files for OAuth testing
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routes
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(yahoo_router, prefix=f"{settings.API_V1_STR}/fantasy/yahoo", tags=["fantasy", "yahoo"])
app.include_router(user_leagues_router, prefix=f"{settings.API_V1_STR}/leagues", tags=["leagues", "user-management"])
app.include_router(llm_keys_router, prefix=f"{settings.API_V1_STR}/llm-keys", tags=["llm", "api-keys"])
app.include_router(nlq_router, prefix=f"{settings.API_V1_STR}/nlq", tags=["natural-language", "queries"])
app.include_router(provider_preferences_router, prefix=f"{settings.API_V1_STR}/provider-preferences", tags=["llm", "preferences"])
app.include_router(security_router, prefix=f"{settings.API_V1_STR}/security", tags=["security", "monitoring"])
app.include_router(templates_router, prefix=f"{settings.API_V1_STR}/templates", tags=["templates", "style-analysis"])
app.include_router(recaps_router, prefix=f"{settings.API_V1_STR}/recaps", tags=["recaps", "generation"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fantasy Recaps API",
        "version": settings.API_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "authentication": "Supabase Auth"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Fantasy Recaps API is running",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": os.sys.version,
        "environment": settings.ENVIRONMENT,
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)
    }


@app.get(f"{settings.API_V1_STR}")
async def api_info():
    """API version information"""
    return {
        "message": "Fantasy Recaps API v1",
        "version": settings.API_VERSION,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "api": settings.API_V1_STR,
            "auth": f"{settings.API_V1_STR}/auth"
        },
        "authentication": "Bearer token required for protected endpoints"
    }


@app.get(f"{settings.API_V1_STR}/me")
async def get_current_user_info(current_user: dict = Depends(require_authentication)):
    """Get current authenticated user information"""
    return {
        "user": current_user,
        "message": "Successfully authenticated"
    }


@app.get(f"{settings.API_V1_STR}/protected")
async def protected_endpoint(current_user: dict = Depends(require_authentication)):
    """Example protected endpoint that requires authentication"""
    return {
        "message": f"Hello {current_user.get('email', 'User')}!",
        "user_id": current_user.get("id"),
        "authenticated": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get(f"{settings.API_V1_STR}/public")
async def public_endpoint(current_user: dict = Depends(optional_authentication)):
    """Example public endpoint that works with or without authentication"""
    if current_user:
        return {
            "message": f"Hello {current_user.get('email', 'authenticated user')}!",
            "authenticated": True,
            "user_id": current_user.get("id")
        }
    else:
        return {
            "message": "Hello anonymous user!",
            "authenticated": False
        }


# Future API Routes will be added here
# from app.api.leagues import router as leagues_router
# from app.api.recaps import router as recaps_router
# app.include_router(leagues_router, prefix=f"{settings.API_V1_STR}/leagues", tags=["leagues"])
# app.include_router(recaps_router, prefix=f"{settings.API_V1_STR}/recaps", tags=["recaps"])


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["app"]
    )
