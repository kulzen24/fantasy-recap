"""
Recap models for fantasy football recap generation
Handles recap requests, responses, and generated content
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from app.models.llm import RecapTone, RecapLength
from app.models.fantasy import League, Matchup, Team, Player


class RecapStatus(str, Enum):
    """Status of a recap generation"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"


class InsightType(str, Enum):
    """Types of fantasy insights"""
    TOP_PERFORMER = "top_performer"
    UNDERACHIEVER = "underachiever"
    CLOSE_MATCHUP = "close_matchup"
    BLOWOUT = "blowout"
    NOTABLE_PERFORMANCE = "notable_performance"
    TREND_ANALYSIS = "trend_analysis"
    WAIVER_PICKUP = "waiver_pickup"
    INJURY_IMPACT = "injury_impact"
    COMEBACK_STORY = "comeback_story"
    DISAPPOINTING_STAR = "disappointing_star"


class PerformanceInsight(BaseModel):
    """Single insight extracted from league data"""
    insight_type: InsightType
    title: str = Field(description="Brief title for the insight")
    description: str = Field(description="Detailed description of the insight")
    
    # Participants
    primary_team: Optional[str] = None
    secondary_team: Optional[str] = None
    players_involved: List[str] = Field(default_factory=list)
    
    # Metrics
    score_impact: Optional[float] = None
    percentage_change: Optional[float] = None
    rank_change: Optional[int] = None
    
    # Context
    week: int
    season: int
    confidence_score: float = Field(ge=0, le=1, description="Confidence in this insight")
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Narrative elements
    is_positive: bool = Field(description="Whether this is positive or negative news")
    narrative_weight: float = Field(ge=0, le=1, description="How important this is for the story")


class WeeklyInsights(BaseModel):
    """Collection of insights for a specific week"""
    week: int
    season: int
    league_id: str
    
    insights: List[PerformanceInsight] = Field(default_factory=list)
    
    # Summary statistics
    total_points_scored: float
    average_points: float
    highest_score: float
    lowest_score: float
    closest_margin: float
    biggest_blowout: float
    
    # Meta information
    generated_at: datetime
    data_source: str = Field(description="Source of the league data")
    analysis_version: str = "1.0"


class RecapGenerationRequest(BaseModel):
    """Request to generate a fantasy football recap"""
    user_id: str
    league_id: str
    week: int
    season: int
    
    # Generation preferences
    tone: Optional[RecapTone] = None
    length: RecapLength = RecapLength.MEDIUM
    use_template: bool = True
    template_id: Optional[str] = None
    
    # Content preferences
    include_awards: bool = True
    include_predictions: bool = True
    focus_on_user_team: bool = False
    
    # Advanced options
    custom_insights: List[PerformanceInsight] = Field(default_factory=list)
    exclude_teams: List[str] = Field(default_factory=list)
    highlight_players: List[str] = Field(default_factory=list)


class GeneratedRecap(BaseModel):
    """Generated fantasy football recap"""
    id: str
    user_id: str
    league_id: str
    week: int
    season: int
    
    # Content
    title: str
    content: str
    word_count: int
    
    # Generation details
    tone_used: RecapTone
    length: RecapLength
    template_id: Optional[str] = None
    insights_used: List[str] = Field(default_factory=list, description="IDs of insights used")
    
    # Metadata
    generated_at: datetime
    generation_time: float = Field(description="Time taken to generate in seconds")
    llm_provider: str
    llm_model: str
    tokens_used: int
    cost: float
    
    # Quality metrics
    style_match_score: Optional[float] = Field(ge=0, le=1, description="How well it matches user's style")
    content_completeness: Optional[float] = Field(ge=0, le=1, description="How complete the content is")
    
    # Status
    status: RecapStatus = RecapStatus.COMPLETED
    error_message: Optional[str] = None


class RecapResponse(BaseModel):
    """Response containing generated recap and metadata"""
    recap: GeneratedRecap
    insights_used: List[PerformanceInsight]
    template_info: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    cache_hit: bool = False
    processing_steps: List[str] = Field(default_factory=list)
    
    # Quality assessment
    quality_score: Optional[float] = Field(ge=0, le=1)
    recommendations: List[str] = Field(default_factory=list)


class RecapHistory(BaseModel):
    """Historical recap information for a user"""
    user_id: str
    total_recaps: int
    recent_recaps: List[GeneratedRecap]
    
    # Statistics
    favorite_tone: RecapTone
    average_length: RecapLength
    most_used_template: Optional[str] = None
    
    # Usage patterns
    weekly_generation_rate: float
    average_generation_time: float
    total_tokens_used: int
    total_cost: float
    
    # Quality trends
    average_style_match: float
    improvement_trend: str = Field(description="improving, stable, or declining")


class InsightAnalysisConfig(BaseModel):
    """Configuration for insight analysis"""
    # Thresholds for different insight types
    blowout_threshold: float = 30.0  # Point difference for blowouts
    close_game_threshold: float = 5.0  # Point difference for close games
    high_score_percentile: float = 0.9  # Top 10% for high scores
    low_score_percentile: float = 0.1  # Bottom 10% for low scores
    
    # Performance analysis
    underperform_threshold: float = -20.0  # % below projection
    overperform_threshold: float = 20.0   # % above projection
    
    # Trend analysis
    trend_weeks: int = 3  # Number of weeks to analyze for trends
    significant_trend_threshold: float = 15.0  # % change for significant trends
    
    # Quality filters
    min_confidence_score: float = 0.6  # Minimum confidence to include insight
    max_insights_per_type: int = 3  # Maximum insights per type
    narrative_weight_threshold: float = 0.3  # Minimum narrative weight
    
    # Player-specific
    min_projected_points: float = 5.0  # Minimum points to consider for analysis
    breakout_performance_threshold: float = 25.0  # Points for breakout performances
