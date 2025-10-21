"""
LLM Provider abstraction for experiment framework.

Supports:
- Anthropic (Claude Sonnet, Opus, Haiku)
- OpenAI (GPT-4, GPT-3.5)
- OpenRouter (any model)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> str:
        """Generate a completion given system and user messages."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier."""
        pass

    def is_free_tier(self) -> bool:
        """Check if this is a free-tier model (typically has stricter rate limits)."""
        model_name = self.get_model_name()
        return ":free" in model_name.lower()


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude models)."""

    def __init__(self, model: str, api_key: str):
        """
        Initialize Anthropic provider.

        Args:
            model: Model ID (e.g., "claude-sonnet-4-5-20250929")
            api_key: Anthropic API key
        """
        import anthropic

        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> str:
        """Generate completion using Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT models)."""

    def __init__(self, model: str, api_key: str):
        """
        Initialize OpenAI provider.

        Args:
            model: Model ID (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key
        """
        import openai

        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> str:
        """Generate completion using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content or ""

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (any model)."""

    def __init__(self, model: str, api_key: str, site_url: Optional[str] = None):
        """
        Initialize OpenRouter provider.

        Args:
            model: Model ID (e.g., "anthropic/claude-sonnet-4", "openai/gpt-4")
            api_key: OpenRouter API key
            site_url: Optional site URL for rankings
        """
        import openai

        self.model = model
        # OpenRouter uses OpenAI-compatible API
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.site_url = site_url

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> str:
        """Generate completion using OpenRouter API."""
        extra_headers = {}
        if self.site_url:
            extra_headers["HTTP-Referer"] = self.site_url

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            extra_headers=extra_headers,
        )
        return response.choices[0].message.content or ""

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model


def create_provider(
    provider_type: str, model: str, api_key: str, **kwargs: Any
) -> LLMProvider:
    """
    Factory function to create LLM providers.

    Args:
        provider_type: One of "anthropic", "openai", "openrouter"
        model: Model identifier
        api_key: API key for the provider
        **kwargs: Additional provider-specific arguments

    Returns:
        LLMProvider instance

    Example:
        >>> provider = create_provider("anthropic", "claude-sonnet-4-5-20250929", api_key)
        >>> provider = create_provider("openai", "gpt-4", api_key)
        >>> provider = create_provider("openrouter", "anthropic/claude-sonnet-4", api_key)
    """
    provider_type = provider_type.lower()

    if provider_type == "anthropic":
        return AnthropicProvider(model, api_key)
    if provider_type == "openai":
        return OpenAIProvider(model, api_key)
    if provider_type == "openrouter":
        return OpenRouterProvider(model, api_key, **kwargs)

    raise ValueError(
        f"Unknown provider type: {provider_type}. "
        "Must be one of: anthropic, openai, openrouter"
    )
