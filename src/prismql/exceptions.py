"""PrismQL exceptions."""

from typing import Any, Optional


class PrismQLError(Exception):
    """Base exception for all PrismQL errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class PrismQLSyntaxError(PrismQLError):
    """Raised when there's a syntax error in the PrismQL query."""

    def __init__(
        self, message: str, line: Optional[int] = None, column: Optional[int] = None
    ):
        details = {}
        if line is not None:
            details["line"] = line
        if column is not None:
            details["column"] = column
        super().__init__(message, details)


class PrismQLRuntimeError(PrismQLError):
    """Raised when there's a runtime error during query execution."""

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
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
        self, message: str, backend_name: str, operation: Optional[str] = None
    ):
        details = {"backend": backend_name}
        if operation is not None:
            details["operation"] = operation
        super().__init__(message, details)


class ConfigurationError(PrismQLError):
    """Raised when there's a configuration error."""

    pass
