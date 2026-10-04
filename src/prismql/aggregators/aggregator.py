"""Core aggregation logic for PrismQL queries."""

import re
from collections import defaultdict
from collections.abc import Sequence
from statistics import mean
from typing import Any

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

    _TEMPORAL = re.compile(r"^__(HOURS|DAYS|WEEKS|MONTHS|YEARS)__\((.+)\)$")
    _UNITS = {
        "HOURS": TemporalUnit.HOUR,
        "DAYS": TemporalUnit.DAY,
        "WEEKS": TemporalUnit.WEEK,
        "MONTHS": TemporalUnit.MONTH,
        "YEARS": TemporalUnit.YEAR,
    }

    def group_by(self, results: QueryResult, fields: Sequence[str]) -> GroupedResult:
        """
        Group query results by specified fields.

        Each matched group lands in exactly one bucket, keyed by its first
        event: a plain field's value there, or the time unit it falls in for
        a temporal field (``__DAYS__(time)``, from ``GROUP BY DAYS(time)``;
        units HOURS, DAYS, WEEKS, MONTHS, YEARS). Plain and temporal fields
        combine into one key, joined by ``|``.

        Args:
            results: Query results to group
            fields: Field names to group by (may include temporal grouping)

        Returns:
            Grouped results
        """
        all_ids: set[MessageId] = set()
        for group in results:
            all_ids.update(group)
        id_field = getattr(self.search_backend, "id_field", "id")
        docs_by_id: dict[MessageId, dict[str, Any]] = {}
        if any(not self._TEMPORAL.match(f) for f in fields):
            try:
                documents = self.search_backend.get_documents(list(all_ids))
            except NotImplementedError:
                return GroupedResult(
                    groups={"__all__": results}, group_by_fields=fields
                )
            docs_by_id = {
                d[id_field]: d for d in documents if d.get(id_field) is not None
            }
        buckets: dict[str, dict[MessageId, str]] = {}
        for f in fields:
            match = self._TEMPORAL.match(f)
            if match:
                unit = self._UNITS[match.group(1)]
                found = self._temporal_buckets(all_ids, match.group(2), unit)
                if found is None:
                    return GroupedResult(
                        groups={"__all__": results}, group_by_fields=fields
                    )
                buckets[f] = found

        groups: dict[str, list[MessageGroup]] = defaultdict(list)
        for group in results:
            if not group:
                continue
            first = group[0]
            parts: list[str] = []
            for f in fields:
                if f in buckets:
                    parts.append(buckets[f].get(first, "__none__"))
                elif first in docs_by_id:
                    parts.append(str(docs_by_id[first].get(f, "__none__")))
                else:
                    parts = ["__unknown__"]
                    break
            groups["|".join(parts)].append(group)
        return GroupedResult(groups=dict(groups), group_by_fields=fields)

    def _temporal_buckets(
        self, ids: set[MessageId], field_name: str, unit: TemporalUnit
    ) -> dict[MessageId, str] | None:
        """Each event's time-unit key, or None when the backend cannot hand
        over its documents."""
        backend = self.search_backend
        if (
            hasattr(backend, "has_timestamp_field")
            and hasattr(backend, "group_by_temporal_unit")
            and backend.has_timestamp_field(field_name)
        ):
            temporal_groups = backend.group_by_temporal_unit(
                list(ids), field_name, unit.value
            )
        else:
            try:
                documents = backend.get_documents(list(ids))
            except NotImplementedError:
                return None
            temporal_groups = TemporalProcessor.group_by_temporal_unit(
                ids,
                documents,
                field_name,
                unit,
                id_field=getattr(backend, "id_field", "id"),
            )
        return {m: key for key, members in temporal_groups.items() for m in members}

    def aggregate(
        self,
        results: QueryResult,
        function: AggregationFunction,
        field: str | None = None,
        grouped_results: GroupedResult | None = None,
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
        field: str | None = None,
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
        field: str | None,
    ) -> AggregateResult:
        """Apply statistical aggregation (SUM, AVG, MIN, MAX)."""
        if not field:
            raise ValueError(f"{function.value.upper()} requires a field name")

        # Get numeric field values
        values = self._get_numeric_field_values(results, field)

        if not values:
            raw = self._get_raw_field_values(results, field)
            if not raw:
                return AggregateResult(value=None, function=function, field=field)
            return self._non_numeric(raw, function, field)

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
        field: str | None = None,
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

    def _non_numeric(
        self, raw: list[Any], function: AggregationFunction, field: str
    ) -> AggregateResult:
        """A field that holds values but no numbers: min/max of timestamps is
        the earliest/latest one as written; anything else refuses instead of
        answering null (graph @aleph/prismql, #179)."""
        name = function.value.lower()
        if function in (AggregationFunction.MIN, AggregationFunction.MAX):
            from ..backends.order import epoch_micros

            timed = [(epoch_micros(v), v) for v in raw]
            known = [(t, v) for t, v in timed if t is not None]
            if len(known) == len(timed):
                pick = min if function == AggregationFunction.MIN else max
                value = pick(known, key=lambda tv: tv[0])[1]
                return AggregateResult(value=value, function=function, field=field)
        kinds = "numbers or times" if name in ("min", "max") else "numbers"
        raise ValueError(
            f"{name}({field}): the field holds values, but no {kinds} — "
            f"{name}() would answer null. Count its values with "
            f"count(DISTINCT {field}) or list them with distinct({field})."
        )

    def _get_raw_field_values(self, results: QueryResult, field: str) -> list[Any]:
        """The field's non-null values across all results."""
        all_ids: set[MessageId] = set()
        for group in results:
            all_ids.update(group)
        try:
            documents = self.search_backend.get_documents(list(all_ids))
        except NotImplementedError:
            # Backend doesn't support document retrieval
            return []
        return [doc.get(field) for doc in documents if doc.get(field) is not None]

    def _get_numeric_field_values(
        self, results: QueryResult, field: str
    ) -> list[float]:
        """Get numeric values for a field across all results."""
        values: list[float] = []
        for value in self._get_raw_field_values(results, field):
            try:
                values.append(float(value))
            except (ValueError, TypeError):
                continue  # non-numeric values are skipped
        return values
