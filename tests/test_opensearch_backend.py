"""Tests for OpenSearch backend."""

from unittest.mock import MagicMock

import pytest
from prismql.backends.opensearch import OpenSearchBackend


class TestOpenSearchBackend:
    """Test suite for OpenSearch backend."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock OpenSearch client
        self.mock_client = MagicMock()

        # Basic configuration
        self.config = {
            "index_name": "test_messages",
            "field_mappings": {
                "text": "message_content",
                "user": "author_name",
                "id": "message_id",
            },
            "search_settings": {"default_operator": "OR", "fuzziness": "AUTO"},
        }

        self.backend = OpenSearchBackend(self.mock_client, self.config)

    def test_init_with_basic_config(self):
        """Test backend initialization with basic configuration."""
        assert self.backend.index_name == "test_messages"
        assert self.backend.text_field == "message_content"
        assert self.backend.user_field == "author_name"
        assert self.backend.id_field == "message_id"
        assert self.backend.default_operator == "OR"
        assert self.backend.fuzziness == "AUTO"

    def test_init_with_minimal_config(self):
        """Test backend initialization with minimal configuration."""
        minimal_config = {"index_name": "test"}
        backend = OpenSearchBackend(self.mock_client, minimal_config)

        # Should use defaults
        assert backend.text_field == "text"
        assert backend.user_field == "user"
        assert backend.id_field == "id"
        assert backend.default_operator == "OR"
        assert backend.fuzziness is None

    def test_map_field(self):
        """Test field name mapping."""
        assert self.backend._map_field("text") == "message_content"
        assert self.backend._map_field("user") == "author_name"
        assert self.backend._map_field("id") == "message_id"
        assert self.backend._map_field("unknown") == "unknown"

    def test_search_text_single_term(self):
        """Test text search with single term."""
        # Mock response
        self.mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"message_id": "msg1"}},
                    {"_source": {"message_id": "msg2"}},
                ]
            }
        }

        result = self.backend.search_text(["hello"], field="text")

        # Verify the query
        call_args = self.mock_client.search.call_args
        assert call_args[1]["index"] == "test_messages"
        assert call_args[1]["size"] == 10000
        assert call_args[1]["_source"] == ["message_id"]

        query = call_args[1]["body"]["query"]
        assert "match" in query
        assert query["match"]["message_content"]["query"] == "hello"
        assert query["match"]["message_content"]["operator"] == "or"
        assert query["match"]["message_content"]["fuzziness"] == "AUTO"

        # Verify result
        assert result == {"msg1", "msg2"}

    def test_search_text_multiple_terms_or(self):
        """Test text search with multiple terms using OR operator."""
        self.mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"message_id": "msg1"}}]}
        }

        result = self.backend.search_text(["hello", "world"], operator="OR")

        query = self.mock_client.search.call_args[1]["body"]["query"]
        assert "bool" in query
        assert "should" in query["bool"]
        assert len(query["bool"]["should"]) == 2
        assert query["bool"]["minimum_should_match"] == 1

        assert result == {"msg1"}

    def test_search_text_multiple_terms_and(self):
        """Test text search with multiple terms using AND operator."""
        self.mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"message_id": "msg1"}}]}
        }

        result = self.backend.search_text(["hello", "world"], operator="AND")

        query = self.mock_client.search.call_args[1]["body"]["query"]
        assert "bool" in query
        assert "must" in query["bool"]
        assert len(query["bool"]["must"]) == 2

        assert result == {"msg1"}

    def test_search_text_empty_terms(self):
        """Test text search with empty terms list."""
        result = self.backend.search_text([])
        assert result == set()
        self.mock_client.search.assert_not_called()

    def test_search_by_field_exact(self):
        """Test exact field search."""
        self.mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"message_id": "msg1"}}]}
        }

        result = self.backend.search_by_field("user", "alice", exact=True)

        # Should try .keyword field first
        query = self.mock_client.search.call_args[1]["body"]["query"]
        assert "term" in query
        assert "author_name.keyword" in query["term"]
        assert query["term"]["author_name.keyword"] == "alice"

        assert result == {"msg1"}

    def test_search_by_field_exact_fallback(self):
        """Test exact field search with fallback when .keyword fails."""
        # First call fails, second succeeds
        self.mock_client.search.side_effect = [
            Exception("keyword field not found"),
            {"hits": {"hits": [{"_source": {"message_id": "msg1"}}]}},
        ]

        result = self.backend.search_by_field("user", "alice", exact=True)

        # Should have been called twice
        assert self.mock_client.search.call_count == 2

        # Second call should use regular field
        second_call = self.mock_client.search.call_args_list[1]
        query = second_call[1]["body"]["query"]
        assert "author_name" in query["term"]
        assert "author_name.keyword" not in query["term"]

        assert result == {"msg1"}

    def test_search_by_field_partial(self):
        """Test partial field search."""
        self.mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"message_id": "msg1"}}]}
        }

        result = self.backend.search_by_field("user", "ali", exact=False)

        query = self.mock_client.search.call_args[1]["body"]["query"]
        assert "match" in query
        assert query["match"]["author_name"]["query"] == "ali"
        assert query["match"]["author_name"]["operator"] == "and"

        assert result == {"msg1"}

    def test_get_total_documents(self):
        """Test getting total document count."""
        self.mock_client.count.return_value = {"count": 42}

        result = self.backend.get_total_documents()

        self.mock_client.count.assert_called_once_with(index="test_messages")
        assert result == 42

    def test_get_total_documents_error(self):
        """Test error handling in get_total_documents."""
        self.mock_client.count.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError, match="Failed to get document count"):
            self.backend.get_total_documents()

    def test_get_all_document_ids_small(self):
        """Test getting all document IDs for small dataset."""
        self.mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"message_id": "msg1"}},
                    {"_source": {"message_id": "msg2"}},
                ]
            }
        }

        result = self.backend.get_all_document_ids(limit=100)

        query = self.mock_client.search.call_args[1]["body"]["query"]
        assert query == {"match_all": {}}
        assert self.mock_client.search.call_args[1]["size"] == 100

        assert result == {"msg1", "msg2"}

    def test_get_all_document_ids_with_scroll(self):
        """Test getting all document IDs using scroll API."""
        # Mock scroll responses
        initial_response = {
            "_scroll_id": "scroll123",
            "hits": {
                "hits": [
                    {"_source": {"message_id": "msg1"}},
                    {"_source": {"message_id": "msg2"}},
                ]
            },
        }

        scroll_response = {
            "hits": {"hits": []}  # Empty response to end scroll
        }

        self.mock_client.search.return_value = initial_response
        self.mock_client.scroll.return_value = scroll_response

        result = self.backend.get_all_document_ids(limit=15000)  # Triggers scroll

        # Verify scroll setup
        search_call = self.mock_client.search.call_args[1]
        assert search_call["size"] == 1000
        assert search_call["scroll"] == "1m"

        # Verify scroll call
        self.mock_client.scroll.assert_called_once_with(
            scroll_id="scroll123", scroll="1m"
        )

        # Verify cleanup
        self.mock_client.clear_scroll.assert_called_once_with(scroll_id="scroll123")

        assert result == {"msg1", "msg2"}

    def test_get_documents(self):
        """Test retrieving documents by IDs."""
        self.mock_client.mget.return_value = {
            "docs": [
                {"found": True, "_source": {"message_id": "msg1", "content": "Hello"}},
                {"found": True, "_source": {"message_id": "msg2", "content": "World"}},
                {
                    "found": False  # Document not found
                },
            ]
        }

        result = self.backend.get_documents(["msg1", "msg2", "msg3"])

        # Verify mget call
        mget_call = self.mock_client.mget.call_args[1]["body"]
        expected_docs = [
            {"_index": "test_messages", "_id": "msg1"},
            {"_index": "test_messages", "_id": "msg2"},
            {"_index": "test_messages", "_id": "msg3"},
        ]
        assert mget_call["docs"] == expected_docs

        # Should only return found documents
        assert len(result) == 2
        assert result[0]["message_id"] == "msg1"
        assert result[1]["message_id"] == "msg2"

    def test_get_documents_empty(self):
        """Test retrieving documents with empty ID list."""
        result = self.backend.get_documents([])
        assert result == []
        self.mock_client.mget.assert_not_called()

    def test_search_error_handling(self):
        """Test error handling in search operations."""
        self.mock_client.search.side_effect = Exception("Search failed")

        with pytest.raises(RuntimeError, match="OpenSearch query failed"):
            self.backend.search_text(["hello"])

    def test_mget_error_handling(self):
        """Test error handling in document retrieval."""
        self.mock_client.mget.side_effect = Exception("Mget failed")

        with pytest.raises(RuntimeError, match="Failed to retrieve documents"):
            self.backend.get_documents(["msg1"])

    def test_field_mapping_precedence(self):
        """Test that field mappings override defaults."""
        config = {
            "index_name": "test",
            "field_mappings": {"text": "custom_text", "user": "custom_user"},
        }
        backend = OpenSearchBackend(self.mock_client, config)

        # Mapped fields
        assert backend._map_field("text") == "custom_text"
        assert backend._map_field("user") == "custom_user"

        # Unmapped field uses original name
        assert backend._map_field("id") == "id"  # No mapping, uses default

    def test_without_fuzziness(self):
        """Test search without fuzziness setting."""
        config = {
            "index_name": "test",
            "search_settings": {},  # No fuzziness
        }
        backend = OpenSearchBackend(self.mock_client, config)

        self.mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"id": "msg1"}}]}
        }

        backend.search_text(["hello"])

        query = self.mock_client.search.call_args[1]["body"]["query"]
        # Should not have fuzziness in the query
        match_query = query["match"]["text"]
        assert "fuzziness" not in match_query
