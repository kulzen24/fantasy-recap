"""
Fantasy Football Recap Generator - FastAPI Backend
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Fantasy Recaps API",
    description="Backend API for Fantasy Football Recap Generator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.vercel.app"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Fantasy Recaps API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Fantasy Recaps API is running",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": os.sys.version,
        "environment": os.getenv("ENVIRONMENT", "development")
    }


@app.get("/api/v1")
async def api_info():
    """API version information"""
    return {
        "message": "Fantasy Recaps API v1",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api/v1"
        }
    }


# API Routes will be added here
# from app.api.auth import router as auth_router
# from app.api.leagues import router as leagues_router
# from app.api.recaps import router as recaps_router

# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(leagues_router, prefix="/api/v1/leagues", tags=["leagues"])
# app.include_router(recaps_router, prefix="/api/v1/recaps", tags=["recaps"])


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
