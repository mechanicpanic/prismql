"""Sequence/window primitives as a Polars plan (spec 2026-09-18, P2).

Optional: requires the ``[plan]`` extra (polars, pyarrow). Nothing here is
wired into the executor yet; the engine at HEAD is the oracle these
primitives are tested against — only where STATE.md says it is valid.
"""

from __future__ import annotations

from typing import Any

from ..exceptions import PrismQLRuntimeError


class PlanUnavailableError(PrismQLRuntimeError):
    """polars is not installed: uv pip install 'prismql[plan]'."""


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
