"""
Simple Yahoo OAuth2 implementation for testing
"""

import json
import logging
import asyncio
import aiohttp
from urllib.parse import urlencode, parse_qs
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SimpleYahooOAuth:
    """Simple Yahoo OAuth2 implementation for testing purposes"""
    
    def __init__(self):
        self.client_id = settings.YAHOO_CLIENT_ID
        self.client_secret = settings.YAHOO_CLIENT_SECRET
        self.redirect_uri = "http://localhost:8000/api/v1/fantasy/yahoo/callback"
        
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
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access token"""
        async with aiohttp.ClientSession() as session:
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
            
            async with session.post(self.token_url, data=data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self._access_token = token_data.get("access_token")
                    self._refresh_token = token_data.get("refresh_token")
                    
                    logger.info("Successfully exchanged code for Yahoo access token")
                    return {"success": True, "token_data": token_data}
                else:
                    error_text = await response.text()
                    logger.error(f"Token exchange failed: {response.status} - {error_text}")
                    return {"success": False, "error": f"Token exchange failed: {error_text}"}
    
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
