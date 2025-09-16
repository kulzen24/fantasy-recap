"""
Natural Language Query API Endpoints
StatMuse-like natural language query endpoints for fantasy leagues
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.core.auth import get_current_user
from app.models.nlq import NLQRequest, NLQResponse
from app.services.nlq.nlq_service import NaturalLanguageQueryService
from app.services.llm.provider_manager import LLMProviderManager
from app.services.fantasy.yahoo_service import YahooFantasyService

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize services (in production, these would be dependency injected)
provider_manager = LLMProviderManager()
fantasy_service = YahooFantasyService("yahoo")  # Platform will be configurable
nlq_service = NaturalLanguageQueryService(provider_manager, fantasy_service)


@router.post("/query", response_model=NLQResponse)
async def process_natural_language_query(
    request: NLQRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process a natural language query about fantasy leagues
    
    Example queries:
    - "Who scored the most points in my league this week?"
    - "How is my team performing compared to the league average?"
    - "Show me the closest matchup this week"
    - "What are the current league standings?"
    """
    try:
        logger.info(f"Processing NLQ from user {current_user['id']}: '{request.query}'")
        
        # Validate league access (simplified - in production, check user has access to league)
        if not request.league_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="League ID is required"
            )
        
        # Process the query
        response = await nlq_service.process_query(request, current_user["id"])
        
        if response.success:
            logger.info(f"Successfully processed NLQ for user {current_user['id']}")
        else:
            logger.warning(f"Failed to process NLQ for user {current_user['id']}: {response.error}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing NLQ: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/examples")
async def get_query_examples(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, List[str]]:
    """
    Get example natural language queries for user guidance
    """
    try:
        examples = await nlq_service.get_query_examples()
        
        return {
            "success": True,
            "examples": examples,
            "categories": {
                "player_stats": [
                    "Who scored the most points this week?",
                    "Show me my quarterback's performance",
                    "Which players on my team underperformed?"
                ],
                "team_performance": [
                    "How is my team doing this season?",
                    "Compare my team to the league average",
                    "What's my team's strengths and weaknesses?"
                ],
                "league_analysis": [
                    "Show me the current standings",
                    "Who has the best record?",
                    "What's the closest matchup this week?"
                ],
                "trends": [
                    "Which players are trending up?",
                    "Show me breakout performances this season",
                    "Who are the most consistent players?"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting query examples: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get query examples"
        )


@router.get("/health")
async def get_nlq_health_status() -> Dict[str, Any]:
    """
    Get health status of the Natural Language Query system
    """
    try:
        health_status = await nlq_service.get_health_status()
        
        return {
            "success": True,
            "health": health_status,
            "timestamp": "2024-01-01T00:00:00Z"  # Would be actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error checking NLQ health: {e}")
        return {
            "success": False,
            "error": str(e),
            "health": {
                "status": "error",
                "components": {
                    "llm_provider": "unknown",
                    "fantasy_service": "unknown",
                    "query_parser": "unknown",
                    "analytics_service": "unknown"
                }
            }
        }


@router.post("/query/batch")
async def process_batch_queries(
    queries: List[NLQRequest],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process multiple natural language queries in batch
    
    Useful for dashboard widgets or bulk analysis
    """
    try:
        if len(queries) > 10:  # Limit batch size
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 queries per batch request"
            )
        
        responses = []
        for query_request in queries:
            try:
                response = await nlq_service.process_query(query_request, current_user["id"])
                responses.append({
                    "query": query_request.query,
                    "response": response
                })
            except Exception as e:
                responses.append({
                    "query": query_request.query,
                    "response": NLQResponse(
                        success=False,
                        error=f"Failed to process: {str(e)}"
                    )
                })
        
        successful_responses = sum(1 for r in responses if r["response"].success)
        
        return {
            "success": True,
            "total_queries": len(queries),
            "successful_responses": successful_responses,
            "failed_responses": len(queries) - successful_responses,
            "responses": responses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch queries: {str(e)}"
        )


@router.get("/analytics/{league_id}")
async def get_query_analytics(
    league_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get analytics about queries for a specific league
    
    Shows popular query types, user engagement, etc.
    """
    try:
        # In a real implementation, this would fetch from database
        # For now, return mock analytics
        
        return {
            "success": True,
            "league_id": league_id,
            "analytics": {
                "total_queries": 150,
                "avg_response_time_ms": 850,
                "avg_confidence": 0.82,
                "popular_query_types": [
                    {"type": "player_stats", "count": 45, "percentage": 30.0},
                    {"type": "team_performance", "count": 38, "percentage": 25.3},
                    {"type": "league_standings", "count": 32, "percentage": 21.3},
                    {"type": "matchup_analysis", "count": 25, "percentage": 16.7},
                    {"type": "season_trends", "count": 10, "percentage": 6.7}
                ],
                "user_satisfaction": 4.2,  # Out of 5
                "most_common_queries": [
                    "Who scored the most points this week?",
                    "How is my team doing?",
                    "Show me the standings",
                    "What's the closest matchup?"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting query analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get query analytics"
        )


@router.post("/feedback")
async def submit_query_feedback(
    feedback_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback on a query response
    
    Helps improve the NLQ system accuracy over time
    """
    try:
        required_fields = ["query_id", "rating", "feedback_type"]
        for field in required_fields:
            if field not in feedback_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate rating
        rating = feedback_data.get("rating")
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be an integer between 1 and 5"
            )
        
        # In a real implementation, save feedback to database
        logger.info(f"Received feedback for query {feedback_data['query_id']}: rating={rating}")
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "query_id": feedback_data["query_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )
