"""
Simple Yahoo OAuth2 implementation for testing
"""

import json
import logging
import asyncio
import aiohttp
import os
from urllib.parse import urlencode, parse_qs
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleYahooOAuth:
    """Simple Yahoo OAuth2 implementation for testing purposes"""
    
    def __init__(self):
        self.client_id = settings.YAHOO_CLIENT_ID
        self.client_secret = settings.YAHOO_CLIENT_SECRET
        # Always use the static production domain for consistency
        # This ensures the redirect URI matches what's registered in Yahoo app
        self.redirect_uri = "https://statchat-ashen.vercel.app/api/v1/fantasy/yahoo/callback"
        
        logger.info(f"🔧 Yahoo OAuth configured with redirect_uri: {self.redirect_uri}")
        
        # OAuth URLs
        self.auth_url = "https://api.login.yahoo.com/oauth2/request_auth"
        self.token_url = "https://api.login.yahoo.com/oauth2/get_token"
        
        # Store tokens temporarily (in production, use database)
        self._access_token = None
        self._refresh_token = None
    
    def get_authorization_url(self) -> str:
        """Generate Yahoo authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "fspt-r",  # Fantasy Sports read permission
            "state": "fantasy_app_auth"
        }
        
        logger.info(f"🔧 Auth URL generation using redirect_uri: {self.redirect_uri}")
        auth_url_with_params = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"🔧 Generated auth URL: {auth_url_with_params}")
        
        return auth_url_with_params
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access token"""
        import time
        start_time = time.time()
        logger.info(f"🔄 Starting token exchange for code: {authorization_code[:10]}...")
        logger.info(f"🔧 Using redirect_uri: {self.redirect_uri}")
        
        # Use shorter timeout for faster processing to avoid code expiration
        timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
                "grant_type": "authorization_code"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Log the exact data being sent to Yahoo
            logger.info(f"🔧 Token exchange data being sent:")
            logger.info(f"   - client_id: {data['client_id'][:10]}...")
            logger.info(f"   - redirect_uri: {data['redirect_uri']}")
            logger.info(f"   - code: {data['code'][:10]}...")
            logger.info(f"   - grant_type: {data['grant_type']}")
            
            async with session.post(self.token_url, data=data, headers=headers) as response:
                elapsed = time.time() - start_time
                response_text = await response.text()
                
                if response.status == 200:
                    token_data = await response.json() if response_text else {}
                    self._access_token = token_data.get("access_token")
                    self._refresh_token = token_data.get("refresh_token")
                    
                    logger.info(f"✅ Successfully exchanged code for Yahoo access token (took {elapsed:.2f}s)")
                    return {"success": True, "token_data": token_data}
                else:
                    logger.error(f"❌ Token exchange failed after {elapsed:.2f}s: {response.status}")
                    logger.error(f"❌ Response headers: {dict(response.headers)}")
                    logger.error(f"❌ Response body: {response_text}")
                    return {"success": False, "error": f"Token exchange failed: {response_text}"}
    
    async def make_api_request(self, url: str) -> Dict:
        """Make authenticated API request to Yahoo"""
        if not self._access_token:
            return {"success": False, "error": "No access token available"}
        
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data}
                    else:
                        error_text = await response.text()
                        logger.error(f"API request failed: {response.status} - {error_text}")
                        return {"success": False, "error": f"API request failed: {error_text}"}
            except Exception as e:
                logger.error(f"API request exception: {e}")
                return {"success": False, "error": str(e)}
    
    def has_valid_token(self) -> bool:
        """Check if we have a valid access token"""
        return self._access_token is not None


# Global instance for simple testing
yahoo_oauth = SimpleYahooOAuth()
