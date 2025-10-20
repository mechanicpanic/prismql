"""Abstract base classes for PrismQL backends."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Optional

from ..types import Document, MessageId, NERLabel


class SearchBackend(ABC):
    """
    Abstract base class for search engine backends.

    This interface allows PrismQL to work with any search engine
    by implementing these core methods.
    """

    @abstractmethod
    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
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
    ) -> set[MessageId]:
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
    def get_all_document_ids(self, limit: Optional[int] = None) -> set[MessageId]:
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
    Container for precomputed feature indexes.

    When processing large corpora, it's more efficient to precompute
    features once and store them as boolean indexes, rather than computing
    on-the-fly during queries.

    This design is backend-agnostic: features can come from any source:
    - LLM-generated annotations
    - Human annotations from annotation platforms
    - NLP libraries (spaCy, CoreNLP, transformers)
    - Custom rule-based extractors
    - Hybrid approaches

    The query language doesn't care HOW features were computed, only WHICH
    messages have which features.

    Example:
        >>> # From LLM annotations
        >>> indexes = PrecomputedIndexes(
        ...     entities={'ORG': {1, 5}, 'PERSON': {2, 8}},
        ...     questions={1, 3, 7},
        ...     custom_features={
        ...         'action_items': {2, 9},
        ...         'decisions': {4, 6},
        ...         'sentiment_positive': {1, 5, 8}
        ...     }
        ... )
        >>>
        >>> # Use in queries
        >>> engine = PrismQLEngine(
        ...     search_backend=backend,
        ...     precomputed_indexes=indexes
        ... )
    """

    def __init__(
        self,
        entities: Optional[Mapping[NERLabel, set[MessageId]]] = None,
        questions: Optional[set[MessageId]] = None,
        user_mentions: Optional[Mapping[str, set[MessageId]]] = None,
        custom_features: Optional[Mapping[str, set[MessageId]]] = None,
    ) -> None:
        """
        Initialize precomputed indexes.

        Args:
            entities: Named entity indexes (e.g., {'ORG': {1, 5}, 'PERSON': {2}})
            questions: Set of message IDs containing questions
            user_mentions: User mention indexes (e.g., {'alice': {3, 7}})
            custom_features: Arbitrary custom feature indexes
                           (e.g., {'action_items': {2}, 'sentiment_positive': {1, 5}})
        """
        self.entities = entities or {}
        self.questions = questions or set()
        self.user_mentions = user_mentions or {}
        self.custom_features = custom_features or {}

    def get_feature(self, feature_name: str) -> set[MessageId]:
        """
        Get message IDs for a custom feature.

        This allows querying arbitrary features that don't fit into
        standard categories (entities, questions, etc.).

        Args:
            feature_name: Name of the custom feature

        Returns:
            Set of message IDs with this feature, empty set if not found
        """
        return self.custom_features.get(feature_name, set())
