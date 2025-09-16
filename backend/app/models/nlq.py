"""
Natural Language Query (NLQ) Data Models
Models for StatMuse-like natural language queries and responses
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum

from app.models.fantasy import League, Team, Player, Matchup, WeeklyStats, FantasyPlatform


class QueryType(str, Enum):
    """Types of natural language queries"""
    PLAYER_STATS = "player_stats"
    TEAM_PERFORMANCE = "team_performance"
    LEAGUE_STANDINGS = "league_standings"
    MATCHUP_ANALYSIS = "matchup_analysis"
    WEEKLY_RECAP = "weekly_recap"
    SEASON_TRENDS = "season_trends"
    PLAYER_COMPARISON = "player_comparison"
    TEAM_COMPARISON = "team_comparison"
    LEAGUE_INSIGHTS = "league_insights"
    TRADE_ANALYSIS = "trade_analysis"


class QueryIntent(str, Enum):
    """User intent behind the query"""
    GET_STATS = "get_stats"
    COMPARE = "compare"
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    PREDICT = "predict"
    RECOMMEND = "recommend"


class QueryEntity(BaseModel):
    """Extracted entity from natural language query"""
    entity_type: Literal["player", "team", "league", "week", "season", "stat", "position"] 
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    original_text: str = Field(..., description="Original text in query")
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None


class ParsedQuery(BaseModel):
    """Parsed natural language query with extracted intent and entities"""
    original_query: str
    query_type: QueryType
    intent: QueryIntent
    entities: List[QueryEntity] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Query parameters
    target_player_ids: List[str] = Field(default_factory=list)
    target_team_ids: List[str] = Field(default_factory=list)
    target_leagues: List[str] = Field(default_factory=list)
    week_range: Optional[tuple[int, int]] = None
    season: Optional[int] = None
    
    # Query modifiers
    aggregation: Optional[Literal["sum", "avg", "max", "min", "median"]] = None
    comparison_type: Optional[Literal["vs", "against", "better_than", "worse_than"]] = None
    time_period: Optional[Literal["this_week", "last_week", "season", "recent"]] = None


class QueryResponse(BaseModel):
    """Response to a natural language query"""
    query_id: str = Field(..., description="Unique identifier for this query")
    original_query: str
    parsed_query: ParsedQuery
    
    # Response content
    answer: str = Field(..., description="Natural language answer")
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    confidence: float = Field(ge=0.0, le=1.0)
    response_time_ms: int
    data_sources: List[str] = Field(default_factory=list)
    
    # League context
    league_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryExample(BaseModel):
    """Example queries for training and testing"""
    example_query: str
    expected_type: QueryType
    expected_intent: QueryIntent
    expected_entities: List[QueryEntity]
    description: str


class NLQRequest(BaseModel):
    """API request for natural language query"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    league_id: str = Field(..., description="Target league ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    include_visualizations: bool = Field(default=True, description="Include chart/graph suggestions")
    max_response_length: int = Field(default=500, description="Maximum response length in characters")


class NLQResponse(BaseModel):
    """API response for natural language query"""
    success: bool
    query_response: Optional[QueryResponse] = None
    error: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up queries")


class QueryAnalytics(BaseModel):
    """Analytics data for query performance and usage"""
    query_id: str
    user_id: str
    league_id: str
    query_type: QueryType
    intent: QueryIntent
    confidence: float
    response_time_ms: int
    user_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="1-5 rating")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Example queries for different types
EXAMPLE_QUERIES = [
    QueryExample(
        example_query="Who scored the most points in my league this week?",
        expected_type=QueryType.PLAYER_STATS,
        expected_intent=QueryIntent.GET_STATS,
        expected_entities=[
            QueryEntity(entity_type="stat", value="points", confidence=0.9, original_text="points"),
            QueryEntity(entity_type="week", value="this_week", confidence=0.8, original_text="this week")
        ],
        description="Find highest scoring player for current week"
    ),
    QueryExample(
        example_query="How is my team performing compared to the league average?",
        expected_type=QueryType.TEAM_PERFORMANCE,
        expected_intent=QueryIntent.COMPARE,
        expected_entities=[
            QueryEntity(entity_type="team", value="my_team", confidence=0.9, original_text="my team"),
            QueryEntity(entity_type="stat", value="average", confidence=0.8, original_text="average")
        ],
        description="Compare user's team performance to league average"
    ),
    QueryExample(
        example_query="Show me the closest matchup this week",
        expected_type=QueryType.MATCHUP_ANALYSIS,
        expected_intent=QueryIntent.GET_STATS,
        expected_entities=[
            QueryEntity(entity_type="stat", value="closest", confidence=0.9, original_text="closest"),
            QueryEntity(entity_type="week", value="this_week", confidence=0.8, original_text="this week")
        ],
        description="Find the matchup with smallest point difference"
    ),
    QueryExample(
        example_query="Which running backs are trending up this season?",
        expected_type=QueryType.SEASON_TRENDS,
        expected_intent=QueryIntent.ANALYZE,
        expected_entities=[
            QueryEntity(entity_type="position", value="RB", confidence=0.95, original_text="running backs"),
            QueryEntity(entity_type="stat", value="trending_up", confidence=0.8, original_text="trending up"),
            QueryEntity(entity_type="season", value="this_season", confidence=0.9, original_text="this season")
        ],
        description="Identify improving running back performance over the season"
    )
]
