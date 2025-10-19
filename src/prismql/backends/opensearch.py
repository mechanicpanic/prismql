"""OpenSearch backend implementation for PrismQL."""

from collections.abc import Sequence
from typing import Any, Optional

from ..types import Document, MessageId
from .base import SearchBackend


class OpenSearchBackend(SearchBackend):
    """
    OpenSearch/Elasticsearch backend for PrismQL.

    This backend connects to an OpenSearch or Elasticsearch cluster
    and translates PrismQL queries to OpenSearch DSL queries.

    Example configuration:
        config = {
            "index_name": "chat_messages",
            "field_mappings": {
                "text": "message_content",
                "user": "author_name",
                "id": "message_id"
            },
            "search_settings": {
                "default_operator": "AND",
                "fuzziness": "AUTO"
            }
        }

        backend = OpenSearchBackend(opensearch_client, config)
    """

    def __init__(self, client: Any, config: dict[str, Any]) -> None:
        """
        Initialize OpenSearch backend.

        Args:
            client: OpenSearch or Elasticsearch client instance
            config: Configuration dictionary with index settings and field mappings
        """
        self.client = client
        self.config = config

        # Extract configuration
        self.index_name = config["index_name"]
        self.field_mappings = config.get("field_mappings", {})
        self.search_settings = config.get("search_settings", {})

        # Default field mappings
        self.text_field = self.field_mappings.get("text", "text")
        self.user_field = self.field_mappings.get("user", "user")
        self.id_field = self.field_mappings.get("id", "id")

        # Default search settings
        self.default_operator = self.search_settings.get("default_operator", "OR")
        self.fuzziness = self.search_settings.get("fuzziness", None)

    def _map_field(self, field: str) -> str:
        """Map PrismQL field name to actual index field name."""
        return str(self.field_mappings.get(field, field))

    def _execute_search(
        self, query: dict[str, Any], size: int = 10000
    ) -> set[MessageId]:
        """Execute search query and return message IDs."""
        try:
            response = self.client.search(
                index=self.index_name, body=query, size=size, _source=[self.id_field]
            )

            # Extract message IDs from response
            message_ids = set()
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                msg_id = source.get(self.id_field)
                if msg_id is not None:
                    message_ids.add(msg_id)

            return message_ids

        except Exception as e:
            # Re-raise with more context
            raise RuntimeError(f"OpenSearch query failed: {e}") from e

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """
        Search for documents containing the specified terms.

        Args:
            terms: List of terms to search for
            field: Field to search in (will be mapped via field_mappings)
            operator: Boolean operator - "OR" or "AND"

        Returns:
            Set of message IDs matching the search
        """
        if not terms:
            return set()

        # Map field name
        actual_field = self._map_field(field)

        # Build query based on operator
        query: dict[str, Any]
        if len(terms) == 1:
            # Single term - use match query
            query = {
                "query": {
                    "match": {
                        actual_field: {"query": terms[0], "operator": operator.lower()}
                    }
                }
            }
            if self.fuzziness:
                query["query"]["match"][actual_field]["fuzziness"] = self.fuzziness

        else:
            # Multiple terms - use bool query
            if operator == "OR":
                # Should match any term
                should_clauses = []
                for term in terms:
                    if self.fuzziness:
                        match_clause: dict[str, Any] = {
                            "match": {
                                actual_field: {
                                    "query": term,
                                    "fuzziness": self.fuzziness,
                                }
                            }
                        }
                    else:
                        match_clause = {"match": {actual_field: term}}
                    should_clauses.append(match_clause)

                query = {
                    "query": {
                        "bool": {"should": should_clauses, "minimum_should_match": 1}
                    }
                }
            else:  # AND
                # Must match all terms
                must_clauses = []
                for term in terms:
                    if self.fuzziness:
                        match_clause = {
                            "match": {
                                actual_field: {
                                    "query": term,
                                    "fuzziness": self.fuzziness,
                                }
                            }
                        }
                    else:
                        match_clause = {"match": {actual_field: term}}
                    must_clauses.append(match_clause)

                query = {"query": {"bool": {"must": must_clauses}}}

        return self._execute_search(query)

    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> set[MessageId]:
        """
        Search for documents with specific field value.

        Args:
            field: Field name to search in (will be mapped via field_mappings)
            value: Value to search for
            exact: Whether to do exact match or partial match

        Returns:
            Set of message IDs matching the search
        """
        # Map field name
        actual_field = self._map_field(field)

        if exact:
            # Exact match using term query
            query_dict: dict[str, Any] = {
                "query": {"term": {f"{actual_field}.keyword": value}}
            }

            # Fallback to regular field if keyword field doesn't exist
            try:
                return self._execute_search(query_dict)
            except Exception:
                # Try without .keyword suffix
                query_dict = {"query": {"term": {actual_field: value}}}
                return self._execute_search(query_dict)
        else:
            # Partial match using match query
            query_dict = {
                "query": {"match": {actual_field: {"query": value, "operator": "and"}}}
            }
            if self.fuzziness:
                query_dict["query"]["match"][actual_field]["fuzziness"] = self.fuzziness

            return self._execute_search(query_dict)

    def get_total_documents(self) -> int:
        """Get total number of documents in the index."""
        try:
            response = self.client.count(index=self.index_name)
            return int(response["count"])
        except Exception as e:
            raise RuntimeError(f"Failed to get document count: {e}") from e

    def get_all_document_ids(self, limit: Optional[int] = None) -> set[MessageId]:
        """
        Get all document IDs (up to limit).

        Args:
            limit: Maximum number of IDs to return

        Returns:
            Set of all document IDs
        """
        query: dict[str, Any] = {"query": {"match_all": {}}}

        size = limit if limit is not None else 10000

        # For large datasets, use scroll API
        if limit is None or limit > 10000:
            return self._get_all_ids_with_scroll(query, limit)
        return self._execute_search(query, size=size)

    def _get_all_ids_with_scroll(
        self, query: dict[str, Any], limit: Optional[int] = None
    ) -> set[MessageId]:
        """Get all document IDs using scroll API for large datasets."""
        message_ids = set()
        scroll_size = 1000

        try:
            # Initial search
            response = self.client.search(
                index=self.index_name,
                body=query,
                size=scroll_size,
                scroll="1m",
                _source=[self.id_field],
            )

            scroll_id = response["_scroll_id"]

            while True:
                # Process current batch
                for hit in response["hits"]["hits"]:
                    source = hit["_source"]
                    msg_id = source.get(self.id_field)
                    if msg_id is not None:
                        message_ids.add(msg_id)

                    # Check limit
                    if limit is not None and len(message_ids) >= limit:
                        break

                # Break if we've hit the limit or no more hits
                if (limit is not None and len(message_ids) >= limit) or len(
                    response["hits"]["hits"]
                ) == 0:
                    break

                # Get next batch
                response = self.client.scroll(scroll_id=scroll_id, scroll="1m")

            # Clean up scroll
            self.client.clear_scroll(scroll_id=scroll_id)

            # Apply limit if needed
            if limit is not None and len(message_ids) > limit:
                message_ids = set(list(message_ids)[:limit])

            return message_ids

        except Exception as e:
            raise RuntimeError(f"Failed to scroll through documents: {e}") from e

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        """
        Retrieve full documents by IDs.

        Args:
            ids: List of document IDs to retrieve

        Returns:
            List of documents
        """
        if not ids:
            return []

        # Build multi-get query
        docs_to_get = []
        for doc_id in ids:
            docs_to_get.append({"_index": self.index_name, "_id": doc_id})

        try:
            response = self.client.mget(body={"docs": docs_to_get})

            documents = []
            for doc in response["docs"]:
                if doc["found"]:
                    documents.append(doc["_source"])

            return documents

        except Exception as e:
            raise RuntimeError(f"Failed to retrieve documents: {e}") from e
