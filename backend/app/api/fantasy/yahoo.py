"""
Yahoo Fantasy API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from typing import Optional, List
import logging
from pydantic import BaseModel

from app.core.auth import require_authentication, optional_authentication
from app.services.fantasy.yahoo_service import YahooFantasyService
from app.services.fantasy.yahoo_oauth_simple import yahoo_oauth
from app.models.fantasy import FantasyApiResponse, League, Team, Matchup

logger = logging.getLogger(__name__)

router = APIRouter()

class OAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


@router.get("/auth-page")
async def get_auth_page():
    """Serve the OAuth testing page"""
    try:
        with open("app/static/yahoo_auth.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Auth page not found")


@router.get("/auth-url")
async def get_auth_url():
    """Get Yahoo OAuth2 authorization URL"""
    try:
        auth_url = yahoo_oauth.get_authorization_url()
        return {
            "success": True,
            "auth_url": auth_url,
            "message": "Redirect user to this URL for Yahoo authorization"
        }
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback from Yahoo (GET method for direct browser redirects)"""
    try:
        # Extract code from query parameters
        code = request.query_params.get('code')
        error = request.query_params.get('error')
        
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        # Exchange code for token
        result = await yahoo_oauth.exchange_code_for_token(code)
        
        if result["success"]:
            # Return success page or redirect to frontend
            return HTMLResponse(content=f"""
                <html>
                    <body>
                        <h2>✅ Yahoo Authorization Successful!</h2>
                        <p>You can now close this window and return to the main application.</p>
                        <p>Authorization code: <code>{code}</code></p>
                        <script>
                            // Auto-close window if opened in popup
                            if (window.opener) {{
                                window.opener.postMessage({{
                                    type: 'yahoo_auth_success',
                                    code: '{code}'
                                }}, '*');
                                window.close();
                            }}
                        </script>
                    </body>
                </html>
            """)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback")
async def oauth_callback_post(callback_data: OAuthCallbackRequest):
    """Handle OAuth callback via POST (for API clients)"""
    try:
        result = await yahoo_oauth.exchange_code_for_token(callback_data.code)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Token exchanged successfully",
                "token": "session_token_placeholder"  # In production, return session token
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    current_user: dict = Depends(optional_authentication)
):
    """Get all Yahoo Fantasy leagues for the authenticated user"""
    try:
        # Check if OAuth token is available
        if not yahoo_oauth.has_valid_token():
            raise HTTPException(
                status_code=401, 
                detail="No valid Yahoo OAuth token. Please complete OAuth flow first."
            )
        
        # Make direct API call to Yahoo Fantasy API
        leagues_url = f"https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nfl/leagues?format=json"
        result = await yahoo_oauth.make_api_request(leagues_url)
        
        if result["success"]:
            # Parse Yahoo's nested response structure
            yahoo_data = result["data"]
            
            # Extract leagues from Yahoo's complex nested structure
            leagues = []
            try:
                users_data = yahoo_data.get("fantasy_content", {}).get("users", {})
                if "0" in users_data and "user" in users_data["0"]:
                    user_games = users_data["0"]["user"][1].get("games", {})
                    if "0" in user_games and "game" in user_games["0"]:
                        game_leagues = user_games["0"]["game"][1].get("leagues", {})
                        for key, league_data in game_leagues.items():
                            if key.isdigit() and "league" in league_data:
                                league_info = league_data["league"][0]
                                leagues.append({
                                    "league_id": league_info.get("league_key", ""),
                                    "name": league_info.get("name", "Unknown League"),
                                    "season": league_info.get("season", year),
                                    "num_teams": league_info.get("num_teams"),
                                    "url": league_info.get("url", "")
                                })
            except Exception as parse_error:
                logger.warning(f"Failed to parse leagues data: {parse_error}")
                # Return raw data if parsing fails
                return {
                    "success": True,
                    "data": yahoo_data,
                    "message": "Raw Yahoo API response (parsing failed)",
                    "platform": "yahoo"
                }
            
            return {
                "success": True,
                "data": leagues,
                "platform": "yahoo",
                "message": f"Found {len(leagues)} leagues"
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Failed to get Yahoo leagues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues/{league_id}")
async def get_league_details(
    league_id: str,
    current_user: dict = Depends(optional_authentication)
):
    """Get detailed information for a specific Yahoo Fantasy league"""
    try:
        # Check if OAuth token is available
        if not yahoo_oauth.has_valid_token():
            raise HTTPException(
                status_code=401, 
                detail="No valid Yahoo OAuth token. Please complete OAuth flow first."
            )
        
        # Make direct API call to get league details and teams
        league_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_id}/teams?format=json"
        result = await yahoo_oauth.make_api_request(league_url)
        
        if result["success"]:
            yahoo_data = result["data"]
            
            # Parse league and teams data
            try:
                fantasy_content = yahoo_data.get("fantasy_content", {})
                league_data = fantasy_content.get("league", [{}])[0]
                
                # Extract league info
                league_info = {
                    "league_id": league_data.get("league_key", league_id),
                    "name": league_data.get("name", "Unknown League"),
                    "season": league_data.get("season"),
                    "num_teams": league_data.get("num_teams"),
                    "current_week": league_data.get("current_week"),
                    "teams": []
                }
                
                # Extract teams info
                teams_data = league_data.get("teams", {})
                for key, team_data in teams_data.items():
                    if key.isdigit() and "team" in team_data:
                        team_info = team_data["team"][0]
                        managers = team_data["team"][1].get("managers", [{}])
                        manager_name = managers[0].get("manager", {}).get("nickname", "Unknown") if managers else "Unknown"
                        
                        league_info["teams"].append({
                            "team_id": team_info.get("team_key", ""),
                            "name": team_info.get("name", "Unknown Team"),
                            "manager_name": manager_name,
                            "wins": team_info.get("team_standings", {}).get("outcome_totals", {}).get("wins"),
                            "losses": team_info.get("team_standings", {}).get("outcome_totals", {}).get("losses"),
                            "points_for": team_info.get("team_standings", {}).get("points_for"),
                            "points_against": team_info.get("team_standings", {}).get("points_against")
                        })
                
                return {
                    "success": True,
                    "data": league_info,
                    "platform": "yahoo",
                    "message": f"League '{league_info['name']}' with {len(league_info['teams'])} teams"
                }
                
            except Exception as parse_error:
                logger.warning(f"Failed to parse league data: {parse_error}")
                # Return raw data if parsing fails
                return {
                    "success": True,
                    "data": yahoo_data,
                    "message": "Raw Yahoo API response (parsing failed)",
                    "platform": "yahoo"
                }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
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
