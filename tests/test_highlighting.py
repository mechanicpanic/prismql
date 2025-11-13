"""Tests for PrismQL Pygments lexer."""

import pytest

# Skip tests if pygments not installed
pytest.importorskip("pygments")

from pygments import highlight
from pygments.formatters import NullFormatter
from pygments.lexers import get_lexer_by_name
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
)

from prismql.highlighting import PrismQLLexer


class TestPrismQLLexer:
    """Test PrismQL Pygments lexer."""

    def test_lexer_exists(self) -> None:
        """Test that lexer can be instantiated."""
        lexer = PrismQLLexer()
        assert lexer.name == "PrismQL"
        assert "prismql" in lexer.aliases
        assert "pql" in lexer.aliases

    def test_lexer_discoverable(self) -> None:
        """Test that Pygments can discover the lexer by name."""
        lexer = get_lexer_by_name("prismql")
        assert isinstance(lexer, PrismQLLexer)

        lexer = get_lexer_by_name("pql")
        assert isinstance(lexer, PrismQLLexer)

    def test_basic_query_tokens(self) -> None:
        """Test tokenization of basic query."""
        lexer = PrismQLLexer()
        query = "SELECT from(alice) INWINDOW 10"
        tokens = list(lexer.get_tokens(query))

        token_types = [t[0] for t in tokens if t[1].strip()]

        assert Keyword.Reserved in token_types  # SELECT
        assert Name.Builtin in token_types  # from
        assert Keyword in token_types  # INWINDOW
        assert Number.Integer in token_types  # 10

    def test_keywords_highlighted(self) -> None:
        """Test that keywords are properly highlighted."""
        lexer = PrismQLLexer()

        # Test various keywords
        keywords = [
            "SELECT",
            "INWIN",
            "WITHIN",
            "AND",
            "OR",
            "NOT",
            "AGGREGATE",
            "GROUP BY",
        ]

        for keyword in keywords:
            tokens = list(lexer.get_tokens(keyword))
            token_types = [t[0] for t in tokens if t[1].strip()]
            assert any(
                t in (Keyword, Keyword.Reserved, Operator.Word) for t in token_types
            ), f"Keyword {keyword} not highlighted"

    def test_functions_highlighted(self) -> None:
        """Test that functions are properly highlighted."""
        lexer = PrismQLLexer()

        # Fluent syntax functions
        fluent_funcs = [
            "contains",
            "from",
            "is_question",
            "mentions_user",
            "mentions_date",
        ]

        for func in fluent_funcs:
            tokens = list(lexer.get_tokens(f"{func}()"))
            token_types = [t[0] for t in tokens if t[1].strip()]
            assert Name.Builtin in token_types, f"Function {func} not highlighted"

    def test_strings_highlighted(self) -> None:
        """Test that strings are properly highlighted."""
        lexer = PrismQLLexer()

        # Double-quoted string
        tokens = list(lexer.get_tokens('"alice"'))
        assert any(t[0] == String.Double for t in tokens)

        # Single-quoted string
        tokens = list(lexer.get_tokens("'bob'"))
        assert any(t[0] == String.Single for t in tokens)

    def test_variables_highlighted(self) -> None:
        """Test that pattern variables are properly highlighted."""
        lexer = PrismQLLexer()

        tokens = list(lexer.get_tokens("$user"))
        token_types = [t[0] for t in tokens if t[1].strip()]
        assert Name.Variable in token_types

    def test_numbers_highlighted(self) -> None:
        """Test that numbers are properly highlighted."""
        lexer = PrismQLLexer()

        tokens = list(lexer.get_tokens("42"))
        token_types = [t[0] for t in tokens if t[1].strip()]
        assert Number.Integer in token_types

    def test_comments_highlighted(self) -> None:
        """Test that comments are properly highlighted."""
        lexer = PrismQLLexer()

        # Single-line comment with --
        tokens = list(lexer.get_tokens("-- this is a comment"))
        assert any(t[0] == Comment.Single for t in tokens)

        # Single-line comment with //
        tokens = list(lexer.get_tokens("// this is a comment"))
        assert any(t[0] == Comment.Single for t in tokens)

        # Multi-line comment
        tokens = list(lexer.get_tokens("/* multi\nline\ncomment */"))
        assert any(t[0] == Comment.Multiline for t in tokens)

    def test_quantifiers_highlighted(self) -> None:
        """Test that quantifiers are properly highlighted."""
        lexer = PrismQLLexer()

        # Exact quantifier
        tokens = list(lexer.get_tokens("{3}"))
        token_types = [t[0] for t in tokens if t[1].strip()]
        assert Punctuation in token_types
        assert Number.Integer in token_types

    def test_complex_query(self) -> None:
        """Test tokenization of complex query."""
        lexer = PrismQLLexer()
        query = """
        -- Find customer support escalations
        SELECT
            (SELECT from(customer), contains(problems) INWINDOW 3) ;
            (SELECT from(support), contains(solutions) INWINDOW 3)
        INWINDOW 15
        GROUP BY customer
        AGGREGATE count()
        """

        # Should not raise any errors
        tokens = list(lexer.get_tokens(query))
        assert len(tokens) > 0

        # Verify some key tokens are present
        token_types = [t[0] for t in tokens]
        assert Comment.Single in token_types  # Comment
        assert Keyword.Reserved in token_types  # SELECT
        assert Name.Builtin in token_types  # from/contains
        assert Punctuation in token_types  # Parentheses

    def test_highlighting_with_formatter(self) -> None:
        """Test that highlighting works with formatters."""
        lexer = PrismQLLexer()
        query = "SELECT from(alice), is_question() INWINDOW 3"

        # Use NullFormatter (no color codes, just text)
        result = highlight(query, lexer, NullFormatter())
        assert result.strip() == query.strip()

    def test_case_insensitive_keywords(self) -> None:
        """Test that keywords are case-insensitive."""
        lexer = PrismQLLexer()

        # Test different cases
        for keyword in ["SELECT", "select", "Select", "SeLeCt"]:
            tokens = list(lexer.get_tokens(keyword))
            token_types = [t[0] for t in tokens if t[1].strip()]
            assert Keyword.Reserved in token_types

    def test_legacy_functions(self) -> None:
        """Test that legacy functions are highlighted differently."""
        lexer = PrismQLLexer()

        # Legacy function should be highlighted as Builtin.Pseudo
        tokens = list(lexer.get_tokens("haswordofdict()"))
        token_types = [t[0] for t in tokens if t[1].strip()]
        assert Name.Builtin.Pseudo in token_types

    def test_positional_operators(self) -> None:
        """Test that positional operators are highlighted."""
        lexer = PrismQLLexer()

        operators = ["FOLLOWED_BY", "PRECEDED_BY", "NOT_FOLLOWED_BY", "NOT_PRECEDED_BY"]

        for op in operators:
            tokens = list(lexer.get_tokens(op))
            token_types = [t[0] for t in tokens if t[1].strip()]
            assert Operator.Word in token_types, f"Operator {op} not highlighted"

    def test_time_units(self) -> None:
        """Test that time units are highlighted."""
        lexer = PrismQLLexer()

        units = ["SECONDS", "MINUTES", "HOURS", "DAYS", "WEEKS"]

        for unit in units:
            tokens = list(lexer.get_tokens(unit))
            token_types = [t[0] for t in tokens if t[1].strip()]
            assert Keyword.Type in token_types, f"Time unit {unit} not highlighted"
