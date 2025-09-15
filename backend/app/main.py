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
from app.api.auth import router as auth_router
from app.api.fantasy.yahoo import router as yahoo_router

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app", "*.supabase.co"]
)

# Mount static files for OAuth testing
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routes
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(yahoo_router, prefix=f"{settings.API_V1_STR}/fantasy/yahoo", tags=["fantasy", "yahoo"])

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
