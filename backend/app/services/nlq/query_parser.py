"""
Natural Language Query Parser
Converts natural language queries into structured ParsedQuery objects using LLM providers
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.nlq import (
    QueryType, QueryIntent, QueryEntity, ParsedQuery, 
    EXAMPLE_QUERIES, QueryExample
)
from app.models.llm import LLMRequest, LLMProvider
from app.services.llm.provider_manager import LLMProviderManager

logger = logging.getLogger(__name__)


class QueryParser:
    """Parses natural language queries into structured data"""
    
    def __init__(self, provider_manager: LLMProviderManager):
        self.provider_manager = provider_manager
        self.entity_patterns = self._build_entity_patterns()
        
    def _build_entity_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build regex patterns for entity extraction"""
        return {
            "player": [
                re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'),  # Player names
                re.compile(r'\b(my (qb|quarterback|rb|running back|wr|wide receiver|te|tight end|kicker|defense))\b', re.IGNORECASE)
            ],
            "team": [
                re.compile(r'\b(my team)\b', re.IGNORECASE),
                re.compile(r'\b(team \d+)\b', re.IGNORECASE),
                re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+\'s team)\b')
            ],
            "position": [
                re.compile(r'\b(quarterback|qb|running back|rb|wide receiver|wr|tight end|te|kicker|k|defense|def)\b', re.IGNORECASE)
            ],
            "stat": [
                re.compile(r'\b(points?|yards?|touchdowns?|tds?|receptions?|carries?|targets?)\b', re.IGNORECASE),
                re.compile(r'\b(highest|lowest|most|least|best|worst|average|total)\b', re.IGNORECASE)
            ],
            "week": [
                re.compile(r'\b(this week|last week|week \d+)\b', re.IGNORECASE),
                re.compile(r'\b(current week|previous week)\b', re.IGNORECASE)
            ],
            "season": [
                re.compile(r'\b(this season|last season|season|\d{4} season)\b', re.IGNORECASE)
            ]
        }
    
    async def parse_query(self, query: str, league_context: Optional[Dict[str, Any]] = None) -> ParsedQuery:
        """
        Parse a natural language query into structured data
        
        Args:
            query: Natural language query string
            league_context: Optional context about the league/user
            
        Returns:
            ParsedQuery object with extracted intent and entities
        """
        try:
            # Step 1: Extract entities using regex patterns
            entities = self._extract_entities(query)
            
            # Step 2: Use LLM to determine intent and query type
            llm_analysis = await self._analyze_with_llm(query, entities, league_context)
            
            # Step 3: Build ParsedQuery object
            parsed_query = ParsedQuery(
                original_query=query,
                query_type=llm_analysis["query_type"],
                intent=llm_analysis["intent"],
                entities=entities,
                confidence=llm_analysis["confidence"],
                target_player_ids=llm_analysis.get("target_player_ids", []),
                target_team_ids=llm_analysis.get("target_team_ids", []),
                target_leagues=llm_analysis.get("target_leagues", []),
                week_range=llm_analysis.get("week_range"),
                season=llm_analysis.get("season"),
                aggregation=llm_analysis.get("aggregation"),
                comparison_type=llm_analysis.get("comparison_type"),
                time_period=llm_analysis.get("time_period")
            )
            
            logger.info(f"Parsed query: '{query}' -> {parsed_query.query_type.value} ({parsed_query.confidence:.2f})")
            return parsed_query
            
        except Exception as e:
            logger.error(f"Error parsing query '{query}': {e}")
            # Return a fallback ParsedQuery
            return ParsedQuery(
                original_query=query,
                query_type=QueryType.LEAGUE_INSIGHTS,
                intent=QueryIntent.GET_STATS,
                confidence=0.1
            )
    
    def _extract_entities(self, query: str) -> List[QueryEntity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(query)
                for match in matches:
                    entity = QueryEntity(
                        entity_type=entity_type,
                        value=match.group(1).lower(),
                        confidence=0.8,  # Base confidence for regex matches
                        original_text=match.group(0),
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        return entities
    
    async def _analyze_with_llm(
        self, 
        query: str, 
        entities: List[QueryEntity], 
        league_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use LLM to analyze query intent and extract structured information"""
        
        # Build prompt for LLM analysis
        prompt = self._build_analysis_prompt(query, entities, league_context)
        
        try:
            # Get available provider
            provider = self.provider_manager.get_preferred_provider()
            if not provider:
                raise ValueError("No LLM provider available")
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent parsing
            )
            
            # Generate response
            response = await provider.generate_text(llm_request)
            
            # Parse JSON response
            analysis = json.loads(response.content)
            
            # Validate and return
            return self._validate_llm_analysis(analysis)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Return fallback analysis
            return {
                "query_type": QueryType.LEAGUE_INSIGHTS,
                "intent": QueryIntent.GET_STATS,
                "confidence": 0.2
            }
    
    def _build_analysis_prompt(
        self, 
        query: str, 
        entities: List[QueryEntity], 
        league_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for LLM query analysis"""
        
        # Build entities summary
        entities_text = "\n".join([
            f"- {e.entity_type}: {e.value} (from '{e.original_text}')"
            for e in entities
        ])
        
        # Build context summary
        context_text = ""
        if league_context:
            context_text = f"\nLeague Context: {json.dumps(league_context, indent=2)}"
        
        # Build examples
        examples_text = "\n".join([
            f"Query: \"{ex.example_query}\"\nType: {ex.expected_type.value}\nIntent: {ex.expected_intent.value}\n"
            for ex in EXAMPLE_QUERIES[:3]  # Include first 3 examples
        ])
        
        prompt = f"""You are a fantasy football query analyzer. Analyze the following natural language query and return a JSON response with the query type, intent, and extracted parameters.

Query: "{query}"

Extracted Entities:
{entities_text}
{context_text}

Available Query Types:
- player_stats: Questions about individual player performance
- team_performance: Questions about fantasy team performance  
- league_standings: Questions about league rankings/standings
- matchup_analysis: Questions about head-to-head matchups
- weekly_recap: Questions about weekly summaries
- season_trends: Questions about season-long trends
- player_comparison: Comparing multiple players
- team_comparison: Comparing multiple teams
- league_insights: General league analysis
- trade_analysis: Trade-related questions

Available Intents:
- get_stats: Retrieve specific statistics
- compare: Compare entities
- analyze: Deep analysis/insights
- summarize: Summary information
- predict: Predictions/projections
- recommend: Recommendations

Examples:
{examples_text}

Return ONLY a JSON object with these fields:
{{
    "query_type": "one_of_the_available_types",
    "intent": "one_of_the_available_intents", 
    "confidence": 0.0-1.0,
    "target_player_ids": ["id1", "id2"],
    "target_team_ids": ["team1"],
    "target_leagues": ["league1"],
    "week_range": [1, 17] or null,
    "season": 2024 or null,
    "aggregation": "sum|avg|max|min|median" or null,
    "comparison_type": "vs|against|better_than|worse_than" or null,
    "time_period": "this_week|last_week|season|recent" or null
}}"""
        
        return prompt
    
    def _validate_llm_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean LLM analysis response"""
        validated = {}
        
        # Validate query_type
        try:
            validated["query_type"] = QueryType(analysis.get("query_type", "league_insights"))
        except ValueError:
            validated["query_type"] = QueryType.LEAGUE_INSIGHTS
        
        # Validate intent
        try:
            validated["intent"] = QueryIntent(analysis.get("intent", "get_stats"))
        except ValueError:
            validated["intent"] = QueryIntent.GET_STATS
        
        # Validate confidence
        confidence = analysis.get("confidence", 0.5)
        validated["confidence"] = max(0.0, min(1.0, float(confidence)))
        
        # Copy optional fields if present
        for field in ["target_player_ids", "target_team_ids", "target_leagues", 
                     "week_range", "season", "aggregation", "comparison_type", "time_period"]:
            if field in analysis:
                validated[field] = analysis[field]
        
        return validated
    
    def get_query_suggestions(self, query_type: QueryType) -> List[str]:
        """Get suggested follow-up queries based on query type"""
        suggestions = {
            QueryType.PLAYER_STATS: [
                "Show me this player's season trends",
                "Compare this player to others at the position",
                "What's this player's best game this season?"
            ],
            QueryType.TEAM_PERFORMANCE: [
                "How does my team rank in the league?",
                "Show me my team's weekly performance",
                "What positions are strongest on my team?"
            ],
            QueryType.MATCHUP_ANALYSIS: [
                "Show me all close matchups this week",
                "What was the biggest blowout?",
                "Who has the toughest matchup this week?"
            ],
            QueryType.LEAGUE_STANDINGS: [
                "Show me the current playoff picture",
                "Who has the highest points for?",
                "Which teams are trending up?"
            ]
        }
        
        return suggestions.get(query_type, [
            "Tell me about my league",
            "Show me this week's matchups",
            "Who are the top performers?"
        ])
