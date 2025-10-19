"""Aggregation support for PrismQL queries."""

from .aggregator import Aggregator
from .types import AggregateResult, AggregationFunction, GroupedResult

__all__ = ["AggregateResult", "AggregationFunction", "GroupedResult", "Aggregator"]
