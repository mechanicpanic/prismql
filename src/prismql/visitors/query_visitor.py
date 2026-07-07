"""PrismQL query visitor implementation."""

import warnings
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from ..aggregators.aggregator import Aggregator
from ..aggregators.types import AggregateResult, AggregationFunction, GroupedResult
from ..backends.base import NLPBackend, PrecomputedIndexes, SearchBackend
from ..exceptions import PrismQLRuntimeError
from ..grammar.generated.PrismQLParser import PrismQLParser
from ..grammar.generated.PrismQLVisitor import PrismQLVisitor as BasePrismQLVisitor
from ..processors.temporal import TemporalProcessor, TemporalUnit
from ..processors.variables import VariableConstraint, VariableValidator
from ..types import (
    MessageGroup,
    MessageId,
    NamedQueryResult,
    PartialSequence,
    QueryResult,
    WindowConstraint,
)

# Try to import Rust backend for performance
try:
    from prismql_rust import merge_followed_by as rust_merge_followed_by
    from prismql_rust import merge_preceded_by as rust_merge_preceded_by

    RUST_FOLLOWED_BY_AVAILABLE = True
    RUST_PRECEDED_BY_AVAILABLE = True
except ImportError:
    RUST_FOLLOWED_BY_AVAILABLE = False
    RUST_PRECEDED_BY_AVAILABLE = False


class PrismQLVisitor(BasePrismQLVisitor):
    """
    Visitor that traverses the PrismQL parse tree and executes the query.

    This is the core query execution engine that interprets the query
    and calls appropriate backend methods.
    """

    DEFAULT_WINDOW_SIZE = 70
    MAX_MESSAGES_NOT = 1_000_000

    def __init__(
        self,
        search_backend: SearchBackend,
        nlp_backend: Optional[NLPBackend] = None,
        user_dictionaries: Optional[Mapping[str, Sequence[str]]] = None,
        precomputed_indexes: Optional[PrecomputedIndexes] = None,
        timestamp_field: str = "timestamp",
        text_match: str = "substring",
        dictionary_modes: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.search_backend = search_backend
        self.nlp_backend = nlp_backend
        self.user_dictionaries = user_dictionaries or {}
        self.text_match = text_match
        # Per-dictionary single-word match mode (overrides text_match)
        self.dictionary_modes: Mapping[str, str] = dictionary_modes or {}
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        self.aggregator = Aggregator(search_backend)
        self.timestamp_field = timestamp_field

        # Variable tracking for pattern matching
        self.variable_constraints: list[VariableConstraint] = []
        self.current_restriction_position = 0
        # Per-leg constraint buckets for the sequential layer, in
        # chronological group order (FOLLOWED_BY appends, PRECEDED_BY
        # prepends). Rewritten into positions by visitRestrictions.
        self._seq_leg_constraints: list[list[VariableConstraint]] = []
        # Correlation key (var, field) when EVERY leg of the chain carries
        # exactly one constraint on the same variable+field (the EQL
        # `sequence by` shape). Link merges then run greedily WITHIN each
        # field-value partition instead of globally — greedy-global would
        # pick the nearest candidate from any partition and lose chains the
        # post-hoc validator can never recover.
        self._seq_partition_key: Optional[tuple[str, str]] = None

        # Pattern naming for result labeling
        self.pattern_names: list[Optional[str]] = []

    def _extract_window_constraint(self, ctx: Any) -> Optional[WindowConstraint]:
        """
        Extract window constraint from context.

        Args:
            ctx: Parse tree context that may have InWindow, During, or Within

        Returns:
            WindowConstraint (int for INWINDOW, tuple for DURING) or None
        """
        # Check for INWINDOW (positional)
        if hasattr(ctx, "InWindow") and ctx.InWindow():
            return int(ctx.number().getText())

        # Check for DURING (temporal)
        if hasattr(ctx, "During") and ctx.During():
            time_value_ctx = ctx.time_value()
            value = int(time_value_ctx.number().getText())
            unit = time_value_ctx.time_unit().getText().lower()
            return (value, unit)

        # Check for deprecated WITHIN (positional - backward compatibility)
        if hasattr(ctx, "Within") and ctx.Within():
            return int(ctx.number().getText())

        return None

    def visitQuery(
        self, ctx: PrismQLParser.QueryContext
    ) -> Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]:
        """Entry point - visit the query body."""
        return self.visitBody(ctx.body())

    def visitBody(
        self, ctx: PrismQLParser.BodyContext
    ) -> Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]:
        """Process query body with optional window, grouping, aggregation,
        ordering, and limiting."""
        # Reset variable tracking and pattern names for this query
        self.variable_constraints = []
        self.current_restriction_position = 0
        self.pattern_names = []
        self._seq_leg_constraints = []
        self._seq_partition_key = None

        # Step 1: Extract window size if specified (position-based or time-based)
        window_size = self.DEFAULT_WINDOW_SIZE
        temporal_window = None  # Will be set if using temporal DURING

        if ctx.InWindow():
            # Unified positional window operator
            window_size = int(ctx.number().getText())
        elif ctx.InWin():
            # Deprecated: use INWINDOW instead
            window_size = int(ctx.number().getText())
        elif ctx.During():
            # Temporal window operator (time-based filtering with actual timestamps)
            temporal_window = self._parse_time_window_to_timedelta(ctx.time_value())
            # Also use a large positional window as pre-filter for efficiency
            window_size = self._parse_time_window(ctx.time_value())
        elif ctx.Within():
            # Deprecated: use DURING for temporal, INWINDOW for positional
            temporal_window = self._parse_time_window_to_timedelta(ctx.time_value())
            window_size = self._parse_time_window(ctx.time_value())

        # Step 2: Process either restrictions or query sequence to get base results
        if ctx.restrictions():
            # Single query with comma-separated restrictions
            restriction_results, is_sequential = self.visitRestrictions(
                ctx.restrictions()
            )
            # If the result is from a single FOLLOWED_BY/PRECEDED_BY operator,
            # return the pairs directly without merging
            if is_sequential and len(ctx.restrictions().named_restriction()) == 1:
                results = restriction_results
            elif temporal_window is not None:
                # For temporal windows we need ALL combinations (not just
                # non-overlapping pairs from the greedy algorithm). The Rust
                # backend fuses generation + span filtering with pruning, so
                # infeasible combinations are never materialized; the Python
                # fallback builds the full cartesian product and filters it
                # in Step 2.4.
                can_fuse = hasattr(
                    self.search_backend, "merge_within_time_window"
                ) and self.search_backend.has_timestamp_field(  # type: ignore[attr-defined]
                    self.timestamp_field
                )
                if can_fuse:
                    results = self.search_backend.merge_within_time_window(  # type: ignore[attr-defined]
                        restriction_results, self.timestamp_field, temporal_window
                    )
                    # Span filter already applied; skip Step 2.4. (Variable
                    # validation in Step 2.3 commutes with the span filter —
                    # both are per-group predicates — and runs faster on the
                    # already-filtered set.)
                    temporal_window = None
                else:
                    results = self._generate_all_combinations(restriction_results)
            else:
                results = self._merge_restrictions(restriction_results, window_size)
        elif ctx.query_seq():
            # Multiple subqueries in sequence
            subquery_results, is_positional = self.visitQuery_seq(ctx.query_seq())
            # Each subquery validated its own variables inside its visitBody;
            # whatever the last one left behind must not be re-applied to the
            # merged groups (positions would point at the wrong messages).
            self.variable_constraints = []
            # Unwrap NamedQueryResult to plain QueryResult for merging
            unwrapped_results: list[
                Union[QueryResult, AggregateResult, GroupedResult]
            ] = []
            for result in subquery_results:
                if isinstance(result, NamedQueryResult):
                    unwrapped_results.append(result.to_list())
                else:
                    unwrapped_results.append(result)
            has_explicit_window = ctx.InWindow() is not None or ctx.InWin() is not None
            if is_positional:
                # The chain is already merged group-wise; each link carried
                # its own window, so a trailing positional window has nothing
                # left to constrain — re-merging here would smash the groups.
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
                # A single parenthesized subquery without a window is the
                # identity — merging would silently fuse its groups with the
                # default window.
                results = unwrapped_results[0]
            else:
                results = self._merge_queries(unwrapped_results, window_size)
        else:
            results = []

        # Step 2.3: Apply variable validation if any variables were used
        if self.variable_constraints:
            validator = VariableValidator(
                self.search_backend, self.variable_constraints
            )
            results = validator.validate_results(results)

        # Step 2.4: Apply temporal window filtering if DURING was used
        if temporal_window is not None:
            # Use backend's cached timestamps when available (Rust path);
            # otherwise fetch documents and parse per-query (Python path).
            if hasattr(
                self.search_backend, "has_timestamp_field"
            ) and self.search_backend.has_timestamp_field(self.timestamp_field):
                results = self.search_backend.filter_by_time_window(  # type: ignore[attr-defined]
                    results, self.timestamp_field, temporal_window
                )
            else:
                all_msg_ids = set()
                for group in results:
                    all_msg_ids.update(group)
                documents = self.search_backend.get_documents(list(all_msg_ids))
                results = TemporalProcessor.filter_by_time_window(
                    results,
                    documents,
                    self.timestamp_field,
                    temporal_window,
                    id_field=getattr(self.search_backend, "id_field", "id"),
                )

        # Step 2.5: Apply temporal filtering if specified (BEFORE, AFTER, BETWEEN)
        if ctx.temporal_filter():
            start_time, end_time, inclusive = self._parse_temporal_filter(
                ctx.temporal_filter()
            )
            results = self._apply_temporal_filter(
                results, start_time, end_time, inclusive
            )

        # Step 3: Apply GROUP BY if specified
        grouped_results: Optional[GroupedResult] = None
        if ctx.groupby_clause():
            fields = self._extract_group_by_fields(ctx.groupby_clause())
            grouped_results = self.aggregator.group_by(results, fields)

        # Step 4: Apply AGGREGATE if specified
        if ctx.aggregate_clause():
            aggregations = self._extract_aggregations(ctx.aggregate_clause())

            # Apply each aggregation
            aggregate_results = []
            for func, field in aggregations:
                agg_result = self.aggregator.aggregate(
                    results, func, field, grouped_results
                )
                aggregate_results.append(agg_result)

            # If multiple aggregations, return list; if one, return single result
            if len(aggregate_results) == 1:
                return aggregate_results[0]
            # For multiple aggregations, combine into a single result
            # For now, just return the first one (TODO: support multiple)
            return aggregate_results[0]

        # Step 5: If GROUP BY without AGGREGATE, return grouped results
        if grouped_results is not None:
            return grouped_results

        # Step 6: Apply ORDER BY if specified
        if ctx.orderby_clause():
            results = self._apply_ordering(results, ctx.orderby_clause())

        # Step 7: Apply LIMIT/OFFSET if specified
        if ctx.limit_clause():
            results = self._apply_limit(results, ctx.limit_clause())

        # Step 8: Wrap with NamedQueryResult if pattern names were used
        if self.pattern_names and any(name is not None for name in self.pattern_names):
            return NamedQueryResult(results, self.pattern_names)

        return results

    def visitQuery_seq(
        self, ctx: PrismQLParser.Query_seqContext
    ) -> tuple[
        list[Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]],
        bool,
    ]:
        """
        Process a sequence of subqueries.

        Handles both:
        - Unordered subqueries (semicolon-separated): collected for later INWIN merging
        - Positional subqueries (FOLLOWED_BY/PRECEDED_BY): merged sequentially

        Returns a tuple of (results, is_positional). When is_positional is
        True the list holds a single, already-merged sequential result that
        must not be window-merged again.
        """
        # Get first query context (grammar: '(' query ')' query_seq_continuation*)
        first_query = ctx.query()

        # Get all continuations (each has its own query)
        continuations = (
            ctx.query_seq_continuation()
            if hasattr(ctx, "query_seq_continuation")
            else []
        )

        # Build list of all query contexts
        query_contexts = [first_query] + [cont.query() for cont in continuations]

        # If no continuations, just return the single query result as a list
        if not continuations:
            result = self.visitQuery(query_contexts[0])
            return [result], False

        # Check if we have any positional operators
        has_positional = any(
            isinstance(cont, PrismQLParser.PositionalSubqueryContext)
            for cont in continuations
        )

        # If all unordered (semicolons), collect all results for later merging
        if not has_positional:
            results: list[
                Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]
            ] = []
            for query_ctx in query_contexts:
                result = self.visitQuery(query_ctx)
                results.append(result)
            return results, False

        # Otherwise, process sequentially with positional operators
        # Start with the first query
        current_result = self.visitQuery(query_contexts[0])

        # Unwrap if NamedQueryResult
        if isinstance(current_result, NamedQueryResult):
            current_result = current_result.to_list()

        # Validate that it's a QueryResult (not aggregated/grouped)
        if isinstance(current_result, (AggregateResult, GroupedResult)):
            raise ValueError(
                "Positional operators between subqueries require non-aggregated results"
            )

        # Process each continuation
        for i, continuation in enumerate(continuations):
            next_query = self.visitQuery(query_contexts[i + 1])

            # Unwrap if NamedQueryResult
            if isinstance(next_query, NamedQueryResult):
                next_query = next_query.to_list()

            # Validate
            if isinstance(next_query, (AggregateResult, GroupedResult)):
                raise ValueError(
                    "Positional operators between subqueries require non-aggregated results"
                )

            if isinstance(continuation, PrismQLParser.PositionalSubqueryContext):
                # Get operator and window
                op = continuation.positional_op()
                window = int(continuation.number().getText())

                # Apply positional operator
                current_result = self._merge_subqueries_positional(
                    current_result,
                    next_query,
                    op,
                    window,
                )
            else:
                # UnorderedSubquery - this shouldn't happen in our simplified model
                # but if it does, we'd need to collect and merge with INWIN
                raise ValueError(
                    "Mixing semicolon and positional operators in subqueries is not supported"
                )

        # Return as a list with single merged result
        return [current_result], True

    def visitRestrictions(
        self, ctx: PrismQLParser.RestrictionsContext
    ) -> tuple[list[MessageGroup], bool]:
        """
        Process comma-separated restrictions.

        Returns a tuple of (list of message groups, is_sequential_result).
        The is_sequential_result flag indicates if the result contains
        pre-computed sequences from FOLLOWED_BY/PRECEDED_BY operators.
        Handles quantifiers by expanding restrictions.
        """
        restriction_results = []
        has_sequential_operator = False

        # Process each named restriction
        for named_restriction_ctx in ctx.named_restriction():
            # Extract pattern name if present
            pattern_name = None
            if named_restriction_ctx.As():
                # Get QUOTED_STRING and strip quotes
                quoted_name = named_restriction_ctx.QUOTED_STRING().getText()
                # Remove surrounding quotes (either " or ')
                pattern_name = quoted_name[1:-1]

            # Extract quantifier if present
            min_count, max_count = self._extract_quantifier(named_restriction_ctx)

            # Track how many constraints exist before visiting this restriction
            num_constraints_before = len(self.variable_constraints)
            self._seq_leg_constraints = []
            self._seq_partition_key = None

            # Process the underlying restriction
            result = self.visitRestriction(named_restriction_ctx.restriction())

            # A PartialSequence escaping here means a chain's final link had
            # no window — raise a teachable error instead of crashing later.
            if isinstance(result, PartialSequence):
                raise PrismQLRuntimeError(
                    "Sequential chain is missing a window constraint on its final "
                    "link. Add INWINDOW <n> or DURING <time> at the end of the "
                    "chain — a trailing window applies to every windowless link."
                )

            # Check if any new constraints were added (indicating a variable was used)
            new_constraints = self.variable_constraints[num_constraints_before:]

            # Check if result is a sequence (from FOLLOWED_BY/PRECEDED_BY) or a set
            if isinstance(result, list):
                # Result is already a list of message groups (sequences)
                has_sequential_operator = True
                if new_constraints:
                    # Constraints inside a chain were all recorded at the
                    # same position; map each leg's bucket to the leg's
                    # chronological index in the group instead. This is only
                    # well-defined when the chain IS the whole result —
                    # window-merging or permuting it would scramble the
                    # positions the validator relies on.
                    if len(ctx.named_restriction()) > 1 or min_count > 1:
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
                # For quantifiers on sequences, we need enough groups
                if min_count > 1:
                    # We need at least min_count groups
                    # For now, just take the first min_count groups
                    # TODO: Support range matching and finding all combinations
                    if len(result) < min_count:
                        # Not enough matching sequences - return empty
                        return ([], False)
                    # Add each group separately
                    for group in result[:min_count]:
                        restriction_results.append(sorted(group))
                        self.pattern_names.append(pattern_name)
                        self.current_restriction_position += 1
                else:
                    # No quantifier - add all groups
                    for group in result:
                        restriction_results.append(sorted(group))
                        self.pattern_names.append(pattern_name)
                        self.current_restriction_position += 1
            else:
                # Result is a set of message IDs (normal restriction)
                # Convert set to sorted list
                sorted_result = sorted(result)

                # Apply quantifier by expanding the restriction
                # For now, we use min_count (exact or minimum)
                # TODO: Support range matching (min to max)
                if min_count > 1:
                    # Expand the restriction min_count times
                    for i in range(min_count):
                        restriction_results.append(sorted_result)
                        self.pattern_names.append(pattern_name)

                        # If this restriction added variable constraints and it's not the first occurrence,
                        # duplicate those constraints for this position
                        if i > 0 and new_constraints:
                            for constraint in new_constraints:
                                self.variable_constraints.append(
                                    VariableConstraint(
                                        variable_name=constraint.variable_name,
                                        field_name=constraint.field_name,
                                        position=self.current_restriction_position,
                                    )
                                )

                        self.current_restriction_position += 1
                else:
                    # No quantifier or {1} - process normally
                    restriction_results.append(sorted_result)
                    self.pattern_names.append(pattern_name)
                    self.current_restriction_position += 1

        # Return as-is (will be merged by window processor or returned directly if sequential)
        return (restriction_results, has_sequential_operator)

    def visitRestriction(
        self, ctx: PrismQLParser.RestrictionContext
    ) -> Union[set[MessageId], list[MessageGroup], PartialSequence]:
        """
        Process the sequential layer of a restriction.

        The grammar guarantees chains nest LEFT: ``A FOLLOWED_BY B FOLLOWED_BY
        C INWINDOW 10`` arrives as ``((A FOLLOWED_BY B) FOLLOWED_BY C INWINDOW
        10)``, so a trailing window reaches the outermost link and distributes
        to windowless inner links via PartialSequence deferred evaluation.

        Returns:
            - set[MessageId] for plain boolean restrictions (fallthrough)
            - list[MessageGroup] for evaluated sequential operators
            - PartialSequence for a windowless link, to be evaluated with an
              enclosing link's window
        """
        # Fallthrough: no sequential operator at this level
        if (
            not ctx.FollowedBy()
            and not ctx.PrecededBy()
            and not ctx.NotFollowedBy()
            and not ctx.NotPrecededBy()
        ):
            return self.visitBool_restriction(ctx.bool_restriction())

        n_before_lhs = len(self.variable_constraints)
        lhs = self.visitRestriction(ctx.restriction())
        if not self._seq_leg_constraints:
            # Innermost leg of the chain: the lhs visit above fell through to
            # the boolean layer, so everything it recorded is one leg bucket.
            self._seq_leg_constraints = [list(self.variable_constraints[n_before_lhs:])]
            self._seq_partition_key = self._leg_key(self._seq_leg_constraints[0])
        n_before_rhs = len(self.variable_constraints)
        rhs = self.visitBool_restriction(ctx.bool_restriction())
        rhs_leg = list(self.variable_constraints[n_before_rhs:])
        # Correlation key survives only while every leg repeats it exactly.
        if (ctx.FollowedBy() or ctx.PrecededBy()) and (
            self._seq_partition_key is None
            or self._leg_key(rhs_leg) != self._seq_partition_key
        ):
            self._seq_partition_key = None
        window = self._extract_window_constraint(ctx)

        # The right operand comes from the boolean layer; a list or
        # PartialSequence can only appear via parenthesized sequential
        # expressions, which are not supported as right operands.
        if isinstance(rhs, (list, PartialSequence)):
            raise PrismQLRuntimeError(
                "Sequential operators require simple conditions on the "
                "right-hand side, not nested sequences"
            )

        # Track each leg's variable constraints in chronological group order:
        # FOLLOWED_BY appends its rhs message to the group, PRECEDED_BY
        # prepends it. visitRestrictions rewrites constraint positions from
        # these buckets once the chain is complete.
        if ctx.FollowedBy():
            self._seq_leg_constraints.append(rhs_leg)
            return self._apply_sequential_link(lhs, rhs, window, "FOLLOWED_BY")
        if ctx.PrecededBy():
            self._seq_leg_constraints.insert(0, rhs_leg)
            return self._apply_sequential_link(lhs, rhs, window, "PRECEDED_BY")
        if rhs_leg:
            # The excluded message never appears in the result group, so a
            # variable on it has nothing to bind to.
            raise PrismQLRuntimeError(
                "Pattern variables are not supported on the right-hand side "
                "of NOT_FOLLOWED_BY/NOT_PRECEDED_BY — the excluded message "
                "is not part of the result group. Use a concrete condition."
            )
        if ctx.NotFollowedBy():
            return self._apply_negative_link(lhs, rhs, window, "NOT_FOLLOWED_BY")
        return self._apply_negative_link(lhs, rhs, window, "NOT_PRECEDED_BY")

    @staticmethod
    def _leg_key(
        bucket: list[VariableConstraint],
    ) -> Optional[tuple[str, str]]:
        """The (variable, field) a leg correlates on, if exactly one."""
        if len(bucket) == 1:
            return (bucket[0].variable_name, bucket[0].field_name)
        return None

    def _apply_sequential_link(
        self,
        lhs: Union[set[MessageId], list[MessageGroup], PartialSequence],
        rhs: set[MessageId],
        window: Optional[WindowConstraint],
        operator: str,
    ) -> Union[list[MessageGroup], PartialSequence]:
        """Evaluate one FOLLOWED_BY/PRECEDED_BY link, chaining through lhs."""
        # No window: defer — an enclosing link's trailing window evaluates us.
        if window is None:
            return PartialSequence(lhs, rhs, operator)

        evaluated = self._evaluate_partial_sequence(lhs, window)

        # Correlation-key pushdown: when every leg shares one $var on the
        # same field, greedy matching must run within each field-value
        # partition. Greedy-global would pair each lhs with its nearest rhs
        # from ANY partition; the validator then kills the mixed group and
        # the in-partition match it shadowed is silently lost.
        if self._seq_partition_key is not None:
            return self._apply_link_partitioned(
                evaluated, rhs, window, operator, self._seq_partition_key[1]
            )
        return self._apply_link_evaluated(evaluated, rhs, window, operator)

    def _apply_link_evaluated(
        self,
        lhs: Union[set[MessageId], list[MessageGroup]],
        rhs: set[MessageId],
        window: WindowConstraint,
        operator: str,
    ) -> list[MessageGroup]:
        """Dispatch one positive link on an already-evaluated lhs."""
        forward = operator == "FOLLOWED_BY"

        # Temporal window (DURING)
        if isinstance(window, tuple):
            duration = self._duration_tuple_to_timedelta(window)
            if isinstance(lhs, list):
                if forward:
                    return self._extend_sequences_followed_by_temporal(
                        lhs, rhs, duration
                    )
                return self._extend_sequences_preceded_by_temporal(lhs, rhs, duration)
            return self._create_sequential_pairs_temporal(
                lhs, rhs, duration, forward=forward
            )

        # Positional window (INWINDOW)
        window_size: int = window
        if isinstance(lhs, list):
            if forward:
                return self._extend_sequences_followed_by(lhs, rhs, window_size)
            return self._extend_sequences_preceded_by(lhs, rhs, window_size)
        if forward:
            matching_lhs = self._apply_followed_by(lhs, rhs, window_size)
        else:
            matching_lhs = self._apply_preceded_by(lhs, rhs, window_size)
        return self._create_sequential_pairs(
            matching_lhs, rhs, window_size, forward=forward
        )

    def _apply_link_partitioned(
        self,
        lhs: Union[set[MessageId], list[MessageGroup]],
        rhs: set[MessageId],
        window: WindowConstraint,
        operator: str,
        field: str,
    ) -> list[MessageGroup]:
        """Run one positive link independently within each partition of the
        correlation field (the EQL `sequence by` evaluation shape)."""
        id_field = getattr(self.search_backend, "id_field", "id")

        def value_map(ids: set[MessageId]) -> dict[MessageId, Any]:
            docs = self.search_backend.get_documents(list(ids))
            return {doc[id_field]: doc.get(field) for doc in docs if id_field in doc}

        rhs_parts: dict[Any, set[MessageId]] = {}
        for mid, value in value_map(rhs).items():
            if value is not None:
                rhs_parts.setdefault(value, set()).add(mid)

        lhs_parts: dict[Any, Any] = {}
        if isinstance(lhs, list):
            # Sequences: every member shares the key by construction of the
            # previous partitioned link, so key by the first message.
            firsts = {group[0] for group in lhs if group}
            first_values = value_map(firsts)
            for group in lhs:
                value = first_values.get(group[0]) if group else None
                if value is not None:
                    lhs_parts.setdefault(value, []).append(group)
        else:
            for mid, value in value_map(lhs).items():
                if value is not None:
                    lhs_parts.setdefault(value, set()).add(mid)

        results: list[MessageGroup] = []
        for value, lhs_part in lhs_parts.items():
            rhs_part = rhs_parts.get(value)
            if not rhs_part:
                continue
            results.extend(
                self._apply_link_evaluated(lhs_part, rhs_part, window, operator)
            )
        results.sort(key=lambda group: group[0] if group else 0)
        return results

    def _apply_negative_link(
        self,
        lhs: Union[set[MessageId], list[MessageGroup], PartialSequence],
        rhs: set[MessageId],
        window: Optional[WindowConstraint],
        operator: str,
    ) -> Union[set[MessageId], list[MessageGroup]]:
        """Evaluate one NOT_FOLLOWED_BY/NOT_PRECEDED_BY link."""
        forward = operator == "NOT_FOLLOWED_BY"

        # Negative lookarounds must carry their own window and cannot chain.
        if window is None:
            raise PrismQLRuntimeError(
                f"{operator} requires a window constraint (INWINDOW or DURING)"
            )
        lhs = self._evaluate_partial_sequence(lhs, window)
        if isinstance(lhs, list):
            raise PrismQLRuntimeError(
                f"{operator} cannot be chained with other sequential operators"
            )

        if isinstance(window, tuple):
            duration = self._duration_tuple_to_timedelta(window)
            if forward:
                return self._apply_not_followed_by_temporal(lhs, rhs, duration)
            return self._apply_not_preceded_by_temporal(lhs, rhs, duration)
        if forward:
            return self._apply_not_followed_by(lhs, rhs, window)
        return self._apply_not_preceded_by(lhs, rhs, window)

    def visitBool_restriction(
        self, ctx: PrismQLParser.Bool_restrictionContext
    ) -> Union[set[MessageId], list[MessageGroup], PartialSequence]:
        """
        Process the boolean layer: NOT > AND > OR, parentheses, conditions.

        Lists/PartialSequences can only enter this layer through parenthesized
        sequential expressions; the boolean operators reject them explicitly.
        """
        # Handle NOT operator (binds tightest)
        if ctx.Not():
            excluded = self.visitBool_restriction(ctx.bool_restriction(0))
            if isinstance(excluded, (list, PartialSequence)):
                raise PrismQLRuntimeError(
                    "NOT operator cannot be used with sequential operators (FOLLOWED_BY, PRECEDED_BY). "
                    "Sequential operators return message sequences, not individual messages."
                )
            # Get all message IDs up to a reasonable limit
            total_docs = min(
                self.MAX_MESSAGES_NOT, self.search_backend.get_total_documents()
            )
            all_messages = self.search_backend.get_all_document_ids(limit=total_docs)
            return all_messages - excluded  # Set difference

        # Handle AND operator
        if ctx.And():
            lhs = self.visitBool_restriction(ctx.bool_restriction(0))
            rhs = self.visitBool_restriction(ctx.bool_restriction(1))
            # AND requires both operands to be sets, not sequences or partial sequences
            if isinstance(lhs, (list, PartialSequence)) or isinstance(
                rhs, (list, PartialSequence)
            ):
                raise PrismQLRuntimeError(
                    "AND operator cannot be used with sequential operators (FOLLOWED_BY, PRECEDED_BY). "
                    "Sequential operators return message sequences, not individual messages."
                )
            return lhs & rhs  # Set intersection

        # Handle OR operator
        if ctx.Or():
            lhs = self.visitBool_restriction(ctx.bool_restriction(0))
            rhs = self.visitBool_restriction(ctx.bool_restriction(1))
            # OR requires both operands to be sets, not sequences or partial sequences
            if isinstance(lhs, (list, PartialSequence)) or isinstance(
                rhs, (list, PartialSequence)
            ):
                raise PrismQLRuntimeError(
                    "OR operator cannot be used with sequential operators (FOLLOWED_BY, PRECEDED_BY). "
                    "Sequential operators return message sequences, not individual messages."
                )
            return lhs | rhs  # Set union

        # Handle parentheses - the inner expression is a full restriction,
        # so parenthesized sequential expressions are visible to callers
        if ctx.restriction():
            return self.visitRestriction(ctx.restriction())

        # Handle condition
        if ctx.condition():
            return self.visitCondition(ctx.condition())

        # This shouldn't happen with a valid parse tree
        raise PrismQLRuntimeError("Invalid restriction in parse tree")

    def visitCondition(self, ctx: PrismQLParser.ConditionContext) -> set[MessageId]:
        """Evaluate a single condition."""

        # New fluent operators (preferred)
        # contains(dict_name) - same as haswordofdict
        if ctx.Contains():
            dict_name = ctx.hdict().getText()

            # Check if this is wildcard - match all messages
            if dict_name == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # Check if this is a variable
            if dict_name.startswith("$"):
                # Variables in contains() not yet supported - would need text field tracking
                raise PrismQLRuntimeError(
                    "Variables in contains() not yet supported. "
                    "Use from($user) for user-based variables."
                )

            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            return self._search_dictionary(dict_name)

        # contains_tokens(dict_name) - Unicode-aware token matching
        if ctx.ContainsTokens():
            dict_name = ctx.hdict().getText()

            # Check if this is wildcard - match all messages
            if dict_name == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # Check if this is a variable
            if dict_name.startswith("$"):
                # Variables in contains_tokens() not yet supported
                raise PrismQLRuntimeError(
                    "Variables in contains_tokens() not yet supported. "
                    "Use from($user) for user-based variables."
                )

            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            tokens = self.user_dictionaries[dict_name]
            return self.search_backend.search_tokens(
                tokens, field="text", operator="OR"
            )

        # contains_phrase("phrase") - N-gram based phrase matching
        if ctx.ContainsPhrase():
            phrase_text = ctx.QUOTED_STRING().getText()
            # Remove surrounding quotes
            phrase = phrase_text[1:-1]  # Strip first and last character
            return self.search_backend.search_phrase(phrase, field="text")

        # from(username) - same as byuser
        if ctx.From():
            username = ctx.huser().getText()

            # Check if this is wildcard - match all users/messages
            if username == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # Check if this is a variable
            if username.startswith("$"):
                var_name = username[1:]  # Remove $ prefix
                # Record variable constraint
                self.variable_constraints.append(
                    VariableConstraint(
                        variable_name=var_name,
                        field_name="user",
                        position=self.current_restriction_position,
                    )
                )
                # Return all messages (variable will be validated later)
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            return self.search_backend.search_by_field("user", username, exact=True)

        # mentions_user(username) - same as hasusermentioned
        if ctx.MentionsUser():
            username = ctx.huser().getText()

            # Check if this is wildcard - match all messages
            if username == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # First check precomputed index
            if username in self.precomputed_indexes.user_mentions:
                return self.precomputed_indexes.user_mentions[username]
            # Otherwise search in text
            return self.search_backend.search_text([username], field="text")

        # is_question() - same as hasquestion
        if ctx.IsQuestion():
            return self._get_questions()

        # NER-based fluent conditions
        if ctx.MentionsDate():
            return self._get_ner_messages("DATE")
        if ctx.MentionsTime():
            return self._get_ner_messages("TIME")
        if ctx.MentionsPlace():
            return self._get_ner_messages("GPE")  # or "LOC" depending on NLP backend
        if ctx.MentionsOrg():
            return self._get_ner_messages("ORG")
        if ctx.ContainsLink():
            return self._get_ner_messages("URL")

        # Custom feature lookup
        if ctx.HasFeature():
            feature_name = ctx.feature_name().getText()
            return self._get_custom_feature(feature_name)
        if ctx.LabeledAs():
            feature_name = ctx.feature_name().getText()
            return self._get_custom_feature(feature_name)

        # field(name, value[, matcher]) - generic field predicate.
        # from(x) is the canonical alias for field(user, x).
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

            # Wildcard - match all messages
            if raw_value == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # Variable - same-value constraint on this field
            if raw_value.startswith("$"):
                self.variable_constraints.append(
                    VariableConstraint(
                        variable_name=raw_value[1:],
                        field_name=fname,
                        position=self.current_restriction_position,
                    )
                )
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # Strip quotes from QUOTED_STRING values
            if raw_value[0] in "\"'" and raw_value[-1] == raw_value[0]:
                raw_value = raw_value[1:-1]

            return self.search_backend.search_by_field(fname, raw_value, exact=exact)

        # Legacy operators (backward compatibility - DEPRECATED)
        if ctx.HasWordOfDict():
            warnings.warn(
                "haswordofdict() is deprecated and will be removed in v1.0. "
                "Use contains() instead: 'contains(dict_name)'",
                DeprecationWarning,
                stacklevel=2,
            )
            dict_name = ctx.hdict().getText()

            # Check if this is wildcard - match all messages
            if dict_name == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            return self._search_dictionary(dict_name)

        if ctx.ByUser():
            warnings.warn(
                "byuser() is deprecated and will be removed in v1.0. "
                "Use from() instead: 'from(username)'",
                DeprecationWarning,
                stacklevel=2,
            )
            username = ctx.huser().getText()

            # Check if this is wildcard - match all users/messages
            if username == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            # Check if this is a variable
            if username.startswith("$"):
                var_name = username[1:]  # Remove $ prefix
                # Record variable constraint
                self.variable_constraints.append(
                    VariableConstraint(
                        variable_name=var_name,
                        field_name="user",
                        position=self.current_restriction_position,
                    )
                )
                # Return all messages (variable will be validated later)
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            return self.search_backend.search_by_field("user", username, exact=True)

        if ctx.HasUserMentioned():
            warnings.warn(
                "hasusermentioned() is deprecated and will be removed in v1.0. "
                "Use mentions_user() instead: 'mentions_user(username)'",
                DeprecationWarning,
                stacklevel=2,
            )
            username = ctx.huser().getText()

            # Check if this is wildcard - match all messages
            if username == "*":
                total_docs = self.search_backend.get_total_documents()
                return self.search_backend.get_all_document_ids(limit=total_docs)

            if username in self.precomputed_indexes.user_mentions:
                return self.precomputed_indexes.user_mentions[username]
            return self.search_backend.search_text([username], field="text")

        if ctx.HasQuestion():
            warnings.warn(
                "hasquestion() is deprecated and will be removed in v1.0. "
                "Use is_question() instead: 'is_question()'",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._get_questions()

        if ctx.HasDate():
            warnings.warn(
                "hasdate() is deprecated and will be removed in v1.0. "
                "Use mentions_date() instead: 'mentions_date()'",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._get_ner_messages("DATE")
        if ctx.HasTime():
            warnings.warn(
                "hastime() is deprecated and will be removed in v1.0. "
                "Use mentions_time() instead: 'mentions_time()'",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._get_ner_messages("TIME")
        if ctx.HasLocation():
            warnings.warn(
                "haslocation() is deprecated and will be removed in v1.0. "
                "Use mentions_place() instead: 'mentions_place()'",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._get_ner_messages("GPE")
        if ctx.HasOrganization():
            warnings.warn(
                "hasorganization() is deprecated and will be removed in v1.0. "
                "Use mentions_org() instead: 'mentions_org()'",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._get_ner_messages("ORG")
        if ctx.HasURL():
            warnings.warn(
                "hasurl() is deprecated and will be removed in v1.0. "
                "Use contains_link() instead: 'contains_link()'",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._get_ner_messages("URL")

        raise PrismQLRuntimeError("Unknown condition type")

    def _search_dictionary(self, dict_name: str) -> set[MessageId]:
        """Resolve a dictionary condition with per-term routing.

        Multi-word terms always go through the n-gram phrase engine —
        token mode would otherwise silently match nothing for them, and a
        term written with a space can only mean those words in that
        order. Single-word terms use the dictionary's `match` mode when
        declared, else the engine-wide text_match.
        """
        words = self.user_dictionaries[dict_name]
        phrases = [t for t in words if " " in t.strip()]
        singles = [t for t in words if " " not in t.strip()]
        mode = self.dictionary_modes.get(dict_name, self.text_match)

        results: set[MessageId] = set()
        for phrase in phrases:
            results |= self.search_backend.search_phrase(phrase, field="text")
        if singles:
            if mode == "token":
                results |= self.search_backend.search_tokens(
                    singles, field="text", operator="OR"
                )
            else:
                results |= self.search_backend.search_text(
                    singles, field="text", operator="OR"
                )
        return results

    def _get_questions(self) -> set[MessageId]:
        """Helper method to get questions (used by both new and legacy operators)."""
        # A computed questions index is authoritative — even when empty, it
        # must not fall through to the backend heuristic.
        if self.precomputed_indexes.has_questions_index:
            return self.precomputed_indexes.questions

        # Check if backend supports question detection
        if hasattr(self.search_backend, "get_questions"):
            result = self.search_backend.get_questions()
            return set(result) if result is not None else set()

        raise PrismQLRuntimeError(
            "is_question() has no backing here: this backend builds no "
            "question index and none was precomputed. Provide "
            "PrecomputedIndexes(questions={...}) at engine construction — "
            "question detection is vocabulary, not grammar; any "
            "ingestion-time annotator (heuristic, spaCy, LLM) can supply it."
        )

    def _get_ner_messages(self, ner_label: str) -> set[MessageId]:
        """Get messages containing specific NER type."""
        entities = self.precomputed_indexes.entities
        if ner_label in entities:
            return entities[ner_label]

        available = sorted(entities)
        hint = f"Available entity labels: {', '.join(available)}. " if available else ""
        raise PrismQLRuntimeError(
            f"No entity index for label '{ner_label}'. {hint}"
            "Entity conditions (mentions_org(), mentions_date(), ...) are "
            "vocabulary backed by precomputed indexes: provide "
            f"PrecomputedIndexes(entities={{'{ner_label}': {{...}}}}) at "
            "engine construction — annotate at ingestion with spaCy, an "
            "LLM, or any extractor."
        )

    def _get_custom_feature(self, feature_name: str) -> set[MessageId]:
        """
        Get messages with a custom feature.

        This looks up precomputed custom features from the indexes.
        Features must be precomputed during data ingestion (via LLM annotations,
        human labels, or other extraction methods).

        Args:
            feature_name: Name of the custom feature to look up

        Returns:
            Set of message IDs with this feature

        Raises:
            PrismQLRuntimeError: If feature not found in precomputed indexes

        Example:
            >>> # After building indexes with custom features like:
            >>> # PrecomputedIndexes(custom_features={
            >>> #     'sentiment_positive': {1, 5, 8},
            >>> #     'intent_request': {2, 4}
            >>> # })
            >>> result = engine.execute("SELECT has_feature(sentiment_positive)")
        """
        if feature_name in self.precomputed_indexes.custom_features:
            return self.precomputed_indexes.custom_features[feature_name]

        # Feature not found - provide helpful error message
        available_features = list(self.precomputed_indexes.custom_features.keys())
        if available_features:
            raise PrismQLRuntimeError(
                f"Feature '{feature_name}' not found in precomputed indexes. "
                f"Available features: {', '.join(available_features[:10])}"
                + ("..." if len(available_features) > 10 else "")
            )
        raise PrismQLRuntimeError(
            f"Feature '{feature_name}' not found. No custom features have been "
            "precomputed. Use IndexBuilder to create feature indexes from your "
            "annotations (LLM-generated, human labels, etc.)."
        )

    def _generate_all_combinations(self, groups: list[MessageGroup]) -> QueryResult:
        """
        Generate ALL possible combinations of messages from restriction groups.

        This is used for temporal windows where we want all combinations,
        not just non-overlapping pairs from the greedy algorithm.

        Args:
            groups: List of message groups (one per restriction)

        Returns:
            All possible combinations (cartesian product)
        """
        if not groups:
            return []

        # If single group, each message becomes its own result group
        if len(groups) == 1:
            return [[msg_id] for msg_id in groups[0]]

        # Generate cartesian product of all groups
        import itertools

        all_combinations = list(itertools.product(*groups))
        # Convert tuples to lists
        return [list(combo) for combo in all_combinations]

    def _merge_restrictions(
        self, groups: list[MessageGroup], window_size: int
    ) -> QueryResult:
        """
        Merge restriction results within sliding windows.

        This implements the core windowing logic that groups messages
        that appear within window_size of each other.
        """
        if not groups:
            return []

        # If single group, each message becomes its own result group
        if len(groups) == 1:
            return [[msg_id] for msg_id in groups[0]]

        # Otherwise, implement sliding window merge
        # This is a simplified version - full implementation would use
        # the histogram-based algorithm from the C# code
        from ..processors.window import WindowProcessor

        return WindowProcessor.merge_restrictions(groups, window_size)

    def _merge_queries(
        self,
        subquery_results: list[Union[QueryResult, AggregateResult, GroupedResult]],
        window_size: int,
    ) -> QueryResult:
        """Merge results from multiple subqueries."""
        if not subquery_results:
            return []

        # Validate that subqueries don't have aggregations
        for i, result in enumerate(subquery_results):
            if isinstance(result, (AggregateResult, GroupedResult)):
                raise ValueError(
                    f"Subquery {i + 1} contains aggregation/grouping which is not "
                    "supported in query sequences. Apply aggregation at the top level."
                )

        # Flatten all groups from all subqueries
        all_groups: list[MessageGroup] = []
        for subquery_result in subquery_results:
            all_groups.extend(subquery_result)  # type: ignore[arg-type]

        # Apply window processing
        from ..processors.window import WindowProcessor

        return WindowProcessor.merge_queries(all_groups, window_size)

    @staticmethod
    def _groups_by_boundary(
        groups: list[MessageGroup], end: bool
    ) -> dict[MessageId, list[MessageGroup]]:
        """Index groups by their boundary message: last (max) or first (min)."""
        bounds: dict[MessageId, list[MessageGroup]] = {}
        for group in groups:
            boundary = max(group) if end else min(group)
            bounds.setdefault(boundary, []).append(group)
        return bounds

    def _merge_subqueries_positional(
        self,
        lhs_result: QueryResult,
        rhs_result: QueryResult,
        operator_ctx: Any,
        window: int,
    ) -> QueryResult:
        """
        Merge two subquery results using a positional operator.

        Operates on whole groups: group A is FOLLOWED_BY group B when every
        message of A precedes every message of B and the positional distance
        from A's last message to B's first is within the window. Greedy
        closest-match per LHS group, mirroring the restriction-level
        sequential semantics. Matched groups are concatenated chronologically.

        Args:
            lhs_result: Result from the left subquery
            rhs_result: Result from the right subquery
            operator_ctx: The positional operator context (FollowedBy, PrecededBy, etc.)
            window: Window size for the operator

        Returns:
            Merged query result with groups that satisfy the positional constraint
        """
        lhs_groups = [group for group in lhs_result if group]
        rhs_groups = [group for group in rhs_result if group]
        op = operator_ctx.getText().upper().replace("_", "")

        if op in ("FOLLOWEDBY", "NOTFOLLOWEDBY"):
            # Constraint runs forward from each LHS group's end to an RHS
            # group's start.
            lhs_bounds = self._groups_by_boundary(lhs_groups, end=True)
            rhs_bounds = self._groups_by_boundary(rhs_groups, end=False)
        elif op in ("PRECEDEDBY", "NOTPRECEDEDBY"):
            # Constraint runs backward from each LHS group's start to an RHS
            # group's end.
            lhs_bounds = self._groups_by_boundary(lhs_groups, end=False)
            rhs_bounds = self._groups_by_boundary(rhs_groups, end=True)
        else:
            raise ValueError(f"Unknown positional operator: {operator_ctx.getText()}")

        lhs_ids = set(lhs_bounds)
        rhs_ids = set(rhs_bounds)

        if op == "FOLLOWEDBY":
            matching_lhs = self._apply_followed_by(lhs_ids, rhs_ids, window)
            pairs = self._create_sequential_pairs(
                matching_lhs, rhs_ids, window, forward=True
            )
            return [
                sorted(a_group) + sorted(b_group)
                for a_end, b_start in pairs
                for a_group in lhs_bounds[a_end]
                for b_group in rhs_bounds[b_start]
            ]
        if op == "PRECEDEDBY":
            matching_lhs = self._apply_preceded_by(lhs_ids, rhs_ids, window)
            # Pairs come back chronological: [rhs_end, lhs_start]
            pairs = self._create_sequential_pairs(
                matching_lhs, rhs_ids, window, forward=False
            )
            return [
                sorted(b_group) + sorted(a_group)
                for b_end, a_start in pairs
                for b_group in rhs_bounds[b_end]
                for a_group in lhs_bounds[a_start]
            ]
        if op == "NOTFOLLOWEDBY":
            surviving = self._apply_not_followed_by(lhs_ids, rhs_ids, window)
            return [
                sorted(group)
                for boundary in sorted(surviving)
                for group in lhs_bounds[boundary]
            ]
        # NOTPRECEDEDBY
        surviving = self._apply_not_preceded_by(lhs_ids, rhs_ids, window)
        return [
            sorted(group)
            for boundary in sorted(surviving)
            for group in lhs_bounds[boundary]
        ]

    def _evaluate_partial_sequence(
        self,
        value: Union[set[MessageId], list[MessageGroup], PartialSequence],
        window: WindowConstraint,
    ) -> Union[set[MessageId], list[MessageGroup]]:
        """
        Recursively evaluate a PartialSequence with the given window constraint.

        Args:
            value: Either a concrete value (set/list) or PartialSequence to evaluate
            window: Window constraint to use for evaluation

        Returns:
            Evaluated result (set or list, never PartialSequence)
        """
        # Base case: already evaluated
        if not isinstance(value, PartialSequence):
            return value

        # Recursive case: the link's rhs always comes from the boolean layer
        # (a set); evaluate defensively, then delegate to the link helpers,
        # which evaluate the lhs chain themselves with this same window.
        partial = value
        rhs = self._evaluate_partial_sequence(partial.rhs, window)
        if isinstance(rhs, list):
            raise PrismQLRuntimeError(
                "Sequential operators require simple conditions on the "
                "right-hand side, not nested sequences"
            )

        if partial.operator in ("FOLLOWED_BY", "PRECEDED_BY"):
            result = self._apply_sequential_link(
                partial.lhs, rhs, window, partial.operator
            )
            # window is non-None here, so the link is always fully evaluated
            assert not isinstance(result, PartialSequence)
            return result
        if partial.operator in ("NOT_FOLLOWED_BY", "NOT_PRECEDED_BY"):
            return self._apply_negative_link(partial.lhs, rhs, window, partial.operator)

        raise ValueError(f"Unknown sequential operator: {partial.operator}")

    def _create_sequential_pairs(
        self,
        lhs_messages: set[MessageId],
        rhs_messages: set[MessageId],
        window: int,
        forward: bool,
    ) -> QueryResult:
        """
        Create pairs of messages that satisfy a sequential constraint.

        Uses Rust backend when available for 10-100x speedup on FOLLOWED_BY and
        PRECEDED_BY queries.

        Args:
            lhs_messages: Left-hand side message IDs (already filtered to matching ones)
            rhs_messages: Right-hand side message IDs
            window: Window size
            forward: True for FOLLOWED_BY (look forward), False for PRECEDED_BY (look backward)

        Returns:
            List of message groups, each containing a pair [lhs_msg, rhs_msg]
        """
        if not lhs_messages or not rhs_messages:
            return []

        # Try Rust backend for FOLLOWED_BY with numeric IDs (massive performance boost!)
        if (
            forward
            and RUST_FOLLOWED_BY_AVAILABLE
            and all(isinstance(msg_id, int) for msg_id in lhs_messages)
            and all(isinstance(msg_id, int) for msg_id in rhs_messages)
        ):
            try:
                return rust_merge_followed_by(  # type: ignore[no-any-return]
                    list(lhs_messages), list(rhs_messages), window
                )
            except Exception:  # noqa: S110
                # Fall back to Python on any error (intentional)
                pass

        # Try Rust backend for PRECEDED_BY with numeric IDs (massive performance boost!)
        if (
            not forward
            and RUST_PRECEDED_BY_AVAILABLE
            and all(isinstance(msg_id, int) for msg_id in lhs_messages)
            and all(isinstance(msg_id, int) for msg_id in rhs_messages)
        ):
            try:
                return rust_merge_preceded_by(  # type: ignore[no-any-return]
                    list(lhs_messages), list(rhs_messages), window
                )
            except Exception:  # noqa: S110
                # Fall back to Python on any error (intentional)
                pass

        # Python fallback implementation
        # Get all document IDs to establish the full sequence
        all_ids = sorted(
            self.search_backend.get_all_document_ids(limit=self.MAX_MESSAGES_NOT)
        )
        id_to_pos = {msg_id: i for i, msg_id in enumerate(all_ids)}

        result = []
        for lhs_msg in sorted(lhs_messages):
            if lhs_msg not in id_to_pos:
                continue
            pos = id_to_pos[lhs_msg]

            # Find the closest matching RHS message within window
            if forward:
                # Look forward (FOLLOWED_BY)
                for i in range(pos + 1, min(pos + 1 + window, len(all_ids))):
                    if all_ids[i] in rhs_messages:
                        # Found a match - create a pair
                        result.append([lhs_msg, all_ids[i]])
                        break
            else:
                # Look backward (PRECEDED_BY)
                for i in range(max(0, pos - window), pos):
                    if all_ids[i] in rhs_messages:
                        # Found a match - create a pair (RHS first, then LHS for chronological order)
                        result.append([all_ids[i], lhs_msg])
                        break

        return result

    def _extend_sequences_followed_by(
        self,
        lhs_sequences: list[MessageGroup],
        rhs_messages: set[MessageId],
        window: int,
    ) -> list[MessageGroup]:
        """
        Extend existing message sequences with messages from rhs that follow.

        Used for chained FOLLOWED_BY: (A FOLLOWED_BY B) FOLLOWED_BY C
        where lhs_sequences contains pairs [A, B] and we need to extend with C.

        Args:
            lhs_sequences: List of message groups (sequences from previous FOLLOWED_BY)
            rhs_messages: Set of message IDs to look for
            window: Window size for the sequential constraint

        Returns:
            List of extended message groups, each with one additional message appended
        """
        if not lhs_sequences or not rhs_messages:
            return []

        # Get all document IDs to establish the full sequence
        all_ids = sorted(
            self.search_backend.get_all_document_ids(limit=self.MAX_MESSAGES_NOT)
        )
        id_to_pos = {msg_id: i for i, msg_id in enumerate(all_ids)}

        result = []
        for sequence in lhs_sequences:
            # Get the last message in the sequence
            last_msg = sequence[-1]
            if last_msg not in id_to_pos:
                continue
            pos = id_to_pos[last_msg]

            # Look for a message from rhs that follows within window
            for i in range(pos + 1, min(pos + 1 + window, len(all_ids))):
                if all_ids[i] in rhs_messages:
                    # Found a match - extend the sequence
                    extended = sequence + [all_ids[i]]
                    result.append(extended)
                    break

        return result

    def _extend_sequences_preceded_by(
        self,
        lhs_sequences: list[MessageGroup],
        rhs_messages: set[MessageId],
        window: int,
    ) -> list[MessageGroup]:
        """
        Extend existing message sequences with messages from rhs that precede.

        Used for chained PRECEDED_BY: (A PRECEDED_BY B) PRECEDED_BY C
        where lhs_sequences contains pairs [B, A] and we need to prepend C.

        Args:
            lhs_sequences: List of message groups (sequences from previous PRECEDED_BY)
            rhs_messages: Set of message IDs to look for
            window: Window size for the sequential constraint

        Returns:
            List of extended message groups, each with one additional message prepended
        """
        if not lhs_sequences or not rhs_messages:
            return []

        # Get all document IDs to establish the full sequence
        all_ids = sorted(
            self.search_backend.get_all_document_ids(limit=self.MAX_MESSAGES_NOT)
        )
        id_to_pos = {msg_id: i for i, msg_id in enumerate(all_ids)}

        result = []
        for sequence in lhs_sequences:
            # Get the first message in the sequence
            first_msg = sequence[0]
            if first_msg not in id_to_pos:
                continue
            pos = id_to_pos[first_msg]

            # Look for a message from rhs that precedes within window
            for i in range(max(0, pos - window), pos):
                if all_ids[i] in rhs_messages:
                    # Found a match - prepend to the sequence
                    extended = [all_ids[i]] + sequence
                    result.append(extended)
                    break

        return result

    def _parse_time_window(self, ctx: Any) -> int:
        """
        Parse time-based window and convert to position-based window size.

        For now, this is a simple conversion. In the future, this should
        use actual timestamps from messages.

        Args:
            ctx: time_value context from parser

        Returns:
            Approximate position-based window size
        """
        if ctx is None:
            return self.DEFAULT_WINDOW_SIZE

        # Get the number and unit
        number = int(ctx.number().getText())
        unit_text = ctx.time_unit().getText().lower()

        # Simple conversion: estimate messages per time unit
        # These are rough estimates and should be configurable
        conversions = {
            "s": 1,  # 1 message per second
            "second": 1,
            "seconds": 1,
            "m": 10,  # 10 messages per minute
            "minute": 10,
            "minutes": 10,
            "h": 600,  # 600 messages per hour
            "hour": 600,
            "hours": 600,
            "d": 14400,  # 14400 messages per day
            "day": 14400,
            "days": 14400,
            "w": 100000,  # 100k messages per week
            "week": 100000,
            "weeks": 100000,
        }

        multiplier = conversions.get(unit_text, 1)
        return number * multiplier

    def _duration_tuple_to_timedelta(self, window: tuple[int, str]) -> timedelta:
        """Convert a (value, unit) DURING tuple to a timedelta."""
        value, unit = window
        unit = unit.lower()
        if unit in ("s", "second", "seconds"):
            return timedelta(seconds=value)
        if unit in ("m", "minute", "minutes"):
            return timedelta(minutes=value)
        if unit in ("h", "hour", "hours"):
            return timedelta(hours=value)
        if unit in ("d", "day", "days"):
            return timedelta(days=value)
        if unit in ("w", "week", "weeks"):
            return timedelta(weeks=value)
        raise ValueError(f"Unsupported DURING time unit: {unit}")

    def _temporal_link_kernel(self, name: str) -> Optional[Any]:
        """Return the backend's temporal-link kernel method, when usable.

        Backends offering `merge_temporal_link` / `extend_temporal_link`
        (Rust) evaluate temporal sequential links without ids or timestamps
        round-tripping per message. Note: the kernels break timestamp TIES
        by ascending id (deterministic); the Python builders break ties by
        set-iteration order.
        """
        kernel = getattr(self.search_backend, name, None)
        if kernel is None:
            return None
        has_field = getattr(self.search_backend, "has_timestamp_field", None)
        if has_field is not None and not has_field(self.timestamp_field):
            return None
        return kernel

    def _get_timestamps_for_messages(
        self, msg_ids: set[MessageId]
    ) -> dict[MessageId, datetime]:
        """Fetch and parse timestamps for the given message IDs.

        Skips messages without a parseable timestamp.
        """
        if not msg_ids:
            return {}
        # Fast path: backends with a timestamp projection (Rust) return only
        # epoch scalars — no per-document dict materialization, which is the
        # dominant cost of temporal links on large corpora.
        get_timestamps = getattr(self.search_backend, "get_timestamps", None)
        if get_timestamps is not None and (
            not hasattr(self.search_backend, "has_timestamp_field")
            or self.search_backend.has_timestamp_field(self.timestamp_field)
        ):
            projected = get_timestamps(list(msg_ids), self.timestamp_field)
            return dict(projected)
        documents = self.search_backend.get_documents(list(msg_ids))
        result: dict[MessageId, datetime] = {}
        for doc in documents:
            msg_id = doc.get("id")
            ts = doc.get(self.timestamp_field)
            if msg_id is None or ts is None:
                continue
            try:
                if isinstance(ts, datetime):
                    result[msg_id] = ts
                elif isinstance(ts, (int, float)):
                    result[msg_id] = datetime.fromtimestamp(ts)
                else:
                    result[msg_id] = TemporalProcessor.parse_timestamp(str(ts))
            except (ValueError, OSError):
                continue
        return result

    def _create_sequential_pairs_temporal(
        self,
        lhs_messages: set[MessageId],
        rhs_messages: set[MessageId],
        duration: timedelta,
        forward: bool,
    ) -> QueryResult:
        """Sequential pairing using time proximity (DURING).

        Mirrors _create_sequential_pairs but measures distance in timestamps
        instead of position. For each LHS message (in chronological order),
        emits the first RHS match whose timestamp lies in the directional
        window of width `duration` around the LHS timestamp.

        Pairs are emitted in chronological order: forward→[lhs, rhs],
        backward→[rhs, lhs].
        """
        if not lhs_messages or not rhs_messages:
            return []

        kernel = self._temporal_link_kernel("merge_temporal_link")
        if kernel is not None:
            return kernel(  # type: ignore[no-any-return]
                list(lhs_messages),
                list(rhs_messages),
                self.timestamp_field,
                duration,
                forward,
            )

        timestamps = self._get_timestamps_for_messages(lhs_messages | rhs_messages)
        lhs_with_ts = sorted(
            ((mid, timestamps[mid]) for mid in lhs_messages if mid in timestamps),
            key=lambda x: x[1],
        )
        rhs_with_ts = sorted(
            ((mid, timestamps[mid]) for mid in rhs_messages if mid in timestamps),
            key=lambda x: x[1],
        )

        import bisect

        rhs_times = [t for _, t in rhs_with_ts]
        result: QueryResult = []
        for lhs_msg, t_lhs in lhs_with_ts:
            if forward:
                # First rhs strictly after t_lhs (binary search — a linear
                # scan here is O(lhs*rhs) and melts on dense partitions).
                i = bisect.bisect_right(rhs_times, t_lhs)
                if i < len(rhs_with_ts) and rhs_times[i] - t_lhs <= duration:
                    result.append([lhs_msg, rhs_with_ts[i][0]])
            else:
                # PRECEDED_BY: last rhs strictly before t_lhs.
                i = bisect.bisect_left(rhs_times, t_lhs) - 1
                if i >= 0 and t_lhs - rhs_times[i] <= duration:
                    result.append([rhs_with_ts[i][0], lhs_msg])
        return result

    def _extend_sequences_followed_by_temporal(
        self,
        lhs_sequences: list[MessageGroup],
        rhs_messages: set[MessageId],
        duration: timedelta,
    ) -> list[MessageGroup]:
        """
        Temporal counterpart of _extend_sequences_followed_by.

        Extends each sequence with the earliest rhs message whose timestamp
        lies in (t_last, t_last + duration], where t_last is the timestamp of
        the sequence's final message. Sequences whose anchor has no parseable
        timestamp or no qualifying match are dropped.
        """
        if not lhs_sequences or not rhs_messages:
            return []

        kernel = self._temporal_link_kernel("extend_temporal_link")
        if kernel is not None:
            return kernel(  # type: ignore[no-any-return]
                lhs_sequences,
                list(rhs_messages),
                self.timestamp_field,
                duration,
                True,
            )

        anchor_ids = {seq[-1] for seq in lhs_sequences}
        timestamps = self._get_timestamps_for_messages(anchor_ids | rhs_messages)
        rhs_with_ts = sorted(
            ((mid, timestamps[mid]) for mid in rhs_messages if mid in timestamps),
            key=lambda x: x[1],
        )

        import bisect

        rhs_times = [t for _, t in rhs_with_ts]
        result: list[MessageGroup] = []
        for sequence in lhs_sequences:
            t_last = timestamps.get(sequence[-1])
            if t_last is None:
                continue
            # First rhs strictly after t_last (binary search)
            i = bisect.bisect_right(rhs_times, t_last)
            if i < len(rhs_with_ts) and rhs_times[i] - t_last <= duration:
                result.append(sequence + [rhs_with_ts[i][0]])
        return result

    def _extend_sequences_preceded_by_temporal(
        self,
        lhs_sequences: list[MessageGroup],
        rhs_messages: set[MessageId],
        duration: timedelta,
    ) -> list[MessageGroup]:
        """
        Temporal counterpart of _extend_sequences_preceded_by.

        Prepends to each sequence the latest rhs message whose timestamp lies
        in [t_first - duration, t_first), where t_first is the timestamp of
        the sequence's first message.
        """
        if not lhs_sequences or not rhs_messages:
            return []

        kernel = self._temporal_link_kernel("extend_temporal_link")
        if kernel is not None:
            return kernel(  # type: ignore[no-any-return]
                lhs_sequences,
                list(rhs_messages),
                self.timestamp_field,
                duration,
                False,
            )

        anchor_ids = {seq[0] for seq in lhs_sequences}
        timestamps = self._get_timestamps_for_messages(anchor_ids | rhs_messages)
        rhs_with_ts = sorted(
            ((mid, timestamps[mid]) for mid in rhs_messages if mid in timestamps),
            key=lambda x: x[1],
        )

        import bisect

        rhs_times = [t for _, t in rhs_with_ts]
        result: list[MessageGroup] = []
        for sequence in lhs_sequences:
            t_first = timestamps.get(sequence[0])
            if t_first is None:
                continue
            # Last rhs strictly before t_first (binary search)
            i = bisect.bisect_left(rhs_times, t_first) - 1
            if i >= 0 and t_first - rhs_times[i] <= duration:
                result.append([rhs_with_ts[i][0], *sequence])
        return result

    def _apply_not_followed_by_temporal(
        self,
        lhs: set[MessageId],
        rhs: set[MessageId],
        duration: timedelta,
    ) -> QueryResult:
        """Inverse of temporal FOLLOWED_BY: return single-element groups for
        LHS messages that have no qualifying RHS within (t_lhs, t_lhs+duration].
        """
        pairs = self._create_sequential_pairs_temporal(lhs, rhs, duration, forward=True)
        matched = {pair[0] for pair in pairs}
        return [[msg] for msg in sorted(lhs - matched)]

    def _apply_not_preceded_by_temporal(
        self,
        lhs: set[MessageId],
        rhs: set[MessageId],
        duration: timedelta,
    ) -> QueryResult:
        """Inverse of temporal PRECEDED_BY: single-element groups for LHS
        messages with no qualifying RHS within [t_lhs-duration, t_lhs).
        """
        pairs = self._create_sequential_pairs_temporal(
            lhs, rhs, duration, forward=False
        )
        # temporal PRECEDED_BY emits [rhs, lhs] chronologically — lhs is at index 1
        matched = {pair[1] for pair in pairs}
        return [[msg] for msg in sorted(lhs - matched)]

    def _parse_time_window_to_timedelta(self, ctx: Any) -> "timedelta":
        """
        Parse time-based window and convert to timedelta for temporal filtering.

        Args:
            ctx: time_value context from parser

        Returns:
            timedelta representing the time window
        """
        from datetime import timedelta

        if ctx is None:
            # Default to a large time window
            return timedelta(days=365)

        # Get the number and unit
        number = int(ctx.number().getText())
        unit_text = ctx.time_unit().getText().lower()

        # Convert to timedelta
        if unit_text in ("s", "second", "seconds"):
            return timedelta(seconds=number)
        if unit_text in ("m", "minute", "minutes"):
            return timedelta(minutes=number)
        if unit_text in ("h", "hour", "hours"):
            return timedelta(hours=number)
        if unit_text in ("d", "day", "days"):
            return timedelta(days=number)
        if unit_text in ("w", "week", "weeks"):
            return timedelta(weeks=number)
        # Default fallback
        return timedelta(days=number)

    def _extract_group_by_fields(self, ctx: Any) -> list[str]:
        """
        Extract field names from GROUP BY clause.

        Supports both simple fields and temporal grouping.
        For temporal grouping, returns special field names like:
        - "HOUR(timestamp)" for hourly grouping
        - "DAY(timestamp)" for daily grouping
        etc.

        Note: Temporal grouping is handled specially in the aggregator.
        """
        from ..grammar.generated.PrismQLParser import PrismQLParser

        fields = []

        # Get groupby_field contexts
        groupby_fields = ctx.groupby_field()
        if not isinstance(groupby_fields, list):
            groupby_fields = [groupby_fields]

        for field_ctx in groupby_fields:
            if isinstance(field_ctx, PrismQLParser.SimpleGroupByContext):
                # Simple field grouping
                fields.append(field_ctx.field_name().getText().strip("\"'"))
            elif isinstance(field_ctx, PrismQLParser.TemporalGroupByContext):
                # Temporal grouping: HOUR(field), DAY(field), etc.
                func_text = field_ctx.temporal_group_func().getText().upper()
                # Normalize to plural form for aggregator
                func_map = {
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
                func = func_map.get(func_text, func_text)
                field_name = field_ctx.field_name().getText().strip("\"'")
                # Store as special field name that aggregator will recognize
                fields.append(f"__{func}__({field_name})")

        return fields

    def _extract_aggregations(
        self, ctx: Any
    ) -> list[tuple[AggregationFunction, Optional[str]]]:
        """
        Extract aggregation functions from AGGREGATE clause.

        Returns:
            List of (function, field_name) tuples
        """
        from ..grammar.generated.PrismQLParser import PrismQLParser

        aggregations: list[tuple[AggregationFunction, Optional[str]]] = []

        # Get all aggregation function contexts
        agg_funcs = ctx.aggregation_func()
        if not isinstance(agg_funcs, list):
            agg_funcs = [agg_funcs]

        for agg_func_ctx in agg_funcs:
            # Determine which aggregation function this is by checking the type
            if isinstance(agg_func_ctx, PrismQLParser.CountAllContext):
                aggregations.append((AggregationFunction.COUNT, None))

            elif isinstance(agg_func_ctx, PrismQLParser.CountDistinctContext):
                field = agg_func_ctx.field_name().getText()
                aggregations.append((AggregationFunction.COUNT_DISTINCT, field))

            elif isinstance(agg_func_ctx, PrismQLParser.DistinctValuesContext):
                field = agg_func_ctx.field_name().getText()
                aggregations.append((AggregationFunction.DISTINCT, field))

            elif isinstance(agg_func_ctx, PrismQLParser.SumFuncContext):
                field = agg_func_ctx.field_name().getText()
                aggregations.append((AggregationFunction.SUM, field))

            elif isinstance(agg_func_ctx, PrismQLParser.AvgFuncContext):
                field = agg_func_ctx.field_name().getText()
                aggregations.append((AggregationFunction.AVG, field))

            elif isinstance(agg_func_ctx, PrismQLParser.MinFuncContext):
                field = agg_func_ctx.field_name().getText()
                aggregations.append((AggregationFunction.MIN, field))

            elif isinstance(agg_func_ctx, PrismQLParser.MaxFuncContext):
                field = agg_func_ctx.field_name().getText()
                aggregations.append((AggregationFunction.MAX, field))

        return aggregations

    def _apply_ordering(self, results: QueryResult, ctx: Any) -> QueryResult:
        """
        Apply ORDER BY clause to results.

        For now, this orders by the first message ID in each group.
        In the future, this should support ordering by message fields.

        Args:
            results: Query results to order
            ctx: orderby_clause context from parser

        Returns:
            Ordered query results
        """
        # Get field names and sort directions
        field_names = ctx.field_name()
        if not isinstance(field_names, list):
            field_names = [field_names]

        # For now, simple ordering by first message ID
        # TODO: Support ordering by actual message fields
        reverse = False
        if ctx.Desc():
            reverse = True

        # Sort by first message ID in each group
        return sorted(
            results,
            key=lambda group: group[0] if group else 0,
            reverse=reverse,
        )

    def _apply_limit(self, results: QueryResult, ctx: Any) -> QueryResult:
        """
        Apply LIMIT and OFFSET clauses to results.

        Args:
            results: Query results to limit
            ctx: limit_clause context from parser

        Returns:
            Limited query results
        """
        # Get limit value
        numbers = ctx.number()
        if isinstance(numbers, list):
            limit = int(numbers[0].getText())
            offset = int(numbers[1].getText()) if len(numbers) > 1 else 0
        else:
            limit = int(numbers.getText())
            offset = 0

        # Apply offset and limit
        return results[offset : offset + limit]

    def _parse_temporal_filter(
        self, ctx: Any
    ) -> tuple[Optional[datetime], Optional[datetime], bool]:
        """
        Parse temporal filter clause (BEFORE, AFTER, BETWEEN).

        Args:
            ctx: temporal_filter context from parser

        Returns:
            Tuple of (start_time, end_time, inclusive), where:
            - None means unbounded
            - inclusive=True for BETWEEN, False for BEFORE/AFTER
        """
        if ctx.Before():
            # BEFORE(timestamp) -> (None, timestamp, exclusive)
            end_time = self._parse_timestamp(ctx.timestamp(0))
            return (None, end_time, False)

        if ctx.After():
            # AFTER(timestamp) -> (timestamp, None, exclusive)
            start_time = self._parse_timestamp(ctx.timestamp(0))
            return (start_time, None, False)

        if ctx.Between():
            # BETWEEN(timestamp1, timestamp2) -> (timestamp1, timestamp2, inclusive)
            start_time = self._parse_timestamp(ctx.timestamp(0))
            end_time = self._parse_timestamp(ctx.timestamp(1))
            return (start_time, end_time, True)

        return (None, None, False)

    def _parse_timestamp(self, ctx: Any) -> datetime:
        """
        Parse timestamp from context (absolute or relative).

        Args:
            ctx: timestamp context from parser

        Returns:
            Parsed datetime object
        """
        from ..grammar.generated.PrismQLParser import PrismQLParser

        if isinstance(ctx, PrismQLParser.AbsoluteTimestampContext):
            # Absolute timestamp: ISO 8601 string (quoted)
            timestamp_str = ctx.QUOTED_STRING().getText().strip("\"'")
            return TemporalProcessor.parse_timestamp(timestamp_str)

        if isinstance(ctx, PrismQLParser.RelativeTimestampContext):
            # Relative timestamp: "5 hours ago"
            time_value_ctx = ctx.time_value()
            value = int(time_value_ctx.number().getText())
            unit_text = time_value_ctx.time_unit().getText().lower()

            # Map unit text to TemporalUnit
            unit_map = {
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

            unit = unit_map.get(unit_text, TemporalUnit.DAY)
            return TemporalProcessor.parse_relative_time(value, unit)

        raise ValueError(f"Unknown timestamp context type: {type(ctx)}")

    def _apply_temporal_filter(
        self,
        results: QueryResult,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        inclusive: bool = False,
    ) -> QueryResult:
        """
        Apply temporal filtering to query results.

        Args:
            results: Query results to filter
            start_time: Start of time range, None for unbounded
            end_time: End of time range, None for unbounded
            inclusive: If True, bounds are inclusive (BETWEEN); otherwise exclusive

        Returns:
            Filtered query results
        """
        # Get all message IDs from results
        all_ids: set[MessageId] = set()
        for group in results:
            all_ids.update(group)

        # Use backend's cached timestamps when available (Rust path);
        # otherwise fetch documents and parse per-query (Python path).
        if hasattr(
            self.search_backend, "has_timestamp_field"
        ) and self.search_backend.has_timestamp_field(self.timestamp_field):
            filtered_ids = self.search_backend.filter_by_time_range(  # type: ignore[attr-defined]
                list(all_ids),
                self.timestamp_field,
                start_time,
                end_time,
                inclusive,
            )
        else:
            try:
                documents = self.search_backend.get_documents(list(all_ids))
            except NotImplementedError as e:
                # Backend doesn't support document retrieval - cannot filter
                raise PrismQLRuntimeError(
                    "Temporal filtering requires backend support for get_documents()"
                ) from e
            filtered_ids = TemporalProcessor.filter_by_time_range(
                all_ids,
                documents,
                self.timestamp_field,
                start_time,
                end_time,
                inclusive,
                id_field=getattr(self.search_backend, "id_field", "id"),
            )

        # Filter result groups to only include filtered messages
        filtered_results: QueryResult = []
        for group in results:
            filtered_group = [msg_id for msg_id in group if msg_id in filtered_ids]
            if filtered_group:
                filtered_results.append(filtered_group)

        return filtered_results

    def _extract_quantifier(self, ctx: Any) -> tuple[int, Optional[int]]:
        """
        Extract quantifier information from named_restriction context.

        Args:
            ctx: named_restriction context from parser

        Returns:
            Tuple of (min_count, max_count) where:
            - min_count is the minimum required occurrences (default 1)
            - max_count is the maximum allowed occurrences (None = unlimited)

        Examples:
            No quantifier -> (1, 1)
            {3} -> (3, 3)           # exactly 3
            {2,} -> (2, None)       # 2 or more
            {2,5} -> (2, 5)         # between 2 and 5
        """
        from ..grammar.generated.PrismQLParser import PrismQLParser

        if not ctx.quantifier():
            # No quantifier - default to exactly 1
            return (1, 1)

        quantifier_ctx = ctx.quantifier()

        # Check which type of quantifier this is
        if isinstance(quantifier_ctx, PrismQLParser.ExactQuantifierContext):
            # {n} - exactly n occurrences
            count = int(quantifier_ctx.number().getText())
            return (count, count)

        if isinstance(quantifier_ctx, PrismQLParser.AtLeastQuantifierContext):
            # {n,} - n or more occurrences
            min_count = int(quantifier_ctx.number().getText())
            return (min_count, None)

        if isinstance(quantifier_ctx, PrismQLParser.RangeQuantifierContext):
            # {n,m} - between n and m occurrences
            numbers = quantifier_ctx.number()
            min_count = int(numbers[0].getText())
            max_count = int(numbers[1].getText())
            return (min_count, max_count)

        # Should not reach here with valid parse tree
        return (1, 1)

    def _apply_followed_by(
        self, lhs: set[MessageId], rhs: set[MessageId], window: int
    ) -> set[MessageId]:
        """
        Apply FOLLOWED_BY operator: return IDs from lhs that are followed by
        an ID from rhs within the specified window.

        Args:
            lhs: Left-hand side message IDs
            rhs: Right-hand side message IDs
            window: Maximum distance (number of positions) to look ahead

        Returns:
            Set of message IDs from lhs that satisfy the condition

        Example:
            lhs={1,3,5}, rhs={4,6}, window=2
            - ID 1: no rhs within 2 positions after (IDs 2,3 in sequence)
            - ID 3: ID 4 is 1 position after in full sequence -> MATCH
            - ID 5: ID 6 is 1 position after in full sequence -> MATCH
            Result: {3, 5}
        """
        if not lhs or not rhs:
            return set()

        # Get all document IDs to establish the full sequence
        # Use a reasonable limit to avoid performance issues
        all_ids = sorted(
            self.search_backend.get_all_document_ids(limit=self.MAX_MESSAGES_NOT)
        )
        id_to_pos = {msg_id: i for i, msg_id in enumerate(all_ids)}

        result = set()
        for msg_id in lhs:
            if msg_id not in id_to_pos:
                continue
            pos = id_to_pos[msg_id]
            # Check if any rhs ID appears within window positions after this ID
            for i in range(pos + 1, min(pos + 1 + window, len(all_ids))):
                if all_ids[i] in rhs:
                    result.add(msg_id)
                    break

        return result

    def _apply_preceded_by(
        self, lhs: set[MessageId], rhs: set[MessageId], window: int
    ) -> set[MessageId]:
        """
        Apply PRECEDED_BY operator: return IDs from lhs that are preceded by
        an ID from rhs within the specified window.

        Args:
            lhs: Left-hand side message IDs
            rhs: Right-hand side message IDs
            window: Maximum distance (number of positions) to look behind

        Returns:
            Set of message IDs from lhs that satisfy the condition

        Example:
            lhs={3,5,7}, rhs={2,6}, window=2
            - ID 3: ID 2 is 1 position before in full sequence -> MATCH
            - ID 5: no rhs within 2 positions before (IDs 3,4 in sequence)
            - ID 7: ID 6 is 1 position before in full sequence -> MATCH
            Result: {3, 7}
        """
        if not lhs or not rhs:
            return set()

        # Get all document IDs to establish the full sequence
        all_ids = sorted(
            self.search_backend.get_all_document_ids(limit=self.MAX_MESSAGES_NOT)
        )
        id_to_pos = {msg_id: i for i, msg_id in enumerate(all_ids)}

        result = set()
        for msg_id in lhs:
            if msg_id not in id_to_pos:
                continue
            pos = id_to_pos[msg_id]
            # Check if any rhs ID appears within window positions before this ID
            for i in range(max(0, pos - window), pos):
                if all_ids[i] in rhs:
                    result.add(msg_id)
                    break

        return result

    def _apply_not_followed_by(
        self, lhs: set[MessageId], rhs: set[MessageId], window: int
    ) -> set[MessageId]:
        """
        Apply NOT_FOLLOWED_BY operator: return IDs from lhs that are NOT followed
        by an ID from rhs within the specified window.

        Args:
            lhs: Left-hand side message IDs
            rhs: Right-hand side message IDs
            window: Maximum distance (number of positions) to look ahead

        Returns:
            Set of message IDs from lhs that satisfy the condition

        Example:
            lhs={1,3,5}, rhs={4,6}, window=2
            - ID 1: no rhs within 2 positions after -> MATCH
            - ID 3: ID 4 is 1 position after -> NO MATCH
            - ID 5: ID 6 is 1 position after -> NO MATCH
            Result: {1}
        """
        # Get IDs that ARE followed by, then invert
        followed_by = self._apply_followed_by(lhs, rhs, window)
        return lhs - followed_by

    def _apply_not_preceded_by(
        self, lhs: set[MessageId], rhs: set[MessageId], window: int
    ) -> set[MessageId]:
        """
        Apply NOT_PRECEDED_BY operator: return IDs from lhs that are NOT preceded
        by an ID from rhs within the specified window.

        Args:
            lhs: Left-hand side message IDs
            rhs: Right-hand side message IDs
            window: Maximum distance (number of positions) to look behind

        Returns:
            Set of message IDs from lhs that satisfy the condition

        Example:
            lhs={3,5,7}, rhs={2,6}, window=2
            - ID 3: ID 2 is 1 position before -> NO MATCH
            - ID 5: no rhs within 2 positions before -> MATCH
            - ID 7: ID 6 is 1 position before -> NO MATCH
            Result: {5}
        """
        # Get IDs that ARE preceded by, then invert
        preceded_by = self._apply_preceded_by(lhs, rhs, window)
        return lhs - preceded_by
