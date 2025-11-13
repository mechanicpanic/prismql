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

    def __init__(
        self,
        model: str,
        api_key: str,
        extended_thinking: bool = False,
        base_url: str | None = None,
    ):
        """
        Initialize Anthropic provider.

        Args:
            model: Model ID (e.g., "claude-sonnet-4-5-20250929")
            api_key: Anthropic API key
            extended_thinking: Enable extended thinking mode (captures thinking blocks)
            base_url: Optional custom base URL (e.g., for MiniMax compatibility)
        """
        import anthropic

        self.model = model
        if base_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
        self.extended_thinking = extended_thinking

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> tuple[str, Optional[str]]:
        """Generate completion using Anthropic API."""
        # Use extended thinking if enabled
        # budget_tokens must be >= 1024 and < max_tokens
        if self.extended_thinking:
            # Need at least 1024 for thinking + some for response
            thinking_budget = max(1024, min(max_tokens - 200, 2000))
            if max_tokens <= 1224:  # 1024 + 200 minimum
                # Not enough room for thinking, disable it
                thinking_config = {"type": "disabled"}
            else:
                thinking_config = {"type": "enabled", "budget_tokens": thinking_budget}
        else:
            thinking_config = {"type": "disabled"}

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
                # Thinking blocks use 'thinking' attribute for content
                if hasattr(block, "thinking"):
                    thinking_text += block.thinking + "\n"
                elif hasattr(block, "text"):
                    # Fallback to 'text' attribute if 'thinking' doesn't exist
                    thinking_text += block.text + "\n"
            elif block.type == "text":
                content_text += block.text

        return content_text, thinking_text if thinking_text else None

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports extended thinking mode."""
        return self.extended_thinking


class MinimaxProvider(AnthropicProvider):
    """MiniMax API provider (Anthropic-compatible)."""

    def __init__(self, model: str, api_key: str, extended_thinking: bool = False):
        """
        Initialize MiniMax provider.

        Args:
            model: Model ID (e.g., "MiniMax-M2", "MiniMax-M2-Stable")
            api_key: MiniMax API key
            extended_thinking: Enable extended thinking mode (captures thinking blocks)
        """
        # MiniMax uses Anthropic-compatible API
        super().__init__(
            model=model,
            api_key=api_key,
            extended_thinking=extended_thinking,
            base_url="https://api.minimax.io/anthropic",
        )


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
            # New 2025 reasoning models
            "qwen3",
            "openreasoning-nemotron",
            "acereason-nemotron",
            "phi-4-reasoning",
            "nemotron",  # Covers all Nemotron reasoning variants
        ]
        return any(keyword in self.model.lower() for keyword in reasoning_models)


class VLLMProvider(LLMProvider):
    """vLLM local inference provider."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "EMPTY",
    ):
        """
        Initialize vLLM provider.

        Args:
            model: Model name (must match vLLM server model)
            base_url: vLLM server URL (default: http://localhost:8000/v1)
            api_key: API key (default: "EMPTY" for local vLLM)
        """
        import openai

        self.model = model
        # vLLM uses OpenAI-compatible API
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> tuple[str, Optional[str]]:
        """Generate completion using vLLM server."""
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

        # vLLM doesn't expose reasoning tokens by default
        # but some models may include them in the response
        return content, None

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports reasoning."""
        reasoning_models = [
            "qwen3",
            "nemotron",
            "phi-4-reasoning",
            "deepseek-r1",
            "r1-distill",
        ]
        return any(keyword in self.model.lower() for keyword in reasoning_models)


class OllamaProvider(LLMProvider):
    """Ollama local inference provider."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
    ):
        """
        Initialize Ollama provider.

        Args:
            model: Model name (e.g., "qwen3:14b", "deepseek-r1:32b")
            base_url: Ollama server URL (default: http://localhost:11434)
        """
        import requests

        self.model = model
        self.base_url = base_url.rstrip("/")
        self.requests = requests

    def generate(
        self, system_prompt: str, user_message: str, max_tokens: int = 500
    ) -> tuple[str, Optional[str]]:
        """Generate completion using Ollama API."""
        response = self.requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data.get("message", {}).get("content", "")

        # Ollama doesn't separate reasoning tokens
        # but they may be embedded in the response for reasoning models
        return content, None

    def get_model_name(self) -> str:
        """Get model identifier."""
        return self.model

    def supports_extended_thinking(self) -> bool:
        """Check if this model supports reasoning."""
        reasoning_models = [
            "qwen3",
            "nemotron",
            "phi-4",
            "deepseek-r1",
            "r1",
        ]
        return any(keyword in self.model.lower() for keyword in reasoning_models)


def create_provider(
    provider_type: str, model: str, api_key: str = "EMPTY", **kwargs: Any
) -> LLMProvider:
    """
    Factory function to create LLM providers.

    Args:
        provider_type: One of "anthropic", "openai", "openrouter", "minimax", "vllm", "ollama"
        model: Model identifier
        api_key: API key for the provider (default "EMPTY" for local providers)
        **kwargs: Additional provider-specific arguments

    Returns:
        LLMProvider instance

    Example:
        >>> # API providers
        >>> provider = create_provider("anthropic", "claude-sonnet-4-5-20250929", api_key)
        >>> provider = create_provider("openai", "gpt-4", api_key)
        >>> provider = create_provider("openrouter", "anthropic/claude-sonnet-4", api_key)
        >>> provider = create_provider("minimax", "MiniMax-M2", api_key)

        >>> # Local inference providers
        >>> provider = create_provider("vllm", "Qwen/Qwen3-14B")
        >>> provider = create_provider("ollama", "qwen3:14b")
        >>> provider = create_provider("vllm", "nvidia/OpenReasoning-Nemotron-32B",
        ...                           base_url="http://192.168.1.100:8000/v1")
    """
    provider_type = provider_type.lower()

    if provider_type == "anthropic":
        return AnthropicProvider(model, api_key, **kwargs)
    if provider_type == "openai":
        return OpenAIProvider(model, api_key, **kwargs)
    if provider_type == "openrouter":
        return OpenRouterProvider(model, api_key, **kwargs)
    if provider_type == "minimax":
        return MinimaxProvider(model, api_key, **kwargs)
    if provider_type == "vllm":
        return VLLMProvider(model, **kwargs)
    if provider_type == "ollama":
        return OllamaProvider(model, **kwargs)

    raise ValueError(
        f"Unknown provider type: {provider_type}. "
        "Must be one of: anthropic, openai, openrouter, minimax, vllm, ollama"
    )
