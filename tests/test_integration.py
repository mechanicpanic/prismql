"""Integration tests for PrismQL with new backends."""

from unittest.mock import MagicMock, patch

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

    def test_from_config_opensearch_backend(self):
        """Test engine creation with OpenSearch backend."""
        mock_client = MagicMock()

        # Mock search responses
        mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"msg_id": "msg1"}},
                    {"_source": {"msg_id": "msg3"}},
                ]
            }
        }

        config = {
            "search_backend": {
                "type": "opensearch",
                "client": mock_client,
                "index_name": "chat_messages",
                "field_mappings": {"text": "content", "user": "author", "id": "msg_id"},
            }
        }

        engine = PrismQLEngine.from_config(config)

        # Test query execution
        results = engine.execute("SELECT from(alice)")

        # Verify OpenSearch was called
        mock_client.search.assert_called()
        call_args = mock_client.search.call_args[1]
        assert call_args["index"] == "chat_messages"

        # Verify results
        assert len(results) == 2
        assert ["msg1"] in results
        assert ["msg3"] in results

    def test_from_config_spacy_backend(self):
        """Test engine creation with spaCy NLP backend."""
        # Mock spaCy model
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_nlp.return_value = mock_doc

        # Mock entity extraction
        mock_ent = MagicMock()
        mock_ent.text = "John Doe"
        mock_ent.label_ = "PERSON"
        mock_doc.ents = [mock_ent]

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
                "nlp": mock_nlp,
                "entity_mappings": {"PERSON": "PERSON"},
            },
        }

        engine = PrismQLEngine.from_config(config)

        # Test NLP-based query (this would normally require NLP processing)
        # For now, just verify the engine was created successfully
        assert engine.nlp_backend is not None
        assert hasattr(engine.nlp_backend, "extract_entities")

    def test_from_config_full_stack(self):
        """Test engine creation with all components."""
        mock_client = MagicMock()
        mock_nlp = MagicMock()

        # Mock OpenSearch responses
        mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"id": 1}}, {"_source": {"id": 2}}]}
        }

        config = {
            "search_backend": {
                "type": "opensearch",
                "client": mock_client,
                "index_name": "messages",
                "field_mappings": {"text": "content", "user": "author"},
                "search_settings": {"fuzziness": "AUTO"},
            },
            "nlp_backend": {
                "type": "spacy",
                "nlp": mock_nlp,
                "entity_mappings": {"PERSON": "PERSON", "GPE": "LOCATION"},
            },
            "precomputed_indexes": {
                "questions": [2, 4],
                "entities": {"PERSON": [1, 3], "LOCATION": [2, 5]},
            },
            "user_dictionaries": {
                "sentiment": ["happy", "sad", "angry"],
                "tech": ["python", "javascript"],
            },
        }

        engine = PrismQLEngine.from_config(config)

        # Verify all components are configured
        assert engine.search_backend is not None
        assert engine.nlp_backend is not None
        assert engine.precomputed_indexes is not None
        assert engine.user_dictionaries is not None

        # Test query execution
        results = engine.execute("SELECT from(alice)")
        assert len(results) == 2

    def test_get_example_configs(self):
        """Test getting example configurations."""
        examples = PrismQLEngine.get_example_configs()

        assert isinstance(examples, dict)
        assert "memory_only" in examples
        assert "opensearch_spacy" in examples

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
        config = {
            "search_backend": {
                "type": "opensearch",
                "client": MagicMock(),
                "index_name": "test",
            }
        }

        # Mock ImportError for OpenSearch backend
        with patch.object(
            BackendFactory,
            "_create_opensearch_backend",
            side_effect=ImportError("OpenSearch backend is not available"),
        ), pytest.raises(ImportError, match="OpenSearch backend is not available"):
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

    def test_complex_query_with_multiple_backends(self):
        """Test complex query using multiple backend features."""
        mock_client = MagicMock()

        # Mock different search responses for different queries
        def mock_search(**kwargs: dict) -> dict:
            query = kwargs.get("body", {}).get("query", {})

            # Mock user search
            if "term" in query and "author" in str(query):
                return {
                    "hits": {"hits": [{"_source": {"id": 1}}, {"_source": {"id": 3}}]}
                }

            # Mock text search
            if "match" in query:
                return {"hits": {"hits": [{"_source": {"id": 2}}]}}

            return {"hits": {"hits": []}}

        mock_client.search.side_effect = mock_search

        config = {
            "search_backend": {
                "type": "opensearch",
                "client": mock_client,
                "index_name": "messages",
                "field_mappings": {"user": "author"},
            },
            "precomputed_indexes": {
                "questions": [2]  # Message 2 is a question
            },
        }

        engine = PrismQLEngine.from_config(config)

        # Test complex boolean query
        results = engine.execute("SELECT from(alice) AND is_question()")

        # Should find intersection of alice's messages and questions
        # Based on our mocks: alice has [1, 3], questions are [2]
        # Intersection should be empty
        assert len(results) == 0

    def test_error_propagation_from_backends(self):
        """Test that backend errors are properly propagated."""
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Connection timeout")

        config = {
            "search_backend": {
                "type": "opensearch",
                "client": mock_client,
                "index_name": "test",
            }
        }

        engine = PrismQLEngine.from_config(config)

        # Should propagate the connection error
        with pytest.raises(
            Exception
        ):  # Could be PrismQLRuntimeError wrapping the connection error
            engine.execute("SELECT from(alice)")

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
