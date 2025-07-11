"""In-memory backend implementation for PrismQL."""

import re
from typing import Any, Optional
from collections.abc import Set, Sequence

from .base import SearchBackend
from ..types import MessageId, Document


class MemoryBackend(SearchBackend):
    """
    In-memory search backend for testing and small datasets.

    This backend stores all documents in memory and performs
    searches using Python's built-in data structures.
    """

    def __init__(self, documents: Sequence[Document], id_field: str = "id"):
        """
        Initialize the memory backend with documents.

        Args:
            documents: List of documents to index
            id_field: Field name containing the document ID
        """
        self.documents = list(documents)
        self.id_field = id_field

        # Build indexes
        self._id_to_doc = {}
        self._field_indexes = {}
        self._text_index = {}
        self._question_ids = set()

        for doc in self.documents:
            doc_id = doc.get(id_field)
            if doc_id is None:
                raise ValueError(f"Document missing required '{id_field}' field")

            self._id_to_doc[doc_id] = doc

            # Index all fields
            for field, value in doc.items():
                if field not in self._field_indexes:
                    self._field_indexes[field] = {}

                # Convert value to string for indexing
                str_value = str(value).lower()

                if str_value not in self._field_indexes[field]:
                    self._field_indexes[field][str_value] = set()

                self._field_indexes[field][str_value].add(doc_id)

                # Also index individual words for text fields
                if field in ["text", "content", "message"]:
                    words = re.findall(r"\w+", str_value)
                    for word in words:
                        if word not in self._text_index:
                            self._text_index[word] = set()
                        self._text_index[word].add(doc_id)

                    # Check for questions
                    if self._is_question(str_value):
                        self._question_ids.add(doc_id)

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> Set[MessageId]:
        """Search for documents containing the specified terms."""
        if not terms:
            return set()

        # Search in the text index
        result_sets = []

        for term in terms:
            term_lower = term.lower()
            matching_ids = set()

            # Check exact word matches
            if term_lower in self._text_index:
                matching_ids.update(self._text_index[term_lower])

            # Also check if term appears as substring in field values
            if field in self._field_indexes:
                for value, doc_ids in self._field_indexes[field].items():
                    if term_lower in value:
                        matching_ids.update(doc_ids)

            result_sets.append(matching_ids)

        # Combine results based on operator
        if operator == "AND":
            # Intersection - all terms must match
            result = result_sets[0] if result_sets else set()
            for s in result_sets[1:]:
                result = result & s
        else:  # OR
            # Union - any term matches
            result = set()
            for s in result_sets:
                result = result | s

        return result

    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> Set[MessageId]:
        """Search for documents with specific field value."""
        if field not in self._field_indexes:
            return set()

        value_lower = value.lower()

        if exact:
            # Exact match
            return self._field_indexes[field].get(value_lower, set()).copy()
        else:
            # Partial match
            matching_ids = set()
            for indexed_value, doc_ids in self._field_indexes[field].items():
                if value_lower in indexed_value:
                    matching_ids.update(doc_ids)
            return matching_ids

    def get_total_documents(self) -> int:
        """Get total number of documents."""
        return len(self.documents)

    def get_all_document_ids(self, limit: Optional[int] = None) -> Set[MessageId]:
        """Get all document IDs."""
        all_ids = set(self._id_to_doc.keys())

        if limit is not None:
            # Convert to list, slice, then back to set
            return set(list(all_ids)[:limit])

        return all_ids

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        """Retrieve documents by IDs."""
        docs = []
        for doc_id in ids:
            if doc_id in self._id_to_doc:
                docs.append(self._id_to_doc[doc_id].copy())
        return docs

    def get_questions(self) -> Set[MessageId]:
        """Get IDs of messages that contain questions."""
        return self._question_ids.copy()

    def _is_question(self, text: str) -> bool:
        """Check if text contains a question."""
        # Check for question mark
        if "?" in text:
            return True

        # Check for question words at the beginning
        text_lower = text.lower().strip()
        question_words = [
            "what",
            "who",
            "when",
            "where",
            "why",
            "how",
            "which",
            "can",
            "could",
            "would",
            "should",
            "do",
            "does",
            "did",
            "is",
            "are",
            "was",
            "were",
            "will",
        ]

        for word in question_words:
            if text_lower.startswith(word + " "):
                return True

        return False
