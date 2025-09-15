"""
Base Fantasy Service
Abstract base class for all fantasy platform services
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.models.fantasy import FantasyApiResponse, League, Team, Matchup, WeeklyStats


class BaseFantasyService(ABC):
    """Abstract base class for fantasy platform services"""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the fantasy platform
        
        Returns:
            bool: True if authentication successful
        """
        pass
    
    @abstractmethod
    async def get_user_leagues(self, year: int = 2024) -> FantasyApiResponse:
        """
        Get all leagues for the authenticated user
        
        Args:
            year: NFL season year
            
        Returns:
            FantasyApiResponse with leagues data
        """
        pass
    
    @abstractmethod
    async def get_league(self, league_id: str, year: int = 2024) -> FantasyApiResponse:
        """
        Get league information
        
        Args:
            league_id: Platform-specific league ID
            year: NFL season year
            
        Returns:
            FantasyApiResponse with League data
        """
        pass
    
    @abstractmethod
    async def get_matchups(self, league_id: str, week: int, year: int = 2024) -> FantasyApiResponse:
        """
        Get matchups for a specific week
        
        Args:
            league_id: Platform-specific league ID
            week: NFL week number
            year: NFL season year
            
        Returns:
            FantasyApiResponse with matchups data
        """
        pass
    
    @abstractmethod
    async def get_team_roster(self, league_id: str, team_id: str, week: Optional[int] = None) -> FantasyApiResponse:
        """
        Get team roster for a specific week
        
        Args:
            league_id: Platform-specific league ID
            team_id: Platform-specific team ID
            week: NFL week number (optional, defaults to current week)
            
        Returns:
            FantasyApiResponse with roster data
        """
        pass
    
    async def get_weekly_stats(self, league_id: str, week: int, year: int = 2024) -> FantasyApiResponse:
        """
        Get weekly statistics for all players in a league (optional override)
        
        Args:
            league_id: Platform-specific league ID
            week: NFL week number
            year: NFL season year
            
        Returns:
            FantasyApiResponse with weekly stats data
        """
        # Default implementation - can be overridden by specific services
        return FantasyApiResponse(
            success=False,
            error="Weekly stats not implemented for this platform",
            platform=getattr(self, 'platform', None)
        )
