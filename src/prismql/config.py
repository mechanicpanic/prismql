"""Configuration classes for PrismQL backends."""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class BackendConfig:
    """
    Configuration for PrismQL backends.

    This class controls optional features like n-gram indexing, token matching,
    and memory optimization strategies.

    Example:
        >>> config = BackendConfig(
        ...     enable_ngrams=True,
        ...     ngram_sizes=[2, 3],
        ...     ngram_min_frequency=2
        ... )
        >>> backend = MemoryBackend(messages, config=config)
    """

    # Tokenization
    tokenizer: str | Callable[[str], list[str]] = "unicode"
    """
    Tokenization strategy:
    - 'word': Alphanumeric splitting (simple, fast)
    - 'unicode': Preserves punctuation, emails, URLs, programming terms
    - Custom callable: Function that takes text and returns list of tokens

    Examples:
        tokenizer="unicode"  # Built-in
        tokenizer=lambda text: text.split()  # Custom
        tokenizer=your_spacy_tokenizer  # spaCy
        tokenizer=tiktoken.get_encoding("cl100k_base").encode  # LLM tokens
    """

    preserve_case: bool = False
    """If True, preserve original case in tokens; if False, lowercase everything"""

    # N-gram indexing
    enable_ngrams: bool = False
    """Enable precomputed n-gram indexes for fast phrase matching"""

    ngram_sizes: list[int] = field(default_factory=lambda: [2, 3])
    """Which n-gram sizes to precompute (default: bigrams and trigrams)"""

    ngram_min_frequency: int = 2
    """Minimum frequency threshold for n-grams (filters rare phrases to save memory)"""

    ngram_max_count: int | None = None
    """Maximum n-grams to keep (top-K most frequent). None = no limit"""

    # Substring indexing (future feature)
    enable_substring_index: bool = False
    """Enable trigram index for substring matching (expensive: ~3x memory)"""

    # Field mappings
    text_fields: list[str] = field(
        default_factory=lambda: ["text", "content", "message"]
    )
    """Fields to index for text search"""

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate tokenizer
        if isinstance(self.tokenizer, str):
            if self.tokenizer not in ["word", "unicode"]:
                raise ValueError(
                    f"Invalid tokenizer: {self.tokenizer}. "
                    f"Must be 'word', 'unicode', or a callable"
                )
        elif not callable(self.tokenizer):
            raise ValueError(
                f"Tokenizer must be a string ('word'/'unicode') or callable, "
                f"got {type(self.tokenizer)}"
            )

        if self.enable_ngrams:
            if not self.ngram_sizes:
                raise ValueError("ngram_sizes cannot be empty when enable_ngrams=True")

            for size in self.ngram_sizes:
                if size < 2:
                    raise ValueError(f"N-gram size must be >= 2, got {size}")

            if self.ngram_min_frequency < 1:
                raise ValueError(
                    f"ngram_min_frequency must be >= 1, got {self.ngram_min_frequency}"
                )

            if self.ngram_max_count is not None and self.ngram_max_count < 1:
                raise ValueError(
                    f"ngram_max_count must be >= 1, got {self.ngram_max_count}"
                )

    def get_tokenizer(self) -> Callable[[str], list[str]]:
        """
        Resolve tokenizer to a callable function.

        Returns:
            Tokenizer function that takes text and returns tokens

        Raises:
            ValueError: If tokenizer is invalid
        """
        from prismql.tokenizers import tokenize_unicode, tokenize_words

        if callable(self.tokenizer):
            return self.tokenizer

        if self.tokenizer == "word":
            return tokenize_words
        if self.tokenizer == "unicode":
            return lambda text: tokenize_unicode(text, self.preserve_case)
        raise ValueError(f"Unknown tokenizer: {self.tokenizer}")


# Default configurations for common use cases
DEFAULT_CONFIG = BackendConfig()
"""Default configuration: unicode tokenizer, no n-grams"""

BALANCED_CONFIG = BackendConfig(
    tokenizer="unicode",
    enable_ngrams=True,
    ngram_sizes=[2, 3],
    ngram_min_frequency=2,
)
"""Balanced configuration: token matching + filtered n-grams (~3-4x memory)"""

PERFORMANCE_CONFIG = BackendConfig(
    tokenizer="unicode",
    enable_ngrams=True,
    ngram_sizes=[2, 3, 4],
    ngram_min_frequency=1,
)
"""Performance configuration: all features enabled (higher memory usage)"""

MINIMAL_CONFIG = BackendConfig(
    tokenizer="word",
    enable_ngrams=False,
)
"""Minimal configuration: word matching only (lowest memory)"""
