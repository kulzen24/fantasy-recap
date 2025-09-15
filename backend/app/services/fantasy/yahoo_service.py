"""
Yahoo Fantasy Sports API Service
Handles OAuth2 authentication, API requests, and data normalization for Yahoo Fantasy
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# import aiohttp  # For future use
from yahoo_oauth import OAuth2
import yahoo_fantasy_api as yfa
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.fantasy import (
    FantasyApiResponse, League, Team, Player, Matchup, WeeklyStats,
    FantasyPlatform, PlayerPosition, MatchupStatus
)
from app.services.fantasy.base_service import BaseFantasyService

logger = logging.getLogger(__name__)


class YahooFantasyService(BaseFantasyService):
    """Service for interacting with Yahoo Fantasy Sports API"""
    
    def __init__(self, 
                 consumer_key: Optional[str] = None,
                 consumer_secret: Optional[str] = None,
                 token_file: Optional[str] = None):
        """
        Initialize Yahoo Fantasy service
        
        Args:
            consumer_key: Yahoo app consumer key
            consumer_secret: Yahoo app consumer secret
            token_file: Path to OAuth2 token file
        """
        self.platform = FantasyPlatform.YAHOO
        self.consumer_key = consumer_key or settings.YAHOO_CLIENT_ID
        self.consumer_secret = consumer_secret or settings.YAHOO_CLIENT_SECRET
        self.token_file = token_file or "yahoo_oauth.json"
        
        self._oauth_client: Optional[OAuth2] = None
        self._game_manager: Optional[yfa.Game] = None
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
    async def authenticate(self) -> bool:
        """
        Authenticate with Yahoo using OAuth2
        
        Returns:
            bool: True if authentication successful
        """
        try:
            if not self.consumer_key or not self.consumer_secret:
                logger.error("Yahoo client ID and secret are required")
                return False
                
            # Initialize OAuth2 client
            self._oauth_client = OAuth2(
                self.consumer_key,
                self.consumer_secret,
                from_file=self.token_file
            )
            
            # Test authentication by getting game manager
            self._game_manager = yfa.Game(self._oauth_client, 'nfl')
            
            # Verify we can make a basic API call
            await self._make_api_call(lambda: self._game_manager.league_ids(year=2024))
            
            logger.info("Yahoo Fantasy authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Yahoo Fantasy authentication failed: {e}")
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _make_api_call(self, api_func, *args, **kwargs):
        """
        Make rate-limited API call with retry logic
        
        Args:
            api_func: API function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            API response
        """
        # Rate limiting
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        
        try:
            # Run in thread pool since yahoo_fantasy_api is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, api_func, *args, **kwargs)
            
            self._last_request_time = datetime.now().timestamp()
            return result
            
        except Exception as e:
            logger.warning(f"Yahoo API call failed: {e}")
            raise
    
    async def get_user_leagues(self, year: int = 2024) -> FantasyApiResponse:
        """
        Get all leagues for the authenticated user
        
        Args:
            year: NFL season year
            
        Returns:
            FantasyApiResponse with leagues data
        """
        try:
            if not self._game_manager:
                await self.authenticate()
                
            league_ids = await self._make_api_call(
                lambda: self._game_manager.league_ids(year=year)
            )
            
            leagues = []
            for league_id in league_ids:
                league_data = await self.get_league(league_id, year)
                if league_data.success:
                    leagues.append(league_data.data)
            
            return FantasyApiResponse(
                success=True,
                data=leagues,
                platform=FantasyPlatform.YAHOO
            )
            
        except Exception as e:
            logger.error(f"Failed to get user leagues: {e}")
            return FantasyApiResponse(
                success=False,
                error=str(e),
                platform=FantasyPlatform.YAHOO
            )
    
    async def get_league(self, league_id: str, year: int = 2024) -> FantasyApiResponse:
        """
        Get league information
        
        Args:
            league_id: Yahoo league ID
            year: NFL season year
            
        Returns:
            FantasyApiResponse with League data
        """
        try:
            if not self._game_manager:
                await self.authenticate()
                
            # Get league object
            league_obj = await self._make_api_call(
                lambda: self._game_manager.to_league(league_id)
            )
            
            # Get league settings and metadata
            settings_data = await self._make_api_call(lambda: league_obj.settings())
            teams_data = await self._make_api_call(lambda: league_obj.teams())
            
            # Normalize league data
            league = League(
                id=f"yahoo_{league_id}",
                platform_id=league_id,
                platform=FantasyPlatform.YAHOO,
                name=settings_data.get('name', f'League {league_id}'),
                total_teams=len(teams_data),
                current_week=settings_data.get('current_week', 1),
                current_season=year,
                scoring_type=self._normalize_scoring_type(settings_data.get('scoring_type')),
                teams=await self._normalize_teams(teams_data),
                metadata={
                    'yahoo_settings': settings_data,
                    'playoff_start_week': settings_data.get('playoff_start_week'),
                    'trade_deadline': settings_data.get('trade_deadline')
                }
            )
            
            return FantasyApiResponse(
                success=True,
                data=league,
                platform=FantasyPlatform.YAHOO
            )
            
        except Exception as e:
            logger.error(f"Failed to get league {league_id}: {e}")
            return FantasyApiResponse(
                success=False,
                error=str(e),
                platform=FantasyPlatform.YAHOO
            )
    
    async def get_matchups(self, league_id: str, week: int, year: int = 2024) -> FantasyApiResponse:
        """
        Get matchups for a specific week
        
        Args:
            league_id: Yahoo league ID
            week: NFL week number
            year: NFL season year
            
        Returns:
            FantasyApiResponse with matchups data
        """
        try:
            if not self._game_manager:
                await self.authenticate()
                
            league_obj = await self._make_api_call(
                lambda: self._game_manager.to_league(league_id)
            )
            
            # Get scoreboard for the week
            scoreboard_data = await self._make_api_call(
                lambda: league_obj.scoreboard(week=week)
            )
            
            matchups = await self._normalize_matchups(scoreboard_data, week, year)
            
            return FantasyApiResponse(
                success=True,
                data=matchups,
                platform=FantasyPlatform.YAHOO
            )
            
        except Exception as e:
            logger.error(f"Failed to get matchups for league {league_id}, week {week}: {e}")
            return FantasyApiResponse(
                success=False,
                error=str(e),
                platform=FantasyPlatform.YAHOO
            )
    
    async def get_team_roster(self, league_id: str, team_id: str, week: Optional[int] = None) -> FantasyApiResponse:
        """
        Get team roster for a specific week
        
        Args:
            league_id: Yahoo league ID
            team_id: Yahoo team ID
            week: NFL week number (optional, defaults to current week)
            
        Returns:
            FantasyApiResponse with roster data
        """
        try:
            if not self._game_manager:
                await self.authenticate()
                
            league_obj = await self._make_api_call(
                lambda: self._game_manager.to_league(league_id)
            )
            
            team_obj = await self._make_api_call(
                lambda: league_obj.to_team(team_id)
            )
            
            roster_data = await self._make_api_call(
                lambda: team_obj.roster(week=week) if week else team_obj.roster()
            )
            
            roster = await self._normalize_players(roster_data)
            
            return FantasyApiResponse(
                success=True,
                data=roster,
                platform=FantasyPlatform.YAHOO
            )
            
        except Exception as e:
            logger.error(f"Failed to get roster for team {team_id}: {e}")
            return FantasyApiResponse(
                success=False,
                error=str(e),
                platform=FantasyPlatform.YAHOO
            )
    
    # Normalization methods
    async def _normalize_teams(self, teams_data: List[Dict]) -> List[Team]:
        """Normalize Yahoo team data to unified format"""
        teams = []
        for team_data in teams_data:
            team = Team(
                id=f"yahoo_{team_data.get('team_id')}",
                platform_id=str(team_data.get('team_id')),
                platform=FantasyPlatform.YAHOO,
                name=team_data.get('name', ''),
                owner_name=team_data.get('managers', [{}])[0].get('nickname') if team_data.get('managers') else None,
                wins=int(team_data.get('wins', 0)),
                losses=int(team_data.get('losses', 0)),
                ties=int(team_data.get('ties', 0)),
                points_for=float(team_data.get('points_for', 0)),
                points_against=float(team_data.get('points_against', 0)),
                metadata={'yahoo_data': team_data}
            )
            teams.append(team)
        return teams
    
    async def _normalize_players(self, players_data: List[Dict]) -> List[Player]:
        """Normalize Yahoo player data to unified format"""
        players = []
        for player_data in players_data:
            player = Player(
                id=f"yahoo_{player_data.get('player_id')}",
                platform_id=str(player_data.get('player_id')),
                platform=FantasyPlatform.YAHOO,
                name=player_data.get('name', ''),
                position=self._normalize_position(player_data.get('position')),
                team=player_data.get('editorial_team_abbr'),
                bye_week=player_data.get('bye_week'),
                projected_points=player_data.get('projected_points'),
                actual_points=player_data.get('points'),
                injury_status=player_data.get('injury_status'),
                metadata={'yahoo_data': player_data}
            )
            players.append(player)
        return players
    
    async def _normalize_matchups(self, scoreboard_data: List[Dict], week: int, year: int) -> List[Matchup]:
        """Normalize Yahoo matchup data to unified format"""
        matchups = []
        for matchup_data in scoreboard_data:
            # Extract team data from matchup
            teams = matchup_data.get('teams', [])
            if len(teams) < 2:
                continue
                
            team1_data, team2_data = teams[0], teams[1]
            
            # Create team objects
            team1 = await self._create_team_from_matchup(team1_data)
            team2 = await self._create_team_from_matchup(team2_data)
            
            matchup = Matchup(
                id=f"yahoo_{matchup_data.get('matchup_id', f'{week}_{team1.id}_{team2.id}')}",
                platform=FantasyPlatform.YAHOO,
                week=week,
                year=year,
                team1=team1,
                team2=team2,
                team1_score=float(team1_data.get('points', 0)),
                team2_score=float(team2_data.get('points', 0)),
                status=self._determine_matchup_status(matchup_data),
                metadata={'yahoo_data': matchup_data}
            )
            matchups.append(matchup)
        return matchups
    
    async def _create_team_from_matchup(self, team_data: Dict) -> Team:
        """Create a Team object from matchup data"""
        return Team(
            id=f"yahoo_{team_data.get('team_id')}",
            platform_id=str(team_data.get('team_id')),
            platform=FantasyPlatform.YAHOO,
            name=team_data.get('name', ''),
            owner_name=team_data.get('managers', [{}])[0].get('nickname') if team_data.get('managers') else None,
            metadata={'yahoo_data': team_data}
        )
    
    def _normalize_position(self, yahoo_position: str) -> PlayerPosition:
        """Convert Yahoo position to standard position"""
        position_map = {
            'QB': PlayerPosition.QB,
            'RB': PlayerPosition.RB,
            'WR': PlayerPosition.WR,
            'TE': PlayerPosition.TE,
            'K': PlayerPosition.K,
            'DEF': PlayerPosition.DEF,
            'FLEX': PlayerPosition.FLEX,
            'BN': PlayerPosition.BENCH,
            'IR': PlayerPosition.IR
        }
        return position_map.get(yahoo_position, PlayerPosition.BENCH)
    
    def _normalize_scoring_type(self, yahoo_scoring: str) -> str:
        """Convert Yahoo scoring type to standard format"""
        scoring_map = {
            'head_to_head_points': 'standard',
            'head_to_head_points_decimal': 'decimal',
            'head_to_head_each_category': 'category'
        }
        return scoring_map.get(yahoo_scoring, 'standard')
    
    def _determine_matchup_status(self, matchup_data: Dict) -> MatchupStatus:
        """Determine matchup status from Yahoo data"""
        # This is a simplified status determination
        # In reality, you'd check game times, completion status, etc.
        if matchup_data.get('is_complete'):
            return MatchupStatus.COMPLETED
        elif matchup_data.get('has_started'):
            return MatchupStatus.IN_PROGRESS
        else:
            return MatchupStatus.PREVIEW
