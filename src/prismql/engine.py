"""Main PrismQL engine."""

from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .aggregators.types import AggregateResult, GroupedResult
from .backends.base import NLPBackend, PrecomputedIndexes, SearchBackend
from .backends.factory import BackendFactory
from .dialects.pipe import parse_pipe
from .exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from .grammar.generated.PrismQLLexer import PrismQLLexer
from .grammar.generated.PrismQLParser import PrismQLParser
from .ir.executor import IRExecutor
from .ir.lower import lower_query
from .types import NamedQueryResult, QueryResult


def normalize_dictionaries(
    raw: Optional[Mapping[str, Any]],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Normalize the two accepted dictionary shapes.

    A dictionary value is either a plain term list (matched with the
    engine-wide ``text_match`` mode) or a mapping ``{"terms": [...],
    "match": "substring"|"token"}``. Returns (terms_by_name,
    explicit_mode_by_name). Multi-word terms are always phrase-matched
    regardless of mode, so the mode only governs single-word terms.
    """
    terms_map: dict[str, list[str]] = {}
    modes: dict[str, str] = {}
    for name, value in (raw or {}).items():
        if isinstance(value, Mapping):
            terms_map[name] = [str(t) for t in value.get("terms", [])]
            mode = value.get("match")
            if mode is not None:
                if mode not in ("substring", "token"):
                    raise ValueError(
                        f"Dictionary {name!r}: match must be 'substring' or "
                        f"'token', got {mode!r}"
                    )
                modes[name] = mode
        else:
            terms_map[name] = [str(t) for t in value]
    return terms_map, modes


class PrismQLErrorListener(ErrorListener):
    """Custom error listener for syntax errors."""

    def syntaxError(
        self,
        recognizer: Any,
        offendingSymbol: Any,
        line: int,
        column: int,
        msg: str,
        e: Any,
    ) -> None:
        raise PrismQLSyntaxError(f"Syntax error: {msg}", line=line, column=column)


class PrismQLEngine:
    """
    Main PrismQL query engine.

    This is the primary interface for executing PrismQL queries.
    It handles parsing, validation, and execution of queries using
    the provided backends.

    Example:
        >>> from prismql import PrismQLEngine
        >>> from prismql.backends.memory import MemoryBackend
        >>>
        >>> # Create backend with sample data
        >>> messages = [
        ...     {"id": 1, "text": "Hello world", "user": "Alice"},
        ...     {"id": 2, "text": "How are you?", "user": "Bob"},
        ...     {"id": 3, "text": "I'm fine", "user": "Alice"},
        ... ]
        >>> backend = MemoryBackend(messages)
        >>>
        >>> # Create engine
        >>> engine = PrismQLEngine(search_backend=backend)
        >>>
        >>> # Execute query
        >>> results = engine.execute("SELECT from(Alice) INWIN 10")
        >>> print(results)  # [[1, 3]]
    """

    def __init__(
        self,
        search_backend: SearchBackend,
        nlp_backend: Optional[NLPBackend] = None,
        user_dictionaries: Optional[Mapping[str, Any]] = None,
        precomputed_indexes: Optional[PrecomputedIndexes] = None,
        timestamp_field: str = "timestamp",
        text_match: str = "substring",
        use_ir: bool = True,
    ) -> None:
        """
        Initialize the PrismQL engine.

        Args:
            search_backend: Backend for text search operations
            nlp_backend: DEPRECATED. Use precomputed_indexes instead.
                       NLP features should be precomputed and provided via indexes
                       rather than computed on-the-fly during queries.
            user_dictionaries: Optional mapping of dictionary names to word lists
            precomputed_indexes: Precomputed feature indexes (entities, questions,
                               custom features). This is the recommended way to add
                               NLP features to PrismQL.
            timestamp_field: Name of the timestamp field for temporal operations
            use_ir: Execute via the IR pipeline (parse -> lower -> execute;
                default). Set False to run the legacy parse-tree visitor
                path directly. Both paths share one executor instance and
                produce identical results; the flag exists for A/B checks
                and as an escape hatch while the IR path is young.
            text_match: How contains() matches dictionary terms against text.
                "substring" (default): term anywhere in the text ("hi" matches
                "this") — historical reference behavior, doubles as poor-man's
                stemming for morphology-rich languages. "token": whole-token
                matching via the tokenizer index (Lucene-era semantics).
                contains_tokens() and contains_phrase() are unaffected.

        Note:
            The nlp_backend parameter is deprecated and will be removed in a future
            version. For NLP features:
            1. Precompute features using your preferred method (LLM, spaCy, human
               annotation, etc.)
            2. Build PrecomputedIndexes with your features
            3. Pass indexes to the engine

            Example:
                >>> indexes = PrecomputedIndexes(
                ...     entities={'ORG': {1, 5}},
                ...     custom_features={'action_items': {2, 9}}
                ... )
                >>> engine = PrismQLEngine(
                ...     search_backend=backend,
                ...     precomputed_indexes=indexes
                ... )
        """
        import warnings

        self.search_backend = search_backend

        # Deprecation warning for nlp_backend
        if nlp_backend is not None:
            warnings.warn(
                "The 'nlp_backend' parameter is deprecated and will be removed in "
                "a future version. Please use 'precomputed_indexes' instead. "
                "Precompute NLP features using your preferred method (LLM annotations, "
                "spaCy, human annotation, etc.) and provide them as PrecomputedIndexes.",
                DeprecationWarning,
                stacklevel=2,
            )
        self.nlp_backend = nlp_backend

        self.user_dictionaries, self.dictionary_modes = normalize_dictionaries(
            user_dictionaries
        )
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        self.timestamp_field = timestamp_field

        if text_match not in ("substring", "token"):
            raise ValueError(
                f"text_match must be 'substring' or 'token', got {text_match!r}"
            )
        self.text_match = text_match

        # One instance serves both execution paths: IRExecutor subclasses
        # PrismQLVisitor, so visitor.visit(tree) (legacy path) and
        # visitor.execute(ir) (IR path) share state, helpers, and dictionary
        # references.
        self.use_ir = use_ir
        self.visitor = IRExecutor(
            search_backend=search_backend,
            nlp_backend=nlp_backend,
            user_dictionaries=self.user_dictionaries,
            precomputed_indexes=self.precomputed_indexes,
            timestamp_field=timestamp_field,
            text_match=text_match,
            dictionary_modes=self.dictionary_modes,
        )

    @staticmethod
    def _resolve_dialect(query: str, dialect: str) -> str:
        """Resolve 'auto' to a concrete dialect.

        A query starting with SELECT (any case) is the classic SQL-flavored
        surface; anything else is the pipe dialect. No pipe condition is
        named ``select``, so the prefix is unambiguous.
        """
        if dialect not in ("auto", "classic", "pipe"):
            raise ValueError(
                f"dialect must be 'auto', 'classic', or 'pipe', got {dialect!r}"
            )
        if dialect != "auto":
            return dialect
        return "classic" if query.lstrip()[:6].lower() == "select" else "pipe"

    def _parse_classic(self, query: str) -> Any:
        """Parse the SQL-flavored surface into an ANTLR query context."""
        input_stream = InputStream(query)
        lexer = PrismQLLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(PrismQLErrorListener())

        token_stream = CommonTokenStream(lexer)
        parser = PrismQLParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(PrismQLErrorListener())

        # EOF-anchored entry rule: trailing garbage is a syntax error, not
        # silently ignored input.
        return parser.parse().query()

    def execute(
        self, query: str, dialect: str = "auto"
    ) -> Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]:
        """
        Parse and execute a PrismQL query.

        Args:
            query: PrismQL query string, in either surface syntax
            dialect: 'auto' (default — SELECT-prefixed queries are classic,
                anything else is pipe), 'classic', or 'pipe'

        Returns:
            Query results (QueryResult, AggregateResult, or GroupedResult)

        Raises:
            PrismQLSyntaxError: If the query has syntax errors
            PrismQLRuntimeError: If there's an error during execution
        """
        resolved = self._resolve_dialect(query, dialect)
        try:
            if resolved == "pipe":
                # The pipe dialect exists only as an IR frontend.
                result = self.visitor.execute(parse_pipe(query))
            else:
                tree = self._parse_classic(query)
                # Execute: lower to IR and run the executor (default), or
                # walk the parse tree directly with the legacy visitor path.
                if self.use_ir:
                    result = self.visitor.execute(lower_query(tree))
                else:
                    result = self.visitor.visit(tree)
            # Return empty query result if None (shouldn't happen, but defensive)
            return result if result is not None else []

        except PrismQLSyntaxError:
            # Re-raise syntax errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise PrismQLRuntimeError(
                f"Error executing query: {str(e)}", query=query, cause=e
            ) from e

    def validate(self, query: str, dialect: str = "auto") -> bool:
        """
        Validate a PrismQL query without executing it.

        Args:
            query: PrismQL query string, in either surface syntax
            dialect: 'auto' (default), 'classic', or 'pipe'

        Returns:
            True if the query is syntactically valid

        Raises:
            PrismQLSyntaxError: If the query has syntax errors
        """
        resolved = self._resolve_dialect(query, dialect)
        if resolved == "pipe":
            parse_pipe(query)
            return True
        self._parse_classic(query)
        return True

    def add_dictionary(
        self, name: str, words: Sequence[str], match: Optional[str] = None
    ) -> None:
        """
        Add or update a user dictionary.

        Args:
            name: Dictionary name
            words: List of words in the dictionary. Multi-word entries are
                always phrase-matched.
            match: Optional matching mode for single-word entries
                ("substring" or "token"); defaults to the engine's
                text_match setting.
        """
        if match is not None and match not in ("substring", "token"):
            raise ValueError(f"match must be 'substring' or 'token', got {match!r}")
        self.user_dictionaries[name] = list(words)
        if match is not None:
            self.dictionary_modes[name] = match
        else:
            self.dictionary_modes.pop(name, None)
        # Update visitor's dictionaries too
        self.visitor.user_dictionaries = self.user_dictionaries
        self.visitor.dictionary_modes = self.dictionary_modes

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "PrismQLEngine":
        """
        Create PrismQL engine from configuration dictionary.

        This factory method provides a convenient way to set up the engine
        with all backends using a single configuration dictionary.

        Args:
            config: Configuration dictionary specifying backends and settings

        Returns:
            Configured PrismQLEngine instance

        Raises:
            ValueError: If configuration is invalid
            ImportError: If required dependencies are not available

        Example:
            >>> config = {
            ...     "search_backend": {
            ...         "type": "opensearch",
            ...         "client": opensearch_client,
            ...         "index_name": "messages",
            ...         "field_mappings": {"text": "content", "user": "author"}
            ...     },
            ...     "nlp_backend": {
            ...         "type": "spacy",
            ...         "model": "en_core_web_sm"
            ...     },
            ...     "user_dictionaries": {
            ...         "sentiment": ["happy", "sad", "angry"]
            ...     }
            ... }
            >>> engine = PrismQLEngine.from_config(config)
        """
        # Validate configuration
        validated_config = BackendFactory.validate_config(config)

        # Create backends
        (
            search_backend,
            nlp_backend,
            precomputed_indexes,
            user_dictionaries,
        ) = BackendFactory.create_backends(validated_config)

        # Create engine
        return cls(
            search_backend=search_backend,
            nlp_backend=nlp_backend,
            user_dictionaries=user_dictionaries,
            precomputed_indexes=precomputed_indexes,
        )

    @classmethod
    def get_example_configs(cls) -> dict[str, dict[str, Any]]:
        """
        Get example configurations for common setups.

        Returns:
            Dictionary mapping setup names to example configurations
        """
        return BackendFactory.get_example_configs()

    def remove_dictionary(self, name: str) -> None:
        """
        Remove a user dictionary.

        Args:
            name: Dictionary name to remove
        """
        if name in self.user_dictionaries:
            del self.user_dictionaries[name]
            self.visitor.user_dictionaries = self.user_dictionaries

    def get_dictionaries(self) -> dict[str, list[str]]:
        """
        Get all user dictionaries.

        Returns:
            Dictionary mapping names to word lists
        """
        return {name: list(words) for name, words in self.user_dictionaries.items()}
