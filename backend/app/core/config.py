"""
Application configuration settings
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # LLM Providers (Optional - users provide their own keys)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_AI_API_KEY: Optional[str] = None
    
    # Fantasy Sports APIs
    YAHOO_CLIENT_ID: Optional[str] = None
    YAHOO_CLIENT_SECRET: Optional[str] = None
    ESPN_CLIENT_ID: Optional[str] = None
    ESPN_CLIENT_SECRET: Optional[str] = None
    
    # Security
    JWT_SECRET: Optional[str] = None
    ENCRYPTION_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
