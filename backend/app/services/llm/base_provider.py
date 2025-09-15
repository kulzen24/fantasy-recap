"""
Abstract Base Provider for LLM Integrations
Defines the interface that all LLM providers must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
import asyncio
import logging
from datetime import datetime, timedelta

from app.models.llm import (
    LLMProvider, LLMRequest, LLMResponse, RecapRequest, RecapResponse,
    ProviderConfig, ProviderCapabilities, ProviderStatus,
    ProviderError, AuthenticationError, RateLimitError, QuotaExceededError
)

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers
    
    All provider implementations must inherit from this class and implement
    the required abstract methods to ensure consistent interface across providers.
    """
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize the provider with configuration
        
        Args:
            config: Provider configuration including API keys and settings
        """
        self.config = config
        self.provider = config.provider
        self._status = ProviderStatus(
            provider=self.provider,
            is_available=False,
            last_check=datetime.utcnow(),
            success_rate=0.0,
            requests_count=0,
            total_tokens_used=0,
            total_cost=0.0
        )
        
        # Rate limiting tracking
        self._request_timestamps: List[datetime] = []
        self._lock = asyncio.Lock()
    
    @property
    def status(self) -> ProviderStatus:
        """Get current provider status"""
        return self._status
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request
        
        Returns:
            bool: True if API key is valid, False otherwise
            
        Raises:
            AuthenticationError: If API key is invalid
            ProviderError: For other validation errors
        """
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get provider capabilities and limitations
        
        Returns:
            ProviderCapabilities: Information about what the provider supports
        """
        pass
    
    @abstractmethod
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using the LLM provider
        
        Args:
            request: Standardized LLM request
            
        Returns:
            LLMResponse: Standardized response with generated text
            
        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            QuotaExceededError: If quota is exceeded
            ProviderError: For other provider-specific errors
        """
        pass
    
    @abstractmethod
    async def generate_recap(self, request: RecapRequest) -> RecapResponse:
        """
        Generate a fantasy football recap using the provider
        
        Args:
            request: Fantasy football recap request with league data and preferences
            
        Returns:
            RecapResponse: Generated recap with metadata
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for given text
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            int: Estimated token count
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for a request with given token counts
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            float: Estimated cost in USD
        """
        pass
    
    async def check_health(self) -> bool:
        """
        Check provider health and update status
        
        Returns:
            bool: True if provider is healthy, False otherwise
        """
        try:
            start_time = datetime.utcnow()
            is_valid = await self.validate_api_key()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            self._status.is_available = is_valid
            self._status.last_check = datetime.utcnow()
            self._status.response_time = response_time
            self._status.error_message = None
            
            logger.info(f"{self.provider.value} health check: {'healthy' if is_valid else 'unhealthy'}")
            return is_valid
            
        except Exception as e:
            self._status.is_available = False
            self._status.last_check = datetime.utcnow()
            self._status.error_message = str(e)
            
            logger.error(f"{self.provider.value} health check failed: {e}")
            return False
    
    async def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting
        
        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        if not self.config.rate_limit_per_minute:
            return
        
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=1)
            
            # Remove old timestamps
            self._request_timestamps = [
                ts for ts in self._request_timestamps if ts > cutoff
            ]
            
            # Check if we're at the limit
            if len(self._request_timestamps) >= self.config.rate_limit_per_minute:
                raise RateLimitError(
                    self.provider,
                    f"Rate limit of {self.config.rate_limit_per_minute}/minute exceeded",
                    retry_after=60
                )
            
            # Add current timestamp
            self._request_timestamps.append(now)
    
    async def _update_usage_stats(self, tokens_used: Optional[int], cost: Optional[float]) -> None:
        """
        Update usage statistics
        
        Args:
            tokens_used: Number of tokens used in the request
            cost: Cost of the request
        """
        self._status.requests_count += 1
        
        if tokens_used:
            self._status.total_tokens_used += tokens_used
            
        if cost:
            self._status.total_cost += cost
    
    async def _handle_request(self, request_func, *args, **kwargs):
        """
        Handle a request with rate limiting, error handling, and stats tracking
        
        Args:
            request_func: Function to execute the request
            *args: Arguments for the request function
            **kwargs: Keyword arguments for the request function
            
        Returns:
            Result of the request function
        """
        await self._check_rate_limit()
        
        try:
            result = await request_func(*args, **kwargs)
            
            # Update success rate
            total_requests = self._status.requests_count + 1
            success_count = int(self._status.success_rate * self._status.requests_count) + 1
            self._status.success_rate = success_count / total_requests
            
            # Update usage stats if result contains usage information
            if hasattr(result, 'tokens_used') and hasattr(result, 'cost_estimate'):
                await self._update_usage_stats(result.tokens_used, result.cost_estimate)
            
            return result
            
        except Exception as e:
            # Update success rate for failure
            total_requests = self._status.requests_count + 1
            success_count = int(self._status.success_rate * self._status.requests_count)
            self._status.success_rate = success_count / total_requests
            
            logger.error(f"{self.provider.value} request failed: {e}")
            raise
    
    def _build_fantasy_prompt(self, request: RecapRequest) -> str:
        """
        Build a fantasy football recap prompt from the request
        
        Args:
            request: Recap request with league data and preferences
            
        Returns:
            str: Formatted prompt for the LLM
        """
        league_data = request.league_data
        week = request.week
        season = request.season
        tone = request.tone.value
        length = request.length.value
        
        # Base prompt structure
        prompt_parts = [
            f"Generate a {tone} fantasy football recap for Week {week} of the {season} season.",
            f"Target length: {length}",
            ""
        ]
        
        # Add league context
        if league_data.get('name'):
            prompt_parts.append(f"League: {league_data['name']}")
        
        if league_data.get('total_teams'):
            prompt_parts.append(f"Teams: {league_data['total_teams']}")
        
        prompt_parts.append("")
        
        # Add matchup data if available and requested
        if request.include_matchups and league_data.get('matchups'):
            prompt_parts.append("MATCHUP RESULTS:")
            for matchup in league_data['matchups']:
                team1 = matchup.get('team1', {})
                team2 = matchup.get('team2', {})
                score1 = matchup.get('team1_score', 0)
                score2 = matchup.get('team2_score', 0)
                
                prompt_parts.append(
                    f"- {team1.get('name', 'Team 1')} {score1:.1f} vs "
                    f"{team2.get('name', 'Team 2')} {score2:.1f}"
                )
            prompt_parts.append("")
        
        # Add standings if available and requested
        if request.include_standings and league_data.get('teams'):
            prompt_parts.append("CURRENT STANDINGS:")
            teams = league_data['teams']
            # Sort by wins, then by points for
            sorted_teams = sorted(
                teams, 
                key=lambda t: (-t.get('wins', 0), -t.get('points_for', 0))
            )
            
            for i, team in enumerate(sorted_teams[:6], 1):  # Top 6 teams
                record = f"{team.get('wins', 0)}-{team.get('losses', 0)}"
                if team.get('ties', 0) > 0:
                    record += f"-{team['ties']}"
                
                prompt_parts.append(
                    f"{i}. {team.get('name', 'Unknown')} ({record}) - "
                    f"{team.get('points_for', 0):.1f} PF"
                )
            prompt_parts.append("")
        
        # Add custom awards if provided
        if request.custom_awards:
            prompt_parts.append("CUSTOM AWARDS:")
            for award in request.custom_awards:
                prompt_parts.append(f"- {award.get('name', 'Award')}: {award.get('winner', 'TBD')}")
            prompt_parts.append("")
        
        # Add user template reference if provided
        if request.user_template:
            prompt_parts.extend([
                "STYLE REFERENCE:",
                "Use the following example as a style guide for tone and structure:",
                request.user_template,
                ""
            ])
        
        # Add additional context if provided
        if request.additional_context:
            prompt_parts.extend([
                "ADDITIONAL CONTEXT:",
                request.additional_context,
                ""
            ])
        
        # Add specific instructions based on preferences
        instructions = [
            f"Write in a {tone} tone that will entertain league members.",
            f"Target approximately {self._get_word_count_target(request.length)} words.",
        ]
        
        if request.focus_teams:
            instructions.append(f"Pay special attention to these teams: {', '.join(request.focus_teams)}")
        
        instructions.extend([
            "Include memorable moments, standout performances, and entertaining observations.",
            "Use team names and player names when available.",
            "Make it engaging and fun to read for fantasy football enthusiasts."
        ])
        
        prompt_parts.extend([
            "INSTRUCTIONS:",
            *[f"- {instruction}" for instruction in instructions]
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_word_count_target(self, length: str) -> str:
        """Get word count target description for given length"""
        targets = {
            "short": "150-300",
            "medium": "300-600", 
            "long": "600-1000",
            "detailed": "1000+"
        }
        return targets.get(length, "300-600")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.provider.value})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider.value}, available={self._status.is_available})"
