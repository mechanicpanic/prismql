"""PrismQL query visitor implementation."""

import itertools
import warnings
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Optional, Union

from ..aggregators.aggregator import Aggregator
from ..aggregators.types import AggregateResult, AggregationFunction, GroupedResult
from ..backends.base import NLPBackend, PrecomputedIndexes, SearchBackend
from ..exceptions import PrismQLRuntimeError
from ..grammar.generated.PrismQLParser import PrismQLParser
from ..grammar.generated.PrismQLVisitor import PrismQLVisitor as BasePrismQLVisitor
from ..processors.temporal import TemporalProcessor, TemporalUnit
from ..processors.variables import VariableConstraint, VariableValidator
from ..types import MessageGroup, MessageId, NamedQueryResult, QueryResult


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
    ) -> None:
        self.search_backend = search_backend
        self.nlp_backend = nlp_backend
        self.user_dictionaries = user_dictionaries or {}
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        self.aggregator = Aggregator(search_backend)
        self.timestamp_field = timestamp_field

        # Variable tracking for pattern matching
        self.variable_constraints: list[VariableConstraint] = []
        self.current_restriction_position = 0

        # Pattern naming for result labeling
        self.pattern_names: list[Optional[str]] = []

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

        # Step 1: Extract window size if specified (position-based or time-based)
        window_size = self.DEFAULT_WINDOW_SIZE
        if ctx.InWin():
            window_size = int(ctx.number().getText())
        elif ctx.Within():
            # Time-based window - convert to position-based for now
            # TODO: Implement proper temporal windowing
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
            else:
                results = self._merge_restrictions(restriction_results, window_size)
        elif ctx.query_seq():
            # Multiple subqueries in sequence
            subquery_results = self.visitQuery_seq(ctx.query_seq())
            # Unwrap NamedQueryResult to plain QueryResult for merging
            unwrapped_results: list[
                Union[QueryResult, AggregateResult, GroupedResult]
            ] = []
            for result in subquery_results:
                if isinstance(result, NamedQueryResult):
                    unwrapped_results.append(result.to_list())
                else:
                    unwrapped_results.append(result)
            results = self._merge_queries(unwrapped_results, window_size)
        else:
            results = []

        # Step 2.3: Apply variable validation if any variables were used
        if self.variable_constraints:
            validator = VariableValidator(
                self.search_backend, self.variable_constraints
            )
            results = validator.validate_results(results)

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
    ) -> list[Union[QueryResult, NamedQueryResult, AggregateResult, GroupedResult]]:
        """
        Process a sequence of subqueries.

        Handles both:
        - Unordered subqueries (semicolon-separated): collected for later INWIN merging
        - Positional subqueries (FOLLOWED_BY/PRECEDED_BY): merged sequentially
        """
        # Get all query contexts
        query_contexts = ctx.query()

        # Get all continuations
        continuations = (
            ctx.query_seq_continuation()
            if hasattr(ctx, "query_seq_continuation")
            else []
        )

        # If no continuations, just return the single query result as a list
        if not continuations:
            result = self.visitQuery(query_contexts[0])
            return [result]

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
            return results

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
        return [current_result]

    def visitRestrictions(
        self, ctx: PrismQLParser.RestrictionsContext
    ) -> tuple[list[MessageGroup], bool]:
        """
        Process comma-separated restrictions.

        Returns a tuple of (list of message groups, is_sequential_result).
        The is_sequential_result flag indicates if the result contains
        pre-computed sequences from FOLLOWED_BY/PRECEDED_BY operators.
        If UNR flag is present, returns all permutations.
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

            # Process the underlying restriction
            result = self.visitRestriction(named_restriction_ctx.restriction())

            # Check if any new constraints were added (indicating a variable was used)
            new_constraints = self.variable_constraints[num_constraints_before:]

            # Check if result is a sequence (from FOLLOWED_BY/PRECEDED_BY) or a set
            if isinstance(result, list):
                # Result is already a list of message groups (sequences)
                has_sequential_operator = True
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

        # Handle UNR (unrelated) flag - generate permutations
        if ctx.Unr():
            # Generate all permutations of taking one message from each group
            permutations = []
            for perm in itertools.product(*restriction_results):
                permutations.append(list(perm))
            return (permutations, False)  # UNR results are not sequential
        # Return as-is (will be merged by window processor or returned directly if sequential)
        return (restriction_results, has_sequential_operator)

    def visitRestriction(
        self, ctx: PrismQLParser.RestrictionContext
    ) -> Union[set[MessageId], list[MessageGroup]]:
        """
        Process a single restriction with boolean operators.

        Returns either a set of message IDs (for normal restrictions) or
        a list of message groups (for sequential operators like FOLLOWED_BY).
        """
        # Handle AND operator
        if ctx.And():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            # AND requires both operands to be sets, not sequences
            if isinstance(lhs, list) or isinstance(rhs, list):
                raise PrismQLRuntimeError(
                    "AND operator cannot be used with sequential operators (FOLLOWED_BY, PRECEDED_BY). "
                    "Sequential operators return message sequences, not individual messages."
                )
            return lhs & rhs  # Set intersection

        # Handle OR operator
        if ctx.Or():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            # OR requires both operands to be sets, not sequences
            if isinstance(lhs, list) or isinstance(rhs, list):
                raise PrismQLRuntimeError(
                    "OR operator cannot be used with sequential operators (FOLLOWED_BY, PRECEDED_BY). "
                    "Sequential operators return message sequences, not individual messages."
                )
            return lhs | rhs  # Set union

        # Handle FOLLOWED_BY operator (lookahead)
        if ctx.FollowedBy():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            window = int(ctx.number().getText())

            # Check if lhs is a sequence (from chained FOLLOWED_BY)
            if isinstance(lhs, list):
                # Extend existing sequences with rhs messages
                # rhs must be a set for now (no double nesting)
                if isinstance(rhs, list):
                    raise PrismQLRuntimeError(
                        "Complex nested sequential operators are not yet supported"
                    )
                return self._extend_sequences_followed_by(lhs, rhs, window)

            # Simple case: both lhs and rhs are sets
            # rhs could be a list if it's nested on the right side
            if isinstance(rhs, list):
                raise PrismQLRuntimeError(
                    "FOLLOWED_BY requires simple conditions, not nested sequences"
                )
            # Create pairs using the existing logic
            matching_lhs = self._apply_followed_by(lhs, rhs, window)
            return self._create_sequential_pairs(
                matching_lhs, rhs, window, forward=True
            )

        # Handle PRECEDED_BY operator (lookbehind)
        if ctx.PrecededBy():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            window = int(ctx.number().getText())

            # Check if lhs is a sequence (from chained PRECEDED_BY)
            if isinstance(lhs, list):
                # Extend existing sequences with rhs messages
                if isinstance(rhs, list):
                    raise PrismQLRuntimeError(
                        "Complex nested sequential operators are not yet supported"
                    )
                return self._extend_sequences_preceded_by(lhs, rhs, window)

            # Simple case: both lhs and rhs are sets
            if isinstance(rhs, list):
                raise PrismQLRuntimeError(
                    "PRECEDED_BY requires simple conditions, not nested sequences"
                )
            # Create pairs using the existing logic
            matching_lhs = self._apply_preceded_by(lhs, rhs, window)
            return self._create_sequential_pairs(
                matching_lhs, rhs, window, forward=False
            )

        # Handle NOT_FOLLOWED_BY operator (negative lookahead)
        if ctx.NotFollowedBy():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            window = int(ctx.number().getText())
            # NOT_FOLLOWED_BY returns only the LHS messages, not pairs
            if isinstance(lhs, list) or isinstance(rhs, list):
                raise PrismQLRuntimeError(
                    "NOT_FOLLOWED_BY cannot be chained with other sequential operators"
                )
            return self._apply_not_followed_by(lhs, rhs, window)

        # Handle NOT_PRECEDED_BY operator (negative lookbehind)
        if ctx.NotPrecededBy():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            window = int(ctx.number().getText())
            # NOT_PRECEDED_BY returns only the LHS messages, not pairs
            if isinstance(lhs, list) or isinstance(rhs, list):
                raise PrismQLRuntimeError(
                    "NOT_PRECEDED_BY cannot be chained with other sequential operators"
                )
            return self._apply_not_preceded_by(lhs, rhs, window)

        # Handle NOT operator
        if ctx.Not():
            excluded = self.visitRestriction(ctx.restriction(0))
            # NOT requires a set, not sequences
            if isinstance(excluded, list):
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

        # Handle parentheses - just visit the inner restriction
        if ctx.getChildCount() == 3 and ctx.getChild(0).getText() == "(":
            return self.visitRestriction(ctx.restriction(0))

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
            words = self.user_dictionaries[dict_name]
            return self.search_backend.search_text(words, field="text", operator="OR")

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
            words = self.user_dictionaries[dict_name]
            return self.search_backend.search_text(words, field="text", operator="OR")

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

    def _get_questions(self) -> set[MessageId]:
        """Helper method to get questions (used by both new and legacy operators)."""
        # First check precomputed index
        if self.precomputed_indexes.questions:
            return self.precomputed_indexes.questions

        # Check if backend supports question detection
        if hasattr(self.search_backend, "get_questions"):
            result = self.search_backend.get_questions()
            return set(result) if result is not None else set()

        # Otherwise would need NLP backend
        if not self.nlp_backend:
            raise PrismQLRuntimeError(
                "Question detection requires NLP backend or precomputed indexes"
            )
        # This would require iterating through all messages - not efficient
        raise PrismQLRuntimeError(
            "Question detection requires precomputed indexes for large datasets"
        )

    def _get_ner_messages(self, ner_label: str) -> set[MessageId]:
        """Get messages containing specific NER type."""
        # First check precomputed index
        if ner_label in self.precomputed_indexes.entities:
            return self.precomputed_indexes.entities[ner_label]

        # Otherwise would need NLP backend
        if not self.nlp_backend:
            raise PrismQLRuntimeError(
                "NER condition requires NLP backend or precomputed indexes"
            )

        # This would require iterating through all messages - not efficient
        raise PrismQLRuntimeError(
            "NER conditions require precomputed indexes for large datasets"
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
        else:
            raise PrismQLRuntimeError(
                f"Feature '{feature_name}' not found. No custom features have been "
                "precomputed. Use IndexBuilder to create feature indexes from your "
                "annotations (LLM-generated, human labels, etc.)."
            )

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

    def _merge_subqueries_positional(
        self,
        lhs_result: QueryResult,
        rhs_result: QueryResult,
        operator_ctx: Any,
        window: int,
    ) -> QueryResult:
        """
        Merge two subquery results using a positional operator.

        Args:
            lhs_result: Result from the left subquery
            rhs_result: Result from the right subquery
            operator_ctx: The positional operator context (FollowedBy, PrecededBy, etc.)
            window: Window size for the operator

        Returns:
            Merged query result with groups that satisfy the positional constraint
        """
        # Flatten subquery results into sets of message IDs
        lhs_messages = set()
        for group in lhs_result:
            lhs_messages.update(group)

        rhs_messages = set()
        for group in rhs_result:
            rhs_messages.update(group)

        # Determine the operator type and apply it
        operator_text = operator_ctx.getText().upper()

        if "FOLLOWEDBY" in operator_text or "FOLLOWED_BY" in operator_text:
            # LHS messages that are followed by RHS messages
            matching_lhs = self._apply_followed_by(lhs_messages, rhs_messages, window)
            # Find matching pairs
            return self._create_sequential_pairs(
                matching_lhs, rhs_messages, window, forward=True
            )
        if "PRECEDEDBY" in operator_text or "PRECEDED_BY" in operator_text:
            # LHS messages that are preceded by RHS messages
            matching_lhs = self._apply_preceded_by(lhs_messages, rhs_messages, window)
            # Find matching pairs
            return self._create_sequential_pairs(
                matching_lhs, rhs_messages, window, forward=False
            )
        if "NOTFOLLOWEDBY" in operator_text or "NOT_FOLLOWED_BY" in operator_text:
            # LHS messages that are NOT followed by RHS messages
            matching_lhs = self._apply_not_followed_by(
                lhs_messages, rhs_messages, window
            )
            # Return just the matching LHS messages as single-element groups
            return [[msg] for msg in sorted(matching_lhs)]
        if "NOTPRECEDEDBY" in operator_text or "NOT_PRECEDED_BY" in operator_text:
            # LHS messages that are NOT preceded by RHS messages
            matching_lhs = self._apply_not_preceded_by(
                lhs_messages, rhs_messages, window
            )
            # Return just the matching LHS messages as single-element groups
            return [[msg] for msg in sorted(matching_lhs)]

        raise ValueError(f"Unknown positional operator: {operator_text}")

    def _create_sequential_pairs(
        self,
        lhs_messages: set[MessageId],
        rhs_messages: set[MessageId],
        window: int,
        forward: bool,
    ) -> QueryResult:
        """
        Create pairs of messages that satisfy a sequential constraint.

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

        # Get documents with timestamps
        try:
            documents = self.search_backend.get_documents(list(all_ids))
        except NotImplementedError as e:
            # Backend doesn't support document retrieval - cannot filter
            raise PrismQLRuntimeError(
                "Temporal filtering requires backend support for get_documents()"
            ) from e

        # Filter message IDs by time range
        filtered_ids = TemporalProcessor.filter_by_time_range(
            all_ids, documents, self.timestamp_field, start_time, end_time, inclusive
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
