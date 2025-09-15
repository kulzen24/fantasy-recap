"""
Fantasy Sports Data Models
Unified data structures for all fantasy platforms (Yahoo, ESPN, Sleeper)
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class FantasyPlatform(str, Enum):
    """Supported fantasy platforms"""
    YAHOO = "yahoo"
    ESPN = "espn"
    SLEEPER = "sleeper"


class PlayerPosition(str, Enum):
    """Standard player positions"""
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DEF = "DEF"
    FLEX = "FLEX"
    BENCH = "BENCH"
    IR = "IR"


class MatchupStatus(str, Enum):
    """Matchup status"""
    PREVIEW = "preview"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Player(BaseModel):
    """Unified player model"""
    id: str = Field(..., description="Platform-specific player ID")
    platform_id: str = Field(..., description="Original platform player ID")
    platform: FantasyPlatform
    name: str
    position: PlayerPosition
    team: Optional[str] = None  # NFL team
    bye_week: Optional[int] = None
    
    # Current week stats
    projected_points: Optional[float] = None
    actual_points: Optional[float] = None
    
    # Additional metadata
    injury_status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Team(BaseModel):
    """Unified team model"""
    id: str = Field(..., description="Platform-specific team ID")
    platform_id: str = Field(..., description="Original platform team ID") 
    platform: FantasyPlatform
    name: str
    owner_name: Optional[str] = None
    
    # Team stats
    wins: int = 0
    losses: int = 0
    ties: int = 0
    points_for: float = 0.0
    points_against: float = 0.0
    
    # Roster
    roster: List[Player] = Field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Matchup(BaseModel):
    """Unified matchup model"""
    id: str = Field(..., description="Platform-specific matchup ID")
    platform: FantasyPlatform
    week: int
    year: int
    
    # Teams
    team1: Team
    team2: Team
    
    # Scores
    team1_score: Optional[float] = None
    team2_score: Optional[float] = None
    
    # Status
    status: MatchupStatus = MatchupStatus.PREVIEW
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class League(BaseModel):
    """Unified league model"""
    id: str = Field(..., description="Platform-specific league ID")
    platform_id: str = Field(..., description="Original platform league ID")
    platform: FantasyPlatform
    name: str
    
    # League settings
    total_teams: int
    current_week: int
    current_season: int
    
    # Scoring
    scoring_type: str = "standard"  # standard, ppr, half_ppr, etc.
    
    # Teams
    teams: List[Team] = Field(default_factory=list)
    
    # Current matchups
    current_matchups: List[Matchup] = Field(default_factory=list)
    
    # League metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WeeklyStats(BaseModel):
    """Weekly statistics for players"""
    player_id: str
    platform: FantasyPlatform
    week: int
    year: int
    
    # Stats
    projected_points: Optional[float] = None
    actual_points: Optional[float] = None
    
    # Detailed stats (will vary by position)
    stats: Dict[str, Union[int, float]] = Field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FantasyApiResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    platform: FantasyPlatform
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Rate limiting info
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
