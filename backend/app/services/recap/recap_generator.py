"""
Main recap generation service
Orchestrates data analysis, template integration, and LLM generation
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.recap import (
    RecapGenerationRequest, GeneratedRecap, RecapResponse, WeeklyInsights,
    PerformanceInsight, RecapStatus
)
from app.models.fantasy import League, Matchup
from app.models.template import PromptTemplate
from app.models.llm import LLMRequest, RecapTone, RecapLength

from app.services.recap.insight_analyzer import insight_analyzer
from app.services.template.template_service import template_service
from app.services.llm.provider_manager import provider_manager
from app.core.supabase import supabase_client

logger = logging.getLogger(__name__)


class RecapGenerator:
    """Main service for generating fantasy football recaps"""
    
    def __init__(self):
        self.supabase = supabase_client.client
    
    async def generate_recap(self, request: RecapGenerationRequest) -> RecapResponse:
        """
        Generate a personalized fantasy football recap
        
        Args:
            request: Recap generation request
            
        Returns:
            RecapResponse: Complete recap with metadata
        """
        start_time = datetime.utcnow()
        processing_steps = []
        
        try:
            # Step 1: Validate request and check for cached recap
            processing_steps.append("validation")
            await self._validate_request(request)
            
            # Check for existing recap (caching)
            cached_recap = await self._get_cached_recap(request)
            if cached_recap:
                return RecapResponse(
                    recap=cached_recap,
                    insights_used=[],
                    cache_hit=True,
                    processing_steps=["cache_retrieval"],
                    quality_score=cached_recap.style_match_score
                )
            
            # Step 2: Fetch league data
            processing_steps.append("data_retrieval")
            league_data = await self._fetch_league_data(request.league_id)
            matchups = await self._fetch_week_matchups(request.league_id, request.week, request.season)
            
            # Step 3: Analyze data and extract insights
            processing_steps.append("insight_analysis")
            insights = await self._analyze_league_data(
                league_data, matchups, request.week, request.season
            )
            
            # Step 4: Get user template (if requested)
            processing_steps.append("template_retrieval")
            user_template = None
            if request.use_template:
                user_template = await self._get_user_template(request.user_id, request.template_id)
            
            # Step 5: Construct LLM prompt
            processing_steps.append("prompt_construction")
            llm_prompt = await self._construct_llm_prompt(
                insights, request, user_template, league_data, matchups
            )
            
            # Step 6: Generate recap with LLM
            processing_steps.append("llm_generation")
            llm_response = await self._generate_with_llm(llm_prompt, request.user_id)
            
            # Step 7: Process and validate generated content
            processing_steps.append("content_processing")
            recap = await self._process_generated_content(
                llm_response, request, insights, user_template, start_time
            )
            
            # Step 8: Store recap
            processing_steps.append("storage")
            await self._store_recap(recap)
            
            # Step 9: Calculate quality metrics
            processing_steps.append("quality_assessment")
            quality_score = await self._assess_quality(recap, user_template, insights)
            
            logger.info(f"Recap generated successfully: {recap.id}")
            
            return RecapResponse(
                recap=recap,
                insights_used=insights.insights,
                template_info=self._extract_template_info(user_template) if user_template else None,
                cache_hit=False,
                processing_steps=processing_steps,
                quality_score=quality_score,
                recommendations=await self._generate_recommendations(recap, quality_score)
            )
            
        except Exception as e:
            logger.error(f"Recap generation failed: {e}")
            
            # Create failed recap record
            failed_recap = GeneratedRecap(
                id=str(uuid.uuid4()),
                user_id=request.user_id,
                league_id=request.league_id,
                week=request.week,
                season=request.season,
                title="Generation Failed",
                content="",
                word_count=0,
                tone_used=request.tone or RecapTone.PROFESSIONAL,
                length=request.length,
                generated_at=datetime.utcnow(),
                generation_time=(datetime.utcnow() - start_time).total_seconds(),
                llm_provider="unknown",
                llm_model="unknown",
                tokens_used=0,
                cost=0.0,
                status=RecapStatus.FAILED,
                error_message=str(e)
            )
            
            return RecapResponse(
                recap=failed_recap,
                insights_used=[],
                processing_steps=processing_steps,
                quality_score=0.0,
                recommendations=["Review league data availability", "Check template configuration"]
            )
    
    async def _validate_request(self, request: RecapGenerationRequest) -> None:
        """Validate the recap generation request"""
        if not request.user_id:
            raise ValueError("User ID is required")
        
        if not request.league_id:
            raise ValueError("League ID is required")
        
        if request.week < 1 or request.week > 18:
            raise ValueError("Week must be between 1 and 18")
        
        # Additional validation could be added here
    
    async def _get_cached_recap(self, request: RecapGenerationRequest) -> Optional[GeneratedRecap]:
        """Check for existing recap (caching mechanism)"""
        try:
            # Query for existing recap with same parameters
            response = self.supabase.table("generated_recaps").select("*").eq(
                "user_id", request.user_id
            ).eq(
                "league_id", request.league_id
            ).eq(
                "week", request.week
            ).eq(
                "season", request.season
            ).eq(
                "status", RecapStatus.COMPLETED.value
            ).order("generated_at", desc=True).limit(1).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return self._row_to_recap(row)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to check for cached recap: {e}")
            return None
    
    async def _fetch_league_data(self, league_id: str) -> League:
        """Fetch league information"""
        # This would integrate with the fantasy API services
        # For now, return a mock league
        from app.models.fantasy import Platform
        
        return League(
            id=league_id,
            name="Mock Fantasy League",
            platform=Platform.YAHOO,
            platform_id="mock_123",
            current_season=2024,
            total_teams=12,
            scoring_type="standard",
            league_type="redraft"
        )
    
    async def _fetch_week_matchups(self, league_id: str, week: int, season: int) -> List[Matchup]:
        """Fetch matchup data for the week"""
        # This would integrate with the fantasy API services
        # For now, return mock matchups
        from app.models.fantasy import MatchupStatus
        
        return [
            Matchup(
                id="mock_1",
                league_id=league_id,
                week=week,
                season=season,
                home_team_id="team_1",
                away_team_id="team_2",
                home_team_name="Team Alpha",
                away_team_name="Team Beta",
                home_score=145.6,
                away_score=132.8,
                status=MatchupStatus.COMPLETED
            ),
            # Additional mock matchups would be added here
        ]
    
    async def _analyze_league_data(
        self, 
        league: League, 
        matchups: List[Matchup], 
        week: int, 
        season: int
    ) -> WeeklyInsights:
        """Analyze league data and extract insights"""
        return insight_analyzer.analyze_week(league, matchups, week, season)
    
    async def _get_user_template(self, user_id: str, template_id: Optional[str] = None) -> Optional[PromptTemplate]:
        """Get user's template for recap generation"""
        if template_id:
            # Get specific template
            template = await template_service.get_template(template_id, user_id)
            if template and template.generated_prompt:
                return template.generated_prompt
        
        # Get user's active/default template
        return await template_service.get_active_prompt_template(user_id)
    
    async def _construct_llm_prompt(
        self,
        insights: WeeklyInsights,
        request: RecapGenerationRequest,
        user_template: Optional[PromptTemplate],
        league: League,
        matchups: List[Matchup]
    ) -> str:
        """Construct the LLM prompt for recap generation"""
        
        if user_template:
            # Use user's personalized template
            from app.services.template.prompt_generator import prompt_generator
            
            league_data = {
                "league": league.dict(),
                "matchups": [m.dict() for m in matchups],
                "insights": [i.dict() for i in insights.insights],
                "statistics": {
                    "total_points": insights.total_points_scored,
                    "average_points": insights.average_points,
                    "highest_score": insights.highest_score,
                    "lowest_score": insights.lowest_score,
                    "closest_margin": insights.closest_margin,
                    "biggest_blowout": insights.biggest_blowout
                }
            }
            
            return prompt_generator.generate_recap_prompt(
                user_template, league_data, request.week, request.season, request.length
            )
        
        else:
            # Use default prompt template
            return self._generate_default_prompt(insights, request, league, matchups)
    
    def _generate_default_prompt(
        self,
        insights: WeeklyInsights,
        request: RecapGenerationRequest,
        league: League,
        matchups: List[Matchup]
    ) -> str:
        """Generate a default prompt when no user template is available"""
        
        tone_instructions = {
            RecapTone.PROFESSIONAL: "Write in a professional, analytical tone suitable for a sports publication.",
            RecapTone.HUMOROUS: "Write with humor and wit, making the recap entertaining and fun to read.",
            RecapTone.DRAMATIC: "Write with dramatic flair and excitement, bringing the action to life.",
            RecapTone.CASUAL: "Write in a casual, conversational tone as if talking to friends."
        }
        
        length_instructions = {
            RecapLength.SHORT: "Keep the recap concise and focused (300-500 words).",
            RecapLength.MEDIUM: "Write a comprehensive recap (500-800 words).",
            RecapLength.LONG: "Create a detailed, thorough recap (800+ words)."
        }
        
        tone = request.tone or RecapTone.PROFESSIONAL
        
        # Build the prompt
        prompt_parts = [
            f"You are a fantasy football analyst writing a weekly recap for Week {request.week} of the {request.season} season.",
            "",
            f"TONE: {tone_instructions[tone]}",
            f"LENGTH: {length_instructions[request.length]}",
            "",
            "LEAGUE DATA:",
            f"League: {league.name} ({league.total_teams} teams)",
            "",
            "WEEK STATISTICS:",
            f"- Total Points Scored: {insights.total_points_scored:.1f}",
            f"- Average Score: {insights.average_points:.1f}",
            f"- Highest Score: {insights.highest_score:.1f}",
            f"- Lowest Score: {insights.lowest_score:.1f}",
            f"- Closest Game: {insights.closest_margin:.1f} point margin",
            f"- Biggest Blowout: {insights.biggest_blowout:.1f} point margin",
            "",
            "KEY INSIGHTS:",
        ]
        
        for i, insight in enumerate(insights.insights[:5], 1):  # Top 5 insights
            prompt_parts.append(f"{i}. {insight.title}: {insight.description}")
        
        prompt_parts.extend([
            "",
            "MATCHUP RESULTS:",
        ])
        
        for matchup in matchups:
            if matchup.status.value == "completed":
                winner = matchup.home_team_name if matchup.home_score > matchup.away_score else matchup.away_team_name
                loser = matchup.away_team_name if matchup.home_score > matchup.away_score else matchup.home_team_name
                winner_score = max(matchup.home_score, matchup.away_score)
                loser_score = min(matchup.home_score, matchup.away_score)
                prompt_parts.append(f"- {winner} defeated {loser} {winner_score:.1f} - {loser_score:.1f}")
        
        prompt_parts.extend([
            "",
            f"Write an engaging fantasy football recap for Week {request.week} that incorporates the key insights and matchup results above. Focus on telling the story of the week with specific details about performances and outcomes."
        ])
        
        return "\n".join(prompt_parts)
    
    async def _generate_with_llm(self, prompt: str, user_id: str) -> Any:
        """Generate recap content using LLM"""
        llm_request = LLMRequest(
            prompt=prompt,
            max_tokens=1500,  # Adjust based on length preference
            temperature=0.7,
            user_id=user_id
        )
        
        return await provider_manager.generate_text(llm_request, user_id, "recap_generation")
    
    async def _process_generated_content(
        self,
        llm_response: Any,
        request: RecapGenerationRequest,
        insights: WeeklyInsights,
        user_template: Optional[PromptTemplate],
        start_time: datetime
    ) -> GeneratedRecap:
        """Process the LLM response into a GeneratedRecap"""
        
        content = llm_response.text.strip()
        word_count = len(content.split())
        
        # Extract title from content or generate one
        lines = content.split('\n')
        title = lines[0].strip() if lines else f"Week {request.week} Fantasy Recap"
        
        # If first line looks like a title, remove it from content
        if len(lines) > 1 and len(lines[0]) < 100 and not lines[0].endswith('.'):
            content = '\n'.join(lines[1:]).strip()
        
        recap = GeneratedRecap(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            league_id=request.league_id,
            week=request.week,
            season=request.season,
            title=title,
            content=content,
            word_count=word_count,
            tone_used=request.tone or RecapTone.PROFESSIONAL,
            length=request.length,
            template_id=user_template.template_id if user_template else None,
            insights_used=[insight.insight_type.value for insight in insights.insights],
            generated_at=datetime.utcnow(),
            generation_time=(datetime.utcnow() - start_time).total_seconds(),
            llm_provider=llm_response.provider_name,
            llm_model=llm_response.model_used,
            tokens_used=getattr(llm_response, 'tokens_used', 0),
            cost=getattr(llm_response, 'cost', 0.0),
            status=RecapStatus.COMPLETED
        )
        
        return recap
    
    async def _store_recap(self, recap: GeneratedRecap) -> None:
        """Store the generated recap in the database"""
        data = {
            "id": recap.id,
            "user_id": recap.user_id,
            "league_id": recap.league_id,
            "week": recap.week,
            "season": recap.season,
            "title": recap.title,
            "content": recap.content,
            "word_count": recap.word_count,
            "tone_used": recap.tone_used.value,
            "length": recap.length.value,
            "template_id": recap.template_id,
            "insights_used": recap.insights_used,
            "generated_at": recap.generated_at.isoformat(),
            "generation_time": recap.generation_time,
            "llm_provider": recap.llm_provider,
            "llm_model": recap.llm_model,
            "tokens_used": recap.tokens_used,
            "cost": recap.cost,
            "status": recap.status.value,
            "style_match_score": recap.style_match_score,
            "content_completeness": recap.content_completeness
        }
        
        response = self.supabase.table("generated_recaps").insert(data).execute()
        if not response.data:
            raise Exception("Failed to store recap in database")
    
    async def _assess_quality(
        self, 
        recap: GeneratedRecap, 
        user_template: Optional[PromptTemplate], 
        insights: WeeklyInsights
    ) -> float:
        """Assess the quality of the generated recap"""
        score = 0.7  # Base score
        
        # Length appropriateness
        target_lengths = {
            RecapLength.SHORT: (300, 500),
            RecapLength.MEDIUM: (500, 800),
            RecapLength.LONG: (800, 1200)
        }
        
        target_min, target_max = target_lengths[recap.length]
        if target_min <= recap.word_count <= target_max:
            score += 0.2
        elif abs(recap.word_count - target_min) < 100:
            score += 0.1
        
        # Content completeness (has insights)
        if recap.insights_used:
            score += 0.1
        
        return min(1.0, score)
    
    async def _generate_recommendations(self, recap: GeneratedRecap, quality_score: float) -> List[str]:
        """Generate recommendations for improving future recaps"""
        recommendations = []
        
        if quality_score < 0.7:
            recommendations.append("Consider uploading a style template to improve personalization")
        
        if recap.word_count < 200:
            recommendations.append("Try using a longer length setting for more detailed recaps")
        
        if not recap.insights_used:
            recommendations.append("Ensure league data is available for more insightful content")
        
        return recommendations
    
    def _extract_template_info(self, template: PromptTemplate) -> Dict[str, Any]:
        """Extract template information for response"""
        return {
            "template_id": template.template_id,
            "tone": template.based_on_analysis.tone.value,
            "usage_count": template.usage_count,
            "is_default": template.is_default
        }
    
    def _row_to_recap(self, row: Dict[str, Any]) -> GeneratedRecap:
        """Convert database row to GeneratedRecap"""
        return GeneratedRecap(
            id=row["id"],
            user_id=row["user_id"],
            league_id=row["league_id"],
            week=row["week"],
            season=row["season"],
            title=row["title"],
            content=row["content"],
            word_count=row["word_count"],
            tone_used=RecapTone(row["tone_used"]),
            length=RecapLength(row["length"]),
            template_id=row.get("template_id"),
            insights_used=row.get("insights_used", []),
            generated_at=datetime.fromisoformat(row["generated_at"]),
            generation_time=row["generation_time"],
            llm_provider=row["llm_provider"],
            llm_model=row["llm_model"],
            tokens_used=row["tokens_used"],
            cost=row["cost"],
            status=RecapStatus(row["status"]),
            style_match_score=row.get("style_match_score"),
            content_completeness=row.get("content_completeness")
        )


# Global instance
recap_generator = RecapGenerator()
