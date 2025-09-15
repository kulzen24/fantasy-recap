"""
LLM Provider Manager
Manages multiple LLM providers and handles provider selection and routing
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Union
from datetime import datetime, timedelta

from app.models.llm import (
    LLMProvider, LLMRequest, LLMResponse, RecapRequest, RecapResponse,
    ProviderConfig, ProviderStatus, ProviderError, AuthenticationError
)
from .base_provider import BaseLLMProvider
from .providers import OpenAIProvider, AnthropicProvider, GoogleProvider

logger = logging.getLogger(__name__)


class LLMProviderManager:
    """
    Manager for multiple LLM providers
    
    Handles provider registration, selection, routing, and fallback logic
    """
    
    def __init__(self):
        """Initialize the provider manager"""
        self._providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self._provider_classes: Dict[LLMProvider, Type[BaseLLMProvider]] = {}
        self._default_provider: Optional[LLMProvider] = None
        self._fallback_order: List[LLMProvider] = []
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = datetime.utcnow() - timedelta(minutes=10)  # Force initial check
        
        # Auto-register built-in provider classes
        self._register_builtin_providers()
    
    def register_provider_class(self, provider: LLMProvider, provider_class: Type[BaseLLMProvider]) -> None:
        """
        Register a provider class for lazy initialization
        
        Args:
            provider: Provider enum value
            provider_class: Provider class to register
        """
        self._provider_classes[provider] = provider_class
        logger.info(f"Registered provider class: {provider.value}")
    
    def _register_builtin_providers(self) -> None:
        """Register all built-in provider classes"""
        self.register_provider_class(LLMProvider.OPENAI, OpenAIProvider)
        self.register_provider_class(LLMProvider.ANTHROPIC, AnthropicProvider)
        self.register_provider_class(LLMProvider.GOOGLE, GoogleProvider)
        logger.info("Registered all built-in provider classes")
    
    async def add_provider(self, config: ProviderConfig) -> bool:
        """
        Add and initialize a provider
        
        Args:
            config: Provider configuration
            
        Returns:
            bool: True if provider was added successfully
        """
        try:
            provider_class = self._provider_classes.get(config.provider)
            if not provider_class:
                logger.error(f"No provider class registered for {config.provider.value}")
                return False
            
            # Initialize provider
            provider_instance = provider_class(config)
            
            # Validate API key
            is_valid = await provider_instance.validate_api_key()
            if not is_valid:
                logger.error(f"Invalid API key for {config.provider.value}")
                return False
            
            # Add to providers
            self._providers[config.provider] = provider_instance
            
            # Set as default if it's the first provider
            if not self._default_provider:
                self._default_provider = config.provider
                
            # Add to fallback order if not already present
            if config.provider not in self._fallback_order:
                self._fallback_order.append(config.provider)
            
            logger.info(f"Successfully added provider: {config.provider.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add provider {config.provider.value}: {e}")
            return False
    
    def remove_provider(self, provider: LLMProvider) -> bool:
        """
        Remove a provider
        
        Args:
            provider: Provider to remove
            
        Returns:
            bool: True if provider was removed
        """
        if provider in self._providers:
            del self._providers[provider]
            
            # Update default if needed
            if self._default_provider == provider:
                self._default_provider = next(iter(self._providers.keys()), None)
            
            # Remove from fallback order
            if provider in self._fallback_order:
                self._fallback_order.remove(provider)
            
            logger.info(f"Removed provider: {provider.value}")
            return True
        
        return False
    
    def get_provider(self, provider: LLMProvider) -> Optional[BaseLLMProvider]:
        """
        Get a specific provider instance
        
        Args:
            provider: Provider to get
            
        Returns:
            Optional[BaseLLMProvider]: Provider instance or None
        """
        return self._providers.get(provider)
    
    def get_available_providers(self) -> List[LLMProvider]:
        """
        Get list of available providers
        
        Returns:
            List[LLMProvider]: List of available providers
        """
        return [
            provider for provider, instance in self._providers.items()
            if instance.status.is_available
        ]
    
    def get_all_providers(self) -> List[LLMProvider]:
        """
        Get list of all registered providers
        
        Returns:
            List[LLMProvider]: List of all providers
        """
        return list(self._providers.keys())
    
    def set_default_provider(self, provider: LLMProvider) -> bool:
        """
        Set the default provider
        
        Args:
            provider: Provider to set as default
            
        Returns:
            bool: True if set successfully
        """
        if provider in self._providers:
            self._default_provider = provider
            logger.info(f"Set default provider: {provider.value}")
            return True
        
        logger.error(f"Cannot set default provider {provider.value}: not available")
        return False
    
    def set_fallback_order(self, providers: List[LLMProvider]) -> None:
        """
        Set the fallback order for providers
        
        Args:
            providers: List of providers in fallback order
        """
        # Only include providers that are actually available
        self._fallback_order = [
            provider for provider in providers
            if provider in self._providers
        ]
        logger.info(f"Set fallback order: {[p.value for p in self._fallback_order]}")
    
    async def get_provider_statuses(self) -> Dict[LLMProvider, ProviderStatus]:
        """
        Get status of all providers
        
        Returns:
            Dict[LLMProvider, ProviderStatus]: Provider statuses
        """
        await self._check_provider_health()
        return {
            provider: instance.status
            for provider, instance in self._providers.items()
        }
    
    async def _check_provider_health(self) -> None:
        """Check health of all providers if needed"""
        now = datetime.utcnow()
        if (now - self._last_health_check).total_seconds() < self._health_check_interval:
            return
        
        logger.info("Performing provider health checks")
        
        # Check all providers concurrently
        tasks = [
            instance.check_health()
            for instance in self._providers.values()
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self._last_health_check = now
    
    async def _select_provider(self, preferred_provider: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """
        Select a provider for a request
        
        Args:
            preferred_provider: Preferred provider if specified
            
        Returns:
            BaseLLMProvider: Selected provider instance
            
        Raises:
            ProviderError: If no providers are available
        """
        await self._check_provider_health()
        
        # Try preferred provider first
        if preferred_provider and preferred_provider in self._providers:
            instance = self._providers[preferred_provider]
            if instance.status.is_available:
                return instance
            logger.warning(f"Preferred provider {preferred_provider.value} is not available")
        
        # Try default provider
        if self._default_provider and self._default_provider in self._providers:
            instance = self._providers[self._default_provider]
            if instance.status.is_available:
                return instance
        
        # Try fallback providers in order
        for provider in self._fallback_order:
            if provider in self._providers:
                instance = self._providers[provider]
                if instance.status.is_available:
                    logger.info(f"Using fallback provider: {provider.value}")
                    return instance
        
        # No providers available
        available = self.get_available_providers()
        raise ProviderError(
            LLMProvider.OPENAI,  # Default for error
            f"No LLM providers available. Registered: {len(self._providers)}, Available: {len(available)}"
        )
    
    async def generate_text(
        self,
        request: LLMRequest,
        preferred_provider: Optional[LLMProvider] = None
    ) -> LLMResponse:
        """
        Generate text using the best available provider
        
        Args:
            request: LLM request
            preferred_provider: Preferred provider if specified
            
        Returns:
            LLMResponse: Generated response
            
        Raises:
            ProviderError: If generation fails
        """
        provider_instance = await self._select_provider(preferred_provider)
        
        try:
            logger.info(f"Generating text with {provider_instance.provider.value}")
            return await provider_instance.generate_text(request)
            
        except Exception as e:
            logger.error(f"Text generation failed with {provider_instance.provider.value}: {e}")
            
            # Try fallback if the selected provider wasn't the preferred one
            if (preferred_provider and 
                provider_instance.provider != preferred_provider and 
                len(self.get_available_providers()) > 1):
                
                logger.info("Attempting fallback provider for text generation")
                fallback_provider = await self._select_provider()
                if fallback_provider.provider != provider_instance.provider:
                    return await fallback_provider.generate_text(request)
            
            raise
    
    async def generate_recap(
        self,
        request: RecapRequest,
        preferred_provider: Optional[LLMProvider] = None
    ) -> RecapResponse:
        """
        Generate a fantasy football recap using the best available provider
        
        Args:
            request: Recap request
            preferred_provider: Preferred provider if specified
            
        Returns:
            RecapResponse: Generated recap
            
        Raises:
            ProviderError: If generation fails
        """
        provider_instance = await self._select_provider(preferred_provider)
        
        try:
            logger.info(f"Generating recap with {provider_instance.provider.value}")
            return await provider_instance.generate_recap(request)
            
        except Exception as e:
            logger.error(f"Recap generation failed with {provider_instance.provider.value}: {e}")
            
            # Try fallback if the selected provider wasn't the preferred one
            if (preferred_provider and 
                provider_instance.provider != preferred_provider and 
                len(self.get_available_providers()) > 1):
                
                logger.info("Attempting fallback provider for recap generation")
                fallback_provider = await self._select_provider()
                if fallback_provider.provider != provider_instance.provider:
                    return await fallback_provider.generate_recap(request)
            
            raise
    
    async def estimate_cost(
        self,
        request: Union[LLMRequest, RecapRequest],
        provider: Optional[LLMProvider] = None
    ) -> Dict[LLMProvider, float]:
        """
        Estimate cost for a request across available providers
        
        Args:
            request: Request to estimate cost for
            provider: Specific provider to estimate for, or None for all
            
        Returns:
            Dict[LLMProvider, float]: Cost estimates by provider
        """
        estimates = {}
        
        providers_to_check = [provider] if provider else self.get_available_providers()
        
        for provider_enum in providers_to_check:
            if provider_enum in self._providers:
                instance = self._providers[provider_enum]
                
                if isinstance(request, RecapRequest):
                    # Build prompt to estimate tokens
                    prompt = instance._build_fantasy_prompt(request)
                    input_tokens = instance.estimate_tokens(prompt)
                    output_tokens = instance.estimate_tokens("") + 500  # Estimate output size
                else:
                    input_tokens = instance.estimate_tokens(request.prompt)
                    output_tokens = request.max_tokens or 1000
                
                cost = instance.estimate_cost(input_tokens, output_tokens)
                estimates[provider_enum] = cost
        
        return estimates
    
    def get_cheapest_provider(self, estimates: Dict[LLMProvider, float]) -> Optional[LLMProvider]:
        """
        Get the cheapest provider from cost estimates
        
        Args:
            estimates: Cost estimates by provider
            
        Returns:
            Optional[LLMProvider]: Cheapest provider or None
        """
        if not estimates:
            return None
        
        return min(estimates.keys(), key=lambda p: estimates[p])
    
    async def shutdown(self) -> None:
        """Shutdown the provider manager and clean up resources"""
        logger.info("Shutting down LLM Provider Manager")
        self._providers.clear()
        self._provider_classes.clear()
        self._default_provider = None
        self._fallback_order.clear()


# Global provider manager instance
provider_manager = LLMProviderManager()
