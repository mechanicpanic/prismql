"""Claude Code session transcripts → one event per content block.

Format observed on the live surface (graph ``@aleph/prismql``, node #56):
``~/.claude/projects/<project-slug>/*.jsonl``, one JSON record per line.
The stream is made of the ``user`` and ``assistant`` records; every other
record type is bookkeeping and is skipped — counted, not silent. Inside a
stream record an unknown content block is an error, never a skip.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import polars as pl

from ..core import normalize

STREAM_TYPES = {"user", "assistant"}
TEXT_CAP = 4000

SCHEMA = {
    "id": pl.Utf8,
    "time": pl.Utf8,
    "session": pl.Utf8,
    "project": pl.Utf8,
    "model": pl.Utf8,
    "role": pl.Utf8,
    "kind": pl.Utf8,
    "tool": pl.Utf8,
    "error": pl.Boolean,
    "sidechain": pl.Boolean,
    "text": pl.Utf8,
    "parent": pl.Utf8,
}


def read_claude_code(path: Path) -> pl.DataFrame:
    """A transcript file or a project folder → the canonical stream.

    Rows are ordered by timestamp across sessions; ``session`` keeps them
    apart (``field(session, $s)`` = "in the same session").
    """
    files = (
        [path]
        if path.is_file()
        else sorted(p for p in path.rglob("*.jsonl") if "memory" not in p.parts)
    )
    if not files:
        raise ValueError(f"no .jsonl transcripts under {path}")
    project = path.parent.name if path.is_file() else path.name
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for file in files:
        rows.extend(_read_file(file, project, skipped))
    if skipped:
        summary = ", ".join(f"{t}×{n}" for t, n in skipped.most_common())
        print(f"  skipped bookkeeping records: {summary}")
    df = pl.DataFrame(rows, schema=SCHEMA)
    return normalize(df, id_col="id", time_col="time", sort="time")


def _read_file(file: Path, project: str, skipped: Counter[str]) -> list[dict[str, Any]]:
    tool_names: dict[str, str] = {}
    out: list[dict[str, Any]] = []
    with file.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            rtype = rec.get("type")
            if rtype not in STREAM_TYPES:
                skipped[str(rtype)] += 1
                continue
            msg = rec.get("message") or {}
            base = {
                "time": rec.get("timestamp"),
                "session": rec.get("sessionId"),
                "project": project,
                "model": msg.get("model"),
                "role": rtype,
                "sidechain": bool(rec.get("isSidechain", False)),
                "parent": rec.get("parentUuid"),
            }
            content = msg.get("content")
            blocks = (
                [{"type": "text", "text": content}]
                if isinstance(content, str)
                else content
            )
            if not isinstance(blocks, list):
                raise ValueError(
                    f"{file}:{lineno}: message.content is {type(content).__name__}"
                )
            for i, block in enumerate(blocks):
                row = _block_row(block, rtype, tool_names, f"{file}:{lineno}")
                if row is None:
                    continue
                row.update(base)
                row["id"] = f"{rec.get('uuid')}:{i}"
                out.append(row)
    return out


def _block_row(
    block: dict[str, Any], rtype: str, tool_names: dict[str, str], where: str
) -> dict[str, Any] | None:
    btype = block.get("type")
    if btype == "text":
        text = block.get("text") or ""
        if not text.strip():
            return None
        kind = "prompt" if rtype == "user" else "text"
        return {"kind": kind, "tool": None, "error": None, "text": _cap(text)}
    if btype == "thinking":
        return {
            "kind": "thinking",
            "tool": None,
            "error": None,
            "text": _cap(block.get("thinking") or ""),
        }
    if btype == "tool_use":
        name = str(block.get("name"))
        tool_names[str(block.get("id"))] = name
        payload = json.dumps(block.get("input"), ensure_ascii=False)
        return {"kind": "tool_use", "tool": name, "error": None, "text": _cap(payload)}
    if btype == "tool_result":
        result_tool = tool_names.get(str(block.get("tool_use_id")))
        content = block.get("content")
        if isinstance(content, list):
            content = "\n".join(
                str(c.get("text", "")) for c in content if isinstance(c, dict)
            )
        return {
            "kind": "tool_result",
            "tool": result_tool,
            "error": bool(block.get("is_error", False)),
            "text": _cap(str(content or "")),
        }
    if btype == "fallback":
        # The harness switched models mid-turn: an event worth keeping.
        src = (block.get("from") or {}).get("model")
        dst = (block.get("to") or {}).get("model")
        return {
            "kind": "fallback",
            "tool": None,
            "error": None,
            "text": f"{src} -> {dst}",
        }
    if btype in ("image", "document"):
        return {"kind": btype, "tool": None, "error": None, "text": None}
    raise ValueError(f"{where}: unknown content block type {btype!r}")


def _cap(text: str) -> str:
    return text if len(text) <= TEXT_CAP else text[:TEXT_CAP]
