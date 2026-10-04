"""Main PrismQL engine."""

from collections.abc import Mapping, Sequence
from typing import Any

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

from .aggregators.types import AggregateResult, GroupedResult
from .backends.base import PrecomputedIndexes, SearchBackend
from .backends.factory import BackendFactory
from .dialects.pipe import parse_pipe
from .exceptions import (
    PrismQLRuntimeError,
    PrismQLSyntaxError,
    dictionary_not_word_advice,
    negated_literal_hint,
    unquoted_value_hint,
)
from .grammar.generated.PrismQLLexer import PrismQLLexer
from .grammar.generated.PrismQLParser import PrismQLParser
from .ir.executor import IRExecutor
from .ir.lower import lower_query
from .processors.time_field import has_time, measures_time, missing_time_error
from .types import NamedQueryResult, QueryResult

MATCH_MODES = ("stem", "token", "substring")


def normalize_dictionaries(
    raw: Mapping[str, Any] | None,
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Normalize the two accepted dictionary shapes.

    A dictionary value is either a plain term list (matched with the
    engine-wide ``text_match`` mode) or a mapping ``{"terms": [...],
    "match": "stem"|"token"|"substring"}``. Returns (terms_by_name,
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
                if mode not in MATCH_MODES:
                    raise ValueError(
                        f"Dictionary {name!r}: match must be one of "
                        f"{MATCH_MODES}, got {mode!r}"
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
        hint = _contains_word_hint(recognizer, offendingSymbol)
        prefix = "token recognition error at: '"
        if not hint and msg.startswith(prefix) and len(msg) > len(prefix):
            char = msg[len(prefix)]
            hint = unquoted_value_hint(char)
            if char == "!":
                start = recognizer._tokenStartCharIndex
                hint = negated_literal_hint(recognizer.inputStream.strdata, start)
        raise PrismQLSyntaxError(f"Syntax error: {msg}{hint}", line=line, column=column)


def _contains_word_hint(recognizer: Any, token: Any) -> str:
    """A quoted word in contains(…): the grammar's STRING is a bare name, so
    the parser's own message names it and still refuses the quotes."""
    text = getattr(token, "text", None) or ""
    stream = getattr(recognizer, "getTokenStream", lambda: None)()
    index = getattr(token, "tokenIndex", -1)
    if text[:1] not in "\"'" or stream is None or index < 2:
        return ""
    name, paren = stream.get(index - 2).text, stream.get(index - 1).text
    if paren != "(" or name.lower() not in ("contains", "contains_tokens"):
        return ""
    return " — " + dictionary_not_word_advice(name, text)


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
        >>> print(results)  # [[1], [3]]
    """

    def __init__(
        self,
        search_backend: SearchBackend,
        user_dictionaries: Mapping[str, Any] | None = None,
        precomputed_indexes: PrecomputedIndexes | None = None,
        timestamp_field: str = "timestamp",
        text_match: str = "stem",
        use_ir: bool = True,
        quantifier_ceiling: int | None = None,
        actor_field: str = "user",
        mentions_column: str | None = None,
    ) -> None:
        """
        Initialize the PrismQL engine.

        Args:
            search_backend: Backend for text search operations
            user_dictionaries: Optional mapping of dictionary names to word lists
            precomputed_indexes: Precomputed feature indexes (entities, questions,
                               custom features). Text annotation happens at
                               ingest time and reaches the engine this way.
            timestamp_field: Name of the timestamp field for temporal operations
            use_ir: Execute via the IR pipeline (parse -> lower -> execute;
                default). Set False to run the legacy parse-tree visitor
                path directly. Both paths share one executor instance and
                produce identical results; the flag exists for A/B checks
                and as an escape hatch while the IR path is young.
            text_match: How contains() matches dictionary terms against text.
                "stem" (default): the term's Snowball stem against the stemmed
                tokens. "token": whole-token matching via the tokenizer index
                (Lucene-era semantics). "substring": term anywhere in the text
                ("hi" matches "this") — historical reference behavior.
                contains_tokens() and contains_phrase() are unaffected.
            actor_field: The field naming each event's author; an @mention
                is ``@`` and one of its values (``mentions_user``). The
                language's own ``from()`` reads ``user``, hence the default.
            mentions_column: An ingest-stamped column holding each event's
                mentions; without one they are found once in the text.
            quantifier_ceiling: Upper bound that closes an open range {n,}
                as {n,m}. None (default): an open range is an error — the
                engine enumerates groups up to an explicit size and never
                truncates silently (graph @aleph/prismql #46).
        """
        self.search_backend = search_backend

        self.user_dictionaries, self.dictionary_modes = normalize_dictionaries(
            user_dictionaries
        )
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        self.timestamp_field = timestamp_field

        if text_match not in MATCH_MODES:
            raise ValueError(
                f"text_match must be one of {MATCH_MODES}, got {text_match!r}"
            )
        self.text_match = text_match
        # Refuse, never substitute: a backend that cannot honour the mode a
        # dictionary will be matched with is an error at construction, not a
        # different answer at query time (graph #59).
        if self.user_dictionaries:
            self._check_match_support(text_match)
            for name, mode in self.dictionary_modes.items():
                self._check_match_support(mode, dictionary=name)
        if quantifier_ceiling is not None and quantifier_ceiling < 1:
            raise ValueError("quantifier_ceiling must be >= 1")
        self.quantifier_ceiling = quantifier_ceiling
        self.actor_field = actor_field
        self.mentions_column = mentions_column

        # One instance serves both execution paths: IRExecutor subclasses
        # PrismQLVisitor, so visitor.visit(tree) (legacy path) and
        # visitor.execute(ir) (IR path) share state, helpers, and dictionary
        # references.
        self.use_ir = use_ir
        self.visitor = IRExecutor(
            search_backend=search_backend,
            user_dictionaries=self.user_dictionaries,
            precomputed_indexes=self.precomputed_indexes,
            timestamp_field=timestamp_field,
            text_match=text_match,
            dictionary_modes=self.dictionary_modes,
            quantifier_ceiling=quantifier_ceiling,
            actor_field=actor_field,
            mentions_column=mentions_column,
        )

    def _check_match_support(self, mode: str, dictionary: str | None = None) -> None:
        supports = getattr(self.search_backend, "supports_match", None)
        if supports is not None and not supports(mode):
            where = f"dictionary {dictionary!r}" if dictionary else "text_match"
            raise ValueError(
                f"{type(self.search_backend).__name__} cannot match {mode!r} "
                f"({where}); choose a mode this backend supports "
                "(tantivy: stem, token; memory: stem, token, substring)"
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
    ) -> QueryResult | NamedQueryResult | AggregateResult | GroupedResult:
        """
        Parse and execute a PrismQL query.

        Args:
            query: PrismQL query string, in either surface syntax
            dialect: 'auto' (default — SELECT-prefixed queries are classic,
                anything else is pipe), 'classic', or 'pipe'

        Returns:
            Query results (QueryResult, NamedQueryResult, AggregateResult, or
            GroupedResult)

        Raises:
            PrismQLSyntaxError: If the query has syntax errors
            PrismQLRuntimeError: If there's an error during execution
        """
        resolved = self._resolve_dialect(query, dialect)
        try:
            if resolved == "pipe":
                # The pipe dialect exists only as an IR frontend.
                ir = parse_pipe(query)
                self._check_variables(ir)
                self._check_time_field(ir)
                result = self.visitor.execute(ir)
            else:
                tree = self._parse_classic(query)
                ir = lower_query(tree)
                self._check_variables(ir)
                self._check_time_field(ir)
                # Execute: run the IR executor (default), or walk the parse
                # tree directly with the legacy visitor path.
                if self.use_ir:
                    result = self.visitor.execute(ir)
                else:
                    result = self.visitor.visit(tree)
            # Return empty query result if None (shouldn't happen, but defensive)
            return result if result is not None else []

        except PrismQLSyntaxError:
            # Re-raise syntax errors as-is
            raise
        except PrismQLRuntimeError:
            # Already ours (incl. PositionalUnsupportedError): the type is the
            # contract a caller catches — never wrap it into the base class.
            raise
        except Exception as e:
            # Wrap other exceptions
            raise PrismQLRuntimeError(
                f"Error executing query: {str(e)}", query=query, cause=e
            ) from e

    def _check_variables(self, ir: Any) -> None:
        """Refuse an own-leg ``!$a`` across OR or NOT before either path
        runs it (graph @aleph/prismql, #152)."""
        from .ir.variables import guarded_own_negations, own_negation_message

        names = guarded_own_negations(ir)
        if names:
            raise PrismQLRuntimeError(own_negation_message(names[0]))

    def _check_time_field(self, ir: Any) -> None:
        """A query that measures time on a corpus with none in its time
        field is refused, not answered empty (graph @aleph/prismql, #117).
        Asked once per engine; the corpus does not change under it."""
        if not measures_time(ir):
            return
        field = self.timestamp_field
        known: dict[str, bool] = self.__dict__.setdefault("_time_present", {})
        if field not in known:
            known[field] = has_time(self.search_backend, field)
        if not known[field]:
            raise missing_time_error(self.search_backend, field)

    def to_ir(self, query: str, dialect: str = "auto") -> Any:
        """The query's IR (``ir.nodes.Query``) without executing it."""
        if self._resolve_dialect(query, dialect) == "pipe":
            return parse_pipe(query)
        return lower_query(self._parse_classic(query))

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
        self, name: str, words: Sequence[str], match: str | None = None
    ) -> None:
        """
        Add or update a user dictionary.

        Args:
            name: Dictionary name
            words: List of words in the dictionary. Multi-word entries are
                always phrase-matched.
            match: Optional matching mode for single-word entries
                ("stem", "token" or "substring"); defaults to the engine's
                text_match setting.
        """
        if match is not None and match not in MATCH_MODES:
            raise ValueError(f"match must be one of {MATCH_MODES}, got {match!r}")
        self._check_match_support(match or self.text_match, dictionary=name)
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
            ...         "type": "memory",
            ...         "documents": [{"id": 1, "text": "hi", "user": "alice"}],
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
            precomputed_indexes,
            user_dictionaries,
        ) = BackendFactory.create_backends(validated_config)

        # Create engine
        return cls(
            search_backend=search_backend,
            user_dictionaries=user_dictionaries,
            text_match=config.get("text_match", "stem"),
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
