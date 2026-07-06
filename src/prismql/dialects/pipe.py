"""The pipe dialect: a pipeline-style surface syntax lowering to PrismQL IR.

A hand-written tokenizer + recursive-descent parser producing
:mod:`prismql.ir.nodes` directly — no ANTLR, no transpiling through the
SQL-flavored surface. Both dialects meet at the IR, so semantics are shared
by construction.

Surface summary::

    from(alice) and contains(greet) |> within(10)
    from(alice) + contains(solutions){2} as pair |> within(10)
    from($u) ~> from($u) |> during(1h)
    from(a) ~>(3) from(b) ~>(1h) from(c)
    contains(question) !~> from(support) |> within(5)
    [from(a) ~> from(b) |> within(3)] ~>(10) [contains(x)]
    contains(crisis) |> group(day(timestamp)) |> count()
    ... |> before("2024-01-01") |> sort(ts, desc) |> top(5) |> skip(2)

Design rules:

- ``+`` is the SQL comma: unordered co-occurrence restrictions.
- Arrows: ``~>`` FOLLOWED_BY, ``<~`` PRECEDED_BY, ``!~>`` NOT_FOLLOWED_BY,
  ``!<~`` NOT_PRECEDED_BY. An arrow takes an optional window argument:
  ``~>(5)`` positional (message distance), ``~>(1h)`` temporal.
- A trailing ``|> within(n)`` / ``|> during(t)`` attaches to the final link
  of a chain when that link is windowless (the SQL grammar's greedy
  attachment, which the executor distributes to all windowless links);
  otherwise it becomes the body-level window — byte-compatible with what the
  SQL surface can express, quirks included.
- ``[ ... ]`` brackets delimit subqueries (whole-group semantics); ``( ... )``
  parens are precedence grouping only. Positional links between subqueries
  must carry a positional window: ``[a] ~>(10) [b]``.
- No legacy operators: the pipe dialect starts clean.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from ..aggregators.types import AggregationFunction
from ..exceptions import PrismQLSyntaxError
from ..ir.nodes import (
    AbsoluteTs,
    And,
    Contains,
    ContainsPhrase,
    ContainsTokens,
    Expr,
    FieldMatch,
    HasFeature,
    IsQuestion,
    LimitClause,
    Literal,
    MentionsEntity,
    MentionsUser,
    NamedRestriction,
    Not,
    Or,
    OrderBy,
    Query,
    RelativeTs,
    RestrictionsRow,
    SequenceLink,
    SubqueryChain,
    SubqueryContinuation,
    TemporalFilter,
    Term,
    TimestampSpec,
    TimeValue,
    Variable,
    Wildcard,
    normalize_time_unit,
)

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
    (?P<WS>\s+)
  | (?P<PIPE>\|>)
  | (?P<NFB>!~>)
  | (?P<NPB>!<~)
  | (?P<FB>~>)
  | (?P<PB><~)
  | (?P<PLUS>\+)
  | (?P<LPAREN>\()
  | (?P<RPAREN>\))
  | (?P<LBRACKET>\[)
  | (?P<RBRACKET>\])
  | (?P<LBRACE>\{)
  | (?P<RBRACE>\})
  | (?P<COMMA>,)
  | (?P<STRING>"[^"]*"|'[^']*')
  | (?P<TIME>\d+\s*(?:seconds?|minutes?|hours?|days?|weeks?|[smhdw])\b)
  | (?P<INT>\d+)
  | (?P<VARIABLE>\$[A-Za-z_][A-Za-z0-9_]*)
  | (?P<STAR>\*)
  | (?P<NAME>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE | re.IGNORECASE,
)

_TIME_SPLIT_RE = re.compile(r"(\d+)\s*([A-Za-z]+)")

ARROW_OPS = {
    "FB": "FOLLOWED_BY",
    "PB": "PRECEDED_BY",
    "NFB": "NOT_FOLLOWED_BY",
    "NPB": "NOT_PRECEDED_BY",
}

_KEYWORDS = {"and", "or", "not", "as", "ago", "asc", "desc"}


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    pos: int


def _tokenize(source: str) -> list[_Token]:
    tokens: list[_Token] = []
    pos = 0
    while pos < len(source):
        m = _TOKEN_RE.match(source, pos)
        if m is None:
            raise PrismQLSyntaxError(
                f"Unexpected character {source[pos]!r} in pipe query",
                line=1,
                column=pos,
            )
        kind = m.lastgroup or ""
        text = m.group()
        pos = m.end()
        if kind == "WS":
            continue
        if kind == "NAME" and text.lower() in _KEYWORDS:
            kind = text.upper()
        tokens.append(_Token(kind, text, m.start()))
    tokens.append(_Token("EOF", "", len(source)))
    return tokens


# ---------------------------------------------------------------------------
# Condition table
# ---------------------------------------------------------------------------

_NULLARY_CONDITIONS: dict[str, Callable[[], Expr]] = {
    "is_question": IsQuestion,
    "mentions_date": lambda: MentionsEntity("DATE"),
    "mentions_time": lambda: MentionsEntity("TIME"),
    "mentions_place": lambda: MentionsEntity("GPE"),
    "mentions_org": lambda: MentionsEntity("ORG"),
    "contains_link": lambda: MentionsEntity("URL"),
}

_TIME_UNIT_WORDS = {
    "s",
    "second",
    "seconds",
    "m",
    "minute",
    "minutes",
    "h",
    "hour",
    "hours",
    "d",
    "day",
    "days",
    "w",
    "week",
    "weeks",
    "month",
    "months",
    "year",
    "years",
}

_GROUP_FUNCS = {
    "hour": "HOURS",
    "hours": "HOURS",
    "day": "DAYS",
    "days": "DAYS",
    "week": "WEEKS",
    "weeks": "WEEKS",
    "month": "MONTHS",
    "months": "MONTHS",
    "year": "YEARS",
    "years": "YEARS",
}

_AGG_STAGES = {
    "count": AggregationFunction.COUNT,
    "count_distinct": AggregationFunction.COUNT_DISTINCT,
    "distinct": AggregationFunction.DISTINCT,
    "sum": AggregationFunction.SUM,
    "avg": AggregationFunction.AVG,
    "min": AggregationFunction.MIN,
    "max": AggregationFunction.MAX,
}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class _PipeParser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens = _tokenize(source)
        self.i = 0

    # -- token helpers ------------------------------------------------------

    def peek(self, offset: int = 0) -> _Token:
        return self.tokens[min(self.i + offset, len(self.tokens) - 1)]

    def next(self) -> _Token:
        tok = self.tokens[self.i]
        if tok.kind != "EOF":
            self.i += 1
        return tok

    def accept(self, kind: str) -> _Token | None:
        if self.peek().kind == kind:
            return self.next()
        return None

    def expect(self, kind: str, what: str) -> _Token:
        tok = self.peek()
        if tok.kind != kind:
            raise PrismQLSyntaxError(
                f"Expected {what}, got {tok.text or 'end of query'!r}",
                line=1,
                column=tok.pos,
            )
        return self.next()

    def error(self, message: str) -> PrismQLSyntaxError:
        tok = self.peek()
        return PrismQLSyntaxError(message, line=1, column=tok.pos)

    # -- entry --------------------------------------------------------------

    def parse(self) -> Query:
        query = self.parse_query()
        if self.peek().kind != "EOF":
            raise self.error(f"Unexpected {self.peek().text!r} after query")
        return query

    def parse_query(self) -> Query:
        source = self.parse_source()
        query = Query(source=source)
        while self.accept("PIPE"):
            query = self.parse_stage(query)
        return query

    # -- source: subquery chain or restrictions row -------------------------

    def parse_source(self) -> RestrictionsRow | SubqueryChain:
        if self.peek().kind == "LBRACKET":
            return self.parse_subquery_chain()
        return self.parse_row()

    def parse_subquery_chain(self) -> SubqueryChain:
        head = self.parse_bracketed_query()
        continuations: list[SubqueryContinuation] = []
        while True:
            if self.accept("PLUS"):
                continuations.append(
                    SubqueryContinuation(query=self.parse_bracketed_query())
                )
                continue
            arrow = self.peek().kind
            if arrow in ARROW_OPS:
                self.next()
                window = self.parse_arrow_window()
                if not isinstance(window, int):
                    raise self.error(
                        "A positional link between [subqueries] requires a "
                        "positional window, e.g. [a] ~>(10) [b]"
                    )
                continuations.append(
                    SubqueryContinuation(
                        query=self.parse_bracketed_query(),
                        op=ARROW_OPS[arrow].replace("_", ""),
                        window=window,
                    )
                )
                continue
            break
        return SubqueryChain(head, tuple(continuations))

    def parse_bracketed_query(self) -> Query:
        self.expect("LBRACKET", "'[' opening a subquery")
        query = self.parse_query()
        self.expect("RBRACKET", "']' closing the subquery")
        return query

    def parse_row(self) -> RestrictionsRow:
        items = [self.parse_element()]
        while self.accept("PLUS"):
            items.append(self.parse_element())
        return RestrictionsRow(tuple(items))

    def parse_element(self) -> NamedRestriction:
        expr = self.parse_chain()
        min_count = 1
        max_count: int | None = 1
        if self.accept("LBRACE"):
            min_count = int(self.expect("INT", "a count inside {}").text)
            max_count = min_count
            if self.accept("COMMA"):
                max_count = int(self.next().text) if self.peek().kind == "INT" else None
            self.expect("RBRACE", "'}' closing the quantifier")
        name = None
        if self.accept("AS"):
            tok = self.peek()
            if tok.kind == "STRING":
                name = self.next().text[1:-1]
            elif tok.kind == "NAME":
                name = self.next().text
            else:
                raise self.error("Expected a name after 'as'")
        return NamedRestriction(
            expr=expr, min_count=min_count, max_count=max_count, name=name
        )

    # -- expression layers ---------------------------------------------------

    def parse_chain(self) -> Expr:
        expr = self.parse_or()
        while self.peek().kind in ARROW_OPS:
            op = ARROW_OPS[self.next().kind]
            window = self.parse_arrow_window()
            rhs = self.parse_or()
            expr = SequenceLink(op, expr, rhs, window)
        return expr

    def parse_arrow_window(self) -> int | tuple[int, str] | None:
        """Optional ``(5)`` or ``(1h)`` immediately after an arrow."""
        if self.peek().kind != "LPAREN":
            return None
        # Only treat the parens as a window when they hold a number/time;
        # otherwise they open the rhs expression (e.g. ``~> (a or b)``).
        if self.peek(1).kind not in ("INT", "TIME"):
            return None
        self.next()  # consume '('
        window = self.parse_window_value()
        self.expect("RPAREN", "')' closing the window")
        return window

    def parse_window_value(self) -> int | tuple[int, str]:
        tok = self.peek()
        if tok.kind == "TIME":
            self.next()
            m = _TIME_SPLIT_RE.fullmatch(tok.text.strip())
            assert m is not None
            return (int(m.group(1)), normalize_time_unit(m.group(2)))
        if tok.kind == "INT":
            value = int(self.next().text)
            if (
                self.peek().kind == "NAME"
                and self.peek().text.lower() in _TIME_UNIT_WORDS
            ):
                return (value, normalize_time_unit(self.next().text))
            return value
        raise self.error("Expected a window: messages (5) or time (1h)")

    def parse_or(self) -> Expr:
        expr = self.parse_and()
        while self.accept("OR"):
            expr = Or(expr, self.parse_and())
        return expr

    def parse_and(self) -> Expr:
        expr = self.parse_not()
        while self.accept("AND"):
            expr = And(expr, self.parse_not())
        return expr

    def parse_not(self) -> Expr:
        if self.accept("NOT"):
            return Not(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Expr:
        if self.accept("LPAREN"):
            expr = self.parse_chain()
            self.expect("RPAREN", "')'")
            return expr
        if self.peek().kind == "NAME":
            return self.parse_condition()
        raise self.error(
            f"Expected a condition, got {self.peek().text or 'end of query'!r}"
        )

    # -- conditions ----------------------------------------------------------

    def parse_condition(self) -> Expr:  # noqa: C901 - one branch per condition
        name = self.next().text.lower()
        self.expect("LPAREN", f"'(' after {name}")

        if name in _NULLARY_CONDITIONS:
            self.expect("RPAREN", f"')' — {name} takes no arguments")
            return _NULLARY_CONDITIONS[name]()

        if name in ("contains", "contains_tokens"):
            term = self.parse_term()
            self.expect("RPAREN", "')'")
            return Contains(term) if name == "contains" else ContainsTokens(term)

        if name == "contains_phrase":
            tok = self.expect("STRING", 'a quoted phrase: contains_phrase("...")')
            self.expect("RPAREN", "')'")
            return ContainsPhrase(tok.text[1:-1])

        if name == "from":
            term = self.parse_term()
            self.expect("RPAREN", "')'")
            return FieldMatch("user", term, exact=True)

        if name == "mentions_user":
            tok = self.peek()
            if tok.kind in ("NAME", "STAR", "VARIABLE", "INT"):
                self.next()
                user = tok.text
            elif tok.kind == "STRING":
                self.next()
                user = tok.text[1:-1]
            else:
                raise self.error("Expected a username in mentions_user()")
            self.expect("RPAREN", "')'")
            return MentionsUser(user)

        if name in ("has_feature", "labeled_as"):
            tok = self.expect("NAME", f"a feature name in {name}()")
            self.expect("RPAREN", "')'")
            return HasFeature(tok.text)

        if name == "field":
            fname = self.expect("NAME", "a field name in field()").text
            self.expect("COMMA", "',' between field name and value")
            value = self.parse_term(allow_quoted=True)
            exact = True
            if self.accept("COMMA"):
                mode = self.expect("NAME", "'exact' or 'partial'").text.lower()
                if mode == "partial":
                    exact = False
                elif mode != "exact":
                    raise self.error(
                        f"Unknown field() matcher {mode!r}: use 'exact' or 'partial'"
                    )
            self.expect("RPAREN", "')'")
            return FieldMatch(fname, value, exact=exact)

        raise self.error(f"Unknown condition {name!r}")

    def parse_term(self, allow_quoted: bool = False) -> Term:
        tok = self.peek()
        if tok.kind == "STAR":
            self.next()
            return Wildcard()
        if tok.kind == "VARIABLE":
            self.next()
            return Variable(tok.text[1:])
        if tok.kind in ("NAME", "INT"):
            self.next()
            return Literal(tok.text)
        if tok.kind == "TIME":
            # e.g. from(2d) is nonsense, but a bare NAME like '2d' tokenizes
            # as TIME; treat it as a literal for fidelity with the SQL surface.
            self.next()
            return Literal(tok.text)
        if allow_quoted and tok.kind == "STRING":
            self.next()
            return Literal(tok.text[1:-1])
        raise self.error(f"Expected a value, got {tok.text or 'end of query'!r}")

    # -- pipe stages ---------------------------------------------------------

    def parse_stage(self, query: Query) -> Query:  # noqa: C901
        tok = self.expect("NAME", "a stage name after |>")
        stage = tok.text.lower()
        self.expect("LPAREN", f"'(' after |> {stage}")

        if stage == "within":
            window = self.parse_window_value()
            self.expect("RPAREN", "')'")
            if not isinstance(window, int):
                raise self.error(
                    "within() takes a message count; use during() for time"
                )
            return self._attach_window(query, window)

        if stage == "during":
            window = self.parse_window_value()
            self.expect("RPAREN", "')'")
            if isinstance(window, int):
                raise self.error(
                    "during() takes a time span like 1h or 2 days; "
                    "use within() for message counts"
                )
            return self._attach_window(query, window)

        if stage in ("before", "after"):
            ts = self.parse_timestamp()
            self.expect("RPAREN", "')'")
            tf = (
                TemporalFilter("before", end=ts)
                if stage == "before"
                else TemporalFilter("after", start=ts)
            )
            return _replace(query, temporal_filter=tf)

        if stage == "between":
            start = self.parse_timestamp()
            self.expect("COMMA", "',' between the two timestamps")
            end = self.parse_timestamp()
            self.expect("RPAREN", "')'")
            return _replace(
                query, temporal_filter=TemporalFilter("between", start=start, end=end)
            )

        if stage == "group":
            fields = [self.parse_group_field()]
            while self.accept("COMMA"):
                fields.append(self.parse_group_field())
            self.expect("RPAREN", "')'")
            return _replace(query, group_by=tuple(fields))

        if stage in _AGG_STAGES:
            func = _AGG_STAGES[stage]
            field = None
            if func != AggregationFunction.COUNT:
                field = self.expect("NAME", f"a field name in {stage}()").text
            self.expect("RPAREN", "')'")
            return _replace(query, aggregations=query.aggregations + ((func, field),))

        if stage == "sort":
            fields = []
            reverse = False
            while True:
                tok = self.peek()
                if tok.kind == "NAME" and tok.text.lower() not in ("asc", "desc"):
                    fields.append(self.next().text)
                elif tok.kind in ("ASC", "DESC"):
                    if self.next().kind == "DESC":
                        reverse = True
                else:
                    raise self.error("Expected a field name (or asc/desc) in sort()")
                if not self.accept("COMMA"):
                    break
            self.expect("RPAREN", "')'")
            return _replace(query, order_by=OrderBy(tuple(fields), reverse=reverse))

        if stage == "top":
            n = int(self.expect("INT", "a count in top()").text)
            self.expect("RPAREN", "')'")
            offset = query.limit.offset if query.limit else 0
            return _replace(query, limit=LimitClause(n, offset))

        if stage == "skip":
            n = int(self.expect("INT", "a count in skip()").text)
            self.expect("RPAREN", "')'")
            if query.limit is None:
                raise self.error("skip() requires a top(n) stage before it")
            return _replace(query, limit=LimitClause(query.limit.limit, n))

        raise self.error(f"Unknown stage |> {stage}")

    def parse_group_field(self) -> str:
        tok = self.expect("NAME", "a field or time bucket in group()")
        if tok.text.lower() in _GROUP_FUNCS and self.peek().kind == "LPAREN":
            self.next()
            field = self.expect("NAME", f"a field name in {tok.text}()").text
            self.expect("RPAREN", "')'")
            return f"__{_GROUP_FUNCS[tok.text.lower()]}__({field})"
        return tok.text

    def parse_timestamp(self) -> TimestampSpec:
        tok = self.peek()
        if tok.kind == "STRING":
            self.next()
            return AbsoluteTs(tok.text[1:-1])
        if tok.kind in ("TIME", "INT"):
            window = self.parse_window_value()
            if isinstance(window, int):
                raise self.error(
                    "A relative timestamp needs a unit, e.g. before(2d ago)"
                )
            self.expect("AGO", "'ago' after the time span")
            return RelativeTs(window[0], window[1])
        raise self.error(
            'Expected a timestamp: a quoted date ("2024-01-01") or "2d ago"'
        )

    # -- trailing window attachment -------------------------------------------

    def _attach_window(self, query: Query, window: int | tuple[int, str]) -> Query:
        """Reproduce the SQL grammar's greedy window attachment.

        When the source is a single chain whose final link is windowless, the
        window belongs to that link (and the executor distributes it to every
        windowless inner link). Otherwise it is the body-level window.
        """
        source = query.source
        if (
            isinstance(source, RestrictionsRow)
            and len(source.items) == 1
            and isinstance(source.items[0].expr, SequenceLink)
            and source.items[0].expr.window is None
        ):
            item = source.items[0]
            link = item.expr
            assert isinstance(link, SequenceLink)
            new_link = SequenceLink(link.op, link.lhs, link.rhs, window)
            new_item = NamedRestriction(
                expr=new_link,
                min_count=item.min_count,
                max_count=item.max_count,
                name=item.name,
            )
            return _replace(query, source=RestrictionsRow((new_item,)))
        if isinstance(window, int):
            return _replace(query, positional_window=window)
        return _replace(query, temporal_window=TimeValue(window[0], window[1]))


def _replace(query: Query, **changes: object) -> Query:
    import dataclasses

    return dataclasses.replace(query, **changes)  # type: ignore[arg-type]


def parse_pipe(source: str) -> Query:
    """Parse a pipe-dialect query into a PrismQL IR :class:`Query`."""
    return _PipeParser(source).parse()
