"""
Examples of custom tokenizers for PrismQL.

This module demonstrates how to use different tokenization strategies
for indexing and searching conversational data.
"""

from prismql.backends.memory import MemoryBackend
from prismql.config import BackendConfig

# Sample conversation data
SAMPLE_MESSAGES = [
    {"id": 1, "user": "alice", "text": "Check out https://github.com/example"},
    {"id": 2, "user": "bob", "text": "Email me at bob@company.com"},
    {"id": 3, "user": "alice", "text": "I love programming in C++"},
    {"id": 4, "user": "bob", "text": "Don't forget to test!"},
    {"id": 5, "user": "alice", "text": "The model uses 1000 tokens"},
]


# Example 1: Built-in tokenizers
def example_builtin_tokenizers():
    """Compare built-in 'word' vs 'unicode' tokenizers."""
    print("=" * 60)
    print("Example 1: Built-in Tokenizers")
    print("=" * 60)

    # Word tokenizer: Simple alphanumeric splitting
    config_word = BackendConfig(tokenizer="word")
    backend_word = MemoryBackend(SAMPLE_MESSAGES, config=config_word)

    # Unicode tokenizer: Preserves emails, URLs, C++, contractions
    config_unicode = BackendConfig(tokenizer="unicode")
    backend_unicode = MemoryBackend(SAMPLE_MESSAGES, config=config_unicode)

    # Search for "C++"
    results_word = backend_word.search_text(["c++"])
    results_unicode = backend_unicode.search_text(["c++"])

    print("\nSearch for 'C++':")
    print(f"  Word tokenizer: {sorted(results_word)} (splits C++ into 'c')")
    print(f"  Unicode tokenizer: {sorted(results_unicode)} (preserves 'c++')")

    # Search for email
    results_word2 = backend_word.search_text(["bob@company.com"])
    results_unicode2 = backend_unicode.search_text(["bob@company.com"])

    print("\nSearch for 'bob@company.com':")
    print(
        f"  Word tokenizer: {sorted(results_word2)} (splits into 'bob', 'company', 'com')"
    )
    print(
        f"  Unicode tokenizer: {sorted(results_unicode2)} (preserves 'bob@company.com')"
    )


# Example 2: spaCy tokenizer
def example_spacy_tokenizer():
    """Use spaCy's linguistic tokenization."""
    print("\n" + "=" * 60)
    print("Example 2: spaCy Tokenizer (Linguistic)")
    print("=" * 60)

    try:
        import spacy

        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")

        # Create spaCy tokenizer wrapper
        def spacy_tokenizer(text: str) -> list[str]:
            """Tokenize using spaCy's linguistic rules."""
            doc = nlp(text)
            return [token.text.lower() for token in doc]

        config = BackendConfig(tokenizer=spacy_tokenizer)
        backend = MemoryBackend(SAMPLE_MESSAGES, config=config)

        # spaCy handles contractions differently
        results = backend.search_text(["n't"])  # spaCy splits "don't" -> ["do", "n't"]
        print('\nSearch for "n\'t" (contraction part):')
        print(f"  Results: {sorted(results)}")
        print('  spaCy splits "don\'t" into ["do", "n\'t"]')

    except ImportError:
        print("\n⚠️  spaCy not installed. Install with: pip install spacy")
        print("    Then download model: python -m spacy download en_core_web_sm")


# Example 3: LLM tokenizer (tiktoken for GPT models)
def example_llm_tokenizer():
    """Use LLM tokenization to analyze conversations with token counts."""
    print("\n" + "=" * 60)
    print("Example 3: LLM Tokenizer (tiktoken for GPT)")
    print("=" * 60)

    try:
        import tiktoken

        # Get GPT-4 tokenizer
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4, GPT-3.5-turbo

        # Create wrapper that returns token IDs as strings
        def llm_tokenizer(text: str) -> list[str]:
            """Tokenize using GPT-4's tokenizer."""
            token_ids = encoding.encode(text)
            # Return tokens as strings (for compatibility with string-based indexes)
            return [str(tid) for tid in token_ids]

        config = BackendConfig(
            tokenizer=llm_tokenizer,
            enable_ngrams=True,
            ngram_sizes=[2, 3],  # Token bigrams and trigrams
            ngram_min_frequency=1,
        )
        backend = MemoryBackend(SAMPLE_MESSAGES, config=config)

        print("\nToken-level indexing complete!")
        print(f"  Total documents: {backend.get_total_documents()}")
        print(f"  N-gram indexes built: {list(backend._ngram_indexes.keys())}")

        # Example: Find messages with similar token patterns
        # This is useful for finding semantically similar phrases
        # even if the actual words differ

        # Decode a sample to show tokens
        sample_text = "Don't forget to test!"
        tokens = encoding.encode(sample_text)
        decoded = [encoding.decode([t]) for t in tokens]
        print(f"\nExample tokenization of: '{sample_text}'")
        print(f"  Tokens: {tokens}")
        print(f"  Decoded: {decoded}")

    except ImportError:
        print("\n⚠️  tiktoken not installed. Install with: pip install tiktoken")


# Example 4: Domain-specific tokenizer
def example_domain_specific_tokenizer():
    """Custom tokenizer for code-heavy conversations."""
    print("\n" + "=" * 60)
    print("Example 4: Domain-Specific Tokenizer (Code-aware)")
    print("=" * 60)

    import re

    def code_aware_tokenizer(text: str) -> list[str]:
        """
        Tokenizer optimized for code-heavy conversations.

        Preserves:
        - Function calls: split() -> "split("
        - Variable names: snake_case, camelCase
        - Operators: ==, !=, <=, >=
        - Code symbols: ->, =>, ::
        """
        pattern = r"""
            (?:[a-zA-Z_][a-zA-Z0-9_]*\()|  # Function calls
            (?:->|=>|::)|                   # Code arrows/scope
            (?:==|!=|<=|>=)|                # Comparison operators
            (?:\w+)|                        # Regular words
            (?:[+\-*/%])                    # Math operators
        """
        tokens = re.findall(pattern, text, re.VERBOSE)
        return [t.lower() for t in tokens if t]

    messages = [
        {"id": 1, "text": "Call split() on the string"},
        {"id": 2, "text": "Use the -> operator for pointer"},
        {"id": 3, "text": "Check if value == 0"},
    ]

    config = BackendConfig(tokenizer=code_aware_tokenizer)
    backend = MemoryBackend(messages, config=config)

    # Search for function call
    results = backend.search_text(["split("])
    print("\nSearch for 'split(' (function call):")
    print(f"  Results: {sorted(results)}")

    # Search for operator
    results2 = backend.search_text(["->"])
    print("\nSearch for '->' (pointer operator):")
    print(f"  Results: {sorted(results2)}")


# Example 5: Byte-level tokenizer
def example_byte_level_tokenizer():
    """Byte-level tokenization for multilingual support."""
    print("\n" + "=" * 60)
    print("Example 5: Byte-Level Tokenizer (Multilingual)")
    print("=" * 60)

    def byte_level_tokenizer(text: str) -> list[str]:
        """
        Byte-level tokenization.

        Useful for:
        - Multilingual text
        - Text with emojis
        - Any Unicode characters
        """
        # Convert to bytes, then to strings
        bytes_list = text.encode("utf-8")
        return [str(b) for b in bytes_list if b > 32]  # Skip control chars

    messages = [
        {"id": 1, "text": "Hello 世界"},  # English + Chinese
        {"id": 2, "text": "Привет world"},  # Russian + English
        {"id": 3, "text": "Thanks! 😊"},  # Emoji
    ]

    config = BackendConfig(tokenizer=byte_level_tokenizer)
    backend = MemoryBackend(messages, config=config)

    print(f"\nIndexed {backend.get_total_documents()} multilingual messages")
    print("  Byte-level indexing handles any Unicode character")


if __name__ == "__main__":
    example_builtin_tokenizers()
    example_spacy_tokenizer()
    example_llm_tokenizer()
    example_domain_specific_tokenizer()
    example_byte_level_tokenizer()

    print("\n" + "=" * 60)
    print("Summary: Custom Tokenizers")
    print("=" * 60)
    print(
        """
Custom tokenizers allow you to:
1. Match how users actually write (preserving punctuation, emojis, etc.)
2. Analyze LLM conversations at the token level (using tiktoken)
3. Use linguistic tokenization (spaCy)
4. Create domain-specific rules (code-aware, math-aware, etc.)
5. Handle multilingual data (byte-level)

Usage:
    config = BackendConfig(
        tokenizer=your_custom_function,
        enable_ngrams=True,
        ngram_sizes=[2, 3]
    )
    backend = MemoryBackend(messages, config=config)
    """
    )
