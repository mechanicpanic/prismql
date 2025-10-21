"""Main PrismQL engine."""

from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .aggregators.types import AggregateResult, GroupedResult
from .backends.base import NLPBackend, PrecomputedIndexes, SearchBackend
from .backends.factory import BackendFactory
from .exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from .grammar.generated.PrismQLLexer import PrismQLLexer
from .grammar.generated.PrismQLParser import PrismQLParser
from .types import NamedQueryResult, QueryResult
from .visitors.query_visitor import PrismQLVisitor


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
        user_dictionaries: Optional[Mapping[str, Sequence[str]]] = None,
        precomputed_indexes: Optional[PrecomputedIndexes] = None,
        timestamp_field: str = "timestamp",
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

        self.user_dictionaries: dict[str, list[str]] = {
            k: list(v) for k, v in (user_dictionaries or {}).items()
        }
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        self.timestamp_field = timestamp_field

        # Create visitor
        self.visitor = PrismQLVisitor(
            search_backend=search_backend,
            nlp_backend=nlp_backend,
            user_dictionaries=self.user_dictionaries,
            precomputed_indexes=self.precomputed_indexes,
            timestamp_field=timestamp_field,
        )

    def execute(
        self, query: str
    ) -> Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]:
        """
        Parse and execute a PrismQL query.

        Args:
            query: PrismQL query string

        Returns:
            Query results (QueryResult, AggregateResult, or GroupedResult)

        Raises:
            PrismQLSyntaxError: If the query has syntax errors
            PrismQLRuntimeError: If there's an error during execution
        """
        try:
            # Create lexer and parser
            input_stream = InputStream(query)
            lexer = PrismQLLexer(input_stream)

            # Add custom error listener
            lexer.removeErrorListeners()
            lexer.addErrorListener(PrismQLErrorListener())

            # Create token stream
            token_stream = CommonTokenStream(lexer)

            # Create parser
            parser = PrismQLParser(token_stream)
            parser.removeErrorListeners()
            parser.addErrorListener(PrismQLErrorListener())

            # Parse the query
            tree = parser.query()

            # Execute using visitor
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

    def validate(self, query: str) -> bool:
        """
        Validate a PrismQL query without executing it.

        Args:
            query: PrismQL query string

        Returns:
            True if the query is syntactically valid

        Raises:
            PrismQLSyntaxError: If the query has syntax errors
        """
        try:
            # Create lexer and parser
            input_stream = InputStream(query)
            lexer = PrismQLLexer(input_stream)
            lexer.removeErrorListeners()
            lexer.addErrorListener(PrismQLErrorListener())

            token_stream = CommonTokenStream(lexer)
            parser = PrismQLParser(token_stream)
            parser.removeErrorListeners()
            parser.addErrorListener(PrismQLErrorListener())

            # Just parse, don't execute
            parser.query()
            return True

        except PrismQLSyntaxError:
            raise

    def add_dictionary(self, name: str, words: Sequence[str]) -> None:
        """
        Add or update a user dictionary.

        Args:
            name: Dictionary name
            words: List of words in the dictionary
        """
        self.user_dictionaries[name] = list(words)
        # Update visitor's dictionaries too
        self.visitor.user_dictionaries = self.user_dictionaries

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
