"""Lowering: ANTLR parse tree -> PrismQL IR.

This module is the ONLY place that touches parse-tree contexts. Every
``ctx.`` access in the old visitor's extraction paths lives here now; the
executor never sees ANTLR.

Fidelity notes:

- Deprecation warnings for legacy operators are emitted here (lowering runs
  inside ``engine.execute``, so the warning still fires per execution like
  the old visit-time warning did).
- Parentheses are unwrapped: ``'(' restriction ')'`` lowers to the inner
  expression. Precedence is already frozen in the tree shape.
- Errors raised here are :class:`PrismQLRuntimeError` with the exact visitor
  messages; the engine wraps them identically either way.
"""

from __future__ import annotations

import warnings
from typing import Any

from ..aggregators.types import AggregationFunction
from ..exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from ..grammar.generated.PrismQLParser import PrismQLParser
from .nodes import (
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
    Run,
    SequenceLink,
    SimilarTo,
    SubqueryChain,
    SubqueryContinuation,
    TemporalFilter,
    Term,
    TimestampSpec,
    TimeValue,
    Variable,
    Wildcard,
    WindowSpec,
    normalize_time_unit,
)

# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------


def _huser(ctx: Any) -> str:
    """A user argument as written, a quoted name without its quotes — names
    like "Claude Opus 4.5" need them (graph @aleph/prismql, #121)."""
    text: str = ctx.huser().getText()
    if len(text) >= 2 and text[0] == text[-1] == '"':
        return text[1:-1]
    return text


def _user_term(ctx: Any) -> Term:
    """from()'s argument: a quoted one is always a name — ``from("*")`` is
    the author called "*", as the pipe dialect reads it."""
    if ctx.huser().QUOTED_STRING() is not None:
        return Literal(_huser(ctx))
    return _term(_huser(ctx))


def _term(text: str) -> Term:
    if text == "*":
        return Wildcard()
    if text.startswith("!$"):
        return Variable(text[2:], negated=True)
    if text.startswith("$"):
        return Variable(text[1:])
    return Literal(text)


def _strip_quotes(text: str) -> str:
    if len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        return text[1:-1]
    return text


def _time_value(ctx: Any) -> TimeValue:
    return TimeValue(
        value=int(ctx.number().getText()),
        unit=normalize_time_unit(ctx.time_unit().getText()),
    )


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------


def _warn_deprecated(old: str, new: str, example: str) -> None:
    warnings.warn(
        f"{old}() is deprecated and will be removed in v1.0. "
        f"Use {new}() instead: '{example}'",
        DeprecationWarning,
        stacklevel=2,
    )


def lower_condition(  # noqa: C901 - one branch per condition alternative
    ctx: PrismQLParser.ConditionContext,
) -> Expr:
    # --- fluent operators ---
    if ctx.Contains():
        return Contains(_term(ctx.hdict().getText()))
    if ctx.ContainsTokens():
        return ContainsTokens(_term(ctx.hdict().getText()))
    if ctx.ContainsPhrase():
        return ContainsPhrase(ctx.QUOTED_STRING().getText()[1:-1])
    if ctx.From():
        return FieldMatch("user", _user_term(ctx), exact=True)
    if ctx.MentionsUser():
        return MentionsUser(_huser(ctx))
    if ctx.IsQuestion():
        return IsQuestion()
    if ctx.MentionsDate():
        return MentionsEntity("DATE")
    if ctx.MentionsTime():
        return MentionsEntity("TIME")
    if ctx.MentionsPlace():
        return MentionsEntity("GPE")
    if ctx.MentionsOrg():
        return MentionsEntity("ORG")
    if ctx.ContainsLink():
        return MentionsEntity("URL")
    if ctx.HasFeature():
        return HasFeature(ctx.feature_name().getText())
    if ctx.LabeledAs():
        return HasFeature(ctx.feature_name().getText())
    if ctx.SimilarTo():
        return SimilarTo(
            text=ctx.QUOTED_STRING().getText()[1:-1],
            threshold=float(ctx.float_number().getText()),
        )
    if ctx.Field():
        fname = ctx.field_name().getText()
        raw_value = ctx.field_value().getText()
        exact = True
        if ctx.match_mode() is not None:
            mode = ctx.match_mode().getText().lower()
            if mode == "partial":
                exact = False
            elif mode != "exact":
                raise PrismQLRuntimeError(
                    f"Unknown field() matcher {mode!r}: use 'exact' "
                    "(default) or 'partial' (substring over field values)"
                )
        if raw_value == "*":
            return FieldMatch(fname, Wildcard(), exact=exact)
        if raw_value.startswith("!$"):
            return FieldMatch(fname, Variable(raw_value[2:], negated=True), exact=exact)
        if raw_value.startswith("$"):
            return FieldMatch(fname, Variable(raw_value[1:]), exact=exact)
        return FieldMatch(fname, Literal(_strip_quotes(raw_value)), exact=exact)

    # --- legacy operators (deprecation warnings preserved verbatim) ---
    if ctx.HasWordOfDict():
        warnings.warn(
            "haswordofdict() is deprecated and will be removed in v1.0. "
            "Use contains() instead: 'contains(dict_name)'",
            DeprecationWarning,
            stacklevel=2,
        )
        return Contains(_term(ctx.hdict().getText()))
    if ctx.ByUser():
        _warn_deprecated("byuser", "from", "from(username)")
        return FieldMatch("user", _user_term(ctx), exact=True)
    if ctx.HasUserMentioned():
        _warn_deprecated("hasusermentioned", "mentions_user", "mentions_user(username)")
        return MentionsUser(_huser(ctx))
    if ctx.HasQuestion():
        _warn_deprecated("hasquestion", "is_question", "is_question()")
        return IsQuestion()
    if ctx.HasDate():
        _warn_deprecated("hasdate", "mentions_date", "mentions_date()")
        return MentionsEntity("DATE")
    if ctx.HasTime():
        _warn_deprecated("hastime", "mentions_time", "mentions_time()")
        return MentionsEntity("TIME")
    if ctx.HasLocation():
        _warn_deprecated("haslocation", "mentions_place", "mentions_place()")
        return MentionsEntity("GPE")
    if ctx.HasOrganization():
        _warn_deprecated("hasorganization", "mentions_org", "mentions_org()")
        return MentionsEntity("ORG")
    if ctx.HasURL():
        _warn_deprecated("hasurl", "contains_link", "contains_link()")
        return MentionsEntity("URL")

    raise PrismQLRuntimeError("Unknown condition type")


# ---------------------------------------------------------------------------
# Boolean / sequential layers
# ---------------------------------------------------------------------------


def lower_bool_restriction(ctx: PrismQLParser.Bool_restrictionContext) -> Expr:
    if ctx.Not():
        return Not(lower_bool_restriction(ctx.bool_restriction(0)))
    if ctx.And():
        return And(
            lower_bool_restriction(ctx.bool_restriction(0)),
            lower_bool_restriction(ctx.bool_restriction(1)),
        )
    if ctx.Or():
        return Or(
            lower_bool_restriction(ctx.bool_restriction(0)),
            lower_bool_restriction(ctx.bool_restriction(1)),
        )
    if ctx.restriction():
        # Parentheses: structural only; the inner expression (possibly a full
        # sequential chain) is visible to callers, exactly like the visitor.
        return lower_restriction(ctx.restriction())
    if ctx.condition():
        return lower_condition(ctx.condition())
    raise PrismQLRuntimeError("Invalid restriction in parse tree")


def _link_window(ctx: Any) -> WindowSpec | None:
    """Extract a per-link or body-level window constraint.

    INWINDOW n -> positional int; DURING t -> (value, unit); WITHIN n -> the
    deprecated positional int form (restriction links only).
    """
    if hasattr(ctx, "InWindow") and ctx.InWindow():
        return int(ctx.number().getText())
    if hasattr(ctx, "During") and ctx.During():
        tv = _time_value(ctx.time_value())
        return (tv.value, tv.unit)
    if hasattr(ctx, "Within") and ctx.Within():
        return int(ctx.number().getText())
    return None


def lower_restriction(ctx: PrismQLParser.RestrictionContext) -> Expr:
    if ctx.Run():
        min_len, max_len = _quantifier(ctx)
        return Run(
            lower_bool_restriction(ctx.bool_restriction()),
            min_len,
            max_len,
            _link_window(ctx),
        )
    if (
        not ctx.FollowedBy()
        and not ctx.PrecededBy()
        and not ctx.NotFollowedBy()
        and not ctx.NotPrecededBy()
    ):
        return lower_bool_restriction(ctx.bool_restriction())

    lhs = lower_restriction(ctx.restriction())
    rhs = lower_bool_restriction(ctx.bool_restriction())
    window = _link_window(ctx)
    if ctx.FollowedBy():
        op = "FOLLOWED_BY"
    elif ctx.PrecededBy():
        op = "PRECEDED_BY"
    elif ctx.NotFollowedBy():
        op = "NOT_FOLLOWED_BY"
    else:
        op = "NOT_PRECEDED_BY"
    return SequenceLink(op, lhs, rhs, window)


# ---------------------------------------------------------------------------
# Restrictions row
# ---------------------------------------------------------------------------


def _quantifier(ctx: Any) -> tuple[int, int | None]:
    if not ctx.quantifier():
        return (1, 1)
    qctx = ctx.quantifier()
    if isinstance(qctx, PrismQLParser.ExactQuantifierContext):
        count = int(qctx.number().getText())
        return (count, count)
    if isinstance(qctx, PrismQLParser.AtLeastQuantifierContext):
        return (int(qctx.number().getText()), None)
    if isinstance(qctx, PrismQLParser.RangeQuantifierContext):
        numbers = qctx.number()
        return (int(numbers[0].getText()), int(numbers[1].getText()))
    return (1, 1)


def lower_restrictions(ctx: PrismQLParser.RestrictionsContext) -> RestrictionsRow:
    items = []
    for nr in ctx.named_restriction():
        name = None
        if nr.As():
            name = nr.QUOTED_STRING().getText()[1:-1]
        min_count, max_count = _quantifier(nr)
        items.append(
            NamedRestriction(
                expr=lower_restriction(nr.restriction()),
                min_count=min_count,
                max_count=max_count,
                name=name,
            )
        )
    return RestrictionsRow(tuple(items))


# ---------------------------------------------------------------------------
# Subquery chains
# ---------------------------------------------------------------------------


def lower_query_seq(ctx: PrismQLParser.Query_seqContext) -> SubqueryChain:
    head = lower_query(ctx.query())
    continuations = []
    conts = (
        ctx.query_seq_continuation() if hasattr(ctx, "query_seq_continuation") else []
    )
    for cont in conts:
        if isinstance(cont, PrismQLParser.PositionalSubqueryContext):
            continuations.append(
                SubqueryContinuation(
                    query=lower_query(cont.query()),
                    op=cont.positional_op().getText().upper().replace("_", ""),
                    window=int(cont.number().getText()),
                )
            )
        elif isinstance(cont, PrismQLParser.PositionalSubqueryDeprecatedContext):
            # The visitor never recognised this form as positional (only
            # PositionalSubqueryContext was checked): all-deprecated chains
            # take the unordered path; mixed chains raise. Preserved.
            continuations.append(
                SubqueryContinuation(
                    query=lower_query(cont.query()),
                    op=cont.positional_op().getText().upper().replace("_", ""),
                    window=int(cont.number().getText()),
                    deprecated=True,
                )
            )
        else:  # UnorderedSubqueryContext
            continuations.append(SubqueryContinuation(query=lower_query(cont.query())))
    return SubqueryChain(head, tuple(continuations))


# ---------------------------------------------------------------------------
# Clauses
# ---------------------------------------------------------------------------


def _timestamp(ctx: Any) -> TimestampSpec:
    if isinstance(ctx, PrismQLParser.AbsoluteTimestampContext):
        return AbsoluteTs(ctx.QUOTED_STRING().getText().strip("\"'"))
    if isinstance(ctx, PrismQLParser.RelativeTimestampContext):
        tv = _time_value(ctx.time_value())
        return RelativeTs(tv.value, tv.unit)
    raise ValueError(f"Unknown timestamp context type: {type(ctx)}")


def _temporal_filter(ctx: Any) -> TemporalFilter:
    if ctx.Before():
        return TemporalFilter("before", end=_timestamp(ctx.timestamp(0)))
    if ctx.After():
        return TemporalFilter("after", start=_timestamp(ctx.timestamp(0)))
    if ctx.Between():
        return TemporalFilter(
            "between",
            start=_timestamp(ctx.timestamp(0)),
            end=_timestamp(ctx.timestamp(1)),
        )
    return TemporalFilter("none")


_GROUPBY_FUNC_MAP = {
    "HOUR": "HOURS",
    "HOURS": "HOURS",
    "DAY": "DAYS",
    "DAYS": "DAYS",
    "WEEK": "WEEKS",
    "WEEKS": "WEEKS",
    "MONTH": "MONTHS",
    "MONTHS": "MONTHS",
    "YEAR": "YEARS",
    "YEARS": "YEARS",
}


def _group_by_fields(ctx: Any) -> tuple[str, ...]:
    fields = []
    groupby_fields = ctx.groupby_field()
    if not isinstance(groupby_fields, list):
        groupby_fields = [groupby_fields]
    for field_ctx in groupby_fields:
        if isinstance(field_ctx, PrismQLParser.SimpleGroupByContext):
            fields.append(field_ctx.field_name().getText().strip("\"'"))
        elif isinstance(field_ctx, PrismQLParser.TemporalGroupByContext):
            func_text = field_ctx.temporal_group_func().getText().upper()
            func = _GROUPBY_FUNC_MAP.get(func_text, func_text)
            field_name = field_ctx.field_name().getText().strip("\"'")
            fields.append(f"__{func}__({field_name})")
    return tuple(fields)


def _aggregations(
    ctx: Any,
) -> tuple[tuple[AggregationFunction, str | None], ...]:
    aggregations: list[tuple[AggregationFunction, str | None]] = []
    agg_funcs = ctx.aggregation_func()
    if not isinstance(agg_funcs, list):
        agg_funcs = [agg_funcs]
    for agg in agg_funcs:
        if isinstance(agg, PrismQLParser.CountAllContext):
            aggregations.append((AggregationFunction.COUNT, None))
        elif isinstance(agg, PrismQLParser.CountDistinctContext):
            aggregations.append(
                (AggregationFunction.COUNT_DISTINCT, agg.field_name().getText())
            )
        elif isinstance(agg, PrismQLParser.DistinctValuesContext):
            aggregations.append(
                (AggregationFunction.DISTINCT, agg.field_name().getText())
            )
        elif isinstance(agg, PrismQLParser.SumFuncContext):
            aggregations.append((AggregationFunction.SUM, agg.field_name().getText()))
        elif isinstance(agg, PrismQLParser.AvgFuncContext):
            aggregations.append((AggregationFunction.AVG, agg.field_name().getText()))
        elif isinstance(agg, PrismQLParser.MinFuncContext):
            aggregations.append((AggregationFunction.MIN, agg.field_name().getText()))
        elif isinstance(agg, PrismQLParser.MaxFuncContext):
            aggregations.append((AggregationFunction.MAX, agg.field_name().getText()))
    return tuple(aggregations)


def _order_by(ctx: Any) -> OrderBy:
    field_names = ctx.field_name()
    if not isinstance(field_names, list):
        field_names = [field_names]
    # One direction sorts the whole key (graph @aleph/prismql, #105): the
    # grammar lets each field carry its own, so a mix is refused rather
    # than silently applied to every field.
    if ctx.Asc() and ctx.Desc():
        raise PrismQLSyntaxError(
            "ORDER BY takes one direction for all its fields: write ASC or "
            "DESC once, after the last field"
        )
    return OrderBy(
        fields=tuple(f.getText() for f in field_names),
        reverse=bool(ctx.Desc()),
    )


def _limit(ctx: Any) -> LimitClause:
    numbers = ctx.number()
    if isinstance(numbers, list):
        limit = int(numbers[0].getText())
        offset = int(numbers[1].getText()) if len(numbers) > 1 else 0
    else:
        limit = int(numbers.getText())
        offset = 0
    return LimitClause(limit, offset)


# ---------------------------------------------------------------------------
# Query root
# ---------------------------------------------------------------------------


def lower_query(ctx: PrismQLParser.QueryContext) -> Query:
    return lower_body(ctx.body())


def lower_body(ctx: PrismQLParser.BodyContext) -> Query:
    positional_window: int | None = None
    temporal_window: TimeValue | None = None
    if ctx.InWindow() or ctx.InWin():
        positional_window = int(ctx.number().getText())
    elif ctx.During() or ctx.Within():
        temporal_window = _time_value(ctx.time_value())

    source: RestrictionsRow | SubqueryChain | None = None
    if ctx.restrictions():
        source = lower_restrictions(ctx.restrictions())
    elif ctx.query_seq():
        source = lower_query_seq(ctx.query_seq())

    return Query(
        source=source,
        positional_window=positional_window,
        temporal_window=temporal_window,
        temporal_filter=(
            _temporal_filter(ctx.temporal_filter()) if ctx.temporal_filter() else None
        ),
        group_by=_group_by_fields(ctx.groupby_clause()) if ctx.groupby_clause() else (),
        aggregations=(
            _aggregations(ctx.aggregate_clause()) if ctx.aggregate_clause() else ()
        ),
        order_by=_order_by(ctx.orderby_clause()) if ctx.orderby_clause() else None,
        limit=_limit(ctx.limit_clause()) if ctx.limit_clause() else None,
    )
