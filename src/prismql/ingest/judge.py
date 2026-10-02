"""Ask a local decision model typed questions about events, at ingest
(graph @aleph/prismql, #154; the surface it speaks to: #153).

A question file names each question, which events it applies to
(``where``: column = value), which columns make the state it reads
(``state``, default ``text``), how much of a long text it reads
(``max_chars``, default all), and below which confidence its answer is
``unsure`` (``min_confidence``). Each answer becomes two columns: the label
a query matches with ``field()`` — ``yes``/``no`` for a yes/no question,
the chosen option, the most likely level of a score, or ``unsure`` — and
``<name>_p``: p(true) for yes/no, the model's confidence otherwise. Events a
question does not apply to hold null. The model and the exact questions are
stamped into the file, so a column can be traced to what produced it.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

import polars as pl

JUDGE_KEY = b"prismql.judge"
DEFAULT_URL = "http://127.0.0.1:8000"
TYPES = ("noul", "choice", "score")

Post = Callable[[Any, dict[str, Any]], dict[str, Any]]


def load_questions(path: str | Path) -> dict[str, dict[str, Any]]:
    """The ``[questions.<name>]`` tables of a TOML file, checked."""
    data = tomllib.loads(Path(path).read_text())
    questions = data.get("questions") or {}
    if not questions:
        raise ValueError(f"{path}: no [questions.<name>] tables")
    for name, q in questions.items():
        kind = q.get("type")
        if kind not in TYPES:
            raise ValueError(f"question {name!r}: type must be one of {TYPES}")
        if not q.get("instructions"):
            raise ValueError(f"question {name!r}: instructions are required")
        if kind == "choice" and not isinstance(q.get("criteria"), dict):
            raise ValueError(f"question {name!r}: a choice needs criteria (a table)")
        if kind == "score" and not isinstance(q.get("criteria"), list):
            raise ValueError(f"question {name!r}: a score needs criteria (a list)")
    return questions


def http_post(url: str) -> Post:
    """A client for ``POST {url}/v1/systemone``."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"--judge-url must be http(s): {url!r}")
    endpoint = url.rstrip("/") + "/v1/systemone"

    def post(state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps({"state": state, "questions": questions}).encode()
        req = urllib.request.Request(  # noqa: S310 - scheme checked above
            endpoint, data=body, headers={"content-type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            return dict(json.loads(resp.read()))

    return post


def _wire(q: dict[str, Any]) -> dict[str, Any]:
    """What the model is sent: its type, instructions and criteria only."""
    return {k: q[k] for k in ("type", "instructions", "criteria") if k in q}


def _clip(state: Any, limit: int) -> Any:
    """The start of each text, ``limit`` characters (0: whole): a long
    message's point is usually in its first lines, and the rest dilutes
    the model's read (observed 2026-10-02, #154)."""
    if not limit:
        return state
    if isinstance(state, str):
        return state[:limit]
    return {k: v[:limit] if isinstance(v, str) else v for k, v in state.items()}


def _applies(q: dict[str, Any], row: dict[str, Any]) -> bool:
    return all(row.get(col) == val for col, val in (q.get("where") or {}).items())


def _label(q: dict[str, Any], answer: dict[str, Any]) -> tuple[str, float]:
    floor = float(q.get("min_confidence", 0.0))
    if q["type"] == "noul":
        p = float(answer["noul"])
        sure = abs(2 * p - 1)
        return ("unsure" if sure < floor else "yes" if p >= 0.5 else "no"), p
    conf = float(answer["confidence"])
    if conf < floor:
        return "unsure", conf
    if q["type"] == "choice":
        return str(answer["choice"]), conf
    probs = answer["probabilities"]
    best = max(probs, key=lambda k: probs[k])
    legend = answer.get("legend") or {str(i): c for i, c in enumerate(q["criteria"])}
    return str(legend[best]), conf


def _check_columns(df: pl.DataFrame, questions: dict[str, dict[str, Any]]) -> None:
    for name, q in questions.items():
        for col in (name, f"{name}_p"):
            if col in df.columns:
                raise ValueError(f"question {name!r}: column {col!r} exists")
        for col in [*(q.get("where") or {}), *q.get("state", ["text"])]:
            if col not in df.columns:
                raise ValueError(f"question {name!r}: no column {col!r}")


def _by_state(
    questions: dict[str, dict[str, Any]], row: dict[str, Any]
) -> dict[tuple[str, ...], dict[str, Any]]:
    """The questions that apply to ``row``, grouped by the columns they read:
    one request per state shape, so they share the model's read of it."""
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for name, q in questions.items():
        if _applies(q, row):
            groups.setdefault(tuple(q.get("state", ["text"])), {})[name] = q
    return groups


def judge(
    df: pl.DataFrame,
    questions: dict[str, dict[str, Any]],
    *,
    post: Post,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """``df`` with a label and a ``_p`` column per question, and the stamp."""
    _check_columns(df, questions)
    labels: dict[str, list[str | None]] = {n: [None] * df.height for n in questions}
    probs: dict[str, list[float | None]] = {n: [None] * df.height for n in questions}
    model = None
    for i, row in enumerate(df.iter_rows(named=True)):
        for cols, qs in _by_state(questions, row).items():
            values = {c: row[c] for c in cols if row[c] is not None}
            if not values:
                continue
            # One column goes as bare text: the model reads it better than
            # the same text wrapped in an object (observed 2026-10-02).
            state = values[cols[0]] if len(cols) == 1 else values
            state = _clip(state, min((q.get("max_chars") or 0) for q in qs.values()))
            reply = post(state, {n: _wire(q) for n, q in qs.items()})
            model = model or reply.get("model")
            for name, answer in reply["answers"].items():
                labels[name][i], probs[name][i] = _label(qs[name], answer)
    out = df.with_columns(
        *[pl.Series(n, labels[n], dtype=pl.Utf8) for n in questions],
        *[pl.Series(f"{n}_p", probs[n], dtype=pl.Float64) for n in questions],
    )
    canonical = json.dumps(questions, sort_keys=True, ensure_ascii=False)
    stamp = {
        "model": model,
        "questions": questions,
        "sha256": hashlib.sha256(canonical.encode()).hexdigest(),
    }
    return out, stamp
