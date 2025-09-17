"""
Award models for custom weekly awards
Handles user-defined awards and award winners tracking
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

from app.models.fantasy import FantasyPlatform


class AwardType(str, Enum):
    """Types of awards that can be created"""
    TEAM_PERFORMANCE = "team_performance"  # Best/worst team performance
    PLAYER_PERFORMANCE = "player_performance"  # Individual player awards
    MATCHUP_BASED = "matchup_based"  # Closest game, biggest blowout, etc.
    SEASON_LONG = "season_long"  # Cumulative awards
    CUSTOM = "custom"  # User-defined criteria


class AwardFrequency(str, Enum):
    """How often the award is given"""
    WEEKLY = "weekly"
    MONTHLY = "monthly" 
    SEASON = "season"
    PLAYOFF = "playoff"


class AwardStatus(str, Enum):
    """Status of an award"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class AwardCriteria(BaseModel):
    """Criteria for determining award winners"""
    # Basic criteria type
    type: AwardType
    
    # Performance-based criteria
    stat_category: Optional[str] = None  # e.g., "points_scored", "turnovers", etc.
    comparison: Optional[str] = None  # "highest", "lowest", "closest_to"
    threshold: Optional[float] = None
    
    # Matchup-based criteria
    margin_type: Optional[str] = None  # "closest", "biggest_blowout"
    
    # Custom criteria (for advanced users)
    custom_formula: Optional[str] = None
    custom_description: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Award(BaseModel):
    """Custom weekly award definition"""
    id: str
    user_id: str
    league_id: str
    
    # Award details
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    emoji: Optional[str] = None  # Trophy emoji or icon
    
    # Award configuration
    criteria: AwardCriteria
    frequency: AwardFrequency = AwardFrequency.WEEKLY
    status: AwardStatus = AwardStatus.ACTIVE
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    # Usage tracking
    times_awarded: int = 0
    last_awarded_week: Optional[int] = None
    last_awarded_season: Optional[int] = None
    
    # Settings
    is_public: bool = False  # Whether other league members can see this award
    auto_assign: bool = False  # Automatically assign based on criteria
    
    # Custom styling
    color: Optional[str] = None  # Hex color for display
    icon_url: Optional[str] = None  # Custom icon URL


class AwardWinner(BaseModel):
    """Record of an award winner"""
    id: str
    award_id: str
    
    # Timing
    week: int
    season: int
    
    # Winner details
    winner_type: str  # "team" or "player"
    winner_id: str  # Platform-specific team or player ID
    winner_name: str
    platform: FantasyPlatform
    
    # Award context
    reason: Optional[str] = None  # Why they won (auto-generated or manual)
    stats: Dict[str, Union[int, float]] = Field(default_factory=dict)  # Supporting statistics
    
    # Metadata
    awarded_at: datetime
    awarded_by: Optional[str] = None  # User ID who manually assigned (if not auto)
    
    # Display
    highlight_message: Optional[str] = None  # Custom message for this win


class AwardCreateRequest(BaseModel):
    """Request for creating a new award"""
    league_id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    emoji: Optional[str] = None
    criteria: AwardCriteria
    frequency: AwardFrequency = AwardFrequency.WEEKLY
    is_public: bool = False
    auto_assign: bool = False
    color: Optional[str] = None


class AwardUpdateRequest(BaseModel):
    """Request for updating an existing award"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    emoji: Optional[str] = None
    criteria: Optional[AwardCriteria] = None
    frequency: Optional[AwardFrequency] = None
    status: Optional[AwardStatus] = None
    is_public: Optional[bool] = None
    auto_assign: Optional[bool] = None
    color: Optional[str] = None


class AwardWinnerAssignRequest(BaseModel):
    """Request for assigning an award winner"""
    week: int
    season: int
    winner_type: str  # "team" or "player"
    winner_id: str
    winner_name: str
    platform: FantasyPlatform
    reason: Optional[str] = None
    stats: Dict[str, Union[int, float]] = Field(default_factory=dict)
    highlight_message: Optional[str] = None


class AwardListResponse(BaseModel):
    """Response for listing awards"""
    awards: List[Award]
    total: int
    page: int
    page_size: int


class AwardWinnersResponse(BaseModel):
    """Response for award winners"""
    award: Award
    winners: List[AwardWinner]
    total_weeks: int


class WeeklyAwardsResponse(BaseModel):
    """Response for all awards for a specific week"""
    week: int
    season: int
    league_id: str
    awards_with_winners: List[Dict[str, Any]]  # Award + winner info
    total_awards: int


class AwardStatsResponse(BaseModel):
    """Response for award statistics"""
    award: Award
    total_winners: int
    weeks_active: int
    most_recent_winner: Optional[AwardWinner] = None
    winner_frequency: Dict[str, int] = Field(default_factory=dict)  # winner_id -> count


class AwardTemplates:
    """Pre-defined award templates for common use cases"""
    
    @staticmethod
    def get_common_templates() -> List[Dict[str, Any]]:
        """Get list of common award templates users can select from"""
        return [
            {
                "name": "Highest Scorer",
                "description": "Team with the most points this week",
                "emoji": "🏆",
                "criteria": {
                    "type": "team_performance",
                    "stat_category": "points_scored",
                    "comparison": "highest"
                }
            },
            {
                "name": "Lowest Scorer",
                "description": "Team with the fewest points this week",
                "emoji": "💩",
                "criteria": {
                    "type": "team_performance", 
                    "stat_category": "points_scored",
                    "comparison": "lowest"
                }
            },
            {
                "name": "Closest Game",
                "description": "Matchup decided by the smallest margin",
                "emoji": "⚡",
                "criteria": {
                    "type": "matchup_based",
                    "margin_type": "closest"
                }
            },
            {
                "name": "Biggest Blowout",
                "description": "Matchup with the largest point difference",
                "emoji": "💥",
                "criteria": {
                    "type": "matchup_based",
                    "margin_type": "biggest_blowout"
                }
            },
            {
                "name": "Bench Points Leader",
                "description": "Team with the most points on their bench",
                "emoji": "🪑",
                "criteria": {
                    "type": "team_performance",
                    "stat_category": "bench_points",
                    "comparison": "highest"
                }
            }
        ]
