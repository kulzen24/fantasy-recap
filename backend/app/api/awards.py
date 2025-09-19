"""
Awards API endpoints for custom weekly awards management
Handles award creation, winner assignment, and integration with leagues
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import uuid

from app.core.auth import get_current_user
from app.core.supabase import get_supabase_client_safe, get_supabase_service_client_safe
from app.models.award import (
    Award, AwardWinner, AwardCreateRequest, AwardUpdateRequest, 
    AwardWinnerAssignRequest, AwardListResponse, AwardWinnersResponse,
    WeeklyAwardsResponse, AwardStatsResponse, AwardTemplates,
    AwardStatus, AwardType, AwardFrequency
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=AwardListResponse)
async def get_user_awards(
    league_id: Optional[str] = None,
    status: Optional[str] = None,
    frequency: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get all awards for the authenticated user"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        
        # Build query
        query = supabase.table("weekly_awards").select("*").eq("user_id", user_id)
        
        # Apply filters
        if league_id:
            query = query.eq("league_id", league_id)
        if status:
            query = query.eq("status", status)
        if frequency:
            query = query.eq("frequency", frequency)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        # Order by created_at desc
        query = query.order("created_at", desc=True)
        
        result = query.execute()
        
        # Convert to Award models
        awards = []
        for row in result.data:
            try:
                award = Award(
                    id=row["id"],
                    user_id=row["user_id"],
                    league_id=row["league_id"],
                    name=row["award_name"],
                    description=row.get("award_description"),
                    emoji=row.get("emoji"),
                    criteria=row.get("criteria", {}),
                    frequency=row.get("frequency", "weekly"),
                    status=row.get("status", "active"),
                    created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00')),
                    times_awarded=row.get("times_awarded", 0),
                    last_awarded_week=row.get("last_awarded_week"),
                    last_awarded_season=row.get("last_awarded_season"),
                    is_public=row.get("is_public", False),
                    auto_assign=row.get("auto_assign", False),
                    color=row.get("color"),
                    icon_url=row.get("icon_url")
                )
                awards.append(award)
            except Exception as e:
                logger.warning(f"Failed to parse award {row.get('id')}: {e}")
                continue
        
        # Get total count for pagination
        count_result = supabase.table("weekly_awards").select("id", count="exact").eq("user_id", user_id).execute()
        total = count_result.count or len(awards)
        
        return AwardListResponse(
            awards=awards,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error fetching user awards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch awards"
        )


@router.post("/", response_model=Dict[str, Any])
async def create_award(
    award_request: AwardCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new custom award"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        award_id = str(uuid.uuid4())
        
        # Verify league belongs to user
        league_check = supabase.table("fantasy_leagues").select("id").eq("id", award_request.league_id).eq("user_id", user_id).execute()
        if not league_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found or access denied"
            )
        
        # Create award record
        award_data = {
            "id": award_id,
            "user_id": user_id,
            "league_id": award_request.league_id,
            "award_name": award_request.name,
            "award_description": award_request.description,
            "emoji": award_request.emoji,
            "criteria": award_request.criteria.dict(),
            "frequency": award_request.frequency,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "times_awarded": 0,
            "is_public": award_request.is_public,
            "auto_assign": award_request.auto_assign,
            "color": award_request.color
        }
        
        result = supabase.table("weekly_awards").insert(award_data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create award"
            )
        
        logger.info(f"Created award {award_id} for user {user_id}")
        
        return {
            "success": True,
            "award_id": award_id,
            "message": "Award created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating award: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create award"
        )


@router.get("/{award_id}", response_model=Award)
async def get_award(
    award_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific award by ID"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        
        result = supabase.table("weekly_awards").select("*").eq("id", award_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Award not found"
            )
        
        row = result.data[0]
        award = Award(
            id=row["id"],
            user_id=row["user_id"],
            league_id=row["league_id"],
            name=row["award_name"],
            description=row.get("award_description"),
            emoji=row.get("emoji"),
            criteria=row.get("criteria", {}),
            frequency=row.get("frequency", "weekly"),
            status=row.get("status", "active"),
            created_at=datetime.fromisoformat(row["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(row["updated_at"].replace('Z', '+00:00')),
            times_awarded=row.get("times_awarded", 0),
            last_awarded_week=row.get("last_awarded_week"),
            last_awarded_season=row.get("last_awarded_season"),
            is_public=row.get("is_public", False),
            auto_assign=row.get("auto_assign", False),
            color=row.get("color"),
            icon_url=row.get("icon_url")
        )
        
        return award
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching award {award_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch award"
        )


@router.put("/{award_id}", response_model=Dict[str, Any])
async def update_award(
    award_id: str,
    award_update: AwardUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing award"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        
        # Check if award exists and belongs to user
        existing = supabase.table("weekly_awards").select("id").eq("id", award_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Award not found"
            )
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if award_update.name is not None:
            update_data["award_name"] = award_update.name
        if award_update.description is not None:
            update_data["award_description"] = award_update.description
        if award_update.emoji is not None:
            update_data["emoji"] = award_update.emoji
        if award_update.criteria is not None:
            update_data["criteria"] = award_update.criteria.dict()
        if award_update.frequency is not None:
            update_data["frequency"] = award_update.frequency
        if award_update.status is not None:
            update_data["status"] = award_update.status
        if award_update.is_public is not None:
            update_data["is_public"] = award_update.is_public
        if award_update.auto_assign is not None:
            update_data["auto_assign"] = award_update.auto_assign
        if award_update.color is not None:
            update_data["color"] = award_update.color
        
        result = supabase.table("weekly_awards").update(update_data).eq("id", award_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update award"
            )
        
        logger.info(f"Updated award {award_id} for user {user_id}")
        
        return {
            "success": True,
            "award_id": award_id,
            "message": "Award updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating award {award_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update award"
        )


@router.delete("/{award_id}", response_model=Dict[str, Any])
async def delete_award(
    award_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an award and all its winners"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        
        # Check if award exists and belongs to user
        existing = supabase.table("weekly_awards").select("id").eq("id", award_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Award not found"
            )
        
        # Delete award winners first (due to foreign key constraint)
        supabase.table("award_winners").delete().eq("award_id", award_id).execute()
        
        # Delete the award
        result = supabase.table("weekly_awards").delete().eq("id", award_id).execute()
        
        logger.info(f"Deleted award {award_id} for user {user_id}")
        
        return {
            "success": True,
            "award_id": award_id,
            "message": "Award deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting award {award_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete award"
        )


@router.post("/{award_id}/winners", response_model=Dict[str, Any])
async def assign_award_winner(
    award_id: str,
    winner_request: AwardWinnerAssignRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign a winner for an award"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        
        # Verify award belongs to user
        award_check = supabase.table("weekly_awards").select("id", "league_id").eq("id", award_id).eq("user_id", user_id).execute()
        if not award_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Award not found"
            )
        
        # Check if winner already exists for this week/season
        existing_winner = supabase.table("award_winners").select("id").eq("award_id", award_id).eq("week", winner_request.week).eq("season", winner_request.season).execute()
        
        winner_id = str(uuid.uuid4())
        winner_data = {
            "id": winner_id,
            "award_id": award_id,
            "week": winner_request.week,
            "season": winner_request.season,
            "winner_type": winner_request.winner_type,
            "winner_id": winner_request.winner_id,
            "winner_name": winner_request.winner_name,
            "platform": winner_request.platform,
            "reason": winner_request.reason,
            "stats": winner_request.stats,
            "awarded_at": datetime.utcnow().isoformat(),
            "awarded_by": user_id,
            "highlight_message": winner_request.highlight_message
        }
        
        if existing_winner.data:
            # Update existing winner
            result = supabase.table("award_winners").update(winner_data).eq("id", existing_winner.data[0]["id"]).execute()
            action = "updated"
        else:
            # Create new winner
            result = supabase.table("award_winners").insert(winner_data).execute()
            action = "assigned"
        
        # Update award stats
        award_update = {
            "times_awarded": supabase.rpc("increment_times_awarded", {"award_id": award_id}),
            "last_awarded_week": winner_request.week,
            "last_awarded_season": winner_request.season,
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("weekly_awards").update(award_update).eq("id", award_id).execute()
        
        logger.info(f"Award winner {action} for award {award_id}, week {winner_request.week}")
        
        return {
            "success": True,
            "winner_id": winner_id,
            "message": f"Award winner {action} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning award winner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign award winner"
        )


@router.get("/{award_id}/winners", response_model=AwardWinnersResponse)
async def get_award_winners(
    award_id: str,
    season: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all winners for a specific award"""
    try:
        supabase = get_supabase_service_client_safe()
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        user_id = current_user["id"]
        
        # Get award details
        award_result = supabase.table("weekly_awards").select("*").eq("id", award_id).eq("user_id", user_id).execute()
        if not award_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Award not found"
            )
        
        # Get winners
        winners_query = supabase.table("award_winners").select("*").eq("award_id", award_id)
        if season:
            winners_query = winners_query.eq("season", season)
        
        winners_result = winners_query.order("week", desc=True).execute()
        
        # Convert to models
        award_row = award_result.data[0]
        award = Award(
            id=award_row["id"],
            user_id=award_row["user_id"],
            league_id=award_row["league_id"],
            name=award_row["award_name"],
            description=award_row.get("award_description"),
            emoji=award_row.get("emoji"),
            criteria=award_row.get("criteria", {}),
            frequency=award_row.get("frequency", "weekly"),
            status=award_row.get("status", "active"),
            created_at=datetime.fromisoformat(award_row["created_at"].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(award_row["updated_at"].replace('Z', '+00:00'))
        )
        
        winners = []
        for row in winners_result.data:
            winner = AwardWinner(
                id=row["id"],
                award_id=row["award_id"],
                week=row["week"],
                season=row["season"],
                winner_type=row["winner_type"],
                winner_id=row["winner_id"],
                winner_name=row["winner_name"],
                platform=row["platform"],
                reason=row.get("reason"),
                stats=row.get("stats", {}),
                awarded_at=datetime.fromisoformat(row["awarded_at"].replace('Z', '+00:00')),
                awarded_by=row.get("awarded_by"),
                highlight_message=row.get("highlight_message")
            )
            winners.append(winner)
        
        return AwardWinnersResponse(
            award=award,
            winners=winners,
            total_weeks=len(winners)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching award winners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch award winners"
        )


@router.get("/templates/common", response_model=List[Dict[str, Any]])
async def get_award_templates():
    """Get common award templates that users can select from"""
    try:
        templates = AwardTemplates.get_common_templates()
        return templates
        
    except Exception as e:
        logger.error(f"Error fetching award templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch award templates"
        )
