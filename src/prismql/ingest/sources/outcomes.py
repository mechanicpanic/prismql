"""A call's end, moved onto the call (graph @aleph/prismql, #129).

A result is a separate event in both harness logs; its outcome, duration
and size are copied onto the call it answers, with the words a query can
name for the numbers.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from typing import Any


def call_id(raw: Any) -> str | None:
    """The id joining a call to its result; a missing id joins nothing."""
    return None if raw is None else str(raw)


def duration_bucket(ms: int | None) -> str | None:
    if ms is None:
        return None
    for limit, word in ((1_000, "instant"), (10_000, "short"), (60_000, "medium")):
        if ms < limit:
            return word
    return "long" if ms < 600_000 else "very_long"


def output_bucket(chars: int | None) -> str | None:
    if chars is None:
        return None
    if chars == 0:
        return "empty"
    for limit, word in ((1_000, "small"), (10_000, "medium"), (100_000, "large")):
        if chars < limit:
            return word
    return "huge"


def attach_outcomes(rows: list[dict[str, Any]]) -> None:
    """Copy each result's outcome, duration and size onto its call row.

    Rows are in file order. A result answers the earliest call with its id
    still waiting, so a record a sub-agent transcript replays pairs with
    its own replayed result, not with the last one in the file.
    """
    waiting: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for row in rows:
        call = row.get("call")
        if row["kind"] == "tool_use":
            row["outcome"] = "none"
            if call:
                waiting[call].append(row)
        elif row["kind"] == "tool_result":
            use = waiting[call].popleft() if call and waiting[call] else None
            # The sub-agent belongs to the call that started it, once.
            spawned = row.pop("spawned", None)
            if use is None:
                continue
            use["outcome"] = "error" if row["error"] else "ok"
            use["duration_ms"] = _millis(use["time"], row["time"])
            use["output_chars"] = row.get("output_chars")
            use["spawned"] = spawned
    for row in rows:
        row["duration_bucket"] = duration_bucket(row.get("duration_ms"))
        row["output_bucket"] = output_bucket(row.get("output_chars"))


def _millis(start: str | None, end: str | None) -> int | None:
    """Milliseconds from call to result; ``None`` when either time is not a
    comparable instant (ingest keeps such rows and reports them)."""
    try:
        a = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
        return round((b - a).total_seconds() * 1000)
    except (TypeError, ValueError):
        return None
