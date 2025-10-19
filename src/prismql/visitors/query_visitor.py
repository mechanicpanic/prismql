"""PrismQL query visitor implementation."""

import itertools
from collections.abc import Mapping, Sequence
from typing import Any, Optional, Union

from ..aggregators.aggregator import Aggregator
from ..aggregators.types import AggregateResult, AggregationFunction, GroupedResult
from ..backends.base import NLPBackend, PrecomputedIndexes, SearchBackend
from ..exceptions import PrismQLRuntimeError
from ..grammar.generated.PrismQLParser import PrismQLParser
from ..grammar.generated.PrismQLVisitor import PrismQLVisitor as BasePrismQLVisitor
from ..types import MessageGroup, MessageId, QueryResult


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
    ) -> None:
        self.search_backend = search_backend
        self.nlp_backend = nlp_backend
        self.user_dictionaries = user_dictionaries or {}
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        self.aggregator = Aggregator(search_backend)

    def visitQuery(
        self, ctx: PrismQLParser.QueryContext
    ) -> Union[QueryResult, AggregateResult, GroupedResult]:
        """Entry point - visit the query body."""
        return self.visitBody(ctx.body())

    def visitBody(
        self, ctx: PrismQLParser.BodyContext
    ) -> Union[QueryResult, AggregateResult, GroupedResult]:
        """Process query body with optional window, grouping, aggregation,
        ordering, and limiting."""
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
            restriction_results = self.visitRestrictions(ctx.restrictions())
            results = self._merge_restrictions(restriction_results, window_size)
        elif ctx.query_seq():
            # Multiple subqueries in sequence
            subquery_results = self.visitQuery_seq(ctx.query_seq())
            results = self._merge_queries(subquery_results, window_size)
        else:
            results = []

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

        return results

    def visitQuery_seq(
        self, ctx: PrismQLParser.Query_seqContext
    ) -> list[Union[QueryResult, AggregateResult, GroupedResult]]:
        """Process a sequence of subqueries."""
        results: list[Union[QueryResult, AggregateResult, GroupedResult]] = []
        for query_ctx in ctx.query():
            result = self.visitQuery(query_ctx)
            results.append(result)
        return results

    def visitRestrictions(
        self, ctx: PrismQLParser.RestrictionsContext
    ) -> list[MessageGroup]:
        """
        Process comma-separated restrictions.

        Returns a list of message groups, one for each restriction.
        If UNR flag is present, returns all permutations.
        """
        restriction_results = []

        # Process each restriction
        for restriction_ctx in ctx.restriction():
            result = self.visitRestriction(restriction_ctx)
            # Convert set to sorted list
            sorted_result = sorted(result)
            restriction_results.append(sorted_result)

        # Handle UNR (unrelated) flag - generate permutations
        if ctx.Unr():
            # Generate all permutations of taking one message from each group
            permutations = []
            for perm in itertools.product(*restriction_results):
                permutations.append(list(perm))
            return permutations
        # Return as-is (will be merged by window processor)
        return restriction_results

    def visitRestriction(self, ctx: PrismQLParser.RestrictionContext) -> set[MessageId]:
        """Process a single restriction with boolean operators."""
        # Handle AND operator
        if ctx.And():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            return lhs & rhs  # Set intersection

        # Handle OR operator
        if ctx.Or():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            return lhs | rhs  # Set union

        # Handle NOT operator
        if ctx.Not():
            excluded = self.visitRestriction(ctx.restriction(0))
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
            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            words = self.user_dictionaries[dict_name]
            return self.search_backend.search_text(words, field="text", operator="OR")

        # from(username) - same as byuser
        if ctx.From():
            username = ctx.huser().getText()
            return self.search_backend.search_by_field("user", username, exact=True)

        # mentions_user(username) - same as hasusermentioned
        if ctx.MentionsUser():
            username = ctx.huser().getText()
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

        # Legacy operators (backward compatibility)
        if ctx.HasWordOfDict():
            dict_name = ctx.hdict().getText()
            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            words = self.user_dictionaries[dict_name]
            return self.search_backend.search_text(words, field="text", operator="OR")

        if ctx.ByUser():
            username = ctx.huser().getText()
            return self.search_backend.search_by_field("user", username, exact=True)

        if ctx.HasUserMentioned():
            username = ctx.huser().getText()
            if username in self.precomputed_indexes.user_mentions:
                return self.precomputed_indexes.user_mentions[username]
            return self.search_backend.search_text([username], field="text")

        if ctx.HasQuestion():
            return self._get_questions()

        if ctx.HasDate():
            return self._get_ner_messages("DATE")
        if ctx.HasTime():
            return self._get_ner_messages("TIME")
        if ctx.HasLocation():
            return self._get_ner_messages("GPE")
        if ctx.HasOrganization():
            return self._get_ner_messages("ORG")
        if ctx.HasURL():
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
                    f"Subquery {i+1} contains aggregation/grouping which is not "
                    "supported in query sequences. Apply aggregation at the top level."
                )

        # Flatten all groups from all subqueries
        all_groups: list[MessageGroup] = []
        for subquery_result in subquery_results:
            all_groups.extend(subquery_result)  # type: ignore[arg-type]

        # Apply window processing
        from ..processors.window import WindowProcessor

        return WindowProcessor.merge_queries(all_groups, window_size)

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
        """Extract field names from GROUP BY clause."""
        fields = []
        if ctx.field_name():
            # Single field or list of fields
            if isinstance(ctx.field_name(), list):
                for field_ctx in ctx.field_name():
                    fields.append(field_ctx.getText())
            else:
                fields.append(ctx.field_name().getText())
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
