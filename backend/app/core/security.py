"""
Security middleware and configurations for the FastAPI application
Implements OWASP security best practices
"""

import hashlib
import secrets
from typing import Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    Implements OWASP recommended security headers
    """
    
    def __init__(self, app, enable_hsts: bool = True, hsts_max_age: int = 31536000):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HTTP Strict Transport Security (HSTS)
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"
        
        # Content Security Policy (CSP)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com https://api.anthropic.com https://generativelanguage.googleapis.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
        
        # Cache Control for sensitive endpoints
        if any(path in str(request.url) for path in ["/api/v1/llm-keys", "/api/v1/auth", "/api/v1/provider-preferences"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Remove server identification headers
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS in production
    """
    
    def __init__(self, app, force_https: bool = False):
        super().__init__(app)
        self.force_https = force_https
    
    async def dispatch(self, request: Request, call_next):
        # Force HTTPS redirect in production
        if (self.force_https and 
            request.url.scheme == "http" and 
            not request.url.hostname in ["localhost", "127.0.0.1"]):
            
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(https_url), status_code=301)
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Simple rate limiting (in production, use Redis or similar)
        import time
        current_minute = int(time.time() // 60)
        key = f"{client_ip}:{current_minute}"
        
        if key in self.request_counts:
            self.request_counts[key] += 1
        else:
            self.request_counts[key] = 1
            
        # Clean old entries
        self.request_counts = {k: v for k, v in self.request_counts.items() 
                              if int(k.split(":")[1]) >= current_minute - 1}
        
        if self.request_counts[key] > self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return await call_next(request)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for basic input validation and sanitization
    """
    
    def __init__(self, app, max_content_length: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_content_length = max_content_length
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request entity too large"
            )
        
        # Check for common attack patterns in URLs
        suspicious_patterns = [
            "../", "..\\", "<script", "javascript:", "vbscript:", 
            "onload=", "onerror=", "alert(", "eval(", "union select",
            "drop table", "insert into", "delete from"
        ]
        
        url_str = str(request.url).lower()
        for pattern in suspicious_patterns:
            if pattern in url_str:
                logger.warning(f"Suspicious URL pattern detected: {pattern} in {request.url}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request"
                )
        
        return await call_next(request)


def generate_csp_nonce() -> str:
    """Generate a cryptographically secure nonce for CSP"""
    return secrets.token_urlsafe(16)


def calculate_sri_hash(content: str) -> str:
    """Calculate Subresource Integrity hash for external resources"""
    sha256_hash = hashlib.sha256(content.encode()).digest()
    import base64
    return f"sha256-{base64.b64encode(sha256_hash).decode()}"


def validate_api_key_format(api_key: str, provider: str) -> bool:
    """
    Validate API key format for different providers
    """
    if not api_key or len(api_key) < 10:
        return False
    
    # Provider-specific validation
    if provider == "openai":
        return api_key.startswith("sk-") and len(api_key) > 20
    elif provider == "anthropic":
        return api_key.startswith("sk-ant-") and len(api_key) > 30
    elif provider == "google":
        return len(api_key) > 20  # Google API keys don't have a specific prefix
    
    return True


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks
    """
    if not input_str:
        return ""
    
    # Truncate if too long
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "\"", "'", "&", ";", "(", ")", "\\"]
    for char in dangerous_chars:
        input_str = input_str.replace(char, "")
    
    return input_str.strip()


class SecurityConfig:
    """
    Security configuration class
    """
    
    def __init__(self):
        self.enable_hsts = True
        self.hsts_max_age = 31536000  # 1 year
        self.force_https = False  # Set to True in production
        self.rate_limit_per_minute = 60
        self.max_content_length = 10 * 1024 * 1024  # 10MB
        self.session_timeout = 3600  # 1 hour
        self.password_min_length = 8
        self.require_mfa = False  # Set to True for high-security environments
    
    @property
    def cors_allowed_origins(self) -> List[str]:
        """Get CORS allowed origins based on environment"""
        # In production, this should be more restrictive
        return [
            "http://localhost:3000",
            "https://localhost:3000",
            "https://*.vercel.app",
            "https://*.netlify.app"
        ]
    
    @property
    def trusted_hosts(self) -> List[str]:
        """Get trusted hosts based on environment"""
        return [
            "localhost",
            "127.0.0.1",
            "*.vercel.app",
            "*.netlify.app",
            "*.supabase.co"
        ]


# Global security configuration
security_config = SecurityConfig()
