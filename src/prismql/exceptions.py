"""PrismQL exceptions."""

from typing import Any


class PrismQLError(Exception):
    """Base exception for all PrismQL errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class PrismQLSyntaxError(PrismQLError):
    """Raised when there's a syntax error in the PrismQL query."""

    def __init__(
        self, message: str, line: int | None = None, column: int | None = None
    ) -> None:
        details = {}
        if line is not None:
            details["line"] = line
        if column is not None:
            details["column"] = column
        super().__init__(message, details)
        # Also store as attributes for easier access
        self.line = line
        self.column = column


class PrismQLRuntimeError(PrismQLError):
    """Raised when there's a runtime error during query execution."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = {}
        if query is not None:
            details["query"] = query
        if cause is not None:
            details["cause"] = str(cause)
            details["cause_type"] = type(cause).__name__
        super().__init__(message, details)


class BackendError(PrismQLError):
    """Raised when there's an error with a backend operation."""

    def __init__(
        self, message: str, backend_name: str, operation: str | None = None
    ) -> None:
        details = {"backend": backend_name}
        if operation is not None:
            details["operation"] = operation
        super().__init__(message, details)


class ConfigurationError(PrismQLError):
    """Raised when there's a configuration error."""

    pass


class PositionalUnsupportedError(PrismQLRuntimeError):
    """The backend has no stream-order axis, so positional and sequential
    operators cannot run on it. Boolean/set queries still work.

    Raised by SearchBackend's order-contract defaults; backends that carry
    an OrderIndex (memory, rust_memory, tantivy) override them.
    """


# Characters that end an unquoted value; a value containing one needs quotes.
_VALUE_BREAKERS = "-/:@.#&'"


def unquoted_value_hint(char: str) -> str:
    """A hint for a lexer stop at ``char`` when it most likely sits inside an
    unquoted value (graph @aleph/prismql, #97); empty for other characters."""
    if char in _VALUE_BREAKERS:
        return f' — a value with {char!r} must be in quotes, e.g. field(name, "a-b")'
    return ""
