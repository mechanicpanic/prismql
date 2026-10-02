"""Tokenization utilities for PrismQL.

This module provides different tokenization strategies:
- Word tokenizer: Simple alphanumeric splitting
- Unicode tokenizer: Preserves punctuation, emails, URLs, programming terms
  (the default)
"""

import re
from collections.abc import Sequence


def tokenize_words(text: str) -> list[str]:
    """
    Simple word tokenizer.

    Splits on non-alphanumeric characters.

    Example:
        >>> tokenize_words("Hello, world!")
        ['hello', 'world']
        >>> tokenize_words("user@example.com")
        ['user', 'example', 'com']

    Args:
        text: Input text to tokenize

    Returns:
        List of lowercase word tokens
    """
    return [w.lower() for w in re.findall(r"\w+", text)]


# The same token shapes, as one line for engines with a plain regex
# tokenizer (tantivy's ``Tokenizer.regex``): both backends must cut text
# identically or one dictionary means two sets (graph #59). Kept in step
# with the verbose pattern below by ``tests/test_text_mode_parity.py``.
# What a link is: one token from the scheme to the next whitespace. The link
# annotation (contains_link) uses the same shape (graph @aleph/prismql, #115).
URL_SHAPE = r"https?://\S+"
UNICODE_WORD_SHAPES = URL_SHAPE + r"|\w+@\w+(?:\.\w+)+|\w[+#]+|\w+(?:'\w+)*|\w+"

# Unicode-aware tokenizer pattern
# Preserves: emails, URLs, programming terms (C++, C#), contractions
_UNICODE_TOKEN_PATTERN = re.compile(
    r"""
    (?:https?://\S+)|                    # URLs (http://example.com)
    (?:\w+@\w+(?:\.\w+)+)|               # Emails (user@example.com)
    (?:\w[+#]+)|                         # Programming (C++, C#, F#)
    (?:\w+(?:'\w+)*)|                    # Contractions (don't, isn't)
    (?:\w+)                              # Regular words
    """,
    re.VERBOSE | re.IGNORECASE,
)


def tokenize_unicode(text: str, preserve_case: bool = False) -> list[str]:
    """
    Unicode-aware tokenizer preserving punctuation in meaningful contexts.

    This tokenizer preserves:
    - Email addresses: user@example.com
    - URLs: http://example.com, https://site.org
    - Programming terms: C++, C#, F#
    - Contractions: don't, isn't, you're
    - Regular words: hello, world, 123

    Example:
        >>> tokenize_unicode("Check user@example.com for C++ docs!")
        ['check', 'user@example.com', 'for', 'c++', 'docs']
        >>> tokenize_unicode("Don't use http://bad-site.com")
        ['don't', 'use', 'http://bad-site.com']

    Args:
        text: Input text to tokenize
        preserve_case: If True, keep original case; if False, lowercase

    Returns:
        List of tokens
    """
    tokens = _UNICODE_TOKEN_PATTERN.findall(text)
    if preserve_case:
        return tokens
    return [t.lower() for t in tokens]


def tokenize_batch(
    texts: Sequence[str], mode: str = "unicode", preserve_case: bool = False
) -> list[list[str]]:
    """
    Tokenize multiple texts in batch.

    Args:
        texts: List of texts to tokenize
        mode: Tokenization mode ("word" or "unicode")
        preserve_case: If True, keep original case

    Returns:
        List of token lists

    Raises:
        ValueError: If mode is not recognized
    """
    if mode == "word":
        return [tokenize_words(text) for text in texts]
    if mode == "unicode":
        return [tokenize_unicode(text, preserve_case) for text in texts]
    raise ValueError(f"Unknown tokenization mode: {mode}. Use 'word' or 'unicode'")


def generate_ngrams(tokens: Sequence[str], n: int) -> list[str]:
    """
    Generate n-grams from a sequence of tokens.

    Example:
        >>> tokens = ["hello", "world", "from", "alice"]
        >>> generate_ngrams(tokens, 2)
        ['hello world', 'world from', 'from alice']
        >>> generate_ngrams(tokens, 3)
        ['hello world from', 'world from alice']

    Args:
        tokens: Sequence of tokens
        n: N-gram size (2=bigrams, 3=trigrams)

    Returns:
        List of n-grams (tokens joined by spaces)
    """
    if n < 1:
        raise ValueError(f"N-gram size must be >= 1, got {n}")

    if len(tokens) < n:
        return []

    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def generate_all_ngrams(
    tokens: Sequence[str], sizes: Sequence[int]
) -> dict[int, list[str]]:
    """
    Generate multiple n-gram sizes from tokens.

    Example:
        >>> tokens = ["hello", "world", "from", "alice"]
        >>> ngrams = generate_all_ngrams(tokens, [2, 3])
        >>> ngrams[2]
        ['hello world', 'world from', 'from alice']
        >>> ngrams[3]
        ['hello world from', 'world from alice']

    Args:
        tokens: Sequence of tokens
        sizes: List of n-gram sizes to generate

    Returns:
        Dictionary mapping n-gram size to list of n-grams
    """
    return {n: generate_ngrams(tokens, n) for n in sizes}
