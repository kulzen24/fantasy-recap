"""
Yahoo Fantasy API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from app.core.auth import require_authentication
from app.services.fantasy.yahoo_service import YahooFantasyService
from app.models.fantasy import FantasyApiResponse, League, Team, Matchup

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/test")
async def test_yahoo_connection():
    """Test Yahoo Fantasy API connection (public endpoint for testing)"""
    try:
        service = YahooFantasyService()
        return {
            "message": "Yahoo Fantasy API service initialized",
            "platform": service.platform.value,
            "status": "ready"
        }
    except Exception as e:
        logger.error(f"Yahoo API test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Yahoo API test failed: {str(e)}")


@router.get("/leagues")
async def get_user_leagues(
    year: int = 2024,
    current_user: dict = Depends(require_authentication)
):
    """Get all Yahoo Fantasy leagues for the authenticated user"""
    try:
        # Initialize service with user's stored credentials
        # In production, you'd retrieve OAuth tokens from the database
        service = YahooFantasyService()
        
        # Check if user has Yahoo credentials stored
        # This would typically come from the user's profile/settings
        if not service.consumer_key or not service.consumer_secret:
            raise HTTPException(
                status_code=400, 
                detail="Yahoo Fantasy credentials not configured. Please link your Yahoo account."
            )
        
        response = await service.get_user_leagues(year=year)
        
        if response.success:
            return {
                "success": True,
                "data": response.data,
                "platform": response.platform.value,
                "timestamp": response.timestamp
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        logger.error(f"Failed to get Yahoo leagues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues/{league_id}")
async def get_league_details(
    league_id: str,
    year: int = 2024,
    current_user: dict = Depends(require_authentication)
):
    """Get detailed information for a specific Yahoo Fantasy league"""
    try:
        service = YahooFantasyService()
        response = await service.get_league(league_id, year=year)
        
        if response.success:
            return {
                "success": True,
                "data": response.data,
                "platform": response.platform.value,
                "timestamp": response.timestamp
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        logger.error(f"Failed to get Yahoo league {league_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues/{league_id}/matchups")
async def get_league_matchups(
    league_id: str,
    week: int,
    year: int = 2024,
    current_user: dict = Depends(require_authentication)
):
    """Get matchups for a specific week in a Yahoo Fantasy league"""
    try:
        service = YahooFantasyService()
        response = await service.get_matchups(league_id, week=week, year=year)
        
        if response.success:
            return {
                "success": True,
                "data": response.data,
                "platform": response.platform.value,
                "timestamp": response.timestamp
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        logger.error(f"Failed to get Yahoo matchups for league {league_id}, week {week}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues/{league_id}/teams/{team_id}/roster")
async def get_team_roster(
    league_id: str,
    team_id: str,
    week: Optional[int] = None,
    current_user: dict = Depends(require_authentication)
):
    """Get roster for a specific team in a Yahoo Fantasy league"""
    try:
        service = YahooFantasyService()
        response = await service.get_team_roster(league_id, team_id, week=week)
        
        if response.success:
            return {
                "success": True,
                "data": response.data,
                "platform": response.platform.value,
                "timestamp": response.timestamp
            }
        else:
            raise HTTPException(status_code=400, detail=response.error)
            
    except Exception as e:
        logger.error(f"Failed to get Yahoo roster for team {team_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/authenticate")
async def initiate_oauth(
    current_user: dict = Depends(require_authentication)
):
    """Initiate Yahoo Fantasy OAuth authentication flow"""
    try:
        # In a real implementation, this would:
        # 1. Generate OAuth state parameter
        # 2. Store state in user session/database  
        # 3. Return authorization URL for frontend redirect
        # 4. Handle OAuth callback to exchange code for tokens
        # 5. Store tokens securely in user profile
        
        return {
            "message": "Yahoo OAuth implementation needed",
            "next_steps": [
                "Generate OAuth state parameter",
                "Create authorization URL", 
                "Handle OAuth callback",
                "Store tokens securely"
            ],
            "authorization_url": "https://api.login.yahoo.com/oauth2/request_auth",
            "callback_url": "/api/v1/fantasy/yahoo/callback"
        }
        
    except Exception as e:
        logger.error(f"Yahoo OAuth initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
