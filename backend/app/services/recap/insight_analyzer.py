"""
Insight analysis service for fantasy football data
Extracts key insights like top performers, underachievers, trends, etc.
"""

import logging
import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.models.recap import (
    PerformanceInsight, InsightType, WeeklyInsights, InsightAnalysisConfig
)
from app.models.fantasy import League, Matchup, Team, Player, MatchupStatus

logger = logging.getLogger(__name__)


class InsightAnalyzer:
    """Service for analyzing fantasy league data and extracting insights"""
    
    def __init__(self, config: Optional[InsightAnalysisConfig] = None):
        self.config = config or InsightAnalysisConfig()
    
    def analyze_week(
        self, 
        league: League, 
        matchups: List[Matchup], 
        week: int, 
        season: int,
        historical_data: Optional[List[Matchup]] = None
    ) -> WeeklyInsights:
        """
        Analyze a week's worth of fantasy data and extract insights
        
        Args:
            league: League information
            matchups: List of matchups for the week
            week: Week number
            season: Season year
            historical_data: Previous weeks' data for trend analysis
            
        Returns:
            WeeklyInsights: Comprehensive insights for the week
        """
        try:
            # Calculate week statistics
            week_stats = self._calculate_week_statistics(matchups)
            
            # Extract various types of insights
            insights = []
            
            # Performance-based insights
            insights.extend(self._identify_top_performers(matchups, week, season))
            insights.extend(self._identify_underachievers(matchups, week, season))
            insights.extend(self._identify_notable_performances(matchups, week, season))
            
            # Matchup-based insights
            insights.extend(self._identify_close_matchups(matchups, week, season))
            insights.extend(self._identify_blowouts(matchups, week, season))
            insights.extend(self._identify_comeback_stories(matchups, week, season))
            
            # Trend analysis (if historical data available)
            if historical_data:
                insights.extend(self._analyze_trends(matchups, historical_data, week, season))
            
            # Filter and rank insights
            insights = self._filter_and_rank_insights(insights)
            
            return WeeklyInsights(
                week=week,
                season=season,
                league_id=league.id,
                insights=insights,
                total_points_scored=week_stats["total_points"],
                average_points=week_stats["average_points"],
                highest_score=week_stats["highest_score"],
                lowest_score=week_stats["lowest_score"],
                closest_margin=week_stats["closest_margin"],
                biggest_blowout=week_stats["biggest_blowout"],
                generated_at=datetime.utcnow(),
                data_source=f"league_{league.id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze week {week}: {e}")
            raise
    
    def _calculate_week_statistics(self, matchups: List[Matchup]) -> Dict[str, float]:
        """Calculate basic statistics for the week"""
        all_scores = []
        margins = []
        
        for matchup in matchups:
            if matchup.status == MatchupStatus.COMPLETED:
                scores = [matchup.home_score, matchup.away_score]
                all_scores.extend(scores)
                margins.append(abs(matchup.home_score - matchup.away_score))
        
        return {
            "total_points": sum(all_scores),
            "average_points": statistics.mean(all_scores) if all_scores else 0,
            "highest_score": max(all_scores) if all_scores else 0,
            "lowest_score": min(all_scores) if all_scores else 0,
            "closest_margin": min(margins) if margins else 0,
            "biggest_blowout": max(margins) if margins else 0
        }
    
    def _identify_top_performers(self, matchups: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Identify top performing teams for the week"""
        insights = []
        all_scores = []
        
        # Collect all scores with team info
        for matchup in matchups:
            if matchup.status == MatchupStatus.COMPLETED:
                all_scores.append((matchup.home_team_name, matchup.home_score))
                all_scores.append((matchup.away_team_name, matchup.away_score))
        
        if not all_scores:
            return insights
        
        # Sort by score
        all_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate percentile threshold
        scores_only = [score for _, score in all_scores]
        high_score_threshold = statistics.quantiles(scores_only, n=10)[int(self.config.high_score_percentile * 10) - 1]
        
        # Create insights for top performers
        for i, (team_name, score) in enumerate(all_scores[:3]):  # Top 3
            if score >= high_score_threshold:
                rank_suffix = ["st", "nd", "rd"][i] if i < 3 else "th"
                
                insights.append(PerformanceInsight(
                    insight_type=InsightType.TOP_PERFORMER,
                    title=f"{team_name} Dominates Week {week}",
                    description=f"{team_name} scored {score:.1f} points, ranking {i+1}{rank_suffix} for the week",
                    primary_team=team_name,
                    score_impact=score,
                    week=week,
                    season=season,
                    confidence_score=0.9,
                    is_positive=True,
                    narrative_weight=0.8 - (i * 0.1),
                    supporting_data={
                        "rank": i + 1,
                        "percentile": (len(all_scores) - i) / len(all_scores),
                        "points_above_average": score - statistics.mean(scores_only)
                    }
                ))
        
        return insights
    
    def _identify_underachievers(self, matchups: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Identify underperforming teams"""
        insights = []
        all_scores = []
        
        # Collect all scores
        for matchup in matchups:
            if matchup.status == MatchupStatus.COMPLETED:
                all_scores.append((matchup.home_team_name, matchup.home_score))
                all_scores.append((matchup.away_team_name, matchup.away_score))
        
        if not all_scores:
            return insights
        
        # Sort by score (lowest first)
        all_scores.sort(key=lambda x: x[1])
        
        # Calculate low score threshold
        scores_only = [score for _, score in all_scores]
        low_score_threshold = statistics.quantiles(scores_only, n=10)[int(self.config.low_score_percentile * 10) - 1]
        
        # Create insights for underachievers
        for i, (team_name, score) in enumerate(all_scores[:2]):  # Bottom 2
            if score <= low_score_threshold:
                insights.append(PerformanceInsight(
                    insight_type=InsightType.UNDERACHIEVER,
                    title=f"{team_name} Struggles in Week {week}",
                    description=f"{team_name} managed only {score:.1f} points, one of the lowest scores this week",
                    primary_team=team_name,
                    score_impact=score,
                    week=week,
                    season=season,
                    confidence_score=0.8,
                    is_positive=False,
                    narrative_weight=0.6 - (i * 0.1),
                    supporting_data={
                        "rank_from_bottom": i + 1,
                        "points_below_average": statistics.mean(scores_only) - score,
                        "percentile": (i + 1) / len(all_scores)
                    }
                ))
        
        return insights
    
    def _identify_close_matchups(self, matchups: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Identify nail-biting close matchups"""
        insights = []
        
        for matchup in matchups:
            if matchup.status == MatchupStatus.COMPLETED:
                margin = abs(matchup.home_score - matchup.away_score)
                
                if margin <= self.config.close_game_threshold:
                    winner = matchup.home_team_name if matchup.home_score > matchup.away_score else matchup.away_team_name
                    loser = matchup.away_team_name if matchup.home_score > matchup.away_score else matchup.home_team_name
                    
                    insights.append(PerformanceInsight(
                        insight_type=InsightType.CLOSE_MATCHUP,
                        title=f"Nail-Biter: {winner} Edges {loser}",
                        description=f"In a thrilling matchup, {winner} barely defeated {loser} by just {margin:.1f} points",
                        primary_team=winner,
                        secondary_team=loser,
                        score_impact=margin,
                        week=week,
                        season=season,
                        confidence_score=0.95,
                        is_positive=True,  # Close games are exciting
                        narrative_weight=0.7,
                        supporting_data={
                            "margin": margin,
                            "winner_score": max(matchup.home_score, matchup.away_score),
                            "loser_score": min(matchup.home_score, matchup.away_score)
                        }
                    ))
        
        return insights
    
    def _identify_blowouts(self, matchups: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Identify lopsided blowout games"""
        insights = []
        
        for matchup in matchups:
            if matchup.status == MatchupStatus.COMPLETED:
                margin = abs(matchup.home_score - matchup.away_score)
                
                if margin >= self.config.blowout_threshold:
                    winner = matchup.home_team_name if matchup.home_score > matchup.away_score else matchup.away_team_name
                    loser = matchup.away_team_name if matchup.home_score > matchup.away_score else matchup.home_team_name
                    
                    insights.append(PerformanceInsight(
                        insight_type=InsightType.BLOWOUT,
                        title=f"Blowout Alert: {winner} Crushes {loser}",
                        description=f"{winner} dominated {loser} in a lopsided {margin:.1f}-point victory",
                        primary_team=winner,
                        secondary_team=loser,
                        score_impact=margin,
                        week=week,
                        season=season,
                        confidence_score=0.9,
                        is_positive=False,  # Blowouts are less exciting
                        narrative_weight=0.6,
                        supporting_data={
                            "margin": margin,
                            "winner_score": max(matchup.home_score, matchup.away_score),
                            "loser_score": min(matchup.home_score, matchup.away_score)
                        }
                    ))
        
        return insights
    
    def _identify_notable_performances(self, matchups: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Identify particularly notable individual performances"""
        insights = []
        
        # This would typically analyze individual player performances
        # For now, we'll identify teams with exceptionally high scores
        all_scores = []
        for matchup in matchups:
            if matchup.status == MatchupStatus.COMPLETED:
                all_scores.extend([
                    (matchup.home_team_name, matchup.home_score),
                    (matchup.away_team_name, matchup.away_score)
                ])
        
        if not all_scores:
            return insights
        
        scores_only = [score for _, score in all_scores]
        exceptional_threshold = statistics.mean(scores_only) + (2 * statistics.stdev(scores_only))
        
        for team_name, score in all_scores:
            if score >= exceptional_threshold:
                insights.append(PerformanceInsight(
                    insight_type=InsightType.NOTABLE_PERFORMANCE,
                    title=f"Exceptional Week for {team_name}",
                    description=f"{team_name} posted an outstanding {score:.1f} points, well above the weekly average",
                    primary_team=team_name,
                    score_impact=score,
                    week=week,
                    season=season,
                    confidence_score=0.85,
                    is_positive=True,
                    narrative_weight=0.7,
                    supporting_data={
                        "points_above_average": score - statistics.mean(scores_only),
                        "standard_deviations_above": (score - statistics.mean(scores_only)) / statistics.stdev(scores_only)
                    }
                ))
        
        return insights
    
    def _identify_comeback_stories(self, matchups: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Identify potential comeback stories (placeholder for future implementation)"""
        insights = []
        
        # This would analyze projected vs actual scores, or previous week comparisons
        # For now, return empty list as this requires more complex data
        
        return insights
    
    def _analyze_trends(self, current_matchups: List[Matchup], historical_data: List[Matchup], week: int, season: int) -> List[PerformanceInsight]:
        """Analyze multi-week trends"""
        insights = []
        
        # This would analyze trends like win streaks, scoring trends, etc.
        # For now, return empty list as this requires more complex historical analysis
        
        return insights
    
    def _filter_and_rank_insights(self, insights: List[PerformanceInsight]) -> List[PerformanceInsight]:
        """Filter insights by quality and rank by narrative importance"""
        # Filter by confidence score
        filtered = [
            insight for insight in insights 
            if insight.confidence_score >= self.config.min_confidence_score
        ]
        
        # Limit insights per type
        type_counts = {}
        final_insights = []
        
        for insight in sorted(filtered, key=lambda x: x.narrative_weight, reverse=True):
            count = type_counts.get(insight.insight_type, 0)
            if count < self.config.max_insights_per_type:
                final_insights.append(insight)
                type_counts[insight.insight_type] = count + 1
        
        # Filter by narrative weight threshold
        final_insights = [
            insight for insight in final_insights
            if insight.narrative_weight >= self.config.narrative_weight_threshold
        ]
        
        # Sort by narrative weight
        final_insights.sort(key=lambda x: x.narrative_weight, reverse=True)
        
        return final_insights


# Global instance
insight_analyzer = InsightAnalyzer()
