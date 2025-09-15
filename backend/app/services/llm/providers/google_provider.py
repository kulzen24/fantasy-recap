"""
Google Gemini Provider Implementation
Concrete implementation of BaseLLMProvider for Google's Gemini models
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..base_provider import BaseLLMProvider
from app.models.llm import (
    LLMRequest, LLMResponse, RecapRequest, RecapResponse, 
    ProviderCapabilities, ProviderError, AuthenticationError,
    RateLimitError, ModelNotFoundError
)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        
        # Google Gemini model configurations
        self.model_configs = {
            "gemini-1.5-pro": {
                "max_tokens": 8192,
                "supports_system": True,
                "cost_input": 0.0035,  # per 1K tokens
                "cost_output": 0.0105,
                "context_window": 2000000  # 2M tokens
            },
            "gemini-1.5-flash": {
                "max_tokens": 8192,
                "supports_system": True,
                "cost_input": 0.00075,
                "cost_output": 0.003,
                "context_window": 1000000  # 1M tokens
            },
            "gemini-1.0-pro": {
                "max_tokens": 2048,
                "supports_system": False,
                "cost_input": 0.0005,
                "cost_output": 0.0015,
                "context_window": 32000
            }
        }
        
        # Initialize the model
        self.model_name = config.model_name or "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
    
    async def validate_api_key(self) -> bool:
        """Validate Google API key by making a simple request"""
        try:
            # Make a minimal request to validate the key
            response = await asyncio.to_thread(
                self.model.generate_content,
                "Hi",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1,
                    temperature=0.1
                )
            )
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "api_key" in error_msg or "authentication" in error_msg or "unauthorized" in error_msg:
                raise AuthenticationError(self.provider, "Invalid Google API key")
            elif "connection" in error_msg or "network" in error_msg:
                raise ProviderError(self.provider, "Unable to connect to Google API")
            else:
                self.logger.error(f"Google API key validation failed: {e}")
                return False
    
    async def get_capabilities(self) -> ProviderCapabilities:
        """Get Google provider capabilities"""
        model_config = self.model_configs.get(self.model_name, self.model_configs["gemini-1.5-flash"])
        
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
        """Generate text using Google Gemini models"""
        start_time = datetime.now()
        
        try:
            # Apply rate limiting
            await self._apply_rate_limit()
            
            # Prepare the content
            if request.system_message and self.model_configs[self.model_name]["supports_system"]:
                # Combine system message with user prompt for models that support it
                content = f"System: {request.system_message}\n\nUser: {request.prompt}"
            else:
                content = request.prompt
            
            # Configure generation settings
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or self.config.max_tokens_default or 1000,
                temperature=request.temperature or self.config.temperature_default or 0.7,
                top_p=0.95,
                top_k=40
            )
            
            # Configure safety settings (relaxed for fantasy football content)
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Make the API call (run in thread since it's not natively async)
            response = await asyncio.to_thread(
                self.model.generate_content,
                content,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Extract response data
            if not response.parts:
                raise LLMError("Empty response from Google Gemini")
            
            response_text = response.text
            
            # Calculate tokens (rough estimation since Google doesn't always provide usage)
            input_tokens = self.estimate_tokens(content)
            output_tokens = self.estimate_tokens(response_text)
            total_tokens = input_tokens + output_tokens
            
            cost_estimate = self.estimate_cost(input_tokens, output_tokens)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Update usage tracking
            await self._track_usage(total_tokens, cost_estimate)
            
            # Determine finish reason
            finish_reason = "stop"
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                if response.prompt_feedback.block_reason:
                    finish_reason = "content_filter"
            
            return LLMResponse(
                text=response_text,
                provider=self.provider,
                model_used=self.model_name,
                tokens_used=total_tokens,
                finish_reason=finish_reason,
                cost_estimate=cost_estimate,
                response_time=response_time,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": finish_reason,
                    "safety_ratings": getattr(response, 'safety_ratings', [])
                }
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate" in error_msg:
                await self._handle_rate_limit()
                raise RateLimitError(self.provider, f"Google rate limit exceeded: {e}")
            elif "api_key" in error_msg or "authentication" in error_msg:
                raise AuthenticationError(self.provider, "Google API key is invalid")
            elif "not found" in error_msg or "model" in error_msg:
                raise ModelNotFoundError(self.provider, f"Google model '{self.model_name}' not found")
            else:
                self.logger.error(f"Google text generation failed: {e}")
                raise ProviderError(self.provider, f"Google generation failed: {str(e)}")
    
    async def generate_recap(self, request: RecapRequest) -> RecapResponse:
        """Generate fantasy football recap using Google Gemini"""
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
                    "safety_ratings": llm_response.metadata.get("safety_ratings", [])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Google recap generation failed: {e}")
            raise ProviderError(self.provider, f"Google recap generation failed: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Google models"""
        # Google uses roughly 1 token per 4 characters for English text
        # This is a rough approximation
        return max(1, len(text) // 4)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost estimate for Google API usage"""
        model_config = self.model_configs.get(self.model_name, self.model_configs["gemini-1.5-flash"])
        
        input_cost = (input_tokens / 1000) * model_config["cost_input"]
        output_cost = (output_tokens / 1000) * model_config["cost_output"]
        
        return round(input_cost + output_cost, 6)
    
    def _get_system_message(self, request: RecapRequest) -> str:
        """Get system message for fantasy recap generation"""
        tone_descriptions = {
            "professional": "professional and informative with clear analysis",
            "humorous": "funny and entertaining with clever jokes and witty observations",
            "dramatic": "exciting and dramatic with high energy and thrilling narratives",
            "casual": "friendly and conversational like chatting with friends",
            "sarcastic": "cleverly sarcastic and witty with sharp, humorous commentary",
            "analytical": "detailed and analytical with deep statistical insights and data-driven observations"
        }
        
        length_descriptions = {
            "short": "concise and to-the-point (150-250 words)",
            "medium": "moderately detailed (300-500 words)",
            "long": "comprehensive and detailed (600-800 words)",
            "detailed": "very thorough and in-depth (900+ words)"
        }
        
        tone_desc = tone_descriptions.get(request.tone.value, "engaging")
        length_desc = length_descriptions.get(request.length.value, "moderately detailed")
        
        return f"""You are a skilled fantasy football recap writer specializing in {tone_desc} content. Your expertise lies in creating weekly league recaps that are {length_desc}.

Your responsibilities:
- Create engaging narratives around weekly fantasy performances
- Highlight exceptional player performances and key statistical achievements
- Analyze important matchups, surprising outcomes, and notable moments
- Maintain a consistent {request.tone.value} tone throughout the recap
- Write {length_desc} content as specified
- Appeal to fantasy football enthusiasts who appreciate both entertainment and insight
- Use proper fantasy football terminology and demonstrate deep knowledge of the game
- Make each recap distinctive and memorable for league members

Focus: You're creating entertainment and analysis, not just listing numbers. Tell the story of what happened this week in fantasy football."""
    
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
        
        # Remove any markdown artifacts that Gemini might include inappropriately
        import re
        # Remove excessive asterisks or underscores that might be artifacts
        text = re.sub(r'\*{3,}', '**', text)  # Replace *** with **
        text = re.sub(r'_{3,}', '__', text)   # Replace ___ with __
        
        # Ensure proper formatting
        if not text.startswith('#') and not text.startswith('**'):
            league_name = request.league_data.get('name', 'Fantasy League')
            text = f"**{league_name} - Week {request.week} Recap**\n\n{text}"
        
        return text
