"""
Anthropic Provider Implementation
Concrete implementation of BaseLLMProvider for Anthropic's Claude models
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import anthropic
from anthropic import AsyncAnthropic

from ..base_provider import BaseLLMProvider
from app.models.llm import (
    LLMRequest, LLMResponse, RecapRequest, RecapResponse, 
    ProviderCapabilities, ProviderError, AuthenticationError,
    RateLimitError, ModelNotFoundError
)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider implementation using Claude models"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = AsyncAnthropic(api_key=config.api_key)
        
        # Anthropic model configurations
        self.model_configs = {
            "claude-3-opus-20240229": {
                "max_tokens": 4096,
                "supports_system": True,
                "cost_input": 0.015,  # per 1K tokens
                "cost_output": 0.075,
                "context_window": 200000
            },
            "claude-3-sonnet-20240229": {
                "max_tokens": 4096,
                "supports_system": True,
                "cost_input": 0.003,
                "cost_output": 0.015,
                "context_window": 200000
            },
            "claude-3-haiku-20240307": {
                "max_tokens": 4096,
                "supports_system": True,
                "cost_input": 0.00025,
                "cost_output": 0.00125,
                "context_window": 200000
            },
            "claude-3-5-sonnet-20241022": {
                "max_tokens": 8192,
                "supports_system": True,
                "cost_input": 0.003,
                "cost_output": 0.015,
                "context_window": 200000
            }
        }
    
    async def validate_api_key(self) -> bool:
        """Validate Anthropic API key by making a simple request"""
        try:
            # Make a minimal request to validate the key
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            return True
        except anthropic.AuthenticationError:
            raise AuthenticationError(self.provider, "Invalid Anthropic API key")
        except anthropic.APIConnectionError:
            raise ProviderError(self.provider, "Unable to connect to Anthropic API")
        except Exception as e:
            self.logger.error(f"Anthropic API key validation failed: {e}")
            return False
    
    async def get_capabilities(self) -> ProviderCapabilities:
        """Get Anthropic provider capabilities"""
        model_name = self.config.model_name or "claude-3-5-sonnet-20241022"
        model_config = self.model_configs.get(model_name, self.model_configs["claude-3-5-sonnet-20241022"])
        
        return ProviderCapabilities(
            max_tokens=model_config["max_tokens"],
            supports_system_message=model_config["supports_system"],
            supports_streaming=True,
            supports_function_calling=True,
            available_models=list(self.model_configs.keys()),
            cost_per_1k_input_tokens=model_config["cost_input"],
            cost_per_1k_output_tokens=model_config["cost_output"],
            context_window=model_config["context_window"]
        )
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Anthropic Claude models"""
        start_time = datetime.now()
        
        try:
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Prepare the request
            model_name = self.config.model_name or "claude-3-5-sonnet-20241022"
            
            messages = [{"role": "user", "content": request.prompt}]
            
            # Build request parameters
            request_params = {
                "model": model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens_default or 1000,
                "temperature": request.temperature or self.config.temperature_default or 0.7,
                "stream": False
            }
            
            # Add system message if provided
            if request.system_message:
                request_params["system"] = request.system_message
            
            # Make the API call
            response = await self.client.messages.create(**request_params)
            
            # Extract response data
            response_text = ""
            for content in response.content:
                if content.type == "text":
                    response_text += content.text
            
            # Calculate tokens and cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            cost_estimate = self.estimate_cost(input_tokens, output_tokens)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Update usage tracking
            await self._track_usage(total_tokens, cost_estimate)
            
            return LLMResponse(
                text=response_text,
                provider=self.provider,
                model_used=model_name,
                tokens_used=total_tokens,
                finish_reason=response.stop_reason or "stop",
                cost_estimate=cost_estimate,
                response_time=response_time,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "stop_reason": response.stop_reason,
                    "stop_sequence": response.stop_sequence
                }
            )
            
        except anthropic.RateLimitError as e:
            await self._handle_rate_limit()
            raise RateLimitError(self.provider, f"Anthropic rate limit exceeded: {e}")
        except anthropic.AuthenticationError:
            raise AuthenticationError(self.provider, "Anthropic API key is invalid")
        except anthropic.NotFoundError:
            raise ModelNotFoundError(self.provider, f"Anthropic model '{model_name}' not found")
        except Exception as e:
            self.logger.error(f"Anthropic text generation failed: {e}")
            raise ProviderError(self.provider, f"Anthropic generation failed: {str(e)}")
    
    async def generate_recap(self, request: RecapRequest) -> RecapResponse:
        """Generate fantasy football recap using Anthropic Claude"""
        start_time = datetime.now()
        
        try:
            # Build fantasy-specific prompt
            prompt = self._build_fantasy_prompt(request)
            
            # Create LLM request
            llm_request = LLMRequest(
                prompt=prompt,
                system_message=self._get_system_message(request),
                max_tokens=self._get_max_tokens_for_length(request.length),
                temperature=self._get_temperature_for_tone(request.tone)
            )
            
            # Generate the recap
            llm_response = await self.generate_text(llm_request)
            
            # Parse and validate the recap
            recap_text = self._post_process_recap(llm_response.text, request)
            word_count = len(recap_text.split())
            
            return RecapResponse(
                recap_text=recap_text,
                week=request.week,
                season=request.season,
                league_id=request.league_data.get('league_id', 'unknown'),
                provider_used=self.provider,
                model_used=llm_response.model_used,
                generation_time=start_time,
                word_count=word_count,
                tokens_used=llm_response.tokens_used,
                cost_estimate=llm_response.cost_estimate,
                tone_used=request.tone,
                length_category=request.length,
                metadata={
                    "response_time": llm_response.response_time,
                    "finish_reason": llm_response.finish_reason,
                    "input_tokens": llm_response.metadata.get("input_tokens", 0),
                    "output_tokens": llm_response.metadata.get("output_tokens", 0),
                    "stop_reason": llm_response.metadata.get("stop_reason")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Anthropic recap generation failed: {e}")
            raise ProviderError(self.provider, f"Anthropic recap generation failed: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Anthropic models"""
        # Anthropic uses roughly 1 token per 3.5 characters for English text
        # This is a rough approximation
        return max(1, int(len(text) / 3.5))
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost estimate for Anthropic API usage"""
        model_name = self.config.model_name or "claude-3-5-sonnet-20241022"
        model_config = self.model_configs.get(model_name, self.model_configs["claude-3-5-sonnet-20241022"])
        
        input_cost = (input_tokens / 1000) * model_config["cost_input"]
        output_cost = (output_tokens / 1000) * model_config["cost_output"]
        
        return round(input_cost + output_cost, 6)
    
    def _get_system_message(self, request: RecapRequest) -> str:
        """Get system message for fantasy recap generation"""
        tone_descriptions = {
            "professional": "professional and informative",
            "humorous": "funny and entertaining with witty commentary and clever jokes",
            "dramatic": "exciting and dramatic with high energy and suspense",
            "casual": "friendly and conversational like talking to a buddy",
            "sarcastic": "cleverly sarcastic and witty with sharp observations",
            "analytical": "detailed and analytical with deep statistical insights"
        }
        
        length_descriptions = {
            "short": "concise and to-the-point (150-250 words)",
            "medium": "moderately detailed (300-500 words)",
            "long": "comprehensive and detailed (600-800 words)",
            "detailed": "very thorough and in-depth (900+ words)"
        }
        
        tone_desc = tone_descriptions.get(request.tone.value, "engaging")
        length_desc = length_descriptions.get(request.length.value, "moderately detailed")
        
        return f"""You are an expert fantasy football recap writer with a talent for creating {tone_desc} content. Your specialty is writing weekly league recaps that are {length_desc}.

Your mission:
- Craft compelling narratives around the week's performances
- Highlight the most interesting player performances and statistical achievements
- Focus on key matchups, upsets, and standout moments
- Maintain a {request.tone.value} tone throughout the entire recap
- Target the following length: {length_desc}
- Write for fantasy football enthusiasts who love detailed analysis and entertainment
- Use authentic fantasy football terminology and insider knowledge
- Make every recap unique and memorable

Remember: You're not just reporting stats - you're telling the story of the week in fantasy football."""
    
    def _get_max_tokens_for_length(self, length) -> int:
        """Get appropriate max tokens based on desired length"""
        length_mappings = {
            "short": 400,
            "medium": 800,
            "long": 1200,
            "detailed": 1600
        }
        return length_mappings.get(length.value, 800)
    
    def _get_temperature_for_tone(self, tone) -> float:
        """Get appropriate temperature based on tone"""
        tone_temps = {
            "professional": 0.3,
            "humorous": 0.9,  # Higher for Claude's creativity
            "dramatic": 0.8,
            "casual": 0.7,
            "sarcastic": 0.9,  # Higher for wit and creativity
            "analytical": 0.2
        }
        return tone_temps.get(tone.value, 0.7)
    
    def _post_process_recap(self, text: str, request: RecapRequest) -> str:
        """Post-process the generated recap"""
        # Clean up the text
        text = text.strip()
        
        # Remove any XML tags that Claude might include
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Ensure proper formatting
        if not text.startswith('#') and not text.startswith('**'):
            league_name = request.league_data.get('name', 'Fantasy League')
            text = f"**{league_name} - Week {request.week} Recap**\n\n{text}"
        
        return text
