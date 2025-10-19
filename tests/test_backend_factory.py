"""Tests for backend factory."""

from unittest.mock import MagicMock, patch

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
            "nlp_backend": {"type": "spacy", "model": "en_core_web_sm"},
            "user_dictionaries": {"test": ["word1", "word2"]},
        }

        result = BackendFactory.validate_config(config)
        assert result == config

    def test_validate_config_missing_search_backend(self):
        """Test validation fails without search backend."""
        config = {"nlp_backend": {"type": "spacy"}}

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

    def test_validate_config_invalid_nlp_backend(self):
        """Test validation fails with invalid NLP backend."""
        config = {"search_backend": {"type": "memory"}, "nlp_backend": "not_a_dict"}

        with pytest.raises(ValueError, match="nlp_backend must be a dictionary"):
            BackendFactory.validate_config(config)

    def test_validate_config_missing_nlp_type(self):
        """Test validation fails without NLP backend type."""
        config = {"search_backend": {"type": "memory"}, "nlp_backend": {}}

        with pytest.raises(ValueError, match="nlp_backend must specify 'type'"):
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
            nlp_backend,
            precomputed,
            user_dicts,
        ) = BackendFactory.create_backends(config)

        assert isinstance(search_backend, MemoryBackend)
        assert nlp_backend is None
        assert precomputed is None
        assert user_dicts is None

    def test_create_memory_backend_missing_documents(self):
        """Test memory backend creation fails without documents."""
        config = {"search_backend": {"type": "memory"}}

        with pytest.raises(ValueError, match="Memory backend requires 'documents'"):
            BackendFactory.create_backends(config)

    @patch("prismql.backends.opensearch.OpenSearchBackend")
    def test_create_opensearch_backend(self, mock_opensearch_class):
        """Test creating OpenSearch backend."""
        mock_client = MagicMock()
        mock_backend = MagicMock()
        mock_opensearch_class.return_value = mock_backend

        config = {
            "search_backend": {
                "type": "opensearch",
                "client": mock_client,
                "index_name": "test_index",
                "field_mappings": {"text": "content"},
                "search_settings": {"fuzziness": "AUTO"},
            }
        }

        search_backend, _, _, _ = BackendFactory.create_backends(config)

        # Verify OpenSearch backend was created with correct config
        mock_opensearch_class.assert_called_once()
        call_args = mock_opensearch_class.call_args

        assert call_args[0][0] == mock_client  # First arg is client
        backend_config = call_args[0][1]  # Second arg is config
        assert backend_config["index_name"] == "test_index"
        assert backend_config["field_mappings"] == {"text": "content"}
        assert backend_config["search_settings"] == {"fuzziness": "AUTO"}

        assert search_backend == mock_backend

    def test_create_opensearch_backend_missing_client(self):
        """Test OpenSearch backend creation fails without client."""
        config = {"search_backend": {"type": "opensearch", "index_name": "test"}}

        with pytest.raises(ValueError, match="OpenSearch backend requires 'client'"):
            BackendFactory.create_backends(config)

    def test_create_opensearch_backend_missing_index(self):
        """Test OpenSearch backend creation fails without index name."""
        config = {"search_backend": {"type": "opensearch", "client": MagicMock()}}

        with pytest.raises(
            ValueError, match="OpenSearch backend requires 'index_name'"
        ):
            BackendFactory.create_backends(config)

    def test_create_elasticsearch_backend(self):
        """Test creating Elasticsearch backend (alias for OpenSearch)."""
        with patch("prismql.backends.opensearch.OpenSearchBackend") as mock_class:
            mock_client = MagicMock()
            config = {
                "search_backend": {
                    "type": "elasticsearch",
                    "client": mock_client,
                    "index_name": "test",
                }
            }

            BackendFactory.create_backends(config)

            # Should create OpenSearch backend for elasticsearch type too
            mock_class.assert_called_once()

    def test_create_unknown_search_backend(self):
        """Test creating unknown search backend type."""
        config = {"search_backend": {"type": "unknown_type"}}

        with pytest.raises(
            ValueError, match="Unknown search backend type: unknown_type"
        ):
            BackendFactory.create_backends(config)

    @patch("prismql.backends.spacy.SpacyBackend")
    def test_create_spacy_backend_with_nlp_object(self, mock_spacy_class):
        """Test creating spaCy backend with nlp object."""
        mock_nlp = MagicMock()
        mock_backend = MagicMock()
        mock_spacy_class.return_value = mock_backend

        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "nlp_backend": {
                "type": "spacy",
                "nlp": mock_nlp,
                "entity_mappings": {"PERSON": "PERSON"},
                "batch_size": 50,
            },
        }

        _, nlp_backend, _, _ = BackendFactory.create_backends(config)

        # Verify spaCy backend was created
        mock_spacy_class.assert_called_once()
        call_args = mock_spacy_class.call_args

        assert call_args[0][0] == mock_nlp  # First arg is nlp object
        backend_config = call_args[0][1]  # Second arg is config
        assert backend_config["entity_mappings"] == {"PERSON": "PERSON"}
        assert backend_config["batch_size"] == 50

        assert nlp_backend == mock_backend

    @patch("prismql.backends.spacy.SpacyBackend")
    def test_create_spacy_backend_with_model_name(self, mock_spacy_class):
        """Test creating spaCy backend with model name."""
        mock_nlp = MagicMock()
        mock_backend = MagicMock()
        mock_spacy_class.return_value = mock_backend

        # Mock spacy module and load function
        mock_spacy = MagicMock()
        mock_spacy.load.return_value = mock_nlp

        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "nlp_backend": {"type": "spacy", "model": "en_core_web_sm"},
        }

        with patch.dict("sys.modules", {"spacy": mock_spacy}):
            _, nlp_backend, _, _ = BackendFactory.create_backends(config)

        # Verify spaCy model was loaded
        mock_spacy.load.assert_called_once_with("en_core_web_sm")

        # Verify backend was created with loaded model
        mock_spacy_class.assert_called_once()
        assert mock_spacy_class.call_args[0][0] == mock_nlp

    def test_create_spacy_backend_model_load_error(self):
        """Test spaCy backend creation with model load error."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "nlp_backend": {"type": "spacy", "model": "nonexistent_model"},
        }

        # Mock spacy module
        mock_spacy = MagicMock()
        mock_spacy.load.side_effect = Exception("Model not found")

        with patch.dict("sys.modules", {"spacy": mock_spacy}):
            with pytest.raises(ValueError, match="Failed to load spaCy model"):
                BackendFactory.create_backends(config)

    def test_create_spacy_backend_missing_nlp_and_model(self):
        """Test spaCy backend creation without nlp object or model."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "nlp_backend": {"type": "spacy"},
        }

        with pytest.raises(
            ValueError, match="spaCy backend requires 'nlp' object or 'model' name"
        ):
            BackendFactory.create_backends(config)

    def test_create_unknown_nlp_backend(self):
        """Test creating unknown NLP backend type."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "test"}],
            },
            "nlp_backend": {"type": "unknown_nlp"},
        }

        with pytest.raises(ValueError, match="Unknown NLP backend type: unknown_nlp"):
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

        _, _, precomputed, _ = BackendFactory.create_backends(config)

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

        _, _, precomputed, _ = BackendFactory.create_backends(config)

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

        _, _, _, user_dicts = BackendFactory.create_backends(config)

        expected = {"sentiment": ["happy", "sad"], "colors": ["red", "blue", "green"]}
        assert user_dicts == expected

    def test_get_example_configs(self):
        """Test getting example configurations."""
        examples = BackendFactory.get_example_configs()

        assert isinstance(examples, dict)
        assert "memory_only" in examples
        assert "opensearch_spacy" in examples
        assert "elasticsearch_precomputed" in examples

        # Verify structure of memory example
        memory_config = examples["memory_only"]
        assert memory_config["search_backend"]["type"] == "memory"
        assert "documents" in memory_config["search_backend"]

        # Verify structure of opensearch example
        opensearch_config = examples["opensearch_spacy"]
        assert opensearch_config["search_backend"]["type"] == "opensearch"
        assert opensearch_config["nlp_backend"]["type"] == "spacy"
        assert "user_dictionaries" in opensearch_config

    def test_import_error_handling(self):
        """Test handling of missing dependencies."""
        # Test with missing OpenSearch backend
        with patch.object(
            BackendFactory,
            "_create_opensearch_backend",
            side_effect=ImportError("OpenSearch backend is not available"),
        ):
            config = {
                "search_backend": {
                    "type": "opensearch",
                    "client": MagicMock(),
                    "index_name": "test",
                }
            }

            with pytest.raises(
                ImportError, match="OpenSearch backend is not available"
            ):
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
            nlp_backend,
            precomputed,
            user_dicts,
        ) = BackendFactory.create_backends(config)

        assert isinstance(search_backend, MemoryBackend)
        assert nlp_backend is None
        assert precomputed is None
        assert user_dicts is None

    def test_not_dict_config(self):
        """Test validation with non-dict config."""
        with pytest.raises(ValueError, match="Configuration must be a dictionary"):
            BackendFactory.validate_config("not_a_dict")
