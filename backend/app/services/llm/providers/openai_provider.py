"""
OpenAI Provider Implementation
Concrete implementation of BaseLLMProvider for OpenAI's GPT models
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import openai
from openai import AsyncOpenAI

from ..base_provider import BaseLLMProvider
from app.models.llm import (
    LLMRequest, LLMResponse, RecapRequest, RecapResponse, 
    ProviderCapabilities, ProviderError, AuthenticationError,
    RateLimitError, ModelNotFoundError
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation using GPT models"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=config.api_key)
        
        # OpenAI model configurations
        self.model_configs = {
            "gpt-4": {
                "max_tokens": 8192,
                "supports_system": True,
                "cost_input": 0.03,  # per 1K tokens
                "cost_output": 0.06
            },
            "gpt-4-turbo": {
                "max_tokens": 128000,
                "supports_system": True,
                "cost_input": 0.01,
                "cost_output": 0.03
            },
            "gpt-3.5-turbo": {
                "max_tokens": 16384,
                "supports_system": True,
                "cost_input": 0.0015,
                "cost_output": 0.002
            },
            "gpt-4o": {
                "max_tokens": 128000,
                "supports_system": True,
                "cost_input": 0.005,
                "cost_output": 0.015
            },
            "gpt-4o-mini": {
                "max_tokens": 128000,
                "supports_system": True,
                "cost_input": 0.00015,
                "cost_output": 0.0006
            }
        }
    
    async def validate_api_key(self) -> bool:
        """Validate OpenAI API key by making a simple request"""
        try:
            await self.client.models.list()
            return True
        except openai.AuthenticationError:
            raise AuthenticationError(self.provider, "Invalid OpenAI API key")
        except openai.APIConnectionError:
            raise ProviderError(self.provider, "Unable to connect to OpenAI API")
        except Exception as e:
            self.logger.error(f"OpenAI API key validation failed: {e}")
            return False
    
    async def get_capabilities(self) -> ProviderCapabilities:
        """Get OpenAI provider capabilities"""
        model_name = self.config.model_name or "gpt-4o"
        model_config = self.model_configs.get(model_name, self.model_configs["gpt-4o"])
        
        return ProviderCapabilities(
            max_tokens=model_config["max_tokens"],
            supports_system_message=model_config["supports_system"],
            supports_streaming=True,
            supports_function_calling=True,
            available_models=list(self.model_configs.keys()),
            cost_per_1k_input_tokens=model_config["cost_input"],
            cost_per_1k_output_tokens=model_config["cost_output"]
        )
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using OpenAI GPT models"""
        start_time = datetime.now()
        
        try:
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Prepare the request
            model_name = self.config.model_name or "gpt-4o"
            
            messages = []
            if request.system_message:
                messages.append({"role": "system", "content": request.system_message})
            messages.append({"role": "user", "content": request.prompt})
            
            # Make the API call
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=request.max_tokens or self.config.max_tokens_default,
                temperature=request.temperature or self.config.temperature_default,
                stream=False
            )
            
            # Extract response data
            choice = response.choices[0]
            response_text = choice.message.content
            finish_reason = choice.finish_reason
            
            # Calculate tokens and cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            model_config = self.model_configs.get(model_name, self.model_configs["gpt-4o"])
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
                finish_reason=finish_reason,
                cost_estimate=cost_estimate,
                response_time=response_time,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": finish_reason
                }
            )
            
        except openai.RateLimitError as e:
            await self._handle_rate_limit()
            raise RateLimitError(self.provider, f"OpenAI rate limit exceeded: {e}")
        except openai.AuthenticationError:
            raise AuthenticationError(self.provider, "OpenAI API key is invalid")
        except openai.NotFoundError:
            raise ModelNotFoundError(self.provider, f"OpenAI model '{model_name}' not found")
        except Exception as e:
            self.logger.error(f"OpenAI text generation failed: {e}")
            raise ProviderError(self.provider, f"OpenAI generation failed: {str(e)}")
    
    async def generate_recap(self, request: RecapRequest) -> RecapResponse:
        """Generate fantasy football recap using OpenAI"""
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
                    "output_tokens": llm_response.metadata.get("output_tokens", 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI recap generation failed: {e}")
            raise ProviderError(self.provider, f"OpenAI recap generation failed: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for OpenAI models (rough approximation)"""
        # OpenAI uses roughly 1 token per 4 characters for English text
        # This is a rough approximation - for production, use tiktoken
        return max(1, len(text) // 4)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost estimate for OpenAI API usage"""
        model_name = self.config.model_name or "gpt-4o"
        model_config = self.model_configs.get(model_name, self.model_configs["gpt-4o"])
        
        input_cost = (input_tokens / 1000) * model_config["cost_input"]
        output_cost = (output_tokens / 1000) * model_config["cost_output"]
        
        return round(input_cost + output_cost, 6)
    
    def _get_system_message(self, request: RecapRequest) -> str:
        """Get system message for fantasy recap generation"""
        tone_descriptions = {
            "professional": "professional and informative",
            "humorous": "funny and entertaining with witty commentary",
            "dramatic": "exciting and dramatic with high energy",
            "casual": "friendly and conversational",
            "sarcastic": "cleverly sarcastic and witty",
            "analytical": "detailed and analytical with deep insights"
        }
        
        length_descriptions = {
            "short": "concise and to-the-point (150-250 words)",
            "medium": "moderately detailed (300-500 words)",
            "long": "comprehensive and detailed (600-800 words)",
            "detailed": "very thorough and in-depth (900+ words)"
        }
        
        tone_desc = tone_descriptions.get(request.tone.value, "engaging")
        length_desc = length_descriptions.get(request.length.value, "moderately detailed")
        
        return f"""You are an expert fantasy football recap writer. Your task is to create {tone_desc} weekly recaps that are {length_desc}.

Key requirements:
- Focus on the most interesting storylines and performances
- Include specific player performances and statistics when provided
- Mention standout matchups and surprising results
- Keep the tone consistent throughout: {request.tone.value}
- Target length: {length_desc}
- Make it engaging for fantasy football enthusiasts
- Use fantasy football terminology and insights"""
    
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
            "humorous": 0.8,
            "dramatic": 0.7,
            "casual": 0.6,
            "sarcastic": 0.8,
            "analytical": 0.2
        }
        return tone_temps.get(tone.value, 0.7)
    
    def _post_process_recap(self, text: str, request: RecapRequest) -> str:
        """Post-process the generated recap"""
        # Clean up the text
        text = text.strip()
        
        # Ensure proper formatting
        if not text.startswith('#') and not text.startswith('**'):
            league_name = request.league_data.get('name', 'Fantasy League')
            text = f"**{league_name} - Week {request.week} Recap**\n\n{text}"
        
        return text
