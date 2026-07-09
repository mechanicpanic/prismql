"""Tests for the pipe dialect (pipeline-style surface syntax).

The strongest assertions here are *IR equality*: a pipe query and its classic
SQL-flavored equivalent must lower to the exact same frozen-dataclass IR tree,
which proves identical semantics without executing anything. Execution and
error-path tests back that up.
"""

import warnings

import pytest
from antlr4 import CommonTokenStream, InputStream

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.dialects.pipe import parse_pipe
from prismql.exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from prismql.grammar.generated.PrismQLLexer import PrismQLLexer
from prismql.grammar.generated.PrismQLParser import PrismQLParser
from prismql.ir.lower import lower_query
from prismql.validator import QueryValidator


def lower_classic(query: str):
    parser = PrismQLParser(CommonTokenStream(PrismQLLexer(InputStream(query))))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return lower_query(parser.parse().query())


# Each pair must produce the EXACT same IR tree.
EQUIVALENT = [
    ("from(alice)", "SELECT from(alice)"),
    (
        "from(alice) and contains(greet) |> within(10)",
        "SELECT from(alice) AND contains(greet) INWINDOW 10",
    ),
    (
        "from(alice) + contains(sol) |> within(10)",
        "SELECT from(alice), contains(sol) INWINDOW 10",
    ),
    (
        "from(alice){2} as pair + contains(sol) |> within(10)",
        "SELECT from(alice){2} AS 'pair', contains(sol) INWINDOW 10",
    ),
    (
        "from(alice){2,} |> within(5)",
        "SELECT from(alice){2,} INWINDOW 5",
    ),
    (
        "from(alice){2,4} |> within(5)",
        "SELECT from(alice){2,4} INWINDOW 5",
    ),
    (
        "not from(alice) or is_question()",
        "SELECT NOT from(alice) OR is_question()",
    ),
    (
        "from(a) ~> from(b) ~> from(c) |> within(10)",
        "SELECT from(a) FOLLOWED_BY from(b) FOLLOWED_BY from(c) INWINDOW 10",
    ),
    (
        "from(a) ~>(3) from(b) ~>(1h) from(c)",
        "SELECT from(a) FOLLOWED_BY from(b) INWINDOW 3 "
        "FOLLOWED_BY from(c) DURING 1 hour",
    ),
    (
        "from($u) ~> from($u) |> during(1h)",
        "SELECT from($u) FOLLOWED_BY from($u) DURING 1 hour",
    ),
    (
        "from(a) <~ from(b) |> within(4)",
        "SELECT from(a) PRECEDED_BY from(b) INWINDOW 4",
    ),
    (
        "contains(question) !~> from(support) |> within(5)",
        "SELECT contains(question) NOT_FOLLOWED_BY from(support) INWINDOW 5",
    ),
    (
        "from(a) !<~ from(b) |> within(5)",
        "SELECT from(a) NOT_PRECEDED_BY from(b) INWINDOW 5",
    ),
    (
        "(from(a) or from(b)) ~> contains(x) |> within(6)",
        "SELECT (from(a) OR from(b)) FOLLOWED_BY contains(x) INWINDOW 6",
    ),
    (
        "field(ticker, AAPL) ~> field(ticker, AAPL) |> during(1w)",
        "SELECT field(ticker, AAPL) FOLLOWED_BY field(ticker, AAPL) DURING 1 w",
    ),
    (
        'field(source, "a b", partial)',
        "SELECT field(source, 'a b', partial)",
    ),
    (
        'contains_phrase("thank you")',
        "SELECT contains_phrase('thank you')",
    ),
    (
        "contains_tokens(crisis)",
        "SELECT contains_tokens(crisis)",
    ),
    (
        "mentions_user(bob) + mentions_org()",
        "SELECT mentions_user(bob), mentions_org()",
    ),
    (
        "has_feature(action_items)",
        "SELECT has_feature(action_items)",
    ),
    (
        "contains(*)",
        "SELECT contains(*)",
    ),
    (
        "[from(a)] + [from(b)] |> within(20)",
        "SELECT (SELECT from(a)); (SELECT from(b)) INWINDOW 20",
    ),
    (
        "[from(a) ~> from(b) |> within(3)] ~>(10) [contains(x)]",
        "SELECT (SELECT from(a) FOLLOWED_BY from(b) INWINDOW 3) "
        "FOLLOWED_BY (SELECT contains(x)) INWINDOW 10",
    ),
    (
        "contains(crisis) |> group(day(timestamp)) |> count()",
        "SELECT contains(crisis) GROUP BY DAY(timestamp) AGGREGATE COUNT()",
    ),
    (
        "contains(crisis) |> group(user) |> sum(price)",
        "SELECT contains(crisis) GROUP BY user AGGREGATE SUM(price)",
    ),
    (
        "from(*) |> sort(ts, desc) |> top(5) |> skip(2)",
        "SELECT from(*) ORDER BY ts DESC LIMIT 5 OFFSET 2",
    ),
    (
        'from(alice) |> before("2024-01-01")',
        "SELECT from(alice) BEFORE('2024-01-01')",
    ),
    (
        "from(alice) |> after(2d ago)",
        "SELECT from(alice) AFTER(2 d AGO)",
    ),
    (
        'from(alice) |> between("2024-01-01", "2024-02-01")',
        "SELECT from(alice) BETWEEN('2024-01-01', '2024-02-01')",
    ),
    (
        "from(alice) |> during(90s)",
        "SELECT from(alice) DURING 90 seconds",
    ),
]


class TestIREquivalence:
    @pytest.mark.parametrize(
        ("pipe", "classic"), EQUIVALENT, ids=[p for p, _ in EQUIVALENT]
    )
    def test_pipe_and_classic_lower_to_identical_ir(self, pipe, classic):
        assert parse_pipe(pipe) == lower_classic(classic)


@pytest.fixture
def engine():
    docs = [
        {"id": 1, "user": "alice", "text": "hello world", "timestamp": 1000},
        {"id": 2, "user": "bob", "text": "hi alice", "timestamp": 1060},
        {"id": 3, "user": "alice", "text": "how are you?", "timestamp": 1120},
        {"id": 4, "user": "carol", "text": "fine thanks", "timestamp": 1180},
        {"id": 5, "user": "bob", "text": "great, hello again", "timestamp": 1240},
    ]
    return PrismQLEngine(
        MemoryBackend(docs), user_dictionaries={"greet": ["hello", "hi"]}
    )


class TestExecution:
    def test_autodetect_pipe(self, engine):
        assert engine.execute("from(alice)") == [[1], [3]]

    def test_autodetect_classic(self, engine):
        assert engine.execute("SELECT from(alice)") == [[1], [3]]

    def test_pipe_equals_classic_results(self, engine):
        pipe = engine.execute("from(alice) ~> from(bob) |> within(2)")
        classic = engine.execute("SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2")
        assert pipe == classic == [[1, 2], [3, 5]]

    def test_pipe_dictionary_and_bool(self, engine):
        pipe = engine.execute("contains(greet) and from(bob)")
        classic = engine.execute("SELECT contains(greet) AND from(bob)")
        assert pipe == classic

    def test_pipe_aggregation(self, engine):
        result = engine.execute("from(alice) |> count()")
        classic = engine.execute("SELECT from(alice) AGGREGATE COUNT()")
        assert result.value == classic.value

    def test_explicit_dialect_param(self, engine):
        assert engine.execute("from(alice)", dialect="pipe") == [[1], [3]]
        with pytest.raises(PrismQLSyntaxError):
            engine.execute("from(alice)", dialect="classic")

    def test_validate_both_dialects(self, engine):
        assert engine.validate("from(alice) |> within(5)")
        assert engine.validate("SELECT from(alice) INWINDOW 5")

    def test_named_results_via_pipe(self, engine):
        result = engine.execute("from(alice) as sender + from(bob) |> within(3)")
        assert result.pattern_names == ["sender", None]


class TestPipeErrors:
    def test_unknown_condition(self):
        with pytest.raises(PrismQLSyntaxError, match="Unknown condition"):
            parse_pipe("frobnicate(x)")

    def test_unknown_stage(self):
        with pytest.raises(PrismQLSyntaxError, match="Unknown stage"):
            parse_pipe("from(a) |> yeet(5)")

    def test_within_rejects_time(self):
        with pytest.raises(
            PrismQLSyntaxError, match="within\\(\\) takes a message count"
        ):
            parse_pipe("from(a) |> within(1h)")

    def test_during_rejects_bare_int(self):
        with pytest.raises(PrismQLSyntaxError, match="during\\(\\) takes a time span"):
            parse_pipe("from(a) |> during(5)")

    def test_subquery_link_requires_window(self):
        with pytest.raises(PrismQLSyntaxError, match="requires a positional window"):
            parse_pipe("[from(a)] ~> [from(b)]")

    def test_skip_requires_top(self):
        with pytest.raises(PrismQLSyntaxError, match="skip\\(\\) requires"):
            parse_pipe("from(a) |> skip(2)")

    def test_trailing_garbage(self):
        with pytest.raises(PrismQLSyntaxError):
            parse_pipe("from(a) banana")

    def test_windowless_chain_teachable_error(self, engine):
        # parses fine; the executor raises the same teachable error as classic
        with pytest.raises(PrismQLRuntimeError, match="missing a window constraint"):
            engine.execute("from(alice) ~> from(bob)")

    def test_positional_subqueries_reject_trailing_window(self, engine):
        with pytest.raises(PrismQLRuntimeError, match="cannot take a trailing"):
            engine.execute("[from(alice)] ~>(5) [from(bob)] |> within(10)")


class TestWindowAttachment:
    def test_trailing_within_attaches_to_windowless_final_link(self):
        ir = parse_pipe("from(a) ~> from(b) |> within(7)")
        item = ir.source.items[0]
        assert item.expr.window == 7
        assert ir.positional_window is None

    def test_trailing_within_on_windowed_chain_becomes_body_window(self):
        ir = parse_pipe("from(a) ~>(2) from(b) |> within(7)")
        item = ir.source.items[0]
        assert item.expr.window == 2
        assert ir.positional_window == 7

    def test_trailing_during_on_row_is_body_temporal(self):
        ir = parse_pipe("from(a) + from(b) |> during(1h)")
        assert ir.temporal_window is not None
        # units are canonicalized in the IR so dialects compare equal
        assert (ir.temporal_window.value, ir.temporal_window.unit) == (1, "hours")


class TestValidatorPipeDialect:
    """QueryValidator understands the pipe surface (dialect='auto')."""

    def _validator(self) -> QueryValidator:
        return QueryValidator(user_dictionaries={"greetings": ["hello", "hi"]})

    def test_valid_pipe_query(self):
        result = self._validator().validate("from(alice) ~> from(bob) |> within(3)")
        assert result.valid
        assert not result.errors

    def test_auto_detect_routes_classic(self):
        result = self._validator().validate("SELECT from(alice)")
        assert result.valid

    def test_explicit_dialect_pipe(self):
        result = self._validator().validate("from(alice)", dialect="pipe")
        assert result.valid

    def test_pipe_syntax_error(self):
        result = self._validator().validate("from(alice) ~>")
        assert not result.valid
        assert any(i.code == "SYNTAX_ERROR" for i in result.errors)

    def test_undefined_dictionary(self):
        result = self._validator().validate("contains(nope)")
        assert not result.valid
        assert any(i.code == "UNDEFINED_DICTIONARY" for i in result.errors)

    def test_defined_dictionary_passes(self):
        result = self._validator().validate("contains(greetings)")
        assert result.valid

    def test_wildcard_dictionary_not_flagged(self):
        result = self._validator().validate("contains(*)")
        assert result.valid

    def test_undefined_dictionary_inside_subquery(self):
        result = self._validator().validate("[contains(nope)] + [from(a)] |> within(5)")
        assert not result.valid
        assert any(i.code == "UNDEFINED_DICTIONARY" for i in result.errors)

    def test_windowless_arrow_is_error(self):
        result = self._validator().validate("from(a) ~> from(b)")
        assert not result.valid
        assert any(i.code == "MISSING_WINDOW_CONSTRAINT" for i in result.errors)

    def test_inline_arrow_window_passes(self):
        result = self._validator().validate("from(a) ~>(3) from(b)")
        assert result.valid

    def test_trailing_within_covers_chain(self):
        result = self._validator().validate(
            "from(a) ~> from(b) ~> from(c) |> within(10)"
        )
        assert result.valid

    def test_trailing_during_covers_chain(self):
        result = self._validator().validate("from($u) ~> from($u) |> during(1h)")
        assert result.valid

    def test_mid_chain_window_final_windowless_is_error(self):
        result = self._validator().validate("from(a) ~>(3) from(b) ~> from(c)")
        assert not result.valid
        assert any(i.code == "MISSING_WINDOW_CONSTRAINT" for i in result.errors)

    def test_large_window_warns_but_valid(self):
        result = self._validator().validate("from(a) + from(b) |> within(200)")
        assert result.valid
        assert any(i.code == "LARGE_WINDOW" for i in result.warnings)

    def test_classic_parity_windowless_sequence(self):
        # The same mistake on both surfaces must fail the same way.
        v = self._validator()
        classic = v.validate("SELECT from(a) FOLLOWED_BY from(b)")
        pipe = v.validate("from(a) ~> from(b)")
        assert not classic.valid and not pipe.valid

    def test_classic_parity_undefined_dictionary(self):
        v = self._validator()
        classic = v.validate("SELECT contains(nope)")
        pipe = v.validate("contains(nope)")
        assert not classic.valid and not pipe.valid


class TestResultEquality:
    """Aggregate/grouped results compare by value, so results from the two
    dialect paths (or two runs) can be asserted equal."""

    def test_aggregate_result_value_equality(self):
        from prismql.aggregators.types import AggregateResult, AggregationFunction

        a = AggregateResult(value=24, function=AggregationFunction.COUNT)
        b = AggregateResult(value=24, function=AggregationFunction.COUNT)
        c = AggregateResult(value=25, function=AggregationFunction.COUNT)
        assert a == b
        assert a != c
        assert a != "not a result"

    def test_grouped_result_value_equality(self):
        from prismql.aggregators.types import GroupedResult

        a = GroupedResult({"x": [[1, 2]]}, ["user"])
        b = GroupedResult({"x": [[1, 2]]}, ["user"])
        c = GroupedResult({"x": [[1, 3]]}, ["user"])
        assert a == b
        assert a != c

    def test_dialects_agree_on_aggregation(self):
        docs = [
            {"id": 1, "user": "alice", "text": "one"},
            {"id": 2, "user": "alice", "text": "two"},
            {"id": 3, "user": "bob", "text": "three"},
        ]
        engine = PrismQLEngine(MemoryBackend(docs))
        classic = engine.execute("SELECT from(alice) AGGREGATE count()")
        pipe = engine.execute("from(alice) |> count()")
        assert classic == pipe
