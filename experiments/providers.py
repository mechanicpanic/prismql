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
    ) -> tuple[str, Optional[str]]:
        """
        Generate a completion given system and user messages.

        Returns:
            Tuple of (content, chain_of_thought)
            - content: The main response text
            - chain_of_thought: Reasoning/thinking tokens if available, None otherwise
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier."""
        pass

    def is_free_tier(self) -> bool:
        """Check if this is a free-tier model (typically has stricter rate limits)."""
        model_name = self.get_model_name()
        return ":free" in model_name.lower()

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports extended thinking mode."""
        return False


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude models)."""

    def __init__(self, model: str, api_key: str, extended_thinking: bool = False):
        """
        Initialize Anthropic provider.

        Args:
            model: Model ID (e.g., "claude-sonnet-4-5-20250929")
            api_key: Anthropic API key
            extended_thinking: Enable extended thinking mode (captures thinking blocks)
        """
        import anthropic

        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.extended_thinking = extended_thinking

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> tuple[str, Optional[str]]:
        """Generate completion using Anthropic API."""
        # Use extended thinking if enabled
        thinking_config = (
            {"type": "enabled", "budget_tokens": 5000}
            if self.extended_thinking
            else {"type": "disabled"}
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            thinking=thinking_config,
        )

        # Extract content and thinking blocks
        content_text = ""
        thinking_text = ""

        for block in response.content:
            if block.type == "thinking":
                thinking_text += block.thinking + "\n"
            elif block.type == "text":
                content_text += block.text

        return content_text, thinking_text if thinking_text else None

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports extended thinking mode."""
        return self.extended_thinking


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT models)."""

    def __init__(self, model: str, api_key: str):
        """
        Initialize OpenAI provider.

        Args:
            model: Model ID (e.g., "gpt-4", "gpt-3.5-turbo", "gpt-5")
            api_key: OpenAI API key
        """
        import openai

        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> tuple[str, Optional[str]]:
        """Generate completion using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        # Extract reasoning tokens if available (for o1/o3/gpt-5-thinking models)
        reasoning = None
        if (
            hasattr(choice.message, "reasoning_content")
            and choice.message.reasoning_content
        ):
            reasoning = choice.message.reasoning_content

        return content, reasoning

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports reasoning tokens."""
        # o1/o3 and GPT-5 models support reasoning
        reasoning_models = ["o1", "o3", "gpt-5"]
        return any(keyword in self.model.lower() for keyword in reasoning_models)


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (any model)."""

    def __init__(
        self,
        model: str,
        api_key: str,
        site_url: Optional[str] = None,
        enable_reasoning: bool = False,
    ):
        """
        Initialize OpenRouter provider.

        Args:
            model: Model ID (e.g., "anthropic/claude-sonnet-4", "openai/gpt-4")
            api_key: OpenRouter API key
            site_url: Optional site URL for rankings
            enable_reasoning: Enable reasoning tokens for supported models
        """
        import openai

        self.model = model
        # OpenRouter uses OpenAI-compatible API
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.site_url = site_url
        self.enable_reasoning = enable_reasoning

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> tuple[str, Optional[str]]:
        """Generate completion using OpenRouter API."""
        extra_headers = {}
        if self.site_url:
            extra_headers["HTTP-Referer"] = self.site_url

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "extra_headers": extra_headers,
        }

        # Enable reasoning for supported models
        if self.enable_reasoning and self.supports_extended_thinking():
            request_kwargs["extra_body"] = {"reasoning": {"enabled": True}}

        response = self.client.chat.completions.create(**request_kwargs)

        choice = response.choices[0]
        content = choice.message.content or ""

        # Extract reasoning tokens (OpenRouter format: reasoning_details array)
        reasoning = None

        # Check for reasoning_details (OpenRouter's format)
        if hasattr(choice.message, "reasoning_details"):
            reasoning_details = choice.message.reasoning_details
            if reasoning_details:
                # Combine all reasoning blocks
                reasoning_parts = []
                for detail in reasoning_details:
                    detail_type = detail.get("type", "")
                    if detail_type == "reasoning.text":
                        reasoning_parts.append(detail.get("text", ""))
                    elif detail_type == "reasoning.summary":
                        reasoning_parts.append(f"[Summary] {detail.get('text', '')}")
                if reasoning_parts:
                    reasoning = "\n\n".join(reasoning_parts)

        # Fallback: Check for reasoning_content (OpenAI's format)
        if not reasoning and hasattr(choice.message, "reasoning_content"):
            reasoning = choice.message.reasoning_content

        return content, reasoning

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports reasoning tokens."""
        # Check if it's a reasoning model
        reasoning_models = [
            "gpt-5",
            "o1",
            "o3",
            "thinking",
            "deepseek-r1",
            "deepseek/r1",
            "deepseek-v3",
            "deepseek/v3",
            "gemini-2.0",
            "gemini-2.5",
        ]
        return any(keyword in self.model.lower() for keyword in reasoning_models)


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
        return AnthropicProvider(model, api_key, **kwargs)
    if provider_type == "openai":
        return OpenAIProvider(model, api_key, **kwargs)
    if provider_type == "openrouter":
        return OpenRouterProvider(model, api_key, **kwargs)

    raise ValueError(
        f"Unknown provider type: {provider_type}. "
        "Must be one of: anthropic, openai, openrouter"
    )
