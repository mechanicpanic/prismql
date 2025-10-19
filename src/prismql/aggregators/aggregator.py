"""Core aggregation logic for PrismQL queries."""

import re
from collections import defaultdict
from collections.abc import Sequence
from statistics import mean
from typing import Any, Optional

from ..backends.base import SearchBackend
from ..processors.temporal import TemporalProcessor, TemporalUnit
from ..types import MessageGroup, MessageId, QueryResult
from .types import AggregateResult, AggregationFunction, GroupedResult


class Aggregator:
    """
    Handles aggregation operations on query results.

    Supports grouping, counting, and statistical aggregations.
    """

    def __init__(self, search_backend: SearchBackend) -> None:
        """
        Initialize aggregator.

        Args:
            search_backend: Backend to retrieve document metadata
        """
        self.search_backend = search_backend

    def group_by(self, results: QueryResult, fields: Sequence[str]) -> GroupedResult:
        """
        Group query results by specified fields.

        Supports both simple field grouping and temporal grouping.
        Temporal grouping fields have format: __UNIT__(field_name)
        where UNIT can be HOURS, DAYS, WEEKS, MONTHS, YEARS.

        Args:
            results: Query results to group
            fields: Field names to group by (may include temporal grouping)

        Returns:
            Grouped results
        """
        # Check if any fields are temporal grouping
        temporal_pattern = re.compile(r"^__(HOURS|DAYS|WEEKS|MONTHS|YEARS)__\((.+)\)$")
        has_temporal = any(temporal_pattern.match(f) for f in fields)

        if has_temporal and len(fields) == 1:
            # Pure temporal grouping (single field)
            match = temporal_pattern.match(fields[0])
            if match:
                unit_str = match.group(1)
                field_name = match.group(2)

                # Map unit string to TemporalUnit
                unit_map = {
                    "HOURS": TemporalUnit.HOUR,
                    "DAYS": TemporalUnit.DAY,
                    "WEEKS": TemporalUnit.WEEK,
                    "MONTHS": TemporalUnit.MONTH,
                    "YEARS": TemporalUnit.YEAR,
                }
                unit = unit_map[unit_str]

                # Get all message IDs and documents
                all_ids: set[MessageId] = set()
                for group in results:
                    all_ids.update(group)

                try:
                    documents = self.search_backend.get_documents(list(all_ids))
                except NotImplementedError:
                    return GroupedResult(
                        groups={"__all__": results}, group_by_fields=fields
                    )

                # Use TemporalProcessor to group by temporal unit
                temporal_groups = TemporalProcessor.group_by_temporal_unit(
                    all_ids, documents, field_name, unit
                )

                # Convert message ID groups to message groups
                # (keeping original structure)
                result_groups: dict[str, list[MessageGroup]] = defaultdict(list)
                for group in results:
                    # Find which temporal group each message in this group belongs to
                    for msg_id in group:
                        for temp_key, temp_ids in temporal_groups.items():
                            if msg_id in temp_ids:
                                result_groups[temp_key].append(group)
                                break

                return GroupedResult(groups=dict(result_groups), group_by_fields=fields)

        # Regular field-based grouping
        # Get all message IDs from results
        all_message_ids: set[MessageId] = set()
        for group in results:
            all_message_ids.update(group)

        # Retrieve documents to get field values
        try:
            documents = self.search_backend.get_documents(list(all_message_ids))
        except NotImplementedError:
            # Backend doesn't support document retrieval
            # Fall back to treating all as one group
            return GroupedResult(groups={"__all__": results}, group_by_fields=fields)

        # Build mapping from message ID to field values
        message_fields: dict[MessageId, dict[str, Any]] = {}
        for doc in documents:
            msg_id_value = doc.get("id")
            if msg_id_value is not None:
                message_fields[msg_id_value] = {
                    field: doc.get(field, "__none__") for field in fields
                }

        # Group results by field values
        groups: dict[str, list[MessageGroup]] = defaultdict(list)

        for group in results:
            # Determine group key for this message group
            # Use the field values from the first message in the group
            if not group:
                continue

            first_msg = group[0]
            if first_msg not in message_fields:
                group_key = "__unknown__"
            else:
                # Create compound key from all group-by fields
                key_parts = [
                    str(message_fields[first_msg].get(field, "__none__"))
                    for field in fields
                ]
                group_key = "|".join(key_parts)

            groups[group_key].append(group)

        return GroupedResult(groups=dict(groups), group_by_fields=fields)

    def aggregate(
        self,
        results: QueryResult,
        function: AggregationFunction,
        field: Optional[str] = None,
        grouped_results: Optional[GroupedResult] = None,
    ) -> AggregateResult:
        """
        Apply aggregation function to query results.

        Args:
            results: Query results to aggregate
            function: Aggregation function to apply
            field: Field name to aggregate over (for SUM, AVG, etc.)
            grouped_results: Optional grouped results for grouped aggregation

        Returns:
            Aggregated result
        """
        if grouped_results is not None:
            # Grouped aggregation
            return self._aggregate_grouped(grouped_results, function, field)

        # Non-grouped aggregation
        return self._aggregate_simple(results, function, field)

    def _aggregate_simple(
        self,
        results: QueryResult,
        function: AggregationFunction,
        field: Optional[str] = None,
    ) -> AggregateResult:
        """Apply aggregation to non-grouped results."""

        if function == AggregationFunction.COUNT:
            # Count number of result groups
            return AggregateResult(value=len(results), function=function, field=field)

        if function == AggregationFunction.COUNT_DISTINCT:
            if not field:
                raise ValueError("COUNT DISTINCT requires a field name")

            # Get all unique field values
            unique_values = self._get_unique_field_values(results, field)
            return AggregateResult(
                value=len(unique_values), function=function, field=field
            )

        if function == AggregationFunction.DISTINCT:
            if not field:
                raise ValueError("DISTINCT requires a field name")

            # Get all unique field values
            unique_values = self._get_unique_field_values(results, field)
            return AggregateResult(
                value=sorted(unique_values), function=function, field=field
            )

        if function in (
            AggregationFunction.SUM,
            AggregationFunction.AVG,
            AggregationFunction.MIN,
            AggregationFunction.MAX,
        ):
            return self._aggregate_statistical(results, function, field)

        raise ValueError(f"Unsupported aggregation function: {function}")

    def _aggregate_statistical(
        self,
        results: QueryResult,
        function: AggregationFunction,
        field: Optional[str],
    ) -> AggregateResult:
        """Apply statistical aggregation (SUM, AVG, MIN, MAX)."""
        if not field:
            raise ValueError(f"{function.value.upper()} requires a field name")

        # Get numeric field values
        values = self._get_numeric_field_values(results, field)

        if not values:
            return AggregateResult(value=None, function=function, field=field)

        if function == AggregationFunction.SUM:
            result_value: Any = sum(values)
        elif function == AggregationFunction.AVG:
            result_value = mean(values)
        elif function == AggregationFunction.MIN:
            result_value = min(values)
        elif function == AggregationFunction.MAX:
            result_value = max(values)
        else:
            raise ValueError(f"Unsupported statistical function: {function}")

        return AggregateResult(value=result_value, function=function, field=field)

    def _aggregate_grouped(
        self,
        grouped_results: GroupedResult,
        function: AggregationFunction,
        field: Optional[str] = None,
    ) -> AggregateResult:
        """Apply aggregation to grouped results."""

        grouped_values: dict[str, Any] = {}

        for group_key, group_results in grouped_results.groups.items():
            # Apply aggregation to this group
            result = self._aggregate_simple(group_results, function, field)
            grouped_values[group_key] = result.value

        return AggregateResult(
            grouped_values=grouped_values, function=function, field=field
        )

    def _get_unique_field_values(self, results: QueryResult, field: str) -> set[Any]:
        """Get unique values for a field across all results."""

        unique_values: set[Any] = set()

        # Get all message IDs
        all_ids: set[MessageId] = set()
        for group in results:
            all_ids.update(group)

        try:
            documents = self.search_backend.get_documents(list(all_ids))
            for doc in documents:
                value = doc.get(field)
                if value is not None:
                    unique_values.add(value)
        except NotImplementedError:
            # Backend doesn't support document retrieval
            pass

        return unique_values

    def _get_numeric_field_values(
        self, results: QueryResult, field: str
    ) -> list[float]:
        """Get numeric values for a field across all results."""

        values: list[float] = []

        # Get all message IDs
        all_ids: set[MessageId] = set()
        for group in results:
            all_ids.update(group)

        try:
            documents = self.search_backend.get_documents(list(all_ids))
            for doc in documents:
                value = doc.get(field)
                if value is not None:
                    try:
                        # Try to convert to float
                        numeric_value = float(value)
                        values.append(numeric_value)
                    except (ValueError, TypeError):
                        # Skip non-numeric values
                        continue
        except NotImplementedError:
            # Backend doesn't support document retrieval
            pass

        return values
