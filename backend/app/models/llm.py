"""
LLM Provider Models and Data Structures
Defines common data models for LLM provider interactions
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class RecapTone(str, Enum):
    """Tone options for recap generation"""
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    DRAMATIC = "dramatic"
    CASUAL = "casual"
    SARCASTIC = "sarcastic"
    ANALYTICAL = "analytical"


class RecapLength(str, Enum):
    """Length options for recap generation"""
    SHORT = "short"      # ~150-300 words
    MEDIUM = "medium"    # ~300-600 words
    LONG = "long"        # ~600-1000 words
    DETAILED = "detailed"  # ~1000+ words


class LLMRequest(BaseModel):
    """Standard request format for LLM providers"""
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    model_name: Optional[str] = None
    system_message: Optional[str] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Standard response format from LLM providers"""
    text: str
    provider: LLMProvider
    model_used: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    cost_estimate: Optional[float] = None
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecapRequest(BaseModel):
    """Fantasy football recap generation request"""
    league_data: Dict[str, Any]
    week: int
    season: int
    style_preferences: Dict[str, Any] = Field(default_factory=dict)
    tone: RecapTone = RecapTone.HUMOROUS
    length: RecapLength = RecapLength.MEDIUM
    custom_awards: List[Dict[str, Any]] = Field(default_factory=list)
    user_template: Optional[str] = None
    additional_context: Optional[str] = None
    include_standings: bool = True
    include_matchups: bool = True
    include_player_stats: bool = True
    focus_teams: Optional[List[str]] = None


class RecapResponse(BaseModel):
    """Fantasy football recap generation response"""
    recap_text: str
    week: int
    season: int
    league_id: str
    provider_used: LLMProvider
    model_used: str
    generation_time: datetime
    word_count: int
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    tone_used: RecapTone
    length_category: RecapLength
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderError(Exception):
    """Base exception for LLM provider errors"""
    def __init__(self, provider: LLMProvider, message: str, error_code: Optional[str] = None):
        self.provider = provider
        self.message = message
        self.error_code = error_code
        super().__init__(f"{provider.value}: {message}")


class AuthenticationError(ProviderError):
    """Raised when API key is invalid or authentication fails"""
    pass


class RateLimitError(ProviderError):
    """Raised when rate limit is exceeded"""
    def __init__(self, provider: LLMProvider, message: str, retry_after: Optional[int] = None):
        super().__init__(provider, message, "RATE_LIMIT")
        self.retry_after = retry_after


class QuotaExceededError(ProviderError):
    """Raised when API quota is exceeded"""
    pass


class ModelNotFoundError(ProviderError):
    """Raised when requested model is not available"""
    pass


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider"""
    provider: LLMProvider
    api_key: str
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    organization_id: Optional[str] = None
    max_tokens_default: int = 1000
    temperature_default: float = 0.7
    rate_limit_per_minute: Optional[int] = None
    timeout_seconds: int = 30
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    additional_config: Dict[str, Any] = Field(default_factory=dict)


class ProviderCapabilities(BaseModel):
    """Capabilities and limitations of a provider"""
    max_tokens: int
    supports_system_message: bool
    supports_streaming: bool
    supports_function_calling: bool
    available_models: List[str]
    cost_per_1k_input_tokens: Optional[float] = None
    cost_per_1k_output_tokens: Optional[float] = None
    rate_limits: Dict[str, int] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    """Current status of a provider"""
    provider: LLMProvider
    is_available: bool
    last_check: datetime
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    success_rate: float = 0.0
    requests_count: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
