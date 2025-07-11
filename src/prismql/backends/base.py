"""Abstract base classes for PrismQL backends."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from collections.abc import Set, Mapping, Sequence

from ..types import MessageId, Document, NERLabel


class SearchBackend(ABC):
    """
    Abstract base class for search engine backends.

    This interface allows PrismQL to work with any search engine
    by implementing these core methods.
    """

    @abstractmethod
    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> Set[MessageId]:
        """
        Search for messages containing any (OR) or all (AND) of the terms.

        Args:
            terms: List of terms to search for
            field: Field to search in (default: "text")
            operator: Boolean operator - "OR" or "AND"

        Returns:
            Set of message IDs matching the search
        """
        pass

    @abstractmethod
    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> Set[MessageId]:
        """
        Search for messages with specific field value.

        Args:
            field: Field name to search in
            value: Value to search for
            exact: Whether to do exact match or partial match

        Returns:
            Set of message IDs matching the search
        """
        pass

    @abstractmethod
    def get_total_documents(self) -> int:
        """Get total number of documents in the index."""
        pass

    @abstractmethod
    def get_all_document_ids(self, limit: Optional[int] = None) -> Set[MessageId]:
        """
        Get all document IDs (up to limit).

        Args:
            limit: Maximum number of IDs to return

        Returns:
            Set of all document IDs
        """
        pass

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        """
        Retrieve full documents by IDs.

        This is optional - backends can implement if they support
        document retrieval.

        Args:
            ids: List of document IDs to retrieve

        Returns:
            List of documents
        """
        raise NotImplementedError("This backend does not support document retrieval")


class NLPBackend(ABC):
    """
    Abstract base class for NLP processing backends.

    This interface allows PrismQL to work with different NLP libraries
    (spaCy, CoreNLP, transformers, etc.) for advanced text analysis.
    """

    @abstractmethod
    def extract_entities(self, text: str) -> Mapping[NERLabel, list[str]]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping entity types to lists of entity texts
            Expected keys: DATE, TIME, GPE/LOC, ORG, URL, PERSON
        """
        pass

    @abstractmethod
    def has_question(self, text: str) -> bool:
        """
        Check if text contains a question.

        Args:
            text: Text to analyze

        Returns:
            True if text contains a question
        """
        pass

    def extract_noun_phrases(self, text: str) -> list[str]:
        """
        Extract noun phrases from text.

        This is optional - backends can implement if they support
        syntactic parsing.

        Args:
            text: Text to analyze

        Returns:
            List of noun phrases
        """
        raise NotImplementedError(
            "This backend does not support noun phrase extraction"
        )


class PrecomputedIndexes:
    """
    Container for precomputed NLP indexes.

    When processing large corpora, it's more efficient to precompute
    NLP features once and store them, rather than computing on-the-fly.
    """

    def __init__(
        self,
        entities: Optional[Mapping[NERLabel, Set[MessageId]]] = None,
        questions: Optional[Set[MessageId]] = None,
        user_mentions: Optional[Mapping[str, Set[MessageId]]] = None,
    ):
        self.entities = entities or {}
        self.questions = questions or set()
        self.user_mentions = user_mentions or {}
