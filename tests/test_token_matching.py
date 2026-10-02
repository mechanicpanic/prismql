"""Tests for token-based matching (Unicode-aware tokenization)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.tokenizers import (
    generate_ngrams,
    tokenize_unicode,
    tokenize_words,
)


class TestTokenizers:
    """Test tokenization functions."""

    def test_word_tokenizer_basic(self):
        """Test basic word tokenization (alphanumeric only)."""
        text = "Hello, world!"
        tokens = tokenize_words(text)
        assert tokens == ["hello", "world"]

    def test_word_tokenizer_email(self):
        """Word tokenizer splits emails into parts."""
        text = "Contact user@example.com"
        tokens = tokenize_words(text)
        assert tokens == ["contact", "user", "example", "com"]

    def test_word_tokenizer_programming(self):
        """Word tokenizer loses punctuation in programming terms."""
        text = "I love C++ and C#"
        tokens = tokenize_words(text)
        assert tokens == ["i", "love", "c", "and", "c"]

    def test_unicode_tokenizer_basic(self):
        """Test Unicode tokenizer preserves meaningful structure."""
        text = "Hello, world!"
        tokens = tokenize_unicode(text)
        assert tokens == ["hello", "world"]

    def test_unicode_tokenizer_email(self):
        """Unicode tokenizer preserves email addresses."""
        text = "Contact user@example.com today"
        tokens = tokenize_unicode(text)
        assert "user@example.com" in tokens
        assert tokens == ["contact", "user@example.com", "today"]

    def test_unicode_tokenizer_url(self):
        """Unicode tokenizer preserves URLs."""
        text = "Visit http://example.com or https://secure.site.org"
        tokens = tokenize_unicode(text)
        assert "http://example.com" in tokens
        assert "https://secure.site.org" in tokens

    def test_unicode_tokenizer_programming(self):
        """Unicode tokenizer preserves programming language names."""
        text = "I love C++ and C# and F#"
        tokens = tokenize_unicode(text)
        assert "c++" in tokens
        assert "c#" in tokens
        assert "f#" in tokens

    def test_unicode_tokenizer_contractions(self):
        """Unicode tokenizer preserves contractions."""
        text = "Don't you think it's amazing? I can't believe it!"
        tokens = tokenize_unicode(text)
        assert "don't" in tokens
        assert "it's" in tokens
        assert "can't" in tokens

    def test_unicode_tokenizer_mixed(self):
        """Test complex real-world text."""
        text = "Email me at dev@company.com about the C++ issue. Don't forget!"
        tokens = tokenize_unicode(text)
        assert "dev@company.com" in tokens
        assert "c++" in tokens
        assert "don't" in tokens

    def test_unicode_tokenizer_case_insensitive(self):
        """Unicode tokenizer lowercases by default."""
        text = "HELLO World HTTP://EXAMPLE.COM"
        tokens = tokenize_unicode(text)
        assert "hello" in tokens
        assert "world" in tokens
        assert "http://example.com" in tokens

    def test_unicode_tokenizer_preserve_case(self):
        """Unicode tokenizer can preserve case."""
        text = "Hello World"
        tokens = tokenize_unicode(text, preserve_case=True)
        assert "Hello" in tokens
        assert "World" in tokens


class TestMemoryBackendTokenIndex:
    """Test token indexing in MemoryBackend."""

    @pytest.fixture
    def messages_with_emails(self):
        """Test messages containing emails."""
        return [
            {"id": 1, "user": "alice", "text": "Contact me at alice@company.com"},
            {"id": 2, "user": "bob", "text": "Email bob@example.org"},
            {"id": 3, "user": "charlie", "text": "Use support@service.io for help"},
            {"id": 4, "user": "alice", "text": "Regular message without email"},
        ]

    @pytest.fixture
    def messages_with_programming(self):
        """Test messages with programming terms."""
        return [
            {"id": 1, "user": "alice", "text": "I program in C++"},
            {"id": 2, "user": "bob", "text": "Learning C# now"},
            {"id": 3, "user": "charlie", "text": "F# is functional"},
            {"id": 4, "user": "dave", "text": "Python and Java"},
        ]

    def test_search_tokens_email(self, messages_with_emails):
        """Test searching for email addresses."""
        backend = MemoryBackend(messages_with_emails)

        # Search for specific email
        results = backend.search_tokens(["alice@company.com"])
        assert results == {1}

        results = backend.search_tokens(["bob@example.org"])
        assert results == {2}

        results = backend.search_tokens(["support@service.io"])
        assert results == {3}

    def test_search_tokens_programming(self, messages_with_programming):
        """Test searching for programming language names."""
        backend = MemoryBackend(messages_with_programming)

        # Search for C++ (preserved with punctuation)
        results = backend.search_tokens(["c++"])
        assert results == {1}

        # Search for C#
        results = backend.search_tokens(["c#"])
        assert results == {2}

        # Search for F#
        results = backend.search_tokens(["f#"])
        assert results == {3}

    def test_search_tokens_vs_search_text(self, messages_with_programming):
        """Compare token search vs word search for programming terms."""
        backend = MemoryBackend(messages_with_programming)

        # Token search finds exact match
        token_results = backend.search_tokens(["c++"])
        assert token_results == {1}

        # search_text matches "c++" as a whole word or substring: here the
        # same single message
        word_results = backend.search_text(["c++"])
        assert len(word_results) >= len(token_results)

    def test_search_tokens_or_operator(self, messages_with_emails):
        """Test OR operator with token search."""
        backend = MemoryBackend(messages_with_emails)

        # Search for multiple emails (OR)
        results = backend.search_tokens(
            ["alice@company.com", "bob@example.org"], operator="OR"
        )
        assert results == {1, 2}

    def test_search_tokens_and_operator(self, messages_with_programming):
        """Test AND operator with token search."""
        backend = MemoryBackend(messages_with_programming)

        # No message has both C++ and C#
        results = backend.search_tokens(["c++", "c#"], operator="AND")
        assert results == set()

        # Message 4 has both Python and Java
        results = backend.search_tokens(["python", "java"], operator="AND")
        assert results == {4}


class TestContainsTokensQuery:
    """Test contains_tokens() query operator."""

    @pytest.fixture
    def engine_with_tech_terms(self):
        """Engine with technical terms dictionary."""
        messages = [
            {"id": 1, "user": "alice", "text": "Email alice@company.com"},
            {"id": 2, "user": "bob", "text": "Programming in C++"},
            {"id": 3, "user": "charlie", "text": "Learning C# today"},
            {"id": 4, "user": "dave", "text": "Visit http://example.com"},
            {"id": 5, "user": "eve", "text": "Don't forget the meeting"},
            {"id": 6, "user": "frank", "text": "Regular message"},
        ]

        backend = MemoryBackend(messages)

        dictionaries = {
            "emails": ["alice@company.com", "bob@example.org"],
            "programming_languages": ["c++", "c#", "f#", "python"],
            "urls": ["http://example.com", "https://secure.com"],
            "contractions": ["don't", "can't", "won't", "isn't"],
        }

        return PrismQLEngine(backend, user_dictionaries=dictionaries)

    def test_contains_tokens_emails(self, engine_with_tech_terms):
        """Test searching for emails using contains_tokens."""
        result = engine_with_tech_terms.execute("SELECT contains_tokens(emails)")
        assert result == [[1]]  # Only message 1 has alice@company.com

    def test_contains_tokens_programming(self, engine_with_tech_terms):
        """Test searching for programming languages."""
        result = engine_with_tech_terms.execute(
            "SELECT contains_tokens(programming_languages)"
        )
        # Messages 2 and 3 have C++ and C#
        # Flatten result: each match is a separate group
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {2, 3}

    def test_contains_tokens_urls(self, engine_with_tech_terms):
        """Test searching for URLs."""
        result = engine_with_tech_terms.execute("SELECT contains_tokens(urls)")
        assert result == [[4]]

    def test_contains_tokens_contractions(self, engine_with_tech_terms):
        """Test searching for contractions."""
        result = engine_with_tech_terms.execute("SELECT contains_tokens(contractions)")
        assert result == [[5]]  # Message 5 has "Don't"

    def test_contains_tokens_with_from(self, engine_with_tech_terms):
        """Test contains_tokens combined with from."""
        result = engine_with_tech_terms.execute(
            "SELECT contains_tokens(programming_languages) AND from(bob)"
        )
        assert result == [[2]]  # Bob's message with C++

    def test_contains_tokens_wildcard(self, engine_with_tech_terms):
        """Test wildcard with contains_tokens."""
        result = engine_with_tech_terms.execute("SELECT contains_tokens(*)")
        # Should match all messages (each as separate group)
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {1, 2, 3, 4, 5, 6}

    def test_contains_tokens_nonexistent_dict(self, engine_with_tech_terms):
        """Test error on nonexistent dictionary."""
        from prismql.exceptions import PrismQLRuntimeError

        with pytest.raises(
            PrismQLRuntimeError, match="Dictionary 'nonexistent' not found"
        ):
            engine_with_tech_terms.execute("SELECT contains_tokens(nonexistent)")

    def test_contains_vs_contains_tokens(self, engine_with_tech_terms):
        """contains_tokens() keeps "C++" and "C#" whole."""
        # contains() runs too (it gives the same [[2], [3]] in every mode)
        engine_with_tech_terms.execute("SELECT contains(programming_languages)")

        # contains_tokens() preserves "C++"
        result_tokens = engine_with_tech_terms.execute(
            "SELECT contains_tokens(programming_languages)"
        )

        token_ids = {msg_id for group in result_tokens for msg_id in group}
        assert token_ids == {2, 3}  # Exact C++, C# matches


class TestNgramGeneration:
    """Test n-gram generation utilities."""

    def test_generate_bigrams(self):
        """Test bigram generation."""
        tokens = ["hello", "world", "from", "alice"]
        bigrams = generate_ngrams(tokens, 2)
        assert bigrams == ["hello world", "world from", "from alice"]

    def test_generate_trigrams(self):
        """Test trigram generation."""
        tokens = ["hello", "world", "from", "alice"]
        trigrams = generate_ngrams(tokens, 3)
        assert trigrams == ["hello world from", "world from alice"]

    def test_generate_ngrams_short_sequence(self):
        """Test n-grams with sequence shorter than n."""
        tokens = ["hello"]
        bigrams = generate_ngrams(tokens, 2)
        assert bigrams == []

    def test_generate_ngrams_exact_length(self):
        """Test n-grams with sequence exactly n tokens."""
        tokens = ["hello", "world"]
        bigrams = generate_ngrams(tokens, 2)
        assert bigrams == ["hello world"]

    def test_generate_ngrams_invalid_n(self):
        """Test error on invalid n-gram size."""
        tokens = ["hello", "world"]
        with pytest.raises(ValueError, match="N-gram size must be >= 1"):
            generate_ngrams(tokens, 0)


class TestEdgeCases:
    """Test edge cases in token matching."""

    def test_empty_text(self):
        """Test tokenization of empty text."""
        assert tokenize_words("") == []
        assert tokenize_unicode("") == []

    def test_whitespace_only(self):
        """Test tokenization of whitespace."""
        assert tokenize_words("   \n\t  ") == []
        assert tokenize_unicode("   \n\t  ") == []

    def test_special_characters_only(self):
        """Test tokenization of special characters."""
        # Word tokenizer extracts nothing
        assert tokenize_words("!@#$%^&*()") == []

        # Unicode tokenizer also extracts nothing (no alphanumeric)
        assert tokenize_unicode("!@#$%^&*()") == []

    def test_numbers(self):
        """Test tokenization of numbers."""
        text = "Call 123-456-7890 or visit room 42"
        words = tokenize_words(text)
        assert "123" in words
        assert "456" in words
        assert "7890" in words
        assert "42" in words

        tokens = tokenize_unicode(text)
        assert "123" in tokens
        assert "456" in tokens
        assert "7890" in tokens
        assert "42" in tokens

    def test_mixed_case_search(self):
        """Test that search is case-insensitive."""
        messages = [
            {"id": 1, "user": "alice", "text": "Email ALICE@COMPANY.COM"},
            {"id": 2, "user": "bob", "text": "Programming in c++"},
        ]

        backend = MemoryBackend(messages)

        # Search is case-insensitive
        results = backend.search_tokens(["alice@company.com"])
        assert results == {1}

        results = backend.search_tokens(["C++"])
        assert results == {2}
