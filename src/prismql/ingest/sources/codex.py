"""Codex CLI session rollouts → one event per response item.

Format observed on the live surface (graph ``@aleph/prismql``, node #57):
``~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl``. ``session_meta`` and
``turn_context`` records carry the project and the model; ``response_item``
records are the stream; every other record type (``event_msg`` token
counts and the like) is skipped and counted. An unknown response item is
an error, never a skip.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

from ..core import normalize
from .calls import describe_call
from .claude_code import SCHEMA, TEXT_CAP, _cap
from .outcomes import attach_outcomes, call_id

# The exec tool's own header, at the start of its output — not a phrase
# quoted somewhere inside a successful tool's output.
_EXIT = re.compile(
    r"\AChunk ID: [^\n]*\n(?:Wall time: [^\n]*\n)?Process exited with code (\d+)"
)


def read_codex(path: Path) -> pl.DataFrame:
    """A rollout file or the sessions folder → the canonical stream."""
    if not path.exists():
        raise FileNotFoundError(path)
    files = [path] if path.is_file() else sorted(path.rglob("rollout-*.jsonl"))
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for file in files:
        rows.extend(_read_file(file, skipped))
    if skipped:
        summary = ", ".join(f"{t}×{n}" for t, n in skipped.most_common())
        print(f"  skipped bookkeeping records: {summary}")
    df = pl.DataFrame(rows, schema=SCHEMA)
    return normalize(df, id_col="id", time_col="time", sort="time")


def _read_file(file: Path, skipped: Counter[str]) -> list[dict[str, Any]]:
    session = file.stem
    project: str | None = None
    model: str | None = None
    call_names: dict[str, str] = {}
    out: list[dict[str, Any]] = []
    with file.open(encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped["<truncated line>"] += 1
                continue
            rtype = rec.get("type")
            payload = rec.get("payload") or {}
            if rtype == "session_meta":
                session = payload.get("id") or session
                project = Path(payload["cwd"]).name if payload.get("cwd") else None
                continue
            if rtype == "turn_context":
                model = payload.get("model") or model
                continue
            if rtype != "response_item":
                skipped[str(rtype)] += 1
                continue
            row = _item_row(payload, call_names, f"{file}:{lineno}")
            if row is None:
                continue
            row.update(
                {
                    # A resumed session writes a second rollout file with the
                    # same session id: the file stem keeps ids unique.
                    "id": f"{file.stem}:{lineno}",
                    "time": rec.get("timestamp"),
                    "session": session,
                    "project": project,
                    "model": model,
                    "sidechain": False,
                    "uuid": None,
                    "parent": None,
                }
            )
            out.append(row)
    attach_outcomes(out)
    return out


def _item_row(
    item: dict[str, Any], call_names: dict[str, str], where: str
) -> dict[str, Any] | None:
    itype = item.get("type")
    if itype in ("message", "agent_message"):
        role = item.get("role") or "assistant"
        text = _join_text(item.get("content"))
        if not text.strip():
            return None
        kind = {"user": "prompt", "developer": "developer"}.get(role, "text")
        return {
            "kind": kind,
            "role": role,
            "tool": None,
            "error": None,
            "text": _cap(text),
        }
    if itype == "reasoning":
        text = _join_text(item.get("summary"))
        return {
            "kind": "thinking",
            "role": "assistant",
            "tool": None,
            "error": None,
            "text": _cap(text),
        }
    if itype in ("function_call", "custom_tool_call", "tool_search_call"):
        name = str(item.get("name") or itype.removesuffix("_call"))
        call_names[str(item.get("call_id"))] = name
        payload = item.get("arguments") if "arguments" in item else item.get("input")
        if not isinstance(payload, str):
            payload = json.dumps(payload, ensure_ascii=False)
        return {
            "kind": "tool_use",
            "role": "assistant",
            "tool": name,
            "error": None,
            "text": _cap(payload),
            "call": call_id(item.get("call_id")),
            **describe_call(name, payload),
        }
    if itype == "web_search_call":
        action = item.get("action") or {}
        return {
            "kind": "tool_use",
            "role": "assistant",
            "tool": "web_search",
            "error": None,
            "text": _cap(str(action.get("query") or json.dumps(action))),
            **describe_call("web_search", action),
        }
    if itype in (
        "function_call_output",
        "custom_tool_call_output",
        "tool_search_output",
    ):
        output = item.get("output")
        if not isinstance(output, str):
            output = json.dumps(output, ensure_ascii=False)
        # Same meaning as the Claude Code column: True only where the harness
        # itself reports a failure (a non-zero exit of the exec tool); Codex
        # records no failure flag for other tools, so those are False.
        exit_code = _EXIT.match(output)
        return {
            "kind": "tool_result",
            "role": "user",
            "tool": call_names.get(str(item.get("call_id"))),
            "error": bool(exit_code and int(exit_code.group(1)) != 0),
            "text": _cap(output),
            "call": call_id(item.get("call_id")),
            "output_chars": len(output),
        }
    if itype == "compaction":
        return {
            "kind": "compaction",
            "role": "assistant",
            "tool": None,
            "error": None,
            "text": None,
        }
    raise ValueError(f"{where}: unknown response item type {itype!r}")


def _join_text(blocks: Any) -> str:
    if isinstance(blocks, str):
        return blocks
    if not isinstance(blocks, list):
        return ""
    return "\n".join(
        str(b.get("text", "")) for b in blocks if isinstance(b, dict) and b.get("text")
    )[: TEXT_CAP * 2]
