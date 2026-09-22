"""In-memory backend implementation for PrismQL."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ..config import DEFAULT_CONFIG, BackendConfig
from ..tokenizers import generate_ngrams
from ..types import Document, MessageId
from .base import SearchBackend
from .order import OrderIndex, epoch_micros
from .semantic import SemanticIndex


def _stemmer(language: str) -> Any:
    """A Snowball stemmer; the language name is the one tantivy takes too."""
    import snowballstemmer

    try:
        return snowballstemmer.stemmer(language)
    except KeyError as e:
        raise ValueError(
            f"unknown text_language {language!r}; Snowball knows "
            f"{', '.join(snowballstemmer.algorithms())}"
        ) from e


class MemoryBackend(SearchBackend):
    """
    In-memory search backend for testing and small datasets.

    This backend stores all documents in memory and performs
    searches using Python's built-in data structures.
    """

    def __init__(  # noqa: C901
        self,
        documents: Sequence[Document] | Any,
        id_field: str = "id",
        config: BackendConfig | None = None,
        semantic_index: SemanticIndex | None = None,
        text_language: str = "english",
        timestamp_fields: Sequence[str] | None = None,
    ) -> None:
        """
        Initialize the memory backend with documents.

        Args:
            documents: List of documents to index
            id_field: Field name containing the document ID
            config: Backend configuration (n-grams, tokenization, etc.)
            semantic_index: Embedding index backing similar_to(); without
                it, search_semantic() raises NotImplementedError
            text_language: Snowball stemmer language for ``search_stems``
                (the default ``contains()`` mode); the same name tantivy uses
            timestamp_fields: Fields parsed to UTC micros on the order axis
                (``timestamps_at``); ``timestamp`` is always included
        """
        # A corpus may arrive as an ordered Arrow table (spec, layer 1).
        # Row order is load order; to_pylist() preserves it. (Zero-copy
        # ingest on the Rust side is plan P1b.)
        if hasattr(documents, "to_pylist") and hasattr(documents, "num_rows"):
            documents = documents.to_pylist()
        self.documents = list(documents)
        self.id_field = id_field
        self.config = config or DEFAULT_CONFIG
        self.semantic_index = semantic_index
        self.text_language = text_language
        self._stemmer = _stemmer(text_language)
        self.config.validate()

        # Resolve tokenizer once
        self._tokenize = self.config.get_tokenizer()

        # Build indexes
        self._id_to_doc: dict[MessageId, Document] = {}
        self._field_indexes: dict[str, dict[str, set[MessageId]]] = {}
        self._text_index: dict[
            str, set[MessageId]
        ] = {}  # Token index using configured tokenizer
        self._ngram_indexes: dict[int, dict[str, set[MessageId]]] = {}  # N-gram indexes
        self._question_ids: set[MessageId] = set()

        # Collect tokens for n-gram building
        doc_tokens: dict[MessageId, list[str]] = {}

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

                # Also index individual tokens for text fields
                if field in self.config.text_fields:
                    # Tokenize using configured tokenizer
                    tokens = self._tokenize(str_value)
                    for token in tokens:
                        if token not in self._text_index:
                            self._text_index[token] = set()
                        self._text_index[token].add(doc_id)

                    # Store tokens for n-gram building
                    if self.config.enable_ngrams:
                        doc_tokens[doc_id] = tokens

                    # Check for questions
                    if self._is_question(str_value):
                        self._question_ids.add(doc_id)

        # Build n-gram indexes with frequency filtering
        if self.config.enable_ngrams:
            self._build_ngram_indexes(doc_tokens)

        # Stem the vocabulary once (unique tokens), not every occurrence:
        # the stem index is the token index folded by stem.
        self._stem_index: dict[str, set[MessageId]] = {}
        for token, ids in self._text_index.items():
            stem = self._stemmer.stemWord(token)
            bucket = self._stem_index.get(stem)
            if bucket is None:
                self._stem_index[stem] = set(ids)
            else:
                bucket |= ids

        # The ordinal axis: load order, ids as labels (spec 2026-09-18).
        # Built last so a duplicate id fails before any index is trusted.
        self.timestamp_fields = list(
            dict.fromkeys([*(timestamp_fields or []), "timestamp"])
        )
        self.order = OrderIndex(
            ids=[doc[id_field] for doc in self.documents],
            timestamps={
                f: [epoch_micros(doc.get(f)) for doc in self.documents]
                for f in self.timestamp_fields
            },
        )

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """Search for documents containing the specified terms."""
        if not terms:
            return set()

        # Search in the text index
        result_sets = []

        for term in terms:
            term_lower = term.lower()
            matching_ids: set[MessageId] = set()

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

    def search_tokens(
        self,
        terms: Sequence[str],
        field: str = "text",  # noqa: ARG002 - interface compat; token index covers text
        operator: str = "OR",
    ) -> set[MessageId]:
        """
        Search for documents containing the specified tokens.

        Uses the configured tokenizer (may preserve punctuation for emails, URLs,
        programming terms like C++, contractions like don't, etc. depending on config).

        Args:
            terms: List of tokens to search for
            field: Field to search in (default: "text")
            operator: "OR" (any term) or "AND" (all terms)

        Returns:
            Set of matching message IDs
        """
        if not terms:
            return set()

        # Search in the text index (uses configured tokenizer)
        result_sets = []

        for term in terms:
            term_lower = term.lower()
            matching_ids: set[MessageId] = set()

            # Exact token matches only. The tokenizer already preserves
            # meaningful punctuation (C++, emails, contractions), so no
            # substring fallback — that's what search_text is for.
            if term_lower in self._text_index:
                matching_ids.update(self._text_index[term_lower])

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
    ) -> set[MessageId]:
        """Search for documents with specific field value."""
        if field not in self._field_indexes:
            return set()

        value_lower = value.lower()

        if exact:
            # Exact match
            return self._field_indexes[field].get(value_lower, set()).copy()
        # Partial match
        matching_ids: set[MessageId] = set()
        for indexed_value, doc_ids in self._field_indexes[field].items():
            if value_lower in indexed_value:
                matching_ids.update(doc_ids)
        return matching_ids

    def get_total_documents(self) -> int:
        """Get total number of documents."""
        return len(self.documents)

    def get_all_document_ids(self, limit: int | None = None) -> set[MessageId]:
        """Get all document IDs."""
        all_ids = set(self._id_to_doc.keys())

        if limit is not None:
            # Convert to list, slice, then back to set
            return set(list(all_ids)[:limit])

        return all_ids

    # -- order contract (spec 2026-09-18) ---------------------------------
    def has_order_axis(self) -> bool:
        return True

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        return self.order.positions(ids)

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        return self.order.sorted_positions(ids)

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        return self.order.ids_at(positions)

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[int | None]:
        return self.order.timestamps_at(positions, field)

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        """Retrieve documents by IDs."""
        docs = []
        for doc_id in ids:
            if doc_id in self._id_to_doc:
                docs.append(self._id_to_doc[doc_id].copy())
        return docs

    def get_questions(self) -> set[MessageId]:
        """Get IDs of messages that contain questions."""
        return set(self._question_ids)

    def search_stems(
        self,
        terms: Sequence[str],
        field: str = "text",  # noqa: ARG002 - the stem index covers the text fields
        operator: str = "OR",
    ) -> set[MessageId]:
        """Whole-word match on stems: the query term is stemmed the same way."""
        if not terms:
            return set()
        sets = [
            set(self._stem_index.get(self._stemmer.stemWord(t.lower()), ()))
            for t in terms
        ]
        if operator == "AND":
            out = sets[0]
            for s in sets[1:]:
                out = out & s
            return out
        return set().union(*sets)

    def supports_match(self, mode: str) -> bool:
        return mode in ("stem", "token", "substring")

    def search_phrase(self, phrase: str, field: str = "text") -> set[MessageId]:
        """
        Search for documents containing a specific phrase.

        This uses precomputed n-gram indexes for fast O(1) lookup.
        If n-gram indexes are not enabled, falls back to substring matching.

        Args:
            phrase: Phrase to search for (e.g., "thank you", "out of memory")
            field: Field to search in (default: "text")

        Returns:
            Set of matching message IDs
        """
        if not self.config.enable_ngrams:
            # Fallback: substring matching (slower but works)
            return self._search_phrase_substring(phrase, field)

        # Tokenize the phrase using configured tokenizer
        phrase_tokens = self._tokenize(phrase.lower())
        n = len(phrase_tokens)

        if n < 2:
            # Single token - use text index
            if phrase_tokens:
                return self.search_tokens(phrase_tokens, field=field)
            return set()

        # Check if we have an n-gram index for this size
        if n not in self._ngram_indexes:
            # Fallback to substring matching
            return self._search_phrase_substring(phrase, field)

        # Look up the n-gram in the index
        ngram = " ".join(phrase_tokens)
        ids = self._ngram_indexes[n].get(ngram)
        if ids is not None:
            return ids.copy()

        # An empty lookup is authoritative only when the index is unfiltered.
        # min-frequency / max-count pruning can drop legitimate n-grams, so
        # fall back to substring matching to avoid false negatives.
        index_is_complete = (
            self.config.ngram_min_frequency <= 1 and self.config.ngram_max_count is None
        )
        if index_is_complete:
            return set()
        return self._search_phrase_substring(phrase, field)

    def search_semantic(self, text: str, *, threshold: float) -> set[MessageId]:
        """
        Search for documents semantically similar to the text.

        Requires a SemanticIndex passed at construction; without one this
        raises NotImplementedError like any backend lacking the capability.

        Args:
            text: Query text to embed and compare against documents
            threshold: Minimum cosine similarity in [0.0, 1.0]

        Returns:
            Set of message IDs at or above the threshold
        """
        if self.semantic_index is None:
            return super().search_semantic(text, threshold=threshold)
        return self.semantic_index.search(text, threshold=threshold)

    def _search_phrase_substring(self, phrase: str, field: str) -> set[MessageId]:
        """Phrase = the phrase's tokens adjacent and in order in the text —
        the same meaning as tantivy's phrase query, so "margin call" does not
        match "margin calls" on one backend and not the other."""
        wanted = self._tokenize(phrase.lower())
        if not wanted or field not in self._field_indexes:
            return set()
        n = len(wanted)
        out: set[MessageId] = set()
        for value, ids in self._field_indexes[field].items():
            tokens = self._tokenize(value)
            for k in range(len(tokens) - n + 1):
                if tokens[k : k + n] == wanted:
                    out |= ids
                    break
        return out

    def _build_ngram_indexes(self, doc_tokens: dict[MessageId, list[str]]) -> None:
        """
        Build n-gram indexes with frequency filtering.

        Args:
            doc_tokens: Mapping from doc ID to list of tokens
        """
        for n in self.config.ngram_sizes:
            # Collect all n-grams with their document IDs
            ngram_to_docs: dict[str, set[MessageId]] = {}

            for doc_id, tokens in doc_tokens.items():
                ngrams = generate_ngrams(tokens, n)
                for ngram in ngrams:
                    if ngram not in ngram_to_docs:
                        ngram_to_docs[ngram] = set()
                    ngram_to_docs[ngram].add(doc_id)

            # Filter by frequency
            if self.config.ngram_min_frequency > 1:
                ngram_to_docs = {
                    ngram: docs
                    for ngram, docs in ngram_to_docs.items()
                    if len(docs) >= self.config.ngram_min_frequency
                }

            # Limit to top-K if configured
            if self.config.ngram_max_count is not None:
                # Sort by frequency (descending) and keep top-K
                sorted_ngrams = sorted(
                    ngram_to_docs.items(), key=lambda x: len(x[1]), reverse=True
                )
                ngram_to_docs = dict(sorted_ngrams[: self.config.ngram_max_count])

            # Store the filtered index
            self._ngram_indexes[n] = ngram_to_docs

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

        return any(text_lower.startswith(word + " ") for word in question_words)
