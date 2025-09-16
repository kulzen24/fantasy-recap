"""
User League Management API endpoints
Handles connecting, managing, and syncing user's fantasy leagues
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.core.auth import get_current_user
from app.core.supabase import get_supabase_client_safe, get_supabase_service_client_safe
from app.services.fantasy.yahoo_service import YahooFantasyService
from app.services.fantasy.yahoo_oauth_simple import yahoo_oauth
from app.models.fantasy import FantasyPlatform
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class LeagueConnectionRequest(BaseModel):
    platform: str
    oauth_tokens: Optional[Dict[str, Any]] = None


class LeagueUpdateRequest(BaseModel):
    league_name: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


@router.get("/")
async def get_user_leagues(
    season: int = 2024,
    platform: Optional[str] = None,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Get all fantasy leagues for the authenticated user"""
    try:
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Build query
        query = supabase.table("fantasy_leagues").select("*").eq("user_id", current_user["id"])
        
        if platform:
            query = query.eq("platform", platform.lower())
        
        if active_only:
            query = query.eq("is_active", True)
        
        query = query.eq("season", season).order("created_at", desc=True)
        
        response = query.execute()
        
        if response.data:
            logger.info(f"Retrieved {len(response.data)} leagues for user {current_user['id']}")
            return {
                "success": True,
                "leagues": response.data,
                "data": response.data,  # Keep for backward compatibility
                "count": len(response.data)
            }
        else:
            return {
                "success": True,
                "leagues": [],
                "data": [],  # Keep for backward compatibility
                "count": 0,
                "message": "No leagues found for user"
            }
            
    except Exception as e:
        logger.error(f"Failed to get user leagues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve leagues: {str(e)}"
        )


@router.post("/")
async def add_test_league(
    league_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Add a test league for development/testing purposes"""
    try:
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Create league record
        insert_data = {
            "user_id": current_user["id"],
            "platform": league_data.get("platform", "test"),
            "league_id": league_data.get("league_id", f"test_{int(datetime.now().timestamp())}"),
            "league_name": league_data.get("league_name", "Test League"),
            "season": league_data.get("season", 2024),
            "is_active": league_data.get("is_active", True),
            "league_data": league_data.get("league_data", {})
        }
        
        response = supabase.table("fantasy_leagues").insert(insert_data).execute()
        
        if response.data:
            logger.info(f"Added test league {insert_data['league_name']} for user {current_user['id']}")
            return {
                "success": True,
                "league": response.data[0],
                "data": response.data[0],  # Keep for backward compatibility
                "message": f"Test league '{insert_data['league_name']}' added successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add test league"
            )
            
    except Exception as e:
        logger.error(f"Failed to add test league: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add test league: {str(e)}"
        )


@router.post("/connect/{platform}")
async def connect_platform_leagues(
    platform: str,
    request: LeagueConnectionRequest,
    season: int = 2024,
    current_user: dict = Depends(get_current_user)
):
    """Connect and sync leagues from a fantasy platform"""
    try:
        platform_lower = platform.lower()
        
        if platform_lower not in ['yahoo', 'espn', 'sleeper']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}"
            )
        
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Initialize platform service
        if platform_lower == 'yahoo':
            # Check if we have a valid OAuth token from the simple OAuth flow
            if not yahoo_oauth.has_valid_token():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No valid Yahoo OAuth token. Please complete OAuth flow first."
                )
            
            # Get user's leagues from Yahoo using direct API call
            leagues_url = f"https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nfl/leagues?format=json"
            result = await yahoo_oauth.make_api_request(leagues_url)
            
            if not result["success"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch leagues from Yahoo: {result['error']}"
                )
            
            # Parse Yahoo's response to extract leagues
            leagues_data = []
            try:
                yahoo_data = result["data"]
                users_data = yahoo_data.get("fantasy_content", {}).get("users", {})
                
                if "0" in users_data and "user" in users_data["0"]:
                    user_games = users_data["0"]["user"][1].get("games", {})
                    if "0" in user_games and "game" in user_games["0"]:
                        game_leagues = user_games["0"]["game"][1].get("leagues", {})
                        
                        for key, league_data in game_leagues.items():
                            if key.isdigit() and "league" in league_data:
                                league_info = league_data["league"][0]
                                
                                # Create a simplified league object that matches expected structure
                                league_obj = type('League', (), {
                                    'platform_id': league_info.get("league_key", ""),
                                    'name': league_info.get("name", "Unknown League"),
                                    'total_teams': league_info.get("num_teams", 0),
                                    'current_week': league_info.get("current_week", 1),
                                    'scoring_type': 'standard',  # Default
                                    'teams': [],  # Empty for now
                                    'metadata': league_info
                                })()
                                
                                leagues_data.append(league_obj)
                                
            except Exception as parse_error:
                logger.error(f"Failed to parse Yahoo leagues response: {parse_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to parse Yahoo leagues data"
                )
            connected_leagues = []
            
            for league in leagues_data:
                try:
                    # Check if league already exists
                    existing_query = supabase.table("fantasy_leagues").select("id").eq(
                        "user_id", current_user["id"]
                    ).eq("platform", platform_lower).eq(
                        "league_id", league.platform_id
                    ).eq("season", season)
                    
                    existing_response = existing_query.execute()
                    
                    if existing_response.data:
                        # Update existing league
                        update_data = {
                            "league_name": league.name,
                            "league_data": {
                                "total_teams": league.total_teams,
                                "current_week": league.current_week,
                                "scoring_type": league.scoring_type,
                                "teams": [
                                    {
                                        "id": team.platform_id,
                                        "name": team.name,
                                        "owner": team.owner_name,
                                        "wins": team.wins,
                                        "losses": team.losses,
                                        "ties": team.ties,
                                        "points_for": team.points_for,
                                        "points_against": team.points_against
                                    } for team in league.teams
                                ] if league.teams else [],
                                "metadata": league.metadata or {}
                            },
                            "updated_at": datetime.utcnow().isoformat(),
                            "is_active": True
                        }
                        
                        update_response = supabase.table("fantasy_leagues").update(update_data).eq(
                            "id", existing_response.data[0]["id"]
                        ).execute()
                        
                        connected_leagues.append({
                            "action": "updated",
                            "league_id": league.platform_id,
                            "league_name": league.name,
                            "database_id": existing_response.data[0]["id"]
                        })
                    else:
                        # Create new league record
                        insert_data = {
                            "user_id": current_user["id"],
                            "platform": platform_lower,
                            "league_id": league.platform_id,
                            "league_name": league.name,
                            "season": season,
                            "is_active": True,
                            "league_data": {
                                "total_teams": league.total_teams,
                                "current_week": league.current_week,
                                "scoring_type": league.scoring_type,
                                "teams": [
                                    {
                                        "id": team.platform_id,
                                        "name": team.name,
                                        "owner": team.owner_name,
                                        "wins": team.wins,
                                        "losses": team.losses,
                                        "ties": team.ties,
                                        "points_for": team.points_for,
                                        "points_against": team.points_against
                                    } for team in league.teams
                                ] if league.teams else [],
                                "metadata": league.metadata or {}
                            }
                        }
                        
                        insert_response = supabase.table("fantasy_leagues").insert(insert_data).execute()
                        
                        connected_leagues.append({
                            "action": "created",
                            "league_id": league.platform_id,
                            "league_name": league.name,
                            "database_id": insert_response.data[0]["id"] if insert_response.data else None
                        })
                        
                except Exception as league_error:
                    logger.error(f"Failed to process league {league.platform_id}: {league_error}")
                    connected_leagues.append({
                        "action": "failed",
                        "league_id": league.platform_id,
                        "league_name": league.name,
                        "error": str(league_error)
                    })
            
            return {
                "success": True,
                "platform": platform_lower,
                "season": season,
                "leagues_found": len(leagues_data),
                "leagues_processed": len(connected_leagues),
                "results": connected_leagues
            }
        
        else:
            # Other platforms (ESPN, Sleeper) would be implemented here
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Platform {platform} integration not yet implemented"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to connect platform leagues: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect platform: {str(e)}"
        )


@router.put("/{league_db_id}")
async def update_league(
    league_db_id: str,
    request: LeagueUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a user's league settings"""
    try:
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Verify league belongs to user
        league_query = supabase.table("fantasy_leagues").select("*").eq(
            "id", league_db_id
        ).eq("user_id", current_user["id"])
        
        league_response = league_query.execute()
        
        if not league_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found or access denied"
            )
        
        # Build update data
        update_data = {}
        if request.league_name is not None:
            update_data["league_name"] = request.league_name
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.preferences is not None:
            # Merge with existing league_data
            current_league_data = league_response.data[0].get("league_data", {})
            current_league_data["user_preferences"] = request.preferences
            update_data["league_data"] = current_league_data
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            update_response = supabase.table("fantasy_leagues").update(update_data).eq(
                "id", league_db_id
            ).execute()
            
            return {
                "success": True,
                "message": "League updated successfully",
                "data": update_response.data[0] if update_response.data else None
            }
        else:
            return {
                "success": True,
                "message": "No changes to update"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update league: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update league: {str(e)}"
        )


@router.delete("/{league_db_id}")
async def delete_league(
    league_db_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a league from user's account (soft delete by setting inactive)"""
    try:
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Verify league belongs to user
        league_query = supabase.table("fantasy_leagues").select("id").eq(
            "id", league_db_id
        ).eq("user_id", current_user["id"])
        
        league_response = league_query.execute()
        
        if not league_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found or access denied"
            )
        
        # Soft delete by setting inactive
        update_response = supabase.table("fantasy_leagues").update({
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", league_db_id).execute()
        
        return {
            "success": True,
            "message": "League removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete league: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove league: {str(e)}"
        )


@router.post("/{league_db_id}/sync")
async def sync_league_data(
    league_db_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Sync latest data for a specific league from its platform"""
    try:
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Get league details
        league_query = supabase.table("fantasy_leagues").select("*").eq(
            "id", league_db_id
        ).eq("user_id", current_user["id"])
        
        league_response = league_query.execute()
        
        if not league_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found or access denied"
            )
        
        league = league_response.data[0]
        platform = league["platform"]
        league_id = league["league_id"]
        season = league["season"]
        
        if platform == "yahoo":
            service = YahooFantasyService()
            
            # Authenticate
            auth_success = await service.authenticate()
            if not auth_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to authenticate with Yahoo Fantasy API"
                )
            
            # Get updated league data
            league_response = await service.get_league(league_id, year=season)
            if not league_response.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to sync league data: {league_response.error}"
                )
            
            updated_league = league_response.data
            
            # Update database with fresh data
            update_data = {
                "league_data": {
                    "total_teams": updated_league.total_teams,
                    "current_week": updated_league.current_week,
                    "scoring_type": updated_league.scoring_type,
                    "teams": [
                        {
                            "id": team.platform_id,
                            "name": team.name,
                            "owner": team.owner_name,
                            "wins": team.wins,
                            "losses": team.losses,
                            "ties": team.ties,
                            "points_for": team.points_for,
                            "points_against": team.points_against
                        } for team in updated_league.teams
                    ] if updated_league.teams else [],
                    "metadata": updated_league.metadata or {},
                    "last_sync": datetime.utcnow().isoformat()
                },
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Preserve user preferences if they exist
            current_league_data = league.get("league_data", {})
            if "user_preferences" in current_league_data:
                update_data["league_data"]["user_preferences"] = current_league_data["user_preferences"]
            
            sync_response = supabase.table("fantasy_leagues").update(update_data).eq(
                "id", league_db_id
            ).execute()
            
            return {
                "success": True,
                "message": "League data synced successfully",
                "sync_time": update_data["league_data"]["last_sync"],
                "data": sync_response.data[0] if sync_response.data else None
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Sync not yet implemented for platform: {platform}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync league data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync league: {str(e)}"
        )


@router.get("/stats")
async def get_user_league_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get statistics about user's connected leagues"""
    try:
        # Use service role client to bypass RLS for authenticated operations
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Get all leagues for user
        leagues_query = supabase.table("fantasy_leagues").select("*").eq(
            "user_id", current_user["id"]
        )
        
        leagues_response = leagues_query.execute()
        leagues = leagues_response.data or []
        
        # Calculate statistics
        stats = {
            "total_leagues": len(leagues),
            "active_leagues": len([l for l in leagues if l.get("is_active", True)]),
            "platforms": {},
            "seasons": {},
            "last_sync": None
        }
        
        for league in leagues:
            platform = league["platform"]
            season = league["season"]
            
            # Platform stats
            if platform not in stats["platforms"]:
                stats["platforms"][platform] = {"total": 0, "active": 0}
            stats["platforms"][platform]["total"] += 1
            if league.get("is_active", True):
                stats["platforms"][platform]["active"] += 1
            
            # Season stats
            if season not in stats["seasons"]:
                stats["seasons"][season] = {"total": 0, "active": 0}
            stats["seasons"][season]["total"] += 1
            if league.get("is_active", True):
                stats["seasons"][season]["active"] += 1
            
            # Last sync time
            league_data = league.get("league_data", {})
            last_sync = league_data.get("last_sync")
            if last_sync:
                if not stats["last_sync"] or last_sync > stats["last_sync"]:
                    stats["last_sync"] = last_sync
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get league stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
