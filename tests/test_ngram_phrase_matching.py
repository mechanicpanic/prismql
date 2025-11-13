"""Tests for n-gram phrase matching."""

import pytest
from prismql.backends.memory import MemoryBackend
from prismql.config import BALANCED_CONFIG, MINIMAL_CONFIG, BackendConfig
from prismql.engine import PrismQLEngine


class TestNgramIndexBuilding:
    """Test n-gram index construction and filtering."""

    def test_bigram_index_basic(self):
        """Test basic bigram index building."""
        messages = [
            {"id": 1, "text": "thank you very much"},
            {"id": 2, "text": "thank you for helping"},
            {"id": 3, "text": "you are welcome"},
        ]

        config = BackendConfig(
            enable_ngrams=True, ngram_sizes=[2], ngram_min_frequency=1
        )
        backend = MemoryBackend(messages, config=config)

        # Check that bigram index was built
        assert 2 in backend._ngram_indexes
        bigram_index = backend._ngram_indexes[2]

        # "thank you" appears in messages 1 and 2
        assert "thank you" in bigram_index
        assert bigram_index["thank you"] == {1, 2}

        # "you are" appears only in message 3
        assert "you are" in bigram_index
        assert bigram_index["you are"] == {3}

    def test_trigram_index_basic(self):
        """Test basic trigram index building."""
        messages = [
            {"id": 1, "text": "out of memory error"},
            {"id": 2, "text": "out of memory again"},
            {"id": 3, "text": "memory is full"},
        ]

        config = BackendConfig(enable_ngrams=True, ngram_sizes=[3])
        backend = MemoryBackend(messages, config=config)

        # Check trigram index
        assert 3 in backend._ngram_indexes
        trigram_index = backend._ngram_indexes[3]

        # "out of memory" appears in messages 1 and 2
        assert "out of memory" in trigram_index
        assert trigram_index["out of memory"] == {1, 2}

    def test_multiple_ngram_sizes(self):
        """Test building both bigram and trigram indexes."""
        messages = [
            {"id": 1, "text": "thank you very much"},
            {"id": 2, "text": "thank you again"},
        ]

        config = BackendConfig(
            enable_ngrams=True, ngram_sizes=[2, 3], ngram_min_frequency=1
        )
        backend = MemoryBackend(messages, config=config)

        # Both indexes should exist
        assert 2 in backend._ngram_indexes
        assert 3 in backend._ngram_indexes

        # Bigrams
        assert "thank you" in backend._ngram_indexes[2]

        # Trigrams
        assert "thank you very" in backend._ngram_indexes[3]
        assert "you very much" in backend._ngram_indexes[3]

    def test_frequency_filtering(self):
        """Test that rare n-grams are filtered out."""
        messages = [
            {"id": 1, "text": "thank you"},
            {"id": 2, "text": "thank you"},
            {"id": 3, "text": "hello world"},  # Appears once
        ]

        config = BackendConfig(
            enable_ngrams=True, ngram_sizes=[2], ngram_min_frequency=2
        )
        backend = MemoryBackend(messages, config=config)

        bigram_index = backend._ngram_indexes[2]

        # "thank you" appears twice - should be indexed
        assert "thank you" in bigram_index

        # "hello world" appears once - should be filtered out
        assert "hello world" not in bigram_index

    def test_max_count_filtering(self):
        """Test that only top-K n-grams are kept."""
        messages = [
            {"id": 1, "text": "a b"},  # freq=3
            {"id": 2, "text": "a b"},
            {"id": 3, "text": "a b"},
            {"id": 4, "text": "c d"},  # freq=2
            {"id": 5, "text": "c d"},
            {"id": 6, "text": "e f"},  # freq=1
        ]

        config = BackendConfig(
            enable_ngrams=True,
            ngram_sizes=[2],
            ngram_min_frequency=1,
            ngram_max_count=2,  # Keep only top 2
        )
        backend = MemoryBackend(messages, config=config)

        bigram_index = backend._ngram_indexes[2]

        # Should have exactly 2 n-grams (the most frequent)
        assert len(bigram_index) == 2
        assert "a b" in bigram_index  # freq=3
        assert "c d" in bigram_index  # freq=2
        assert "e f" not in bigram_index  # freq=1, filtered out

    def test_no_ngrams_when_disabled(self):
        """Test that n-grams are not built when disabled."""
        messages = [{"id": 1, "text": "thank you"}]

        config = BackendConfig(enable_ngrams=False)
        backend = MemoryBackend(messages, config=config)

        # N-gram indexes should be empty
        assert not backend._ngram_indexes


class TestSearchPhrase:
    """Test phrase search with n-gram indexes."""

    @pytest.fixture
    def backend_with_ngrams(self):
        """Backend with n-gram indexes enabled."""
        messages = [
            {"id": 1, "text": "Thank you for your help"},
            {"id": 2, "text": "Thank you very much"},
            {"id": 3, "text": "Out of memory error occurred"},
            {"id": 4, "text": "Out of memory again"},
            {"id": 5, "text": "I can't reproduce the bug"},
            {"id": 6, "text": "Don't forget to test"},
        ]

        config = BackendConfig(
            enable_ngrams=True, ngram_sizes=[2, 3], ngram_min_frequency=1
        )
        return MemoryBackend(messages, config=config)

    @pytest.fixture
    def backend_without_ngrams(self):
        """Backend without n-gram indexes (fallback mode)."""
        messages = [
            {"id": 1, "text": "Thank you for your help"},
            {"id": 2, "text": "Thank you very much"},
            {"id": 3, "text": "Out of memory error occurred"},
        ]

        config = BackendConfig(enable_ngrams=False)
        return MemoryBackend(messages, config=config)

    def test_search_phrase_bigram(self, backend_with_ngrams):
        """Test searching for a 2-word phrase."""
        results = backend_with_ngrams.search_phrase("thank you")
        assert results == {1, 2}

    def test_search_phrase_trigram(self, backend_with_ngrams):
        """Test searching for a 3-word phrase."""
        results = backend_with_ngrams.search_phrase("out of memory")
        assert results == {3, 4}

    def test_search_phrase_case_insensitive(self, backend_with_ngrams):
        """Test that phrase search is case-insensitive."""
        results = backend_with_ngrams.search_phrase("THANK YOU")
        assert results == {1, 2}

        results = backend_with_ngrams.search_phrase("Thank You")
        assert results == {1, 2}

    def test_search_phrase_contractions(self, backend_with_ngrams):
        """Test phrase search with contractions."""
        results = backend_with_ngrams.search_phrase("can't reproduce")
        assert results == {5}

        results = backend_with_ngrams.search_phrase("don't forget")
        assert results == {6}

    def test_search_phrase_no_matches(self, backend_with_ngrams):
        """Test phrase that doesn't exist."""
        results = backend_with_ngrams.search_phrase("nonexistent phrase")
        assert results == set()

    def test_search_phrase_single_word(self, backend_with_ngrams):
        """Test single-word phrase (should use token index)."""
        results = backend_with_ngrams.search_phrase("help")
        assert results == {1}

    def test_search_phrase_fallback_substring(self, backend_without_ngrams):
        """Test fallback to substring matching when n-grams disabled."""
        # Should still work via substring matching
        results = backend_without_ngrams.search_phrase("thank you")
        assert results == {1, 2}

        results = backend_without_ngrams.search_phrase("out of memory")
        assert results == {3}

    def test_search_phrase_unsupported_size(self, backend_with_ngrams):
        """Test phrase size not in ngram_sizes (fallback to substring)."""
        # 4-gram not indexed, should fall back to substring
        results = backend_with_ngrams.search_phrase("thank you very much")
        assert results == {2}


class TestContainsPhraseQuery:
    """Test contains_phrase() query operator."""

    @pytest.fixture
    def engine_with_ngrams(self):
        """Engine with n-gram indexes."""
        messages = [
            {"id": 1, "user": "alice", "text": "Thank you for your help"},
            {"id": 2, "user": "bob", "text": "Thank you very much"},
            {"id": 3, "user": "alice", "text": "Out of memory error"},
            {"id": 4, "user": "charlie", "text": "Out of memory again"},
            {"id": 5, "user": "bob", "text": "Can't reproduce the bug"},
            {"id": 6, "user": "alice", "text": "I don't know"},
        ]

        # Use min_frequency=1 to index all phrases (even rare ones)
        config = BackendConfig(
            tokenizer="unicode",
            enable_ngrams=True,
            ngram_sizes=[2, 3],
            ngram_min_frequency=1,  # Index all n-grams
        )
        backend = MemoryBackend(messages, config=config)
        return PrismQLEngine(backend)

    def test_contains_phrase_basic(self, engine_with_ngrams):
        """Test basic phrase search."""
        result = engine_with_ngrams.execute('SELECT contains_phrase("thank you")')
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {1, 2}

    def test_contains_phrase_trigram(self, engine_with_ngrams):
        """Test 3-word phrase."""
        result = engine_with_ngrams.execute('SELECT contains_phrase("out of memory")')
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {3, 4}

    def test_contains_phrase_with_and(self, engine_with_ngrams):
        """Test phrase search combined with user filter."""
        result = engine_with_ngrams.execute(
            'SELECT contains_phrase("thank you") AND from(alice)'
        )
        assert result == [[1]]

    def test_contains_phrase_with_or(self, engine_with_ngrams):
        """Test phrase search with OR."""
        result = engine_with_ngrams.execute(
            'SELECT contains_phrase("thank you") OR contains_phrase("out of memory")'
        )
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {1, 2, 3, 4}

    def test_contains_phrase_in_window(self, engine_with_ngrams):
        """Test phrase search with window constraint."""
        result = engine_with_ngrams.execute(
            'SELECT contains_phrase("thank you"), from(bob) INWINDOW 10'
        )
        # Should find windows where both phrase and user match
        assert len(result) > 0

    def test_contains_phrase_single_quotes(self, engine_with_ngrams):
        """Test phrase with single quotes."""
        result = engine_with_ngrams.execute("SELECT contains_phrase('thank you')")
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {1, 2}

    def test_contains_phrase_contractions(self, engine_with_ngrams):
        """Test phrase with contractions."""
        result = engine_with_ngrams.execute('SELECT contains_phrase("don\'t know")')
        all_ids = {msg_id for group in result for msg_id in group}
        assert all_ids == {6}


class TestNgramMemoryUsage:
    """Test memory usage characteristics of n-grams."""

    def test_index_sizes(self):
        """Compare index sizes for different configurations."""
        messages = [
            {"id": i, "text": f"message {i} with some repeated words"}
            for i in range(100)
        ]

        # Word-only backend
        minimal_backend = MemoryBackend(messages, config=MINIMAL_CONFIG)
        word_index_size = len(minimal_backend._text_index)

        # Word + ngrams backend
        balanced_backend = MemoryBackend(messages, config=BALANCED_CONFIG)
        bigram_size = len(balanced_backend._ngram_indexes.get(2, {}))
        trigram_size = len(balanced_backend._ngram_indexes.get(3, {}))

        # Basic sanity checks
        assert word_index_size > 0
        assert bigram_size >= 0  # Could be 0 if all filtered out
        assert trigram_size >= 0

        # N-grams should be larger than word index (before filtering)
        # But with filtering, may be smaller
        print(f"Word index: {word_index_size}")
        print(f"Bigram index: {bigram_size}")
        print(f"Trigram index: {trigram_size}")


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_tokenizer(self):
        """Test error on invalid tokenizer."""
        config = BackendConfig(tokenizer="invalid")
        with pytest.raises(ValueError, match="Invalid tokenizer"):
            config.validate()

    def test_invalid_ngram_size(self):
        """Test error on invalid n-gram size."""
        config = BackendConfig(enable_ngrams=True, ngram_sizes=[1])  # Must be >= 2
        with pytest.raises(ValueError, match="N-gram size must be >= 2"):
            config.validate()

    def test_invalid_min_frequency(self):
        """Test error on invalid min frequency."""
        config = BackendConfig(enable_ngrams=True, ngram_min_frequency=0)
        with pytest.raises(ValueError, match="ngram_min_frequency must be >= 1"):
            config.validate()

    def test_invalid_max_count(self):
        """Test error on invalid max count."""
        config = BackendConfig(enable_ngrams=True, ngram_max_count=0)
        with pytest.raises(ValueError, match="ngram_max_count must be >= 1"):
            config.validate()

    def test_empty_ngram_sizes(self):
        """Test error when ngram_sizes is empty."""
        config = BackendConfig(enable_ngrams=True, ngram_sizes=[])
        with pytest.raises(ValueError, match="ngram_sizes cannot be empty"):
            config.validate()


class TestEdgeCases:
    """Test edge cases in phrase matching."""

    def test_empty_phrase(self):
        """Test empty phrase."""
        config = BackendConfig(enable_ngrams=True, ngram_sizes=[2, 3])
        backend = MemoryBackend([{"id": 1, "text": "hello world"}], config=config)

        results = backend.search_phrase("")
        assert results == set()

    def test_phrase_with_punctuation(self):
        """Test phrase containing punctuation."""
        messages = [
            {"id": 1, "text": "Email me at alice@company.com"},
            {"id": 2, "text": "Use support@service.io"},
        ]

        config = BackendConfig(
            enable_ngrams=True, ngram_sizes=[2, 3], ngram_min_frequency=1
        )
        backend = MemoryBackend(messages, config=config)

        # Phrase with email should work
        results = backend.search_phrase("me at")
        assert 1 in results

    def test_phrase_at_document_boundaries(self):
        """Test phrase at start and end of document."""
        messages = [
            {"id": 1, "text": "thank you for everything"},
            {"id": 2, "text": "everything ends with thank you"},
        ]

        config = BackendConfig(enable_ngrams=True, ngram_sizes=[2])
        backend = MemoryBackend(messages, config=config)

        results = backend.search_phrase("thank you")
        assert results == {1, 2}

    def test_repeated_phrase(self):
        """Test phrase appearing multiple times in same document."""
        messages = [{"id": 1, "text": "thank you thank you thank you"}]

        config = BackendConfig(
            enable_ngrams=True, ngram_sizes=[2], ngram_min_frequency=1
        )
        backend = MemoryBackend(messages, config=config)

        # Should return document once (not three times)
        results = backend.search_phrase("thank you")
        assert results == {1}
