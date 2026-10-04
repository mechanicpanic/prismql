"""IR executor: evaluates :mod:`prismql.ir.nodes` trees against a backend.

Deliberately subclasses :class:`PrismQLVisitor` so every ctx-free helper —
the window merges, sequential pair builders, temporal filters, partition
logic — is inherited unchanged and semantics stay byte-identical with the
parse-tree path. Only the *traversal* is reimplemented here, reading IR nodes
instead of ANTLR contexts. The per-body state conventions
(``variable_constraints``, ``pattern_names``, ``_seq_leg_constraints``)
are kept exactly, including their reset points, so
behaviour (and behavioural quirks) match the visitor.

A later cleanup can extract the shared helpers into their own module and
retire the visitor; this class then loses its base without changing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..aggregators.types import AggregateResult, GroupedResult
from ..exceptions import PrismQLRuntimeError
from ..plan.bridge import run_body_span
from ..plan.recorded import not_recording
from ..processors.ordering import order_groups
from ..processors.temporal import TemporalProcessor, TemporalUnit
from ..types import (
    MessageGroup,
    MessageId,
    NamedQueryResult,
    PartialSequence,
    QueryResult,
)
from ..visitors.query_visitor import PrismQLVisitor
from .nodes import (
    AbsoluteTs as IRAbsoluteTs,
)
from .nodes import (
    And,
    Contains,
    ContainsPhrase,
    ContainsTokens,
    Expr,
    FieldMatch,
    HasFeature,
    IsQuestion,
    MentionsEntity,
    MentionsUser,
    Not,
    Or,
    Query,
    RestrictionsRow,
    Run,
    SequenceLink,
    SimilarTo,
    SubqueryChain,
    TemporalFilter,
    TimestampSpec,
    TimeValue,
    Variable,
    Wildcard,
)
from .nodes import (
    RelativeTs as IRRelativeTs,
)

# Messages-per-time-unit estimates for the positional pre-filter derived from
# a temporal window (mirrors PrismQLVisitor._parse_time_window).
_TIME_TO_POSITIONS = {
    "s": 1,
    "second": 1,
    "seconds": 1,
    "m": 10,
    "minute": 10,
    "minutes": 10,
    "h": 600,
    "hour": 600,
    "hours": 600,
    "d": 14400,
    "day": 14400,
    "days": 14400,
    "w": 100000,
    "week": 100000,
    "weeks": 100000,
}

_RELATIVE_UNIT_MAP = {
    "second": TemporalUnit.SECOND,
    "seconds": TemporalUnit.SECOND,
    "s": TemporalUnit.SECOND,
    "minute": TemporalUnit.MINUTE,
    "minutes": TemporalUnit.MINUTE,
    "m": TemporalUnit.MINUTE,
    "hour": TemporalUnit.HOUR,
    "hours": TemporalUnit.HOUR,
    "h": TemporalUnit.HOUR,
    "day": TemporalUnit.DAY,
    "days": TemporalUnit.DAY,
    "d": TemporalUnit.DAY,
    "week": TemporalUnit.WEEK,
    "weeks": TemporalUnit.WEEK,
    "w": TemporalUnit.WEEK,
    "month": TemporalUnit.MONTH,
    "months": TemporalUnit.MONTH,
    "year": TemporalUnit.YEAR,
    "years": TemporalUnit.YEAR,
}


class _OpText:
    """Adapter so the inherited subquery merge (which reads
    ``operator_ctx.getText()``) accepts the pre-normalised IR op string."""

    def __init__(self, text: str) -> None:
        self._text = text

    def getText(self) -> str:  # noqa: N802 - mimics the ANTLR ctx API
        return self._text


class IRExecutor(PrismQLVisitor):
    """Executes lowered IR queries. See module docstring."""

    # ------------------------------------------------------------ query root

    def execute(
        self, q: Query
    ) -> QueryResult | NamedQueryResult | AggregateResult | GroupedResult:
        return self.execute_body(q)

    def execute_body(  # noqa: C901 - mirrors visitBody step-for-step
        self, q: Query
    ) -> QueryResult | NamedQueryResult | AggregateResult | GroupedResult:
        self._one_aggregation(q.aggregations)
        # Reset per-body state (mirrors visitBody).
        self.variable_constraints = []
        self.current_restriction_position = 0
        self.pattern_names = []
        self._seq_leg_constraints = []
        self._restriction_ranges = []

        # Step 1: window extraction.
        window_size = self.DEFAULT_WINDOW_SIZE
        temporal_window = None
        if q.positional_window is not None:
            window_size = q.positional_window
        elif q.temporal_window is not None:
            temporal_window = self._duration_tuple_to_timedelta(
                (q.temporal_window.value, q.temporal_window.unit)
            )
            window_size = self._tv_to_positional(q.temporal_window)

        # Step 2: base results from restrictions or subquery chain.
        results: QueryResult | list[MessageGroup]
        if isinstance(q.source, RestrictionsRow):
            restriction_results, is_sequential = self.execute_restrictions(q.source)
            if is_sequential and len(q.source.items) == 1:
                if q.positional_window is not None:
                    raise PrismQLRuntimeError(self.SECOND_INWINDOW)
                results = restriction_results
            elif temporal_window is not None:
                results = self._merge_restrictions(restriction_results, temporal_window)
                temporal_window = None
            else:
                results = self._merge_restrictions(restriction_results, window_size)
        elif isinstance(q.source, SubqueryChain):
            # stages do not carry their variables across (#52): none recorded
            with not_recording():
                subquery_results, is_positional = self.execute_query_seq(q.source)
            # Each subquery validated its own variables inside its body;
            # whatever the last one left behind must not be re-applied.
            self.variable_constraints = []
            unwrapped_results: list[QueryResult | AggregateResult | GroupedResult] = []
            for result in subquery_results:
                if isinstance(result, NamedQueryResult):
                    unwrapped_results.append(result.to_list())
                else:
                    unwrapped_results.append(result)
            has_explicit_window = q.positional_window is not None
            if is_positional:
                if has_explicit_window:
                    raise PrismQLRuntimeError(
                        "A positional subquery chain cannot take a trailing "
                        "INWINDOW — each FOLLOWED_BY/PRECEDED_BY link between "
                        "subqueries carries its own window. Use DURING <time> "
                        "to constrain the overall time span instead."
                    )
                merged = unwrapped_results[0]
                assert isinstance(merged, list)  # positional chains never aggregate
                results = merged
            elif (
                len(unwrapped_results) == 1
                and not has_explicit_window
                and isinstance(unwrapped_results[0], list)
            ):
                # Single parenthesized subquery without a window: identity.
                results = unwrapped_results[0]
            else:
                results = self._merge_queries(unwrapped_results, window_size)
        else:
            results = []

        # Step 2.3 (variable validation) is gone: equalities are held inside
        # candidate selection by the operator layer (graph #8); a post-hoc
        # pass that indexed groups by id order dropped valid groups (A9).

        # Step 2.4: a trailing DURING on a chain — the whole group's span.
        if temporal_window is not None:
            results = run_body_span(
                self.search_backend, self.timestamp_field, results, temporal_window
            )

        # Step 2.5: temporal filter (BEFORE/AFTER/BETWEEN).
        if q.temporal_filter is not None:
            start_time, end_time, inclusive = self._resolve_temporal_filter(
                q.temporal_filter
            )
            results = self._apply_temporal_filter(
                results, start_time, end_time, inclusive
            )

        # Step 3: GROUP BY.
        grouped_results: GroupedResult | None = None
        if q.group_by:
            grouped_results = self.aggregator.group_by(results, list(q.group_by))

        # Step 4: AGGREGATE.
        if q.aggregations:
            aggregate_results = []
            for func, field in q.aggregations:
                agg_result = self.aggregator.aggregate(
                    results, func, field, grouped_results
                )
                aggregate_results.append(agg_result)
            return aggregate_results[0]

        # Step 5: GROUP BY without AGGREGATE.
        if grouped_results is not None:
            return grouped_results

        # Step 6: ORDER BY.
        if q.order_by is not None:
            results = order_groups(
                self.search_backend, results, q.order_by.fields, q.order_by.reverse
            )

        # Step 7: LIMIT/OFFSET.
        if q.limit is not None:
            results = results[q.limit.offset : q.limit.offset + q.limit.limit]

        # Step 8: pattern names.
        if self.pattern_names and any(name is not None for name in self.pattern_names):
            return NamedQueryResult(results, self.pattern_names)

        return results

    # ------------------------------------------------------- subquery chains

    def execute_query_seq(
        self, chain: SubqueryChain
    ) -> tuple[
        list[QueryResult | NamedQueryResult | AggregateResult | GroupedResult],
        bool,
    ]:
        queries = [chain.head] + [cont.query for cont in chain.continuations]

        if not chain.continuations:
            return [self.execute_body(queries[0])], False

        # The deprecated `op (query) WITHIN n` form was never recognised as
        # positional by the visitor; preserved verbatim.
        has_positional = any(
            cont.op is not None and not cont.deprecated for cont in chain.continuations
        )

        if not has_positional:
            return [self.execute_body(query) for query in queries], False

        current_result = self.execute_body(queries[0])
        if isinstance(current_result, NamedQueryResult):
            current_result = current_result.to_list()
        if isinstance(current_result, (AggregateResult, GroupedResult)):
            raise ValueError(
                "Positional operators between subqueries require non-aggregated results"
            )

        for i, continuation in enumerate(chain.continuations):
            next_query = self.execute_body(queries[i + 1])
            if isinstance(next_query, NamedQueryResult):
                next_query = next_query.to_list()
            if isinstance(next_query, (AggregateResult, GroupedResult)):
                raise ValueError(
                    "Positional operators between subqueries require "
                    "non-aggregated results"
                )

            if continuation.op is not None and not continuation.deprecated:
                current_result = self._merge_subqueries_positional(
                    current_result,
                    next_query,
                    _OpText(continuation.op),
                    continuation.window or 0,
                )
            else:
                raise ValueError(
                    "Mixing semicolon and positional operators in subqueries "
                    "is not supported"
                )

        return [current_result], True

    # --------------------------------------------------------- restrictions

    def execute_restrictions(  # noqa: C901 - mirrors visitRestrictions
        self, row: RestrictionsRow
    ) -> tuple[list[MessageGroup], bool]:
        from ..processors.variables import VariableConstraint

        restriction_results: list[MessageGroup] = []
        has_sequential_operator = False

        for item in row.items:
            if _contains_run(item.expr) and (
                len(row.items) > 1 or item.min_count != 1 or item.max_count != 1
            ):
                raise PrismQLRuntimeError(self.RUN_WHOLE_BODY)
            pattern_name = item.name
            min_count = item.min_count
            self._restriction_ranges.append(
                (min_count, self._close_quantifier(min_count, item.max_count))
            )

            num_constraints_before = len(self.variable_constraints)
            self._seq_leg_constraints = []

            result = self.execute_restriction(item.expr)

            if isinstance(result, PartialSequence):
                raise PrismQLRuntimeError(
                    "Sequential chain is missing a window constraint on its final "
                    "link. Add INWINDOW <n> or DURING <time> at the end of the "
                    "chain — a trailing window applies to every windowless link."
                )

            new_constraints = self.variable_constraints[num_constraints_before:]

            if isinstance(result, list):
                has_sequential_operator = True
                if new_constraints:
                    if len(row.items) > 1 or min_count > 1:
                        raise PrismQLRuntimeError(
                            "Pattern variables inside a FOLLOWED_BY/"
                            "PRECEDED_BY chain require the chain to be the "
                            "entire SELECT body — they cannot be combined "
                            "with other comma-separated restrictions or "
                            "quantifiers. Run the chain as its own query."
                        )
                    for leg_index, leg in enumerate(self._seq_leg_constraints):
                        for constraint in leg:
                            constraint.position = leg_index
                if min_count > 1:
                    if len(result) < min_count:
                        return ([], False)
                    for group in result[:min_count]:
                        restriction_results.append(list(group))
                        self.pattern_names.append(pattern_name)
                        self.current_restriction_position += 1
                else:
                    for group in result:
                        restriction_results.append(list(group))
                        self.pattern_names.append(pattern_name)
                        self.current_restriction_position += 1
            else:
                sorted_result = self._in_stream_order(result)
                if min_count > 1:
                    for i in range(min_count):
                        restriction_results.append(sorted_result)
                        self.pattern_names.append(pattern_name)
                        if i > 0 and new_constraints:
                            for constraint in new_constraints:
                                self.variable_constraints.append(
                                    VariableConstraint(
                                        variable_name=constraint.variable_name,
                                        field_name=constraint.field_name,
                                        position=self.current_restriction_position,
                                        negated=constraint.negated,
                                    )
                                )
                        self.current_restriction_position += 1
                else:
                    restriction_results.append(sorted_result)
                    self.pattern_names.append(pattern_name)
                    self.current_restriction_position += 1

        return (restriction_results, has_sequential_operator)

    # ---------------------------------------------------- sequential + bool

    def execute_restriction(
        self, expr: Expr
    ) -> set[MessageId] | list[MessageGroup] | PartialSequence:
        if isinstance(expr, Run):
            n_before = len(self.variable_constraints)
            ids = self.execute_bool(expr.expr)
            constraints = self.variable_constraints[n_before:]
            del self.variable_constraints[n_before:]
            return self._evaluate_run(
                ids, constraints, expr.window, expr.min_len, expr.max_len
            )
        if not isinstance(expr, SequenceLink):
            return self.execute_bool(expr)
        if _contains_run(expr):
            return self._execute_run_link(expr)

        n_before_lhs = len(self.variable_constraints)
        lhs = self.execute_restriction(expr.lhs)
        n_before_rhs = len(self.variable_constraints)
        if not self._seq_leg_constraints:
            self._seq_leg_constraints = [list(self.variable_constraints[n_before_lhs:])]
        lhs_leg = list(self.variable_constraints[n_before_lhs:n_before_rhs])
        rhs = self.execute_bool(expr.rhs)
        rhs_leg = list(self.variable_constraints[n_before_rhs:])
        window = expr.window

        if isinstance(rhs, (list, PartialSequence)):
            raise PrismQLRuntimeError(
                "Sequential operators require simple conditions on the "
                "right-hand side, not nested sequences"
            )

        if expr.op == "FOLLOWED_BY":
            self._seq_leg_constraints.append(rhs_leg)
            return self._apply_sequential_link(
                lhs, rhs, window, "FOLLOWED_BY", lhs_leg, rhs_leg
            )
        if expr.op == "PRECEDED_BY":
            self._seq_leg_constraints.insert(0, rhs_leg)
            return self._apply_sequential_link(
                lhs, rhs, window, "PRECEDED_BY", lhs_leg, rhs_leg
            )
        # The excluded event binds nothing: its variables only narrow what
        # counts as excluded (graph #130), so they leave the row's list.
        del self.variable_constraints[n_before_rhs:]
        return self._apply_negative_link(lhs, rhs, window, expr.op, lhs_leg, rhs_leg)

    def _execute_run_link(self, expr: SequenceLink) -> list[MessageGroup]:
        """A link with a run on one side or both (graph #126)."""
        if isinstance(expr.lhs, SequenceLink) or isinstance(expr.rhs, SequenceLink):
            raise PrismQLRuntimeError(self.RUN_ONE_LINK)

        def side(e: Expr) -> tuple[Any, ...]:
            if isinstance(e, Run):
                return self._run_side_from(
                    lambda: self.execute_bool(e.expr),
                    (e.window, e.min_len, e.max_len),
                )
            return self._run_side_from(lambda: self.execute_bool(e), None)

        return self._evaluate_run_link(
            side(expr.lhs), side(expr.rhs), expr.window, expr.op
        )

    def execute_bool(
        self, expr: Expr
    ) -> set[MessageId] | list[MessageGroup] | PartialSequence:
        if isinstance(expr, Not):
            excluded = self.execute_bool(expr.operand)
            if isinstance(excluded, (list, PartialSequence)):
                raise PrismQLRuntimeError(
                    "NOT operator cannot be used with sequential operators "
                    "(FOLLOWED_BY, PRECEDED_BY). Sequential operators return "
                    "message sequences, not individual messages."
                )
            total_docs = self.search_backend.get_total_documents()
            all_messages = self.search_backend.get_all_document_ids(limit=total_docs)
            return all_messages - excluded

        if isinstance(expr, And):
            lhs = self.execute_bool(expr.left)
            rhs = self.execute_bool(expr.right)
            if isinstance(lhs, (list, PartialSequence)) or isinstance(
                rhs, (list, PartialSequence)
            ):
                raise PrismQLRuntimeError(
                    "AND operator cannot be used with sequential operators "
                    "(FOLLOWED_BY, PRECEDED_BY). Sequential operators return "
                    "message sequences, not individual messages."
                )
            return lhs & rhs

        if isinstance(expr, Or):
            lhs = self.execute_bool(expr.left)
            rhs = self.execute_bool(expr.right)
            if isinstance(lhs, (list, PartialSequence)) or isinstance(
                rhs, (list, PartialSequence)
            ):
                raise PrismQLRuntimeError(
                    "OR operator cannot be used with sequential operators "
                    "(FOLLOWED_BY, PRECEDED_BY). Sequential operators return "
                    "message sequences, not individual messages."
                )
            return lhs | rhs

        if isinstance(expr, SequenceLink):
            # Parenthesized sequential expression inside the boolean layer.
            return self.execute_restriction(expr)
        if isinstance(expr, Run):
            raise PrismQLRuntimeError(self.RUN_WHOLE_BODY)

        return self.execute_condition(expr)

    # ------------------------------------------------------------ conditions

    def _all_documents(self) -> set[MessageId]:
        total_docs = self.search_backend.get_total_documents()
        return self.search_backend.get_all_document_ids(limit=total_docs)

    def execute_condition(  # noqa: C901 - one branch per condition node
        self, cond: Expr
    ) -> set[MessageId]:
        from ..processors.variables import VariableConstraint

        if isinstance(cond, Contains):
            if isinstance(cond.dict_name, Wildcard):
                return self._all_documents()
            if isinstance(cond.dict_name, Variable):
                raise PrismQLRuntimeError(
                    "Variables in contains() not yet supported. "
                    "Use from($user) for user-based variables."
                )
            dict_name = cond.dict_name.text
            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            return self._search_dictionary(dict_name)

        if isinstance(cond, ContainsTokens):
            if isinstance(cond.dict_name, Wildcard):
                return self._all_documents()
            if isinstance(cond.dict_name, Variable):
                raise PrismQLRuntimeError(
                    "Variables in contains_tokens() not yet supported. "
                    "Use from($user) for user-based variables."
                )
            dict_name = cond.dict_name.text
            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            self._require_text(f"contains_tokens({dict_name})")
            tokens = self.user_dictionaries[dict_name]
            return self.search_backend.search_tokens(
                tokens, field="text", operator="OR"
            )

        if isinstance(cond, ContainsPhrase):
            self._require_text("contains_phrase()", "phrase")
            return self.search_backend.search_phrase(cond.phrase, field="text")

        if isinstance(cond, FieldMatch):
            if isinstance(cond.value, Wildcard):
                return self._all_documents()
            if isinstance(cond.value, Variable):
                self.variable_constraints.append(
                    VariableConstraint(
                        variable_name=cond.value.name,
                        field_name=cond.field_name,
                        position=self.current_restriction_position,
                        negated=cond.value.negated,
                    )
                )
                return self._all_documents()
            return self.search_backend.search_by_field(
                cond.field_name, cond.value.text, exact=cond.exact
            )

        if isinstance(cond, MentionsUser):
            return self._mentions_user(cond.user)

        if isinstance(cond, IsQuestion):
            return self._get_questions()

        if isinstance(cond, MentionsEntity):
            return self._get_ner_messages(cond.label)

        if isinstance(cond, HasFeature):
            return self._get_custom_feature(cond.feature)

        if isinstance(cond, SimilarTo):
            return self._get_semantically_similar(cond.text, cond.threshold)

        raise PrismQLRuntimeError("Unknown condition type")

    # ------------------------------------------------------------- clauses

    @staticmethod
    def _tv_to_positional(tv: TimeValue) -> int:
        """Positional pre-filter estimate for a temporal window (mirrors
        PrismQLVisitor._parse_time_window)."""
        return tv.value * _TIME_TO_POSITIONS.get(tv.unit, 1)

    def _resolve_timestamp(self, spec: TimestampSpec | None) -> datetime:
        assert spec is not None  # guaranteed by TemporalFilter kind
        if isinstance(spec, IRAbsoluteTs):
            return TemporalProcessor.parse_timestamp(spec.text)
        if isinstance(spec, IRRelativeTs):
            unit = _RELATIVE_UNIT_MAP.get(spec.unit, TemporalUnit.DAY)
            return TemporalProcessor.parse_relative_time(spec.value, unit)
        raise ValueError(f"Unknown timestamp spec: {spec!r}")

    def _resolve_temporal_filter(
        self, tf: TemporalFilter
    ) -> tuple[datetime | None, datetime | None, bool]:
        if tf.kind == "before":
            return (None, self._resolve_timestamp(tf.end), False)
        if tf.kind == "after":
            return (self._resolve_timestamp(tf.start), None, False)
        if tf.kind == "between":
            return (
                self._resolve_timestamp(tf.start),
                self._resolve_timestamp(tf.end),
                True,
            )
        return (None, None, False)


def _contains_run(expr: Any) -> bool:
    """Whether a restriction's sequence layer holds a RUN."""
    if isinstance(expr, Run):
        return True
    if isinstance(expr, SequenceLink):
        return _contains_run(expr.lhs) or _contains_run(expr.rhs)
    return False
