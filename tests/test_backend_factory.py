"""Tests for backend factory."""

from unittest.mock import patch

import pytest

from prismql.backends.base import PrecomputedIndexes
from prismql.backends.factory import BackendFactory
from prismql.backends.memory import MemoryBackend


class TestBackendFactory:
    """Test suite for backend factory."""

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = {
            "search_backend": {"type": "memory", "documents": []},
            "user_dictionaries": {"test": ["word1", "word2"]},
        }

        result = BackendFactory.validate_config(config)
        assert result == config

    def test_validate_config_missing_search_backend(self):
        """Test validation fails without search backend."""
        config = {}

        with pytest.raises(ValueError, match="must include 'search_backend'"):
            BackendFactory.validate_config(config)

    def test_validate_config_invalid_search_backend(self):
        """Test validation fails with invalid search backend."""
        config = {"search_backend": "not_a_dict"}

        with pytest.raises(ValueError, match="search_backend must be a dictionary"):
            BackendFactory.validate_config(config)

    def test_validate_config_missing_search_type(self):
        """Test validation fails without search backend type."""
        config = {"search_backend": {}}

        with pytest.raises(ValueError, match="search_backend must specify 'type'"):
            BackendFactory.validate_config(config)

    def test_validate_config_nlp_backend_removed(self):
        """nlp_backend was removed (graph @aleph/prismql #106): annotate at
        ingest time or pass precomputed_indexes."""
        config = {
            "search_backend": {"type": "memory"},
            "nlp_backend": {"type": "spacy"},
        }

        with pytest.raises(ValueError, match="'nlp_backend' was removed"):
            BackendFactory.validate_config(config)

    def test_create_memory_backend(self):
        """Test creating memory backend."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [
                    {"id": 1, "text": "hello", "user": "alice"},
                    {"id": 2, "text": "world", "user": "bob"},
                ],
                "id_field": "id",
            }
        }

        (
            search_backend,
            precomputed,
            user_dicts,
        ) = BackendFactory.create_backends(config)

        assert isinstance(search_backend, MemoryBackend)
        assert precomputed is None
        assert user_dicts is None

    def test_create_memory_backend_missing_documents(self):
        """Test memory backend creation fails without documents."""
        config = {"search_backend": {"type": "memory"}}

        with pytest.raises(ValueError, match="Memory backend requires 'documents'"):
            BackendFactory.create_backends(config)

    def test_create_unknown_search_backend(self):
        """Test creating unknown search backend type."""
        config = {"search_backend": {"type": "unknown_type"}}

        with pytest.raises(
            ValueError, match="Unknown search backend type: unknown_type"
        ):
            BackendFactory.create_backends(config)

    def test_create_precomputed_indexes(self):
        """Test creating precomputed indexes."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "precomputed_indexes": {
                "entities": {"PERSON": ["msg1", "msg2"], "LOCATION": ["msg3"]},
                "questions": ["msg4", "msg5"],
                "user_mentions": {"alice": ["msg1", "msg3"], "bob": ["msg2"]},
            },
        }

        _, precomputed, _ = BackendFactory.create_backends(config)

        assert isinstance(precomputed, PrecomputedIndexes)
        assert precomputed.entities["PERSON"] == {"msg1", "msg2"}
        assert precomputed.entities["LOCATION"] == {"msg3"}
        assert precomputed.questions == {"msg4", "msg5"}
        assert precomputed.user_mentions["alice"] == {"msg1", "msg3"}

    def test_create_precomputed_indexes_with_sets(self):
        """Test creating precomputed indexes when data is already sets."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "precomputed_indexes": {
                "entities": {
                    "PERSON": {"msg1", "msg2"}  # Already a set
                },
                "questions": {"msg3", "msg4"},  # Already a set
            },
        }

        _, precomputed, _ = BackendFactory.create_backends(config)

        # Should handle sets correctly
        assert precomputed.entities["PERSON"] == {"msg1", "msg2"}
        assert precomputed.questions == {"msg3", "msg4"}

    def test_create_user_dictionaries(self):
        """Test extracting user dictionaries."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "user_dictionaries": {
                "sentiment": ["happy", "sad"],
                "colors": ["red", "blue", "green"],
            },
        }

        _, _, user_dicts = BackendFactory.create_backends(config)

        expected = {"sentiment": ["happy", "sad"], "colors": ["red", "blue", "green"]}
        assert user_dicts == expected

    def test_get_example_configs(self):
        """Test getting example configurations."""
        examples = BackendFactory.get_example_configs()

        assert isinstance(examples, dict)
        assert "memory_only" in examples
        assert "tantivy_precomputed" in examples
        assert "memory_precomputed" in examples

        # Verify structure of memory example
        memory_config = examples["memory_only"]
        assert memory_config["search_backend"]["type"] == "memory"
        assert "documents" in memory_config["search_backend"]

        # Verify structure of the tantivy example
        tantivy_config = examples["tantivy_precomputed"]
        assert tantivy_config["search_backend"]["type"] == "tantivy"
        assert "precomputed_indexes" in tantivy_config
        assert "user_dictionaries" in tantivy_config

    def test_import_error_handling(self):
        """Test handling of missing dependencies."""
        with patch.object(
            BackendFactory,
            "_create_tantivy_backend",
            side_effect=ImportError("Tantivy backend requires the 'tantivy' package"),
        ):
            config = {"search_backend": {"type": "tantivy", "documents": [{"id": 1}]}}
            with pytest.raises(ImportError, match="requires the 'tantivy' package"):
                BackendFactory.create_backends(config)

    def test_minimal_config(self):
        """Test creating backends with minimal configuration."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            }
        }

        (
            search_backend,
            precomputed,
            user_dicts,
        ) = BackendFactory.create_backends(config)

        assert isinstance(search_backend, MemoryBackend)
        assert precomputed is None
        assert user_dicts is None

    def test_not_dict_config(self):
        """Test validation with non-dict config."""
        with pytest.raises(ValueError, match="Configuration must be a dictionary"):
            BackendFactory.validate_config("not_a_dict")


def test_create_rust_memory_backend():
    pytest.importorskip("prismql_rust")
    from prismql.backends.rust_memory import RustMemoryBackend

    config = {
        "search_backend": {
            "type": "rust_memory",
            "documents": [
                {"id": 0, "user": "a", "text": "hi", "timestamp": 1000},
                {"id": 1, "user": "b", "text": "yo", "timestamp": 1005},
            ],
            "timestamp_fields": ["timestamp"],
        }
    }
    backend, _, _ = BackendFactory.create_backends(config)
    assert isinstance(backend, RustMemoryBackend)
    assert backend.has_timestamp_field("timestamp")
