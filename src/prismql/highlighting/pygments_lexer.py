"""
Pygments lexer for PrismQL query language.

Provides syntax highlighting for PrismQL queries in documentation,
code blocks, and other contexts that support Pygments.
"""

from pygments.lexer import RegexLexer, words
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Whitespace,
)

__all__ = ["PrismQLLexer"]


class PrismQLLexer(RegexLexer):
    """
    Lexer for PrismQL query language.

    PrismQL is a domain-specific language for pattern matching in conversational data.

    Example::

        SELECT from(alice), contains(problems) INWINDOW 10

    .. versionadded:: 1.0
    """

    name = "PrismQL"
    aliases = ["prismql", "pql"]
    filenames = ["*.pql", "*.prismql"]
    mimetypes = ["text/x-prismql"]

    tokens = {
        "root": [
            # Comments (even though not in grammar, useful for examples)
            (r"--.*$", Comment.Single),
            (r"//.*$", Comment.Single),
            (r"/\*", Comment.Multiline, "multiline-comment"),
            # Whitespace
            (r"\s+", Whitespace),
            # Main keyword (case-insensitive)
            (r"(?i)\bSELECT\b", Keyword.Reserved),
            # Window and constraint keywords
            (
                words(
                    (
                        "INWINDOW",
                        "IN_WINDOW",
                        "INWIN",  # Deprecated: use INWINDOW
                        "DURING",  # Temporal window operator
                        "WITHIN",  # Deprecated: use DURING for temporal, INWINDOW for positional
                        "AS",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Keyword,
            ),
            # Boolean operators
            (
                words(
                    ("AND", "OR", "NOT"),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Operator.Word,
            ),
            # Positional operators (lookahead/lookbehind)
            (
                words(
                    (
                        "FOLLOWED_BY",
                        "FOLLOWEDBY",
                        "PRECEDED_BY",
                        "PRECEDEDBY",
                        "NOT_FOLLOWED_BY",
                        "NOTFOLLOWEDBY",
                        "NOT_PRECEDED_BY",
                        "NOTPRECEDEDBY",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Operator.Word,
            ),
            # Aggregation keywords
            (
                words(
                    (
                        "AGGREGATE",
                        "GROUP BY",
                        "GROUPBY",
                        "COUNT",
                        "DISTINCT",
                        "SUM",
                        "AVG",
                        "MIN",
                        "MAX",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Keyword.Reserved,
            ),
            # Ordering and limiting
            (
                words(
                    (
                        "ORDER BY",
                        "ORDERBY",
                        "ASC",
                        "DESC",
                        "LIMIT",
                        "OFFSET",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Keyword.Reserved,
            ),
            # Temporal filtering
            (
                words(
                    (
                        "BEFORE",
                        "AFTER",
                        "BETWEEN",
                        "AGO",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Keyword,
            ),
            # Time units
            (
                words(
                    (
                        "SECONDS",
                        "SECOND",
                        "MINUTES",
                        "MINUTE",
                        "HOURS",
                        "HOUR",
                        "DAYS",
                        "DAY",
                        "WEEKS",
                        "WEEK",
                        "MONTHS",
                        "MONTH",
                        "YEARS",
                        "YEAR",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Keyword.Type,
            ),
            # Fluent condition functions (preferred)
            (
                words(
                    (
                        "contains",
                        "contains_tokens",
                        "containstokens",
                        "contains_phrase",
                        "containsphrase",
                        "from",
                        "field",
                        "has_feature",
                        "hasfeature",
                        "labeled_as",
                        "labeledas",
                        "mentions_user",
                        "mentionsuser",
                        "is_question",
                        "isquestion",
                        "mentions_date",
                        "mentionsdate",
                        "mentions_time",
                        "mentionstime",
                        "mentions_place",
                        "mentionsplace",
                        "mentions_org",
                        "mentionsorg",
                        "contains_link",
                        "containslink",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Name.Builtin,
            ),
            # Legacy condition functions (backward compatibility)
            (
                words(
                    (
                        "haswordofdict",
                        "byuser",
                        "hasusermentioned",
                        "hasquestion",
                        "hasdate",
                        "hastime",
                        "haslocation",
                        "hasorganization",
                        "hasurl",
                    ),
                    prefix=r"(?i)\b",
                    suffix=r"\b",
                ),
                Name.Builtin.Pseudo,
            ),
            # Pattern variables (e.g., $user)
            (r"\$[a-zA-Z_][a-zA-Z0-9_]*", Name.Variable),
            # Quoted strings
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            # Numbers
            (r"\b\d+\b", Number.Integer),
            # Quantifiers
            (r"\{", Punctuation, "quantifier"),
            # Parentheses
            (r"[()]", Punctuation),
            # Semicolon (for subqueries)
            (r";", Punctuation),
            # Comma
            (r",", Punctuation),
            # Unquoted identifiers (field names, dictionary names)
            (r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", Name),
        ],
        "multiline-comment": [
            (r"[^*/]+", Comment.Multiline),
            (r"/\*", Comment.Multiline, "#push"),
            (r"\*/", Comment.Multiline, "#pop"),
            (r"[*/]", Comment.Multiline),
        ],
        "quantifier": [
            (r"\s+", Whitespace),
            (r"\d+", Number.Integer),
            (r",", Punctuation),
            (r"\}", Punctuation, "#pop"),
        ],
    }
