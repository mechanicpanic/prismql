"""Sequence/window primitives as a Polars plan (spec 2026-09-18, P2).

The operator layer: polars and pyarrow are core dependencies (``[plan]`` is
an empty alias), and both executors call it through ``bridge`` — since P3
the engine is this plan.
"""

from __future__ import annotations

from typing import Any

from ..exceptions import PrismQLRuntimeError


class PlanUnavailableError(PrismQLRuntimeError):
    """polars, a core dependency, cannot be imported."""


def _pl() -> Any:
    """Lazy import guard so the core package never imports polars."""
    try:
        import polars as pl
    except ImportError as e:
        raise PlanUnavailableError(
            "The plan primitives require polars: uv pip install 'prismql[plan]'"
        ) from e
    return pl


__all__ = ["PlanUnavailableError"]
