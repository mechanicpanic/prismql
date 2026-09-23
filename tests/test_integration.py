"""Integration tests for PrismQL with new backends."""

from unittest.mock import patch

import pytest

from prismql import PrismQLEngine
from prismql.backends.factory import BackendFactory


class TestPrismQLEngineIntegration:
    """Integration tests for PrismQL engine with various backend combinations."""

    def test_from_config_memory_only(self):
        """Test engine creation with memory backend only."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [
                    {"id": 1, "text": "Hello world", "user": "alice"},
                    {"id": 2, "text": "How are you?", "user": "bob"},
                    {"id": 3, "text": "I'm fine", "user": "alice"},
                ],
            }
        }

        engine = PrismQLEngine.from_config(config)

        # Test basic query
        results = engine.execute("SELECT from(alice)")
        assert len(results) == 2
        assert [1] in results
        assert [3] in results

    def test_from_config_with_user_dictionaries(self):
        """Test engine creation with user dictionaries."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [
                    {"id": 1, "text": "I love Python programming", "user": "dev"},
                    {"id": 2, "text": "JavaScript is great too", "user": "dev"},
                    {"id": 3, "text": "What about Java?", "user": "student"},
                ],
            },
            "user_dictionaries": {"languages": ["python", "javascript", "java"]},
        }

        engine = PrismQLEngine.from_config(config)

        # Test dictionary query
        results = engine.execute("SELECT contains(languages)")
        assert len(results) == 3
        assert [1] in results  # Python
        assert [2] in results  # JavaScript
        assert [3] in results  # Java

    def test_from_config_with_precomputed_indexes(self):
        """Test engine creation with precomputed indexes."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [
                    {"id": 1, "text": "Hello", "user": "alice"},
                    {"id": 2, "text": "How are you?", "user": "bob"},
                    {"id": 3, "text": "Fine thanks", "user": "alice"},
                ],
            },
            "precomputed_indexes": {
                "questions": [2],  # Pre-identified question
                "user_mentions": {"alice": [1, 3], "bob": [2]},
                "entities": {
                    "PERSON": [1, 3]  # Pre-identified person mentions
                },
            },
        }

        engine = PrismQLEngine.from_config(config)

        # Test precomputed question detection
        results = engine.execute("SELECT is_question()")
        assert len(results) == 1
        assert [2] in results

    def test_from_config_with_an_nlp_backend_section_is_refused(self):
        """nlp_backend was removed (graph @aleph/prismql #106): annotate at
        ingest time or pass precomputed_indexes."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [
                    {"id": 1, "text": "John Doe is here", "user": "alice"},
                    {"id": 2, "text": "Where is Mary?", "user": "bob"},
                ],
            },
            "nlp_backend": {
                "type": "spacy",
                "entity_mappings": {"PERSON": "PERSON"},
            },
        }

        with pytest.raises(ValueError, match="'nlp_backend' was removed"):
            PrismQLEngine.from_config(config)

    def test_get_example_configs(self):
        """Test getting example configurations."""
        examples = PrismQLEngine.get_example_configs()

        assert isinstance(examples, dict)
        assert "memory_only" in examples
        assert "tantivy_precomputed" in examples

        # Verify examples are valid
        for _name, config in examples.items():
            # Should not raise an exception
            validated = BackendFactory.validate_config(config)
            assert validated is not None

    def test_config_validation_error(self):
        """Test error handling for invalid configuration."""
        config = {
            "search_backend": {
                # Missing type
                "documents": []
            }
        }

        with pytest.raises(ValueError, match="search_backend must specify 'type'"):
            PrismQLEngine.from_config(config)

    def test_missing_dependency_error(self):
        """Test error handling for missing dependencies."""
        config = {"search_backend": {"type": "tantivy", "documents": [{"id": 1}]}}

        # Mock ImportError for the tantivy backend
        with (
            patch.object(
                BackendFactory,
                "_create_tantivy_backend",
                side_effect=ImportError(
                    "Tantivy backend requires the 'tantivy' package"
                ),
            ),
            pytest.raises(ImportError, match="requires the 'tantivy' package"),
        ):
            PrismQLEngine.from_config(config)

    def test_engine_methods_with_factory_creation(self):
        """Test engine methods work correctly with factory-created engine."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [
                    {"id": 1, "text": "Hello", "user": "alice"},
                    {"id": 2, "text": "World", "user": "bob"},
                ],
            },
            "user_dictionaries": {"greetings": ["hello", "hi"]},
        }

        engine = PrismQLEngine.from_config(config)

        # Test validation
        assert engine.validate("SELECT from(alice)") is True

        # Test adding dictionaries
        engine.add_dictionary("farewells", ["bye", "goodbye"])
        results = engine.execute("SELECT contains(farewells)")
        assert len(results) == 0  # No farewell words in test data

        # Test removing dictionaries
        engine.remove_dictionary("greetings")

        # Original greeting query should now fail
        with pytest.raises(Exception):  # Would be PrismQLRuntimeError
            engine.execute("SELECT contains(greetings)")

    def test_config_modification_after_creation(self):
        """Test modifying configuration after engine creation."""
        config = {
            "search_backend": {
                "type": "memory",
                "documents": [{"id": 1, "text": "original", "user": "alice"}],
            }
        }

        engine = PrismQLEngine.from_config(config)

        # Modify original config
        config["user_dictionaries"] = {"new_dict": ["word"]}

        # Engine should not be affected by config modification
        results = engine.execute("SELECT from(alice)")
        assert len(results) == 1

        # New dictionary should not exist in engine
        with pytest.raises(Exception):
            engine.execute("SELECT contains(new_dict)")
