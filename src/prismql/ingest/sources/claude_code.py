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
from .calls import attach_outcomes, call_id, describe_call

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
    "uuid": pl.Utf8,
    "parent": pl.Utf8,
    # The call as structure (graph #129) and the sub-agent it ran in (#131).
    "call": pl.Utf8,
    "cmd": pl.Utf8,
    "path": pl.Utf8,
    "host": pl.Utf8,
    "action": pl.Utf8,
    "outcome": pl.Utf8,
    "duration_ms": pl.Int64,
    "duration_bucket": pl.Utf8,
    "output_chars": pl.Int64,
    "output_bucket": pl.Utf8,
    "agent": pl.Utf8,
    "spawned": pl.Utf8,
}


def read_claude_code(path: Path) -> pl.DataFrame:
    """A transcript file or a project folder → the canonical stream.

    Rows are ordered by timestamp across sessions; ``session`` keeps them
    apart (``field(session, $s)`` = "in the same session").
    """
    if not path.exists():
        raise FileNotFoundError(path)
    root = path.parent if path.is_file() else path
    files = (
        [path]
        if path.is_file()
        else sorted(p for p in path.rglob("*.jsonl") if "memory" not in p.parts)
    )
    project = root.name
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for file in files:
        rows.extend(_read_file(file, root, project, skipped))
    if skipped:
        summary = ", ".join(f"{t}×{n}" for t, n in skipped.most_common())
        print(f"  skipped bookkeeping records: {summary}")
    df = pl.DataFrame(rows, schema=SCHEMA)
    return normalize(df, id_col="id", time_col="time", sort="time")


def _read_file(
    file: Path, root: Path, project: str, skipped: Counter[str]
) -> list[dict[str, Any]]:
    # Path under the project folder: sub-agent files reuse names across
    # sub-folders, so the stem alone would not be unique.
    stem = file.relative_to(root).with_suffix("").as_posix()
    tool_names: dict[str, str] = {}
    out: list[dict[str, Any]] = []
    with file.open(encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # A transcript cut mid-write (harness crash): the line is not
                # an event of the conversation, but it is counted.
                skipped["<truncated line>"] += 1
                continue
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
                "uuid": rec.get("uuid"),
                "parent": rec.get("parentUuid"),
                "agent": rec.get("agentId"),
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
                if row["kind"] == "tool_result":
                    spawned = rec.get("toolUseResult") or {}
                    row["spawned"] = (
                        spawned.get("agentId") if isinstance(spawned, dict) else None
                    )
                row.update(base)
                # Not the record uuid: it repeats within a file (a sub-agent
                # transcript replays records). File, line and block are unique.
                row["id"] = f"{stem}:{lineno}:{i}"
                out.append(row)
    attach_outcomes(out)
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
        return {
            "kind": "tool_use",
            "tool": name,
            "error": None,
            "text": _cap(payload),
            "call": call_id(block.get("id")),
            **describe_call(name, block.get("input")),
        }
    if btype == "tool_result":
        result_tool = tool_names.get(str(block.get("tool_use_id")))
        content = block.get("content")
        if isinstance(content, list):
            content = "\n".join(
                str(c.get("text", "")) for c in content if isinstance(c, dict)
            )
        text = str(content or "")
        return {
            "kind": "tool_result",
            "tool": result_tool,
            "error": bool(block.get("is_error", False)),
            "text": _cap(text),
            "call": call_id(block.get("tool_use_id")),
            "output_chars": len(text),
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
    """Bound the text and drop lone surrogates (they cannot reach Arrow)."""
    text = text if len(text) <= TEXT_CAP else text[:TEXT_CAP]
    return text.encode("utf-8", "surrogatepass").decode("utf-8", "replace")
