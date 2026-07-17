"""PrismQL query validator with detailed feedback for LLM agents."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from antlr4 import CommonTokenStream, InputStream

from .exceptions import PrismQLSyntaxError
from .grammar.generated.PrismQLLexer import PrismQLLexer
from .grammar.generated.PrismQLParser import PrismQLParser


class ValidationLevel(Enum):
    """Severity level of validation issues."""

    ERROR = "error"  # Query will fail
    WARNING = "warning"  # Query works but inefficient/deprecated
    INFO = "info"  # Suggestions for improvement


@dataclass
class ValidationIssue:
    """A single validation issue found in a query."""

    level: ValidationLevel
    message: str
    suggestion: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None  # Error code for programmatic handling

    def __str__(self) -> str:
        """Format issue as human-readable string."""
        location = ""
        if self.line is not None and self.column is not None:
            location = f" [line {self.line}, col {self.column}]"

        result = f"{self.level.value.upper()}{location}: {self.message}"
        if self.suggestion:
            result += f"\n  Suggestion: {self.suggestion}"
        return result


@dataclass
class ValidationResult:
    """Result of query validation."""

    valid: bool
    issues: list[ValidationIssue]
    query: str

    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.valid

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    @property
    def infos(self) -> list[ValidationIssue]:
        """Get only info-level issues."""
        return [i for i in self.issues if i.level == ValidationLevel.INFO]

    def __str__(self) -> str:
        """Format validation result as human-readable string."""
        if self.valid:
            result = "✓ Query is valid"
            if self.warnings or self.infos:
                result += (
                    f" ({len(self.warnings)} warnings, {len(self.infos)} suggestions)"
                )
        else:
            result = f"✗ Query is invalid ({len(self.errors)} errors)"

        if self.issues:
            result += "\n\n" + "\n\n".join(str(issue) for issue in self.issues)

        return result


class QueryValidator:
    """
    Comprehensive query validator for PrismQL.

    Validates both syntax and semantics, providing detailed feedback
    that helps LLM agents self-correct their queries.

    Example:
        validator = QueryValidator(
            user_dictionaries={"greetings": ["hello", "hi"]},
            available_fields=["text", "user", "timestamp"]
        )

        result = validator.validate("SELECT from(alice)")
        if result.valid:
            print("Query is good!")
        else:
            for error in result.errors:
                print(error)
    """

    def __init__(
        self,
        user_dictionaries: Optional[dict[str, Any]] = None,
        available_fields: Optional[list[str]] = None,
        custom_features: Optional[dict[str, Any]] = None,
        check_deprecated: bool = True,
        check_performance: bool = True,
    ):
        """
        Initialize validator.

        Args:
            user_dictionaries: Available dictionaries for contains()
            available_fields: Available fields in the dataset
            custom_features: Available custom features
            check_deprecated: Whether to warn about deprecated syntax
            check_performance: Whether to suggest performance improvements
        """
        from .engine import normalize_dictionaries

        # Accept both dictionary shapes (plain list or {terms, match})
        self.user_dictionaries, _ = normalize_dictionaries(user_dictionaries)
        self.available_fields = set(available_fields or [])
        self.custom_features = set(custom_features or {})
        self.check_deprecated = check_deprecated
        self.check_performance = check_performance

    def validate(self, query: str, dialect: str = "auto") -> ValidationResult:
        """
        Validate a PrismQL query.

        Args:
            query: Query string to validate, in either surface syntax
            dialect: 'auto' (default — SELECT-prefixed queries are classic,
                everything else is pipe), 'classic', or 'pipe'

        Returns:
            ValidationResult with detailed feedback
        """
        from .engine import PrismQLEngine

        resolved = PrismQLEngine._resolve_dialect(query, dialect)
        if resolved == "pipe":
            return self._validate_pipe(query)

        issues: list[ValidationIssue] = []

        # 1. Syntax validation
        try:
            tree = self._parse_query(query)
        except PrismQLSyntaxError as e:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=str(e),
                    line=getattr(e, "line", None),
                    column=getattr(e, "column", None),
                    code="SYNTAX_ERROR",
                )
            )
            return ValidationResult(valid=False, issues=issues, query=query)

        # 2. Semantic validation
        issues.extend(self._check_semantics(query, tree))

        # 3. Check for deprecated syntax
        if self.check_deprecated:
            issues.extend(self._check_deprecated_syntax(query))

        # 4. Performance suggestions
        if self.check_performance:
            issues.extend(self._check_performance(query))

        # 5. Best practice suggestions
        issues.extend(self._check_best_practices(query))

        # Valid if no errors
        has_errors = any(i.level == ValidationLevel.ERROR for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues, query=query)

    def _validate_pipe(self, query: str) -> ValidationResult:
        """Validate a pipe-dialect query.

        The pipe parser produces IR directly, so semantic checks walk the IR
        instead of regexing the query string. Only checks whose classic
        counterparts can produce ERRORs are implemented (undefined
        dictionaries, missing window constraints) plus the large-window
        warning — so ``valid`` means the same thing on both surfaces.
        Classic-only string heuristics (deprecated aliases, best-practice
        suggestions) have no pipe equivalents and are skipped.
        """
        from .dialects.pipe import parse_pipe

        issues: list[ValidationIssue] = []

        try:
            ir_query = parse_pipe(query)
        except PrismQLSyntaxError as e:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=str(e),
                    line=getattr(e, "line", None),
                    column=getattr(e, "column", None),
                    code="SYNTAX_ERROR",
                )
            )
            return ValidationResult(valid=False, issues=issues, query=query)

        issues.extend(self._check_ir_semantics(ir_query))

        has_errors = any(i.level == ValidationLevel.ERROR for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues, query=query)

    def _check_similar_thresholds(self, query: str) -> list[ValidationIssue]:
        """Regex counterpart of the IR-walk similar_to() threshold check."""
        import re

        issues: list[ValidationIssue] = []
        threshold_pattern = (
            r"similar_to\(\s*['\"][^'\"]*['\"]\s*,\s*(\d+(?:\.\d+)?)\s*\)"
        )
        for match in re.finditer(threshold_pattern, query, re.IGNORECASE):
            threshold = float(match.group(1))
            if not 0.0 <= threshold <= 1.0:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"similar_to() threshold {threshold} is outside [0.0, 1.0]"
                        ),
                        suggestion=(
                            "Cosine similarity lives in [0, 1] here; pick a "
                            "threshold like 0.7"
                        ),
                        code="THRESHOLD_OUT_OF_RANGE",
                    )
                )
        return issues

    def _check_ir_semantics(self, ir_query: Any) -> list[ValidationIssue]:
        """IR-walk counterparts of the classic string checks."""
        issues: list[ValidationIssue] = []
        self._check_ir_query(ir_query, issues)
        return issues

    def _check_ir_query(self, q: Any, issues: list[ValidationIssue]) -> None:
        from .ir import nodes as ir

        # A body window never excuses a windowless final link: for a
        # single-item row the pipe parser already inlined a trailing
        # within/during into the link (_attach_window), and the executor
        # rejects every remaining windowless-final-link shape — including
        # multi-item rows with a body window (review 2026-07-12, #43).
        self._check_ir_window(q.positional_window, issues)
        if isinstance(q.source, ir.RestrictionsRow):
            for item in q.source.items:
                self._check_ir_expr(item.expr, True, issues)
        elif isinstance(q.source, ir.SubqueryChain):
            self._check_ir_query(q.source.head, issues)
            for cont in q.source.continuations:
                self._check_ir_window(cont.window, issues)
                self._check_ir_query(cont.query, issues)

    def _check_ir_expr(
        self, expr: Any, is_final_position: bool, issues: list[ValidationIssue]
    ) -> None:
        from .ir import nodes as ir

        if isinstance(expr, ir.Contains):
            # Parity with the classic `contains(\w+)` regex: only
            # contains() dictionary names are checked.
            if (
                isinstance(expr.dict_name, ir.Literal)
                and expr.dict_name.text not in self.user_dictionaries
            ):
                available = (
                    ", ".join(self.user_dictionaries.keys())
                    if self.user_dictionaries
                    else "none available"
                )
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Dictionary '{expr.dict_name.text}' is not defined",
                        suggestion=f"Define the dictionary or use one of: {available}",
                        code="UNDEFINED_DICTIONARY",
                    )
                )
        elif isinstance(expr, ir.SimilarTo):
            if not 0.0 <= expr.threshold <= 1.0:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"similar_to() threshold {expr.threshold} is outside "
                            "[0.0, 1.0]"
                        ),
                        suggestion=(
                            "Cosine similarity lives in [0, 1] here; pick a "
                            "threshold like 0.7"
                        ),
                        code="THRESHOLD_OUT_OF_RANGE",
                    )
                )
        elif isinstance(expr, ir.Not):
            self._check_sequence_under_boolean(expr.operand, "NOT", issues)
            self._check_ir_expr(expr.operand, False, issues)
        elif isinstance(expr, (ir.And, ir.Or)):
            op_name = "AND" if isinstance(expr, ir.And) else "OR"
            self._check_sequence_under_boolean(expr.left, op_name, issues)
            self._check_sequence_under_boolean(expr.right, op_name, issues)
            self._check_ir_expr(expr.left, False, issues)
            self._check_ir_expr(expr.right, False, issues)
        elif isinstance(expr, ir.SequenceLink):
            self._check_ir_window(expr.window, issues)
            # A chain nests left, so the outermost link is the final one;
            # earlier windowless links defer to an enclosing window
            # (PartialSequence semantics) and are fine.
            if is_final_position and expr.window is None:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            f"Sequential operator {expr.op} must be followed by "
                            "a window constraint"
                        ),
                        suggestion=(
                            "Add a window to the arrow (e.g. ~>(3) or ~>(1h)) "
                            "or a trailing stage: |> within(<n>) / |> during(<time>)"
                        ),
                        code="MISSING_WINDOW_CONSTRAINT",
                    )
                )
            # The rhs of a link must be a boolean/leaf expression — the
            # executor rejects a nested sequence there (chains nest LEFT).
            if isinstance(expr.rhs, ir.SequenceLink):
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=(
                            "Sequential operators require simple conditions on "
                            "the right-hand side, not a nested sequence"
                        ),
                        suggestion=(
                            "Write the chain left-to-right without grouping: "
                            "a ~> b ~> c (chains associate left)"
                        ),
                        code="NESTED_SEQUENCE_RHS",
                    )
                )
            self._check_ir_expr(expr.lhs, False, issues)
            self._check_ir_expr(expr.rhs, False, issues)

    def _check_sequence_under_boolean(
        self, child: Any, op_name: str, issues: list[ValidationIssue]
    ) -> None:
        """Sequences cannot appear under NOT/AND/OR — the executor always
        rejects that shape, so the validator must too (parity contract)."""
        from .ir import nodes as ir

        if isinstance(child, ir.SequenceLink):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=(
                        f"{op_name} operator cannot be used with sequential "
                        "operators (FOLLOWED_BY, PRECEDED_BY)"
                    ),
                    suggestion=(
                        "Sequential results are complete sequences, not sets; "
                        "restructure so boolean operators apply to conditions "
                        "inside each restriction, not to a chain"
                    ),
                    code="SEQUENCE_UNDER_BOOLEAN",
                )
            )

    @staticmethod
    def _check_ir_window(window: Any, issues: list[ValidationIssue]) -> None:
        if isinstance(window, int) and window > 100:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Large window size ({window}) may impact performance",
                    suggestion=(
                        "Consider using smaller windows or adding temporal "
                        "filters (before/after stages)"
                    ),
                    code="LARGE_WINDOW",
                )
            )

    def _parse_query(self, query: str) -> Any:
        """Parse query and return parse tree."""
        from .engine import PrismQLErrorListener

        input_stream = InputStream(query)
        lexer = PrismQLLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(PrismQLErrorListener())

        token_stream = CommonTokenStream(lexer)
        parser = PrismQLParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(PrismQLErrorListener())

        # EOF-anchored: trailing garbage is a syntax error
        return parser.parse().query()

    def _check_semantics(self, query: str, tree: Any) -> list[ValidationIssue]:
        """Check semantic validity of the query."""
        issues: list[ValidationIssue] = []

        import re

        # Check for sequential operators without windows
        # Match FOLLOWED_BY/PRECEDED_BY/etc that are NOT followed by INWINDOW/DURING/WITHIN
        sequential_ops = r"(FOLLOWED_BY|PRECEDED_BY|NOT_FOLLOWED_BY|NOT_PRECEDED_BY)"
        window_ops = r"(INWINDOW|DURING|WITHIN)"

        # Find all sequential operators
        for match in re.finditer(sequential_ops, query, re.IGNORECASE):
            op_pos = match.end()
            # Check what comes after this operator (skip whitespace and content until next keyword)
            remaining = query[op_pos:]

            # Look for the next sequential operator or window operator
            next_seq = re.search(sequential_ops, remaining, re.IGNORECASE)
            next_window = re.search(window_ops, remaining, re.IGNORECASE)

            # If there's another sequential operator before a window operator, that's a chain
            # The final operator in the chain must have a window
            if next_seq and (not next_window or next_seq.start() < next_window.start()):
                # This is a chained operator, continue to check the next one
                continue
            if not next_window:
                # No window operator found after this sequential operator
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Sequential operator {match.group(1)} must be followed by a window constraint (INWINDOW or DURING)",
                        suggestion="Add INWINDOW <number> or DURING <time> after the final sequential operator",
                        code="MISSING_WINDOW_CONSTRAINT",
                    )
                )

        # Check for undefined dictionaries
        dict_pattern = r"contains\((\w+)\)"
        for match in re.finditer(dict_pattern, query):
            dict_name = match.group(1)
            if dict_name not in self.user_dictionaries:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.ERROR,
                        message=f"Dictionary '{dict_name}' is not defined",
                        suggestion=f"Define the dictionary or use one of: {', '.join(self.user_dictionaries.keys()) if self.user_dictionaries else 'none available'}",
                        code="UNDEFINED_DICTIONARY",
                    )
                )

        # Check similar_to() thresholds (parity with the IR-walk check)
        issues.extend(self._check_similar_thresholds(query))

        # Check for undefined custom features
        feature_pattern = r"(\w+)\(\)"
        for match in re.finditer(feature_pattern, query):
            feature = match.group(1)
            # Skip known operators
            if feature in {
                "is_question",
                "mentions_date",
                "mentions_time",
                "mentions_place",
                "mentions_org",
                "contains_link",
            }:
                continue
            # Check if it's a custom feature
            if feature not in self.custom_features and feature + "()" not in query:
                # Might be a custom feature
                if self.custom_features:
                    issues.append(
                        ValidationIssue(
                            level=ValidationLevel.WARNING,
                            message=f"Custom feature '{feature}()' might not be defined",
                            suggestion=f"Available custom features: {', '.join(self.custom_features)}",
                            code="POSSIBLE_UNDEFINED_FEATURE",
                        )
                    )

        return issues

    def _check_deprecated_syntax(self, query: str) -> list[ValidationIssue]:
        """Check for deprecated syntax."""
        issues: list[ValidationIssue] = []

        # Map of deprecated -> replacement
        deprecated_map = {
            "byuser": "from",
            "haswordofdict": "contains",
            "hasquestion": "is_question",
            "hasdate": "mentions_date",
            "hastime": "mentions_time",
            "haslocation": "mentions_place",
            "hasorganization": "mentions_org",
            "hasurl": "contains_link",
            "hasusermentioned": "mentions_user",
        }

        for old, new in deprecated_map.items():
            if old in query.lower():
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"'{old}()' is deprecated",
                        suggestion=f"Use '{new}()' instead. Legacy syntax will be removed in v1.0",
                        code="DEPRECATED_SYNTAX",
                    )
                )

        return issues

    def _check_performance(self, query: str) -> list[ValidationIssue]:
        """Check for potential performance issues."""
        issues: list[ValidationIssue] = []

        # Check for very large windows
        import re

        window_pattern = r"INWINDOW\s+(\d+)|INWIN\s+(\d+)|WITHIN\s+(\d+)"
        for match in re.finditer(window_pattern, query):
            size = int(match.group(1) or match.group(2) or match.group(3))
            if size > 100:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Large window size ({size}) may impact performance",
                        suggestion="Consider using smaller windows or adding temporal filters (AFTER/BEFORE)",
                        code="LARGE_WINDOW",
                    )
                )

        # Check for NOT without other constraints
        if query.strip().startswith("SELECT NOT "):
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="Query starts with NOT, which returns all non-matching messages",
                    suggestion="Consider combining NOT with other conditions using AND",
                    code="NEGATION_ONLY",
                )
            )

        # Check for multiple OR conditions (can be inefficient)
        or_count = query.upper().count(" OR ")
        if or_count > 5:
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Query has {or_count} OR operators",
                    suggestion="Consider using dictionaries to group related terms",
                    code="MANY_OR_CONDITIONS",
                )
            )

        return issues

    def _check_best_practices(self, query: str) -> list[ValidationIssue]:
        """Check for best practice violations."""
        issues: list[ValidationIssue] = []

        # Suggest using named groups for complex queries
        if "INWIN" in query and " AS " not in query:
            # Count comma-separated restrictions
            if query.count(",") >= 2:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.INFO,
                        message="Complex query without named groups",
                        suggestion="Consider using AS to label patterns for clarity",
                        code="MISSING_NAMED_GROUPS",
                    )
                )

        # Suggest temporal filtering for large datasets
        if "AGGREGATE" in query.upper() and "AFTER" not in query.upper():
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.INFO,
                    message="Aggregation query without temporal filter",
                    suggestion="Consider adding AFTER/BEFORE to limit the time range",
                    code="MISSING_TEMPORAL_FILTER",
                )
            )

        # Check for complex boolean expressions without parentheses
        # Look for OR and AND in the query (but not within function calls)
        if " OR " in query.upper() and " AND " in query.upper():
            # Check if there are parens grouping the boolean ops (not just function calls)
            # Simple heuristic: if we have both OR and AND, suggest parentheses
            # unless we can see explicit grouping like (... OR ...) AND ...
            has_grouping_parens = False
            # Check for patterns like (expr) OR/AND (expr)
            import re

            if re.search(r"\([^)]*(?:OR|AND)[^)]*\)", query, re.IGNORECASE):
                has_grouping_parens = True

            if not has_grouping_parens:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message="Mixed AND/OR without explicit grouping",
                        suggestion="Use parentheses to make precedence explicit: (A OR B) AND C",
                        code="AMBIGUOUS_PRECEDENCE",
                    )
                )

        return issues


def validate_query(
    query: str,
    user_dictionaries: Optional[dict[str, list[str]]] = None,
    **kwargs: Any,
) -> ValidationResult:
    """
    Convenience function to validate a query.

    Args:
        query: Query string to validate
        user_dictionaries: Available dictionaries
        **kwargs: Additional validator options

    Returns:
        ValidationResult

    Example:
        result = validate_query(
            "SELECT from(alice)",
            user_dictionaries={"greetings": ["hi", "hello"]}
        )
        print(result)
    """
    validator = QueryValidator(user_dictionaries=user_dictionaries, **kwargs)
    return validator.validate(query)
