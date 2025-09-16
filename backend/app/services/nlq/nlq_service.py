"""
Natural Language Query Service
Main service for processing StatMuse-like natural language queries
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.models.nlq import (
    NLQRequest, NLQResponse, QueryResponse, ParsedQuery,
    QueryAnalytics
)
from app.models.llm import LLMRequest, RecapRequest, RecapTone, RecapLength
from app.services.nlq.query_parser import QueryParser
from app.services.nlq.analytics_service import FantasyAnalyticsService
from app.services.llm.provider_manager import LLMProviderManager
from app.services.fantasy.base_service import BaseFantasyService

logger = logging.getLogger(__name__)


class NaturalLanguageQueryService:
    """Main service for processing natural language queries about fantasy leagues"""
    
    def __init__(
        self, 
        provider_manager: LLMProviderManager,
        fantasy_service: BaseFantasyService
    ):
        self.provider_manager = provider_manager
        self.fantasy_service = fantasy_service
        self.query_parser = QueryParser(provider_manager)
        self.analytics_service = FantasyAnalyticsService(fantasy_service)
    
    async def process_query(
        self, 
        request: NLQRequest, 
        user_id: str
    ) -> NLQResponse:
        """
        Process a natural language query and return a structured response
        
        Args:
            request: NLQ request with query and context
            user_id: ID of the user making the query
            
        Returns:
            NLQResponse with answer and supporting data
        """
        start_time = datetime.utcnow()
        query_id = str(uuid.uuid4())
        
        try:
            logger.info(f"Processing NLQ: '{request.query}' for user {user_id}")
            
            # Step 1: Parse the natural language query
            parsed_query = await self.query_parser.parse_query(
                request.query, 
                league_context=request.context
            )
            
            # Step 2: Get fantasy data analysis
            analysis = await self.analytics_service.analyze_query(
                parsed_query, 
                request.league_id, 
                user_id
            )
            
            # Step 3: Generate natural language response using LLM
            if "error" not in analysis:
                natural_answer = await self._generate_natural_response(
                    parsed_query, 
                    analysis, 
                    request
                )
            else:
                natural_answer = "I'm sorry, I couldn't analyze your query due to a data issue. Please try again."
            
            # Step 4: Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Step 5: Build query response
            query_response = QueryResponse(
                query_id=query_id,
                original_query=request.query,
                parsed_query=parsed_query,
                answer=natural_answer,
                supporting_data=analysis.get("supporting_data", {}),
                visualizations=analysis.get("visualizations", []),
                confidence=parsed_query.confidence,
                response_time_ms=int(response_time),
                data_sources=[self.fantasy_service.__class__.__name__],
                league_id=request.league_id,
                user_id=user_id
            )
            
            # Step 6: Get suggestions for follow-up queries
            suggestions = self.query_parser.get_query_suggestions(parsed_query.query_type)
            
            # Step 7: Log analytics
            await self._log_query_analytics(query_response, user_id)
            
            return NLQResponse(
                success=True,
                query_response=query_response,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Error processing NLQ '{request.query}': {e}")
            return NLQResponse(
                success=False,
                error=f"Failed to process query: {str(e)}",
                suggestions=[
                    "Try asking about your team's performance",
                    "Ask who scored the most points this week",
                    "Check your league standings"
                ]
            )
    
    async def _generate_natural_response(
        self, 
        parsed_query: ParsedQuery, 
        analysis: Dict[str, Any], 
        request: NLQRequest
    ) -> str:
        """Generate a natural language response using LLM"""
        
        try:
            # Use the existing answer if it's already natural
            if "answer" in analysis and isinstance(analysis["answer"], str):
                base_answer = analysis["answer"]
            else:
                base_answer = "Here's what I found:"
            
            # If the answer is already well-formatted, return it
            if len(base_answer) > 50 and not base_answer.startswith("Here's what I found"):
                return base_answer
            
            # Otherwise, enhance it with LLM
            provider = self.provider_manager.get_preferred_provider()
            if not provider:
                return base_answer
            
            # Build enhancement prompt
            prompt = self._build_response_enhancement_prompt(
                parsed_query, 
                analysis, 
                base_answer,
                request.max_response_length
            )
            
            llm_request = LLMRequest(
                prompt=prompt,
                max_tokens=min(request.max_response_length + 100, 800),
                temperature=0.7  # Slightly creative for engaging responses
            )
            
            response = await self.provider_manager.generate_text(llm_request, user_id=user_id)
            
            # Clean up the response
            enhanced_answer = response.content.strip()
            
            # Ensure response isn't too long
            if len(enhanced_answer) > request.max_response_length:
                enhanced_answer = enhanced_answer[:request.max_response_length-3] + "..."
            
            return enhanced_answer
            
        except Exception as e:
            logger.error(f"Error generating natural response: {e}")
            return analysis.get("answer", "I found some information but couldn't format it properly.")
    
    def _build_response_enhancement_prompt(
        self, 
        parsed_query: ParsedQuery, 
        analysis: Dict[str, Any], 
        base_answer: str,
        max_length: int
    ) -> str:
        """Build prompt for enhancing the response with LLM"""
        
        supporting_data = analysis.get("supporting_data", {})
        
        prompt = f"""You are a fantasy football assistant responding to a user's question. 
Make the response engaging, conversational, and insightful while staying accurate to the data.

User's Question: "{parsed_query.original_query}"

Data Analysis Result: {base_answer}

Supporting Data: {supporting_data}

Instructions:
- Keep response under {max_length} characters
- Be conversational and engaging like a knowledgeable friend
- Include specific numbers and stats when relevant
- Add context or insights that would be helpful
- Don't make up information not in the data
- Use fantasy football terminology appropriately

Generate an enhanced response:"""
        
        return prompt
    
    async def _log_query_analytics(self, query_response: QueryResponse, user_id: str):
        """Log analytics data for the query"""
        try:
            analytics = QueryAnalytics(
                query_id=query_response.query_id,
                user_id=user_id,
                league_id=query_response.league_id,
                query_type=query_response.parsed_query.query_type,
                intent=query_response.parsed_query.intent,
                confidence=query_response.confidence,
                response_time_ms=query_response.response_time_ms
            )
            
            # In a real implementation, you'd save this to the database
            logger.info(f"Query analytics: {analytics.query_type.value} - {analytics.confidence:.2f} confidence - {analytics.response_time_ms}ms")
            
        except Exception as e:
            logger.error(f"Error logging query analytics: {e}")
    
    async def get_query_examples(self) -> List[str]:
        """Get example queries for user guidance"""
        return [
            "Who scored the most points in my league this week?",
            "How is my team performing compared to the league average?",
            "Show me the closest matchup this week",
            "What are the current league standings?",
            "Which running backs are trending up this season?",
            "Compare my top two receivers",
            "Who has the toughest matchup this week?",
            "Show me my team's weekly performance",
            "What was the biggest blowout this week?",
            "Which players on my bench are worth starting?"
        ]
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the NLQ service"""
        try:
            # Check LLM provider availability
            provider = self.provider_manager.get_preferred_provider()
            provider_healthy = provider is not None
            
            # Check fantasy service (simplified)
            fantasy_healthy = self.fantasy_service is not None
            
            return {
                "status": "healthy" if (provider_healthy and fantasy_healthy) else "degraded",
                "components": {
                    "llm_provider": "healthy" if provider_healthy else "error",
                    "fantasy_service": "healthy" if fantasy_healthy else "error",
                    "query_parser": "healthy",
                    "analytics_service": "healthy"
                },
                "capabilities": [
                    "player_stats", 
                    "team_performance", 
                    "league_standings", 
                    "matchup_analysis"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error checking NLQ health: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
