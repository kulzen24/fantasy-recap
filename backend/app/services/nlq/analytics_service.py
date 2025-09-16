"""
Fantasy Analytics Service for Natural Language Queries
Processes fantasy data to answer parsed queries with statistical insights
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from statistics import mean, median
import math

from app.models.fantasy import League, Team, Player, Matchup, PlayerPosition
from app.models.nlq import ParsedQuery, QueryType, QueryIntent, QueryResponse
from app.services.fantasy.base_service import BaseFantasyService

logger = logging.getLogger(__name__)


class FantasyAnalyticsService:
    """Analyzes fantasy data to answer natural language queries"""
    
    def __init__(self, fantasy_service: BaseFantasyService):
        self.fantasy_service = fantasy_service
    
    async def analyze_query(
        self, 
        parsed_query: ParsedQuery, 
        league_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a parsed query against fantasy data
        
        Args:
            parsed_query: Structured query object
            league_id: Target league ID
            user_id: User making the query
            
        Returns:
            Dictionary with analysis results and supporting data
        """
        try:
            # Get league data
            league_response = await self.fantasy_service.get_league(league_id)
            if not league_response.success or not league_response.data:
                raise ValueError(f"Could not retrieve league data for {league_id}")
            
            league = league_response.data
            
            # Route to appropriate analysis method
            if parsed_query.query_type == QueryType.PLAYER_STATS:
                return await self._analyze_player_stats(parsed_query, league, user_id)
            elif parsed_query.query_type == QueryType.TEAM_PERFORMANCE:
                return await self._analyze_team_performance(parsed_query, league, user_id)
            elif parsed_query.query_type == QueryType.LEAGUE_STANDINGS:
                return await self._analyze_league_standings(parsed_query, league, user_id)
            elif parsed_query.query_type == QueryType.MATCHUP_ANALYSIS:
                return await self._analyze_matchups(parsed_query, league, user_id)
            elif parsed_query.query_type == QueryType.SEASON_TRENDS:
                return await self._analyze_season_trends(parsed_query, league, user_id)
            elif parsed_query.query_type == QueryType.PLAYER_COMPARISON:
                return await self._analyze_player_comparison(parsed_query, league, user_id)
            elif parsed_query.query_type == QueryType.TEAM_COMPARISON:
                return await self._analyze_team_comparison(parsed_query, league, user_id)
            else:
                return await self._analyze_general_insights(parsed_query, league, user_id)
                
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {
                "error": str(e),
                "supporting_data": {},
                "visualizations": []
            }
    
    async def _analyze_player_stats(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze player statistics queries"""
        
        # Find target players
        target_players = self._find_players_by_query(parsed_query, league)
        
        if not target_players:
            return {
                "answer": "I couldn't find any players matching your query.",
                "supporting_data": {"players_found": 0},
                "visualizations": []
            }
        
        # Get current week or specified week
        week = league.current_week
        if parsed_query.week_range:
            week = parsed_query.week_range[0]
        
        # Analyze based on intent
        if parsed_query.intent == QueryIntent.GET_STATS:
            return self._get_player_stats(target_players, week, parsed_query)
        elif parsed_query.intent == QueryIntent.COMPARE:
            return self._compare_players(target_players, week, parsed_query)
        else:
            return self._analyze_player_trends(target_players, league, parsed_query)
    
    def _get_player_stats(
        self, 
        players: List[Player], 
        week: int, 
        parsed_query: ParsedQuery
    ) -> Dict[str, Any]:
        """Get basic player statistics"""
        
        # Find highest scoring player if looking for "most points"
        has_points_entity = any(e.value in ["points", "most", "highest"] for e in parsed_query.entities)
        
        if has_points_entity:
            # Sort by actual points (descending)
            sorted_players = sorted(players, key=lambda p: p.actual_points or 0, reverse=True)
            top_player = sorted_players[0] if sorted_players else None
            
            if top_player:
                answer = f"{top_player.name} ({top_player.position.value}) scored the most points with {top_player.actual_points:.1f} points"
                if top_player.team:
                    answer += f" for the {top_player.team}"
                answer += f" in week {week}."
                
                return {
                    "answer": answer,
                    "supporting_data": {
                        "top_player": {
                            "name": top_player.name,
                            "position": top_player.position.value,
                            "points": top_player.actual_points,
                            "team": top_player.team,
                            "week": week
                        },
                        "all_players": [
                            {
                                "name": p.name,
                                "position": p.position.value,
                                "points": p.actual_points,
                                "team": p.team
                            } for p in sorted_players[:5]  # Top 5
                        ]
                    },
                    "visualizations": [
                        {
                            "type": "bar_chart",
                            "title": f"Top Scoring Players - Week {week}",
                            "data": [
                                {"name": p.name, "points": p.actual_points or 0}
                                for p in sorted_players[:10]
                            ]
                        }
                    ]
                }
        
        # Default stats response
        player = players[0]
        return {
            "answer": f"{player.name} ({player.position.value}) has {player.actual_points or 0:.1f} actual points and {player.projected_points or 0:.1f} projected points in week {week}.",
            "supporting_data": {
                "player": {
                    "name": player.name,
                    "position": player.position.value,
                    "actual_points": player.actual_points,
                    "projected_points": player.projected_points,
                    "team": player.team,
                    "week": week
                }
            },
            "visualizations": []
        }
    
    async def _analyze_team_performance(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze team performance queries"""
        
        # Find user's team
        user_team = self._find_user_team(league, user_id)
        if not user_team:
            return {
                "answer": "I couldn't find your team in this league.",
                "supporting_data": {},
                "visualizations": []
            }
        
        # Calculate league averages
        league_stats = self._calculate_league_averages(league)
        
        # Compare to league average
        team_avg = user_team.points_for / max(user_team.wins + user_team.losses + user_team.ties, 1)
        league_avg = league_stats["avg_points_per_game"]
        
        comparison = "above" if team_avg > league_avg else "below"
        difference = abs(team_avg - league_avg)
        
        answer = f"Your team ({user_team.name}) is performing {comparison} league average. "
        answer += f"You're averaging {team_avg:.1f} points per game vs league average of {league_avg:.1f} "
        answer += f"({difference:.1f} points {comparison} average). "
        
        # Add record context
        total_games = user_team.wins + user_team.losses + user_team.ties
        if total_games > 0:
            win_pct = user_team.wins / total_games * 100
            answer += f"Your record is {user_team.wins}-{user_team.losses}"
            if user_team.ties > 0:
                answer += f"-{user_team.ties}"
            answer += f" ({win_pct:.1f}%)."
        
        return {
            "answer": answer,
            "supporting_data": {
                "user_team": {
                    "name": user_team.name,
                    "record": f"{user_team.wins}-{user_team.losses}-{user_team.ties}",
                    "points_for": user_team.points_for,
                    "points_against": user_team.points_against,
                    "avg_points": team_avg
                },
                "league_averages": league_stats,
                "comparison": {
                    "performance": comparison,
                    "difference": difference
                }
            },
            "visualizations": [
                {
                    "type": "comparison_chart",
                    "title": "Team vs League Average",
                    "data": {
                        "your_team": team_avg,
                        "league_average": league_avg,
                        "difference": difference
                    }
                }
            ]
        }
    
    async def _analyze_matchups(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze matchup-related queries"""
        
        current_matchups = league.current_matchups
        if not current_matchups:
            return {
                "answer": "No matchup data available for the current week.",
                "supporting_data": {},
                "visualizations": []
            }
        
        # Look for "closest" matchup
        has_closest_entity = any(e.value in ["closest", "close"] for e in parsed_query.entities)
        
        if has_closest_entity:
            # Find closest matchup by point difference
            closest_matchup = None
            smallest_diff = float('inf')
            
            for matchup in current_matchups:
                if matchup.team1_score is not None and matchup.team2_score is not None:
                    diff = abs(matchup.team1_score - matchup.team2_score)
                    if diff < smallest_diff:
                        smallest_diff = diff
                        closest_matchup = matchup
            
            if closest_matchup:
                team1 = self._find_team_by_id(league, closest_matchup.team1_id)
                team2 = self._find_team_by_id(league, closest_matchup.team2_id)
                
                answer = f"The closest matchup this week is {team1.name if team1 else 'Team 1'} "
                answer += f"vs {team2.name if team2 else 'Team 2'} with a difference of "
                answer += f"{smallest_diff:.1f} points ({closest_matchup.team1_score:.1f} - {closest_matchup.team2_score:.1f})."
                
                return {
                    "answer": answer,
                    "supporting_data": {
                        "closest_matchup": {
                            "team1": team1.name if team1 else "Team 1",
                            "team2": team2.name if team2 else "Team 2",
                            "team1_score": closest_matchup.team1_score,
                            "team2_score": closest_matchup.team2_score,
                            "difference": smallest_diff,
                            "week": closest_matchup.week
                        }
                    },
                    "visualizations": [
                        {
                            "type": "matchup_chart",
                            "title": f"Closest Matchup - Week {closest_matchup.week}",
                            "data": {
                                "team1": {"name": team1.name if team1 else "Team 1", "score": closest_matchup.team1_score},
                                "team2": {"name": team2.name if team2 else "Team 2", "score": closest_matchup.team2_score}
                            }
                        }
                    ]
                }
        
        # Default: show all current matchups
        matchup_summaries = []
        for matchup in current_matchups:
            team1 = self._find_team_by_id(league, matchup.team1_id)
            team2 = self._find_team_by_id(league, matchup.team2_id)
            matchup_summaries.append({
                "team1": team1.name if team1 else "Team 1",
                "team2": team2.name if team2 else "Team 2",
                "team1_score": matchup.team1_score,
                "team2_score": matchup.team2_score,
                "status": matchup.status.value
            })
        
        return {
            "answer": f"Here are this week's matchups for week {league.current_week}:",
            "supporting_data": {
                "matchups": matchup_summaries,
                "week": league.current_week,
                "total_matchups": len(current_matchups)
            },
            "visualizations": [
                {
                    "type": "matchups_overview",
                    "title": f"Week {league.current_week} Matchups",
                    "data": matchup_summaries
                }
            ]
        }
    
    async def _analyze_league_standings(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze league standings and rankings"""
        
        # Sort teams by wins, then by points for
        sorted_teams = sorted(
            league.teams, 
            key=lambda t: (t.wins, t.points_for), 
            reverse=True
        )
        
        standings = []
        for i, team in enumerate(sorted_teams):
            total_games = team.wins + team.losses + team.ties
            win_pct = (team.wins / total_games * 100) if total_games > 0 else 0
            
            standings.append({
                "rank": i + 1,
                "team": team.name,
                "record": f"{team.wins}-{team.losses}-{team.ties}",
                "win_percentage": win_pct,
                "points_for": team.points_for,
                "points_against": team.points_against,
                "point_differential": team.points_for - team.points_against
            })
        
        # Find user's team ranking
        user_team = self._find_user_team(league, user_id)
        user_rank = None
        if user_team:
            for standing in standings:
                if standing["team"] == user_team.name:
                    user_rank = standing["rank"]
                    break
        
        answer = f"Current league standings for {league.name}:\n"
        for standing in standings[:5]:  # Top 5
            answer += f"{standing['rank']}. {standing['team']} ({standing['record']}) - {standing['points_for']:.1f} PF\n"
        
        if user_rank:
            answer += f"\nYour team is currently ranked #{user_rank}."
        
        return {
            "answer": answer.strip(),
            "supporting_data": {
                "standings": standings,
                "user_rank": user_rank,
                "league_name": league.name,
                "total_teams": len(league.teams)
            },
            "visualizations": [
                {
                    "type": "standings_table",
                    "title": f"{league.name} Standings",
                    "data": standings
                }
            ]
        }
    
    async def _analyze_season_trends(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze season-long trends"""
        
        # This is a simplified version - in real implementation, 
        # you'd fetch historical week data
        
        return {
            "answer": "Season trends analysis requires historical data that isn't available in this demo.",
            "supporting_data": {
                "message": "Feature requires week-by-week historical data"
            },
            "visualizations": []
        }
    
    async def _analyze_player_comparison(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Compare multiple players"""
        
        players = self._find_players_by_query(parsed_query, league)
        
        if len(players) < 2:
            return {
                "answer": "I need at least two players to make a comparison.",
                "supporting_data": {},
                "visualizations": []
            }
        
        # Compare top 2 players
        p1, p2 = players[0], players[1]
        
        answer = f"Comparing {p1.name} vs {p2.name}:\n"
        answer += f"{p1.name}: {p1.actual_points or 0:.1f} actual points, {p1.projected_points or 0:.1f} projected\n"
        answer += f"{p2.name}: {p2.actual_points or 0:.1f} actual points, {p2.projected_points or 0:.1f} projected"
        
        return {
            "answer": answer,
            "supporting_data": {
                "comparison": [
                    {
                        "name": p1.name,
                        "position": p1.position.value,
                        "actual_points": p1.actual_points,
                        "projected_points": p1.projected_points
                    },
                    {
                        "name": p2.name,
                        "position": p2.position.value,
                        "actual_points": p2.actual_points,
                        "projected_points": p2.projected_points
                    }
                ]
            },
            "visualizations": [
                {
                    "type": "player_comparison",
                    "title": f"{p1.name} vs {p2.name}",
                    "data": {
                        "players": [p1.name, p2.name],
                        "actual_points": [p1.actual_points or 0, p2.actual_points or 0],
                        "projected_points": [p1.projected_points or 0, p2.projected_points or 0]
                    }
                }
            ]
        }
    
    async def _analyze_team_comparison(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """Compare multiple teams"""
        
        # Simple team comparison
        if len(league.teams) >= 2:
            t1, t2 = league.teams[0], league.teams[1]
            
            answer = f"Comparing {t1.name} vs {t2.name}:\n"
            answer += f"{t1.name}: {t1.wins}-{t1.losses} record, {t1.points_for:.1f} PF\n"
            answer += f"{t2.name}: {t2.wins}-{t2.losses} record, {t2.points_for:.1f} PF"
            
            return {
                "answer": answer,
                "supporting_data": {
                    "teams": [
                        {"name": t1.name, "record": f"{t1.wins}-{t1.losses}", "points_for": t1.points_for},
                        {"name": t2.name, "record": f"{t2.wins}-{t2.losses}", "points_for": t2.points_for}
                    ]
                },
                "visualizations": []
            }
        
        return {
            "answer": "Not enough teams for comparison.",
            "supporting_data": {},
            "visualizations": []
        }
    
    async def _analyze_general_insights(
        self, 
        parsed_query: ParsedQuery, 
        league: League, 
        user_id: str
    ) -> Dict[str, Any]:
        """General league insights"""
        
        league_stats = self._calculate_league_averages(league)
        
        answer = f"League insights for {league.name}:\n"
        answer += f"- {len(league.teams)} teams in week {league.current_week}\n"
        answer += f"- Average points per game: {league_stats['avg_points_per_game']:.1f}\n"
        answer += f"- Scoring type: {league.scoring_type}"
        
        return {
            "answer": answer,
            "supporting_data": {
                "league_stats": league_stats,
                "league_info": {
                    "name": league.name,
                    "teams": len(league.teams),
                    "current_week": league.current_week,
                    "scoring_type": league.scoring_type
                }
            },
            "visualizations": []
        }
    
    # Helper methods
    
    def _find_players_by_query(self, parsed_query: ParsedQuery, league: League) -> List[Player]:
        """Find players mentioned in query"""
        all_players = []
        for team in league.teams:
            all_players.extend(team.roster)
        
        # If specific player names in entities, find those
        for entity in parsed_query.entities:
            if entity.entity_type == "player" and " " in entity.value:
                # Look for player by name
                for player in all_players:
                    if entity.value.lower() in player.name.lower():
                        return [player]
        
        # If position mentioned, return players from that position
        for entity in parsed_query.entities:
            if entity.entity_type == "position":
                position_players = [
                    p for p in all_players 
                    if p.position.value.lower() == entity.value.lower() or 
                       entity.value.lower() in ["rb", "running back"] and p.position == PlayerPosition.RB
                ]
                if position_players:
                    return position_players
        
        # Default: return all players
        return all_players
    
    def _find_user_team(self, league: League, user_id: str) -> Optional[Team]:
        """Find the user's team in the league"""
        # In a real implementation, you'd have a mapping of user_id to team_id
        # For now, just return the first team as a placeholder
        return league.teams[0] if league.teams else None
    
    def _find_team_by_id(self, league: League, team_id: str) -> Optional[Team]:
        """Find team by ID"""
        for team in league.teams:
            if team.id == team_id:
                return team
        return None
    
    def _calculate_league_averages(self, league: League) -> Dict[str, float]:
        """Calculate league-wide averages"""
        if not league.teams:
            return {"avg_points_per_game": 0.0, "avg_points_for": 0.0, "avg_points_against": 0.0}
        
        total_points = sum(team.points_for for team in league.teams)
        total_games = sum(team.wins + team.losses + team.ties for team in league.teams)
        
        return {
            "avg_points_per_game": total_points / max(total_games, 1),
            "avg_points_for": total_points / len(league.teams),
            "avg_points_against": sum(team.points_against for team in league.teams) / len(league.teams)
        }
