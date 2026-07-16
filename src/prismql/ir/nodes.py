"""PrismQL intermediate representation: pure-data query nodes.

The IR is the seam between surface syntax and execution. A lowering pass
(:mod:`prismql.ir.lower`) turns the ANTLR parse tree into these nodes; the
executor (:mod:`prismql.ir.executor`) evaluates them against a backend. The
nodes carry no behaviour and no references to ANTLR — a second surface syntax
or a programmatic builder can construct them directly.

Design notes (fidelity to the visitor semantics is the prime rule):

- Parentheses are structural only and are unwrapped at lowering; precedence is
  frozen into the tree shape.
- Legacy operators (``haswordofdict``, ``byuser``, ...) lower to their fluent
  equivalents; the deprecation warning is emitted during lowering, which runs
  inside ``engine.execute`` exactly like the old visit-time warning.
- ``from(x)`` is the alias for ``field(user, x)`` and lowers to
  :class:`FieldMatch` — mirroring the visitor, which routed both through
  ``search_by_field``.
- Window distribution over windowless links keeps the visitor's
  ``PartialSequence`` deferred-evaluation semantics (a windowless link is
  evaluated with the nearest enclosing windowed link's window); the executor
  ports that mechanism verbatim.
- Variable *positions* are inherently runtime values (a chain emits a
  runtime-dependent number of groups, shifting later restrictions), so the IR
  records variable *structure* only; positions are assigned during execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from ..aggregators.types import AggregationFunction

# Canonical time units: every frontend normalizes surface unit spellings
# ('h', 'hour', 'HOURS', ...) through this table so IR trees from different
# dialects compare equal. The executor's converters accept the canonical form.
_CANONICAL_UNITS = {
    "s": "seconds",
    "second": "seconds",
    "seconds": "seconds",
    "m": "minutes",
    "minute": "minutes",
    "minutes": "minutes",
    "h": "hours",
    "hour": "hours",
    "hours": "hours",
    "d": "days",
    "day": "days",
    "days": "days",
    "w": "weeks",
    "week": "weeks",
    "weeks": "weeks",
    "month": "months",
    "months": "months",
    "year": "years",
    "years": "years",
}


def normalize_time_unit(unit: str) -> str:
    """Map any accepted surface spelling of a time unit to its canonical form."""
    return _CANONICAL_UNITS.get(unit.lower(), unit.lower())


# ---------------------------------------------------------------------------
# Terms: arguments to conditions (hdict / huser / field_value)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Literal:
    """A plain textual argument (quotes already stripped)."""

    text: str


@dataclass(frozen=True)
class Variable:
    """A ``$name`` pattern variable (stored without the ``$``)."""

    name: str


@dataclass(frozen=True)
class Wildcard:
    """``*`` — match all documents."""


Term = Union[Literal, Variable, Wildcard]


# ---------------------------------------------------------------------------
# Conditions: leaves that evaluate to set[MessageId]
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Contains:
    """``contains(dict)`` / legacy ``haswordofdict(dict)``."""

    dict_name: Term


@dataclass(frozen=True)
class ContainsTokens:
    """``contains_tokens(dict)`` — token matching via the tokenizer index."""

    dict_name: Term


@dataclass(frozen=True)
class ContainsPhrase:
    """``contains_phrase("...")`` — n-gram phrase matching."""

    phrase: str


@dataclass(frozen=True)
class FieldMatch:
    """``field(name, value[, mode])``; ``from(x)``/``byuser(x)`` lower to
    ``FieldMatch("user", x, exact=True)``."""

    field_name: str
    value: Term
    exact: bool = True


@dataclass(frozen=True)
class MentionsUser:
    """``mentions_user(x)`` / legacy ``hasusermentioned(x)``.

    The raw argument text is preserved: the visitor never treated ``$var``
    specially here (it fell through to a literal text search), only ``*``.
    """

    user: str


@dataclass(frozen=True)
class IsQuestion:
    """``is_question()`` / legacy ``hasquestion()``."""


@dataclass(frozen=True)
class MentionsEntity:
    """NER-index lookup: mentions_date/time/place/org, contains_link and
    their legacy aliases. ``label`` is the NER label (DATE/TIME/GPE/ORG/URL).
    """

    label: str


@dataclass(frozen=True)
class HasFeature:
    """``has_feature(name)`` / ``labeled_as(name)``."""

    feature: str


@dataclass(frozen=True)
class SimilarTo:
    """``similar_to("text", threshold)`` — semantic similarity, threshold-to-set.

    The backend computes a similarity score per message and returns the set of
    messages at or above ``threshold``; the score itself is discarded, so the
    result composes through the boolean/sequential algebra like any other leaf.
    """

    text: str
    threshold: float


ConditionNode = Union[
    Contains,
    ContainsTokens,
    ContainsPhrase,
    FieldMatch,
    MentionsUser,
    IsQuestion,
    MentionsEntity,
    HasFeature,
    SimilarTo,
]


# ---------------------------------------------------------------------------
# Boolean and sequential layers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Not:
    operand: Expr


@dataclass(frozen=True)
class And:
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Or:
    left: Expr
    right: Expr


# WindowConstraint mirrors prismql.types.WindowConstraint:
# int  -> positional window (INWINDOW n / deprecated per-link WITHIN n)
# (value, unit) -> temporal window (DURING value unit)
WindowSpec = Union[int, tuple[int, str]]


@dataclass(frozen=True)
class SequenceLink:
    """One sequential link. Chains nest LEFT: ``A FB B FB C`` is
    ``SequenceLink(op, SequenceLink(op, A, B), C)``.

    ``window is None`` means the link was written without its own window and
    is evaluated with the nearest enclosing windowed link's window (the
    PartialSequence deferral, preserved in the executor).
    """

    op: str  # FOLLOWED_BY | PRECEDED_BY | NOT_FOLLOWED_BY | NOT_PRECEDED_BY
    lhs: Expr
    rhs: Expr
    window: WindowSpec | None = None


Expr = Union[ConditionNode, Not, And, Or, SequenceLink]


# ---------------------------------------------------------------------------
# Restrictions row (the comma level)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NamedRestriction:
    expr: Expr
    min_count: int = 1
    max_count: int | None = 1  # None = unbounded ({n,})
    name: str | None = None  # AS "name"


@dataclass(frozen=True)
class RestrictionsRow:
    items: tuple[NamedRestriction, ...]


# ---------------------------------------------------------------------------
# Subquery chains (the semicolon / positional-subquery level)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SubqueryContinuation:
    """One continuation after the head subquery.

    ``op is None`` -> unordered (semicolon) continuation.
    ``deprecated`` marks the legacy ``op (query) WITHIN n`` form, which the
    visitor never recognised as positional: all-deprecated chains take the
    unordered path, and mixing with real positional links raises. Preserved
    verbatim (code-as-spec).
    """

    query: Query
    op: str | None = None
    window: int | None = None
    deprecated: bool = False


@dataclass(frozen=True)
class SubqueryChain:
    head: Query
    continuations: tuple[SubqueryContinuation, ...] = ()


# ---------------------------------------------------------------------------
# Clauses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TimeValue:
    """A raw ``<number> <unit>`` pair; unit is the lowercased surface text."""

    value: int
    unit: str


@dataclass(frozen=True)
class AbsoluteTs:
    text: str  # quoted string content, quotes stripped


@dataclass(frozen=True)
class RelativeTs:
    """``<n> <unit> AGO`` — resolved against now() at execution time."""

    value: int
    unit: str


TimestampSpec = Union[AbsoluteTs, RelativeTs]


@dataclass(frozen=True)
class TemporalFilter:
    kind: str  # 'before' | 'after' | 'between'
    start: TimestampSpec | None = None
    end: TimestampSpec | None = None


@dataclass(frozen=True)
class OrderBy:
    """ORDER BY clause. The executor (like the visitor) sorts by each group's
    first message id; ``reverse`` is true when ANY field carries DESC."""

    fields: tuple[str, ...]
    reverse: bool = False


@dataclass(frozen=True)
class LimitClause:
    limit: int
    offset: int = 0


# ---------------------------------------------------------------------------
# Query root
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    """One SELECT body. Subqueries nest whole Query nodes."""

    source: RestrictionsRow | SubqueryChain | None
    # Trailing window: at most one of these is set. INWINDOW/INWIN -> positional;
    # DURING/WITHIN -> temporal (with a derived positional pre-filter).
    positional_window: int | None = None
    temporal_window: TimeValue | None = None
    temporal_filter: TemporalFilter | None = None
    group_by: tuple[str, ...] = ()
    aggregations: tuple[tuple[AggregationFunction, str | None], ...] = ()
    order_by: OrderBy | None = None
    limit: LimitClause | None = None
