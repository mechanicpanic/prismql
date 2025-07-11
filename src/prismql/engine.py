"""Main PrismQL engine."""

from typing import Optional, Any
from collections.abc import Mapping, Sequence

from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from .grammar.generated.PrismQLLexer import PrismQLLexer
from .grammar.generated.PrismQLParser import PrismQLParser
from .visitors.query_visitor import PrismQLVisitor
from .backends.base import SearchBackend, NLPBackend, PrecomputedIndexes
from .types import QueryResult
from .exceptions import PrismQLSyntaxError, PrismQLRuntimeError


class PrismQLErrorListener(ErrorListener):
    """Custom error listener for syntax errors."""

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
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
        >>> results = engine.execute("SELECT byuser(Alice) INWIN 10")
        >>> print(results)  # [[1, 3]]
    """

    def __init__(
        self,
        search_backend: SearchBackend,
        nlp_backend: Optional[NLPBackend] = None,
        user_dictionaries: Optional[Mapping[str, Sequence[str]]] = None,
        precomputed_indexes: Optional[PrecomputedIndexes] = None,
    ):
        """
        Initialize the PrismQL engine.

        Args:
            search_backend: Backend for text search operations
            nlp_backend: Optional backend for NLP operations
            user_dictionaries: Optional mapping of dictionary names to word lists
            precomputed_indexes: Optional precomputed NLP indexes
        """
        self.search_backend = search_backend
        self.nlp_backend = nlp_backend
        self.user_dictionaries = user_dictionaries or {}
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()

        # Create visitor
        self.visitor = PrismQLVisitor(
            search_backend=search_backend,
            nlp_backend=nlp_backend,
            user_dictionaries=self.user_dictionaries,
            precomputed_indexes=self.precomputed_indexes,
        )

    def execute(self, query: str) -> QueryResult:
        """
        Parse and execute a PrismQL query.

        Args:
            query: PrismQL query string

        Returns:
            List of message groups matching the query

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
            return self.visitor.visit(tree)

        except PrismQLSyntaxError:
            # Re-raise syntax errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise PrismQLRuntimeError(
                f"Error executing query: {str(e)}", query=query, cause=e
            )

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
