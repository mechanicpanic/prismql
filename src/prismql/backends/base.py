"""Abstract base classes for PrismQL backends."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence

from ..exceptions import PositionalUnsupportedError
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

    def search_tokens(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """
        Search for messages containing tokens (Unicode-aware).

        This is similar to search_text() but uses Unicode-aware tokenization
        that preserves punctuation in meaningful contexts:
        - Emails: user@example.com
        - URLs: http://example.com
        - Programming terms: C++, C#, F#
        - Contractions: don't, isn't

        Optional: a backend without a token index inherits this fallback to
        ``search_text``; ``supports_match("token")`` says whether the mode is
        honoured, and the engine refuses a mode a backend cannot honour.

        Args:
            terms: List of tokens to search for
            field: Field to search in (default: "text")
            operator: Boolean operator - "OR" or "AND"

        Returns:
            Set of message IDs matching the search
        """
        # Default fallback: use word-based search
        return self.search_text(terms, field, operator)

    def search_stems(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """Whole-word search on stemmed tokens (fail/failed/failing are one).

        Optional: a backend that cannot stem leaves this raising, and
        ``supports_match("stem")`` false, so the engine refuses instead of
        substituting another meaning (graph #59).
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not stem; set text_match to "
            "'token' or 'substring' for this backend"
        )

    def supports_match(self, mode: str) -> bool:
        """Which single-word match modes this backend can honour."""
        return mode in ("substring", "token")

    def search_phrase(self, phrase: str, field: str = "text") -> set[MessageId]:
        """
        Search for messages containing a specific phrase.

        A backend may use precomputed n-gram indexes for fast phrase lookup;
        what it does without them is backend-specific (adjacent tokens in
        memory and tantivy, substring in rust_memory).

        This is optional - backends can implement if they support n-gram
        indexing. By default, raises NotImplementedError.

        Args:
            phrase: Phrase to search for (e.g., "thank you", "out of memory")
            field: Field to search in (default: "text")

        Returns:
            Set of message IDs matching the search

        Raises:
            NotImplementedError: If backend doesn't support phrase search
        """
        raise NotImplementedError("Phrase search not supported by this backend")

    def search_semantic(self, text: str, *, threshold: float) -> set[MessageId]:
        """
        Search for messages semantically similar to the given text.

        Backends embed ``text``, score it against a per-message embedding
        index (cosine similarity), and return the set of messages whose
        score is >= ``threshold``. The score itself is discarded — the
        result is a plain set so it composes through the boolean and
        sequential algebra like any other predicate (threshold-to-set).

        This is optional - backends can implement if they carry a semantic
        index. By default, raises NotImplementedError.

        Args:
            text: Query text to embed and compare against messages
            threshold: Minimum similarity score in [0.0, 1.0]

        Returns:
            Set of message IDs at or above the threshold

        Raises:
            NotImplementedError: If backend doesn't support semantic search
        """
        raise NotImplementedError("Semantic search not supported by this backend")

    # ------------------------------------------------------------------
    # Order contract (spec 2026-09-18, layer 2b). Position = load order.
    # Backends without an axis MUST fail loudly here; order is never
    # reconstructed from id values.
    # ------------------------------------------------------------------
    @property
    def text_fields_present(self) -> frozenset[str] | None:
        """The text fields some event holds; None when the backend cannot
        say, and then no text predicate refuses (graph @aleph/prismql, #168)."""
        return None

    def text_fields_read(self, kind: str) -> tuple[str, ...]:  # noqa: ARG002
        """The fields a ``field="text"`` search of ``kind`` (words, phrase)
        reads."""
        return ("text",)

    def has_order_axis(self) -> bool:
        return False

    def _no_axis(self) -> PositionalUnsupportedError:
        return PositionalUnsupportedError(
            f"{type(self).__name__} has no stream-order axis: positional "
            "(INWINDOW, FOLLOWED_BY, ...) and temporal-sequence operators "
            "cannot run on it. Use a backend with an OrderIndex (memory, "
            "rust_memory) or load the corpus with a persisted position column."
        )

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        """Load-order position of each id, order-preserving; KeyError if unknown."""
        raise self._no_axis()

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        raise self._no_axis()

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        raise self._no_axis()

    def timestamps_at(
        self,
        positions: Iterable[int],
        field: str,
    ) -> list[int | None]:
        """UTC epoch microseconds (or None) per position for a timestamp field."""
        raise self._no_axis()

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
    def get_all_document_ids(self, limit: int | None = None) -> set[MessageId]:
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
        entities: Mapping[NERLabel, set[MessageId]] | None = None,
        questions: set[MessageId] | None = None,
        user_mentions: Mapping[str, set[MessageId]] | None = None,
        custom_features: Mapping[str, set[MessageId]] | None = None,
        links: set[MessageId] | None = None,
    ) -> None:
        """
        Initialize precomputed indexes.

        Args:
            entities: Named entity indexes (e.g., {'ORG': {1, 5}, 'PERSON': {2}})
            questions: Set of message IDs containing questions
            user_mentions: User mention indexes (e.g., {'alice': {3, 7}})
            custom_features: Arbitrary custom feature indexes
                           (e.g., {'action_items': {2}, 'sentiment_positive': {1, 5}})
            links: Set of message IDs containing a link (contains_link());
                   like questions, a computed empty set is authoritative
        """
        self.entities = entities or {}
        self.questions = questions if questions is not None else set()
        # A computed-but-empty questions index is not the same as no index:
        # the former answers is_question() with "none", the latter must not
        # silently fall back to a backend heuristic that may contradict it.
        self.has_questions_index = questions is not None
        self.links = links
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
