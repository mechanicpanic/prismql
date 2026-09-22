# Results as server objects, responses as windows — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every `/evaluate`, `/search` and `/similar` result is kept on the server in folded form (positions, plus scores for hits) under a `result_id`. The response is its first page. Any page can be fetched later, hydrated on demand, or streamed whole as JSONL.

**Architecture:** A new `server/results.py` holds `StoredResult` (flat `array` of positions with group offsets) and `ResultStore` (id → result, byte budget, oldest evicted first, cleared on `/reload`). A new `server/pages.py` turns a window of a stored result into the wire payload. It maps positions to ids and times through the backend's order axis and hydrates only when asked, projected to `fields`. `app.py` stores every non-aggregate result, answers with page 0 plus `result_id` and `total`, and adds `GET /results/{id}` and `GET /results/{id}.jsonl`. File output becomes "materialize the stored result". Scouting ranks to a fixed depth and reports the true match count.

**Tech Stack:** Python ≥ 3.12, FastAPI, stdlib `array`, tantivy 0.26.2 (`Searcher.search(..., count=True).count`, observed on the installed package), numpy optional (`SemanticIndex`).

**Spec:** the decision node — graph `@aleph/prismql` #65 («Результат — объект сервера, ответ — окно в него»), anga to the board transformation #63. There is no spec file. The node's before/after and done criteria are the spec.

## Global Constraints

- The engine is untouched: it already computes the whole result. Only the server's shaping changes.
- `truncated` means one thing on every endpoint: **paging further returns more** (`offset + count < kept`, where `kept` = stored items; for `/evaluate` `kept == total`). When scouting kept fewer than it found, `kept < total` says so; `truncated` never promises items paging cannot reach (a client looping `offset += count` while `truncated` must terminate).
- `count` is the number of items in this response (unchanged meaning). `total` is the number found. Scouting adds `kept` (how many are stored, `min(total, scout_depth)`).
- `max_results` (request and config) keeps its name and becomes the page size / the largest page. No rename: the demo, the MCP shim and the skill already send it.
- Aggregate and grouped (`GROUP BY`) results are small by construction: they are not stored and carry no `result_id`.
- Positions are the order axis's load-order positions (`backend.positions(ids)`). Ids are labels.
- Times in payloads are ISO-8601 UTC strings from `backend.timestamps_at(positions, corpus_cfg.timestamp_field)`, or `null` when the corpus has no such field.
- The store lives in memory only. `/reload` clears it. A server restart loses it. The journal summary survives both.
- New files stay under 150 lines each (AGENTS.md stage review rule). `app.py` is already large, so new logic goes into the new modules, not into `app.py`.
- Gate: `make check`. Commit with explicit paths only. Commit trailer per the session's attribution lines. Never push.

## File Structure

- Create `src/prismql/server/results.py`: `StoredResult`, `ResultStore`. Pure data, no FastAPI, no backend.
- Create `src/prismql/server/pages.py`: `page_payload(...)`, `iso_micros(...)`. Backend-facing, no FastAPI.
- Modify `src/prismql/server/config.py`: `results_memory_mb`, `scout_depth`, per-corpus `board_fields`.
- Modify `src/prismql/server/app.py`: store on evaluate and scouting, the `/results` routes, journal fields, `/corpora` board fields, reload clears the store. Remove `result_to_payload`'s slicing and hydration (moved to `pages.py`) and `_hits_payload` / `_scout_limit`.
- Modify `src/prismql/backends/tantivy.py`, `src/prismql/backends/semantic.py`: `rank_counted`.
- Modify `src/prismql/server/mcp.py`: a `result_page` tool.
- Tests: create `tests/test_server_results.py` (store and pages units); modify `tests/test_server_app.py`, `tests/test_server_mcp.py`, `tests/test_semantic.py`, `tests/test_tantivy_backend.py`.
- Docs: `docs/USER-GUIDE.md` (server section), `docs/AGENT-USE.md`, `skills/prismql/SKILL.md`, `README.md` (server bullet), `CHANGELOG.md`, `STATE.md`.

---

### Task 1: `StoredResult` and `ResultStore`

**Files:**
- Create: `src/prismql/server/results.py`
- Test: `tests/test_server_results.py`

**Interfaces:**
- Produces:
  - `StoredResult.from_groups(kind: str, corpus: str, groups: list[list[int]], labels: list[str] | None = None) -> StoredResult`
  - `StoredResult.from_hits(corpus: str, hits: list[tuple[int, float]], total: int) -> StoredResult`
  - `StoredResult.window(offset: int, limit: int) -> list[tuple[list[int], float | None]]`
  - `len(StoredResult)` = stored items. Attributes `.kind`, `.corpus`, `.labels`, `.total`, `.nbytes`.
  - `ResultStore(budget_bytes: int)` with `.put(r) -> str`, `.get(rid) -> StoredResult | None`, `.clear()`.

- [ ] **Step 1: Write the failing tests**

```python
"""The server's result store: folded results under ids (graph #65)."""

from prismql.server.results import ResultStore, StoredResult


def test_groups_are_folded_and_windowed():
    r = StoredResult.from_groups("groups", "c", [[0, 5], [7, 9], [12, 30]])
    assert len(r) == 3 and r.total == 3 and r.kind == "groups"
    assert r.window(1, 5) == [([7, 9], None), ([12, 30], None)]
    assert r.window(3, 5) == []


def test_hits_keep_scores_and_the_true_total():
    r = StoredResult.from_hits("c", [(4, 0.9), (1, 0.5)], total=17)
    assert len(r) == 2 and r.total == 17 and r.kind == "hits"
    assert r.window(0, 1) == [([4], 0.9)]


def test_store_evicts_oldest_over_budget_but_keeps_the_newest():
    one = StoredResult.from_groups("groups", "c", [[i] for i in range(100)])
    store = ResultStore(budget_bytes=one.nbytes * 2)
    a, b, c = (store.put(StoredResult.from_groups("groups", "c", [[i] for i in range(100)])) for _ in range(3))
    assert store.get(a) is None and store.get(b) and store.get(c)
    huge = StoredResult.from_groups("groups", "c", [[i] for i in range(10_000)])
    h = store.put(huge)  # bigger than the whole budget: kept alone
    assert store.get(h) is huge and store.get(c) is None


def test_ids_are_unique_and_clear_forgets_everything():
    store = ResultStore(budget_bytes=1 << 20)
    r1 = store.put(StoredResult.from_groups("groups", "c", [[1]]))
    r2 = store.put(StoredResult.from_groups("groups", "c", [[2]]))
    assert r1 != r2 and r1.startswith("r")
    store.clear()
    assert store.get(r1) is None and store.get(r2) is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_server_results.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'prismql.server.results'`.

- [ ] **Step 3: Write the implementation**

```python
"""Query results kept on the server, folded: positions (and scores), no data.

A result is an object under an id; a response is a window into it
(graph @aleph/prismql, node #65). Memory is a byte budget; the oldest
results go first, their journal summaries stay.
"""

from __future__ import annotations

import threading
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from itertools import count


@dataclass
class StoredResult:
    kind: str  # "groups" | "named" | "hits"
    corpus: str
    offsets: array  # item i spans positions[offsets[i]:offsets[i + 1]]
    positions: array
    scores: array | None = None  # one per item, hits only
    labels: list[str] | None = None
    total: int = 0  # found; exceeds len() when scouting kept only a depth

    @classmethod
    def from_groups(
        cls,
        kind: str,
        corpus: str,
        groups: list[list[int]],
        labels: list[str] | None = None,
    ) -> StoredResult:
        offsets, positions = array("q", [0]), array("q")
        for g in groups:
            positions.extend(g)
            offsets.append(len(positions))
        return cls(kind, corpus, offsets, positions, None, labels, len(groups))

    @classmethod
    def from_hits(
        cls, corpus: str, hits: list[tuple[int, float]], total: int
    ) -> StoredResult:
        offsets = array("q", range(len(hits) + 1))
        positions = array("q", (p for p, _ in hits))
        scores = array("d", (s for _, s in hits))
        return cls("hits", corpus, offsets, positions, scores, None, total)

    def __len__(self) -> int:
        return len(self.offsets) - 1

    @property
    def nbytes(self) -> int:
        size = self.offsets.itemsize * len(self.offsets)
        size += self.positions.itemsize * len(self.positions)
        if self.scores is not None:
            size += self.scores.itemsize * len(self.scores)
        return size

    def window(self, offset: int, limit: int) -> list[tuple[list[int], float | None]]:
        end = min(len(self), offset + limit)
        return [
            (
                list(self.positions[self.offsets[i] : self.offsets[i + 1]]),
                self.scores[i] if self.scores is not None else None,
            )
            for i in range(max(0, offset), end)
        ]


class ResultStore:
    def __init__(self, budget_bytes: int) -> None:
        self.budget = budget_bytes
        self._items: OrderedDict[str, StoredResult] = OrderedDict()
        self._bytes = 0
        self._ids = count(1)
        self._lock = threading.Lock()

    def put(self, result: StoredResult) -> str:
        with self._lock:
            rid = f"r{next(self._ids)}"
            self._items[rid] = result
            self._bytes += result.nbytes
            while self._bytes > self.budget and len(self._items) > 1:
                _, old = self._items.popitem(last=False)
                self._bytes -= old.nbytes
            return rid

    def get(self, rid: str) -> StoredResult | None:
        with self._lock:
            return self._items.get(rid)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._bytes = 0
```

Note the eviction loop in `test_store_evicts_oldest...`: when `huge` goes in, everything older is evicted, because the loop runs while over budget and more than one item remains.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_server_results.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/prismql/server/results.py tests/test_server_results.py
git commit -m "Server: a result store that keeps query results folded under ids"
```

---

### Task 2: `page_payload`, a window of a stored result on the wire

**Files:**
- Create: `src/prismql/server/pages.py`
- Test: `tests/test_server_results.py` (append)

**Interfaces:**
- Consumes: `StoredResult` (Task 1); the backend order contract `ids_at`, `timestamps_at`, `get_documents`.
- Produces: `page_payload(result: StoredResult, backend: Any, *, id_field: str, time_field: str, offset: int, limit: int, hydrate: bool, fields: list[str] | None) -> dict[str, Any]`, returning:
  - groups / named: `{"kind", "total", "offset", "count", "truncated", "results": [{"ids", "positions", "times", "events"?}], "labels"?}`
  - hits: `{"kind": "hits", "total", "kept", "offset", "count", "truncated", "hits": [{"id", "position", "score", "time", "event"?}]}`

  Also `iso_micros(us: int | None) -> str | None`.

- [ ] **Step 1: Write the failing tests**

```python
from prismql.backends.memory import MemoryBackend
from prismql.server.pages import page_payload

DOCS = [
    {"id": "a", "text": "one", "kind": "x", "timestamp": "2026-06-03T18:02:11Z"},
    {"id": "b", "text": "two", "kind": "y", "timestamp": "2026-06-03T18:19:40Z"},
    {"id": "c", "text": "three", "kind": "x", "timestamp": "2026-06-03T18:30:00Z"},
]


def _backend() -> MemoryBackend:
    return MemoryBackend(DOCS, id_field="id", timestamp_fields=["timestamp"])


def test_group_page_carries_positions_times_and_projected_events():
    r = StoredResult.from_groups("groups", "c", [[0, 2], [1]])
    p = page_payload(
        r, _backend(), id_field="id", time_field="timestamp",
        offset=0, limit=1, hydrate=True, fields=["text"],
    )
    assert p["total"] == 2 and p["count"] == 1 and p["truncated"] is True
    g = p["results"][0]
    assert g["ids"] == ["a", "c"] and g["positions"] == [0, 2]
    assert g["times"] == ["2026-06-03T18:02:11+00:00", "2026-06-03T18:30:00+00:00"]
    assert g["events"] == [{"id": "a", "text": "one"}, {"id": "c", "text": "three"}]


def test_unhydrated_page_has_no_events_and_unknown_time_field_is_null():
    r = StoredResult.from_groups("groups", "c", [[1]])
    p = page_payload(
        r, _backend(), id_field="id", time_field="nope",
        offset=0, limit=10, hydrate=False, fields=None,
    )
    assert "events" not in p["results"][0]
    assert p["results"][0]["times"] == [None] and p["truncated"] is False


def test_hit_page_reports_kept_and_total():
    r = StoredResult.from_hits("c", [(2, 0.9), (0, 0.4)], total=5)
    p = page_payload(
        r, _backend(), id_field="id", time_field="timestamp",
        offset=1, limit=10, hydrate=False, fields=None,
    )
    assert p["kind"] == "hits" and p["kept"] == 2 and p["total"] == 5
    assert p["hits"] == [
        {"id": "a", "position": 0, "score": 0.4, "time": "2026-06-03T18:02:11+00:00"}
    ]
    assert p["truncated"] is False  # 3 more were found but not kept: kept < total says so
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_server_results.py -v`
Expected: the three new tests FAIL with `ModuleNotFoundError: No module named 'prismql.server.pages'`.

- [ ] **Step 3: Write the implementation**

```python
"""A window of a stored result, shaped for the wire (graph #65).

Positions map to ids and times through the backend's order axis;
documents are fetched only when hydrating, projected to ``fields``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .results import StoredResult


def iso_micros(us: int | None) -> str | None:
    if us is None:
        return None
    return datetime.fromtimestamp(us / 1_000_000, UTC).isoformat()


def _times(backend: Any, positions: list[int], field: str) -> list[str | None]:
    try:
        raw = backend.timestamps_at(positions, field)
    except KeyError:  # the corpus has no such timestamp field
        return [None] * len(positions)
    return [iso_micros(v) for v in raw]


def page_payload(
    result: StoredResult,
    backend: Any,
    *,
    id_field: str,
    time_field: str,
    offset: int,
    limit: int,
    hydrate: bool,
    fields: list[str] | None,
) -> dict[str, Any]:
    window = result.window(offset, limit)
    flat = [p for positions, _ in window for p in positions]
    ids = backend.ids_at(flat)
    times = _times(backend, flat, time_field)
    by_id: dict[Any, dict[str, Any]] = {}
    if hydrate and ids:
        for doc in backend.get_documents(list(dict.fromkeys(ids))):
            if fields is not None:
                doc = {k: doc[k] for k in [id_field, *fields] if k in doc}
            by_id[doc.get(id_field)] = doc
    payload: dict[str, Any] = {
        "kind": result.kind,
        "total": result.total,
        "offset": offset,
        "count": len(window),
        "truncated": offset + len(window) < len(result),
    }
    items: list[dict[str, Any]] = []
    cursor = 0
    for positions, score in window:
        n = len(positions)
        span_ids, span_times = ids[cursor : cursor + n], times[cursor : cursor + n]
        cursor += n
        if result.kind == "hits":
            item: dict[str, Any] = {
                "id": span_ids[0], "position": positions[0],
                "score": round(score or 0.0, 4), "time": span_times[0],
            }
            if hydrate and span_ids[0] in by_id:
                item["event"] = by_id[span_ids[0]]
        else:
            item = {"ids": span_ids, "positions": positions, "times": span_times}
            if hydrate:
                item["events"] = [by_id[i] for i in span_ids if i in by_id]
        items.append(item)
    if result.kind == "hits":
        payload["kept"] = len(result)
        payload["hits"] = items
    else:
        payload["results"] = items
        if result.labels is not None:
            payload["labels"] = result.labels
    return payload
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_server_results.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add src/prismql/server/pages.py tests/test_server_results.py
git commit -m "Server: page a stored result, with positions, times and projected events"
```

---

### Task 3: Config — memory budget, scouting depth, board fields

**Files:**
- Modify: `src/prismql/server/config.py` (`CorpusConfig`, `ServerConfig`, `corpus()`, `load_config`)
- Test: `tests/test_server_config.py`

**Interfaces:**
- Produces: `ServerConfig.results_memory_mb: int = 256`, `ServerConfig.scout_depth: int = 1000`, `CorpusConfig.board_fields: dict[str, str]` and `ServerConfig.board_fields` (flat mirror), parsed from `[server] results_memory_mb`, `[server] scout_depth`, `[corpora.<name>.board] kind = "…", actor = "…"` (flat form: `[board]`).

- [ ] **Step 1: Write the failing test**

```python
def test_results_budget_scout_depth_and_board_fields(tmp_path):
    cfg_path = tmp_path / "prismql.toml"
    data = tmp_path / "e.jsonl"
    data.write_text('{"id": 1, "text": "x"}\n')
    cfg_path.write_text(
        f"""
[server]
results_memory_mb = 64
scout_depth = 300

[corpora.village]
type = "memory"
data = "{data}"

[corpora.village.board]
kind = "kind"
actor = "agent_id"
"""
    )
    cfg = load_config(cfg_path)
    assert cfg.results_memory_mb == 64 and cfg.scout_depth == 300
    assert cfg.corpus("village").board_fields == {"kind": "kind", "actor": "agent_id"}
```

(`load_config` reads corpora as `[corpora.<name>]` with keys `type`, `data` — `config.py:154-167` — and `[server]` keys via `server.get(...)`; `load_config` is already imported in this test file.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_server_config.py -k board -v`
Expected: FAIL with `AttributeError: 'ServerConfig' object has no attribute 'results_memory_mb'`.

- [ ] **Step 3: Implement**

In `CorpusConfig`, after `semantic_text_field`:

```python
    # [corpora.<name>.board]: which fields the board shows as an event's
    # kind and actor; the text field is always shown (graph #63).
    board_fields: dict[str, str] = field(default_factory=dict)
```

In `ServerConfig`, after `activity_max`:

```python
    # Folded results kept for paging (graph #65): a byte budget, oldest
    # evicted first; scouting keeps its best `scout_depth` hits.
    results_memory_mb: int = 256
    scout_depth: int = 1000
```

and the flat mirror `board_fields: dict[str, str] = field(default_factory=dict)` next to `semantic_text_field`. Pass `board_fields=self.board_fields` in `corpus()`'s legacy branch. In `load_config`, the corpus section gets `board_fields=dict(section.get("board", {}))`. The server section gets `results_memory_mb=int(server.get("results_memory_mb", 256))` and `scout_depth=int(server.get("scout_depth", 1000))`. The flat form reads `raw.get("board", {})`, following the pattern the flat `[semantic]` section already uses.

- [ ] **Step 4: Run the config tests**

Run: `uv run pytest tests/test_server_config.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/prismql/server/config.py tests/test_server_config.py
git commit -m "Server config: a result memory budget, a scouting depth, and board fields per corpus"
```

---

### Task 4: `/evaluate` stores its result and answers with page 0

**Files:**
- Modify: `src/prismql/server/app.py` (`ServerState.__init__`, `reload`, `result_to_payload`, the `/evaluate` body, `_record_failure`, the evaluate `state.record` call)
- Test: `tests/test_server_app.py`

**Interfaces:**
- Consumes: `ResultStore`, `StoredResult.from_groups` (Task 1); `page_payload` (Task 2); `config.results_memory_mb` (Task 3).
- Produces: `state.results: ResultStore`. Evaluate responses gain `result_id`, `total`, `offset`, and per group `positions` and `times`. Journal entries gain `result_id`, `total`. Syntax failures record `line`, `column`. Also `_fold(result) -> tuple[str, list[list[Any]], list[str] | None] | None` (None for aggregate/grouped).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_server_app.py`)

```python
# --- results as objects (graph #65)


def test_evaluate_reports_total_and_a_result_id(client):
    body = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 2}
    ).json()
    assert body["count"] == 2 and body["total"] == 3 and body["truncated"] is True
    assert body["result_id"].startswith("r") and body["offset"] == 0
    g = body["results"][0]
    assert g["positions"] == [0] and len(g["times"]) == 1


def test_aggregates_are_not_stored(client):
    body = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a) AGGREGATE count()"}
    ).json()
    assert "result_id" not in body


def test_journal_links_the_result_and_records_syntax_positions(client):
    client.post("/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1})
    client.post("/evaluate", json={"query": "SELECT from("})
    ok, bad = client.get("/activity").json()["entries"]
    assert ok["result_id"] and ok["total"] == 3 and ok["count"] == 1
    assert bad["error"]["line"] == 1 and bad["error"]["column"] is not None
```

The existing tests `test_evaluate_truncation_and_clamp`, `test_evaluate_clamps_to_server_cap`, `test_evaluate_output_file_bypasses_cap` and `test_file_output_group_cap` must keep passing unchanged. Their `count` / `truncated` meanings are preserved.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_server_app.py -k "result_id or not_stored or syntax_positions" -v`
Expected: FAIL (`KeyError: 'total'` / `'result_id'`).

- [ ] **Step 3: Implement**

1. In `ServerState.__init__`: `self.results = ResultStore(config.results_memory_mb * 1024 * 1024)`. In `ServerState.reload`, inside the lock: `self.results.clear()`. Positions are only valid for the load they were computed on.
2. Replace `result_to_payload` with two helpers (same place in the file):

```python
def _fold(result: Any) -> tuple[str, list[list[Any]], list[str] | None] | None:
    """(kind, id groups, labels) of a group-shaped result; None for the
    aggregate shapes, which are small and answered inline."""
    if isinstance(result, (AggregateResult, GroupedResult)):
        return None
    if isinstance(result, NamedQueryResult):
        return "named", result.to_list(), list(result.pattern_names)
    return "groups", list(result), None


def _small_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, AggregateResult):
        return {"kind": "aggregate", **result.to_dict()}
    return {"kind": "grouped", **result.to_dict()}
```

3. In `/evaluate`, inside `with exec_lock:` after `result = engine.execute(...)` succeeds:

```python
            backend = engine.search_backend
            folded = _fold(result)
            rid: str | None = None
            if folded is None:
                payload = _small_payload(result)
            else:
                kind, groups, labels = folded
                stored = StoredResult.from_groups(
                    kind,
                    req.corpus or config.default_corpus,
                    [backend.positions(g) for g in groups],
                    labels,
                )
                rid = state.results.put(stored)
                page = partial(
                    page_payload,
                    stored,
                    backend,
                    id_field=corpus_cfg.id_field,
                    time_field=corpus_cfg.timestamp_field,
                    offset=0,
                    hydrate=hydrate,
                    fields=req.fields,
                )
                if file_mode:
                    full = page(limit=config.file_output_max_groups)
                else:
                    payload = page(limit=max_results)
                    payload["result_id"] = rid
```

`file_mode` keeps its current definition (`req.output == "file"` and not an aggregate shape). Compute it before this block. `_write_results_file(full, req, config)` stays outside the lock as now. After it, set `payload["result_id"] = rid` and `payload["total"] = stored.total`. The file's `truncated` is still `full["truncated"]`: the file holds fewer than `total` exactly when the file cap bit. Add `fields: list[str] | None = None` to `EvaluateRequest` (after `hydrate`), with the comment `# hydrate only these event fields (plus the id); None = all`.

4. The evaluate `state.record({...})` adds `"result_id": payload.get("result_id")` and `"total": payload.get("total")`.
5. `_record_failure` gains `extra: dict[str, Any] | None = None`, merged into `"error"`. The syntax branch passes `{"line": getattr(e, "line", None), "column": getattr(e, "column", None)}`.
6. Imports: `from functools import partial`, `from .pages import page_payload`, `from .results import ResultStore, StoredResult`.

- [ ] **Step 4: Run the whole server suite**

Run: `uv run pytest tests/test_server_app.py -v`
Expected: all pass, including the four existing truncation and file tests.

- [ ] **Step 5: Commit**

```bash
git add src/prismql/server/app.py tests/test_server_app.py
git commit -m "Evaluate keeps its result under an id and answers with the first page and the total"
```

---

### Task 5: `GET /results/{id}` and `GET /results/{id}.jsonl`

**Files:**
- Modify: `src/prismql/server/app.py` (two routes, declared **`.jsonl` first**)
- Test: `tests/test_server_app.py`

**Interfaces:**
- Consumes: `state.results`, `page_payload`, `state.engine_for(stored.corpus)`.
- Produces:
  - `GET /results/{rid}?offset=0&limit=20&hydrate=&fields=a,b` → the page payload plus `result_id`, `ok: true`. `limit` is capped at `config.max_results`. `fields` is comma-separated.
  - `GET /results/{rid}.jsonl?hydrate=&fields=` → `application/x-ndjson`, every stored item, one per line, streamed in windows of 1000.
  - An unknown or evicted id, or one computed on an earlier corpus load (`stored.load != state.generation`, set by Task 4's fix: an evaluate in flight across `/reload` must never be paged through the new order axis) → 404 `{"ok": false, "error": {"type": "gone", "message": "result r7 is not kept any more (evicted or the corpus was reloaded); run the query again"}}`.

- [ ] **Step 1: Write the failing tests**

```python
def test_results_pages_through_a_stored_result(client):
    rid = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1}
    ).json()["result_id"]
    p = client.get(f"/results/{rid}?offset=1&limit=5&hydrate=false").json()
    assert p["ok"] and p["offset"] == 1 and p["count"] == 2 and p["total"] == 3
    assert [g["ids"] for g in p["results"]] == [[2], [4]]
    assert "events" not in p["results"][0]
    p = client.get(f"/results/{rid}?limit=1&fields=text").json()
    assert p["results"][0]["events"] == [{"id": 1, "text": "price spike"}]


def test_results_stream_whole_as_jsonl(client):
    rid = client.post(
        "/evaluate", json={"query": "SELECT from(tick_a)", "max_results": 1}
    ).json()["result_id"]
    r = client.get(f"/results/{rid}.jsonl?hydrate=false")
    assert r.status_code == 200
    lines = [json.loads(x) for x in r.text.splitlines()]
    assert [x["ids"] for x in lines] == [[1], [2], [4]]


def test_unknown_or_reloaded_results_are_gone(tmp_path):
    c = _make_client(tmp_path, enable_reload=True)
    rid = c.post("/evaluate", json={"query": "SELECT from(tick_a)"}).json()["result_id"]
    assert c.get(f"/results/{rid}").status_code == 200
    c.post("/reload")
    r = c.get(f"/results/{rid}")
    assert r.status_code == 404 and r.json()["error"]["type"] == "gone"
    assert c.get("/results/r999.jsonl").status_code == 404
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_server_app.py -k "results_" -v`
Expected: FAIL with 404 from the unrouted path on the first two tests.

- [ ] **Step 3: Implement** (next to `/activity`)

```python
    def _gone(rid: str) -> JSONResponse:
        return _error(
            404,
            "gone",
            f"result {rid} is not kept any more (evicted or the corpus was "
            "reloaded); run the query again",
        )

    def _page_args(hydrate: bool | None, fields: str | None) -> dict[str, Any]:
        return {
            "hydrate": config.hydrate if hydrate is None else hydrate,
            "fields": [f for f in fields.split(",") if f] if fields else None,
        }

    @app.get("/results/{rid}.jsonl")
    def result_jsonl(
        rid: str, hydrate: bool | None = None, fields: str | None = None
    ) -> Any:
        stored = state.results.get(rid)
        if stored is None or stored.load != state.generation:
            return _gone(rid)
        engine, corpus_cfg, _lock = state.engine_for(stored.corpus)
        args = _page_args(hydrate, fields)

        def lines() -> Any:
            for offset in range(0, len(stored), 1000):
                page = page_payload(
                    stored, engine.search_backend, id_field=corpus_cfg.id_field,
                    time_field=corpus_cfg.timestamp_field, offset=offset,
                    limit=1000, **args,
                )
                for item in page.get("results") or page.get("hits") or []:
                    yield json.dumps(item, ensure_ascii=False, default=str) + "\n"

        return StreamingResponse(lines(), media_type="application/x-ndjson")

    @app.get("/results/{rid}")
    def result_page(
        rid: str,
        offset: int = 0,
        limit: int = 20,
        hydrate: bool | None = None,
        fields: str | None = None,
    ) -> Any:
        stored = state.results.get(rid)
        if stored is None or stored.load != state.generation:
            return _gone(rid)
        engine, corpus_cfg, _lock = state.engine_for(stored.corpus)
        payload = page_payload(
            stored, engine.search_backend, id_field=corpus_cfg.id_field,
            time_field=corpus_cfg.timestamp_field, offset=max(0, offset),
            limit=max(1, min(limit, config.max_results)),
            **_page_args(hydrate, fields),
        )
        return {"ok": True, "result_id": rid, **payload}
```

`_error` is defined after the scout routes. Move its definition above the first route that uses it, or declare these routes after it. Keep one definition.

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_server_app.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/prismql/server/app.py tests/test_server_app.py
git commit -m "Server: page any kept result by id, or stream it whole as JSONL"
```

---

### Task 6: Scouting ranks to a depth, reports the true total, keeps its hits

**Files:**
- Modify: `src/prismql/backends/tantivy.py` (`rank_counted`; `rank` delegates to it)
- Modify: `src/prismql/backends/semantic.py` (`rank_counted`; `rank` delegates to it)
- Modify: `src/prismql/server/app.py` (`/search`, `/similar`, `_scout_response`, `_record_scout`; delete `_hits_payload` and `_scout_limit`)
- Test: `tests/test_tantivy_backend.py`, `tests/test_semantic.py`, `tests/test_server_app.py`

**Interfaces:**
- Produces: `TantivyBackend.rank_counted(query: str, *, limit: int) -> tuple[list[tuple[MessageId, float]], int]` (hits, match count). `SemanticIndex.rank_counted(text: str, *, limit: int, threshold: float | None = None) -> tuple[list[tuple[MessageId, float]], int]` (hits, count of scores ≥ threshold, or all non-skipped rows when no threshold). Scout responses gain `total`, `kept`, `offset`, `result_id`, and per hit `position` and `time`. `truncated` = paging further returns more (`offset + count < kept`).

- [ ] **Step 1: Write the failing tests**

In `tests/test_tantivy_backend.py` (module-level test using the file's `backend` fixture; "package" stems to the same term in docs 3 and 5):

```python
def test_rank_counted_reports_every_match_beyond_the_limit(backend):
    hits, total = backend.rank_counted("package", limit=1)
    assert len(hits) == 1 and hits[0][0] in (3, 5) and total == 2
    assert backend.rank_counted("package", limit=0) == ([], 0)
```

In `tests/test_semantic.py`, in `class TestRankAndPaths` (FakeEmbedder axes oil/panic/weather: vs "oil", docs 1 and 4 score 1.0, doc 5 scores ≈0.707, docs 2 and 3 score 0):

```python
    def test_rank_counted_counts_everything_over_the_threshold(self):
        index = SemanticIndex(FakeEmbedder(), DOCS)
        hits, total = index.rank_counted("oil", limit=1, threshold=0.7)
        assert len(hits) == 1 and hits[0][0] in (1, 4) and total == 3
        _, everything = index.rank_counted("oil", limit=1)
        assert everything == 5  # no threshold: every indexed row counts
        assert index.rank("oil", limit=3) == index.rank_counted("oil", limit=3)[0]
```

And in `test_numpy_and_python_paths_agree`, add `index.rank_counted("oil panic", limit=2, threshold=0.5)[1]` to both the `fast` and `slow` tuples, and assert `fast[2] == slow[2]`.

In `tests/test_server_app.py`:

```python
def test_scouting_keeps_hits_and_pages_them(client):
    pytest.importorskip("tantivy")
    body = client.post(
        "/search", json={"query": "spike OR reversal", "limit": 1, "hydrate": False}
    ).json()
    assert body["count"] == 1 and body["total"] == 2 and body["kept"] == 2
    assert body["truncated"] is True and body["hits"][0]["position"] in (0, 1)
    more = client.get(f"/results/{body['result_id']}?offset=1&hydrate=false").json()
    assert more["count"] == 1 and more["hits"][0]["id"] in (1, 2)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_tantivy_backend.py tests/test_semantic.py tests/test_server_app.py -k "rank_counted or keeps_hits" -v`
Expected: FAIL (`AttributeError: ... has no attribute 'rank_counted'`, then `KeyError: 'total'`).

- [ ] **Step 3: Implement**

`tantivy.py`: move the body of `rank` into `rank_counted`, calling `self._searcher.search(parsed, limit, count=True)` and returning `(hits, result.count)`. When `limit <= 0` or the index is empty, return `([], 0)`. `rank` becomes `return self.rank_counted(query, limit=limit)[0]`.

`semantic.py`: move `rank`'s body into `rank_counted`. `total` is `int((arr >= threshold).sum())` on the numpy path and `sum(1 for s in scores if s >= threshold)` on the Python path. With `threshold=None` it is `len(scores)`. `rank` delegates.

`app.py`, both scout routes, replacing `_scout_limit` / `_hits_payload`:

```python
        hits, total = scout.rank_counted(req.query, limit=config.scout_depth)
        # (similar: index.rank_counted(req.text, limit=config.scout_depth,
        #  threshold=req.threshold))
        backend = engine.search_backend
        positions = backend.positions([i for i, _ in hits])
        stored = StoredResult.from_hits(
            req.corpus or config.default_corpus,
            list(zip(positions, (s for _, s in hits), strict=True)),
            total,
        )
        rid = state.results.put(stored)
        payload = _scout_response(stored, rid, backend, corpus_cfg, req, key, start)
```

`_scout_response(stored, rid, backend, corpus_cfg, req, key, start)` builds the page with `page_payload(..., offset=0, limit=min(req.limit, config.max_results), hydrate=..., fields=None)` for inline output. For `output == "file"` it builds `page_payload(..., limit=config.file_output_max_groups)` and passes `page["hits"]` to `_write_hits_file`, keeping `truncated = len(rows) < total`. It then sets `result_id`, `ok`, `elapsed_ms`. `_record_scout` adds `result_id` and `total`. `SearchRequest` and `SimilarRequest` keep `limit` as the page size; the old cap test (`test_scouting_limits_are_capped_by_the_server`) must still pass with the new meaning, and does (see Global Constraints).

- [ ] **Step 4: Run the scouting, backend and semantic tests**

Run: `uv run pytest tests/test_server_app.py tests/test_tantivy_backend.py tests/test_semantic.py -v`
Expected: all pass (numpy-dependent cases skip where numpy is absent).

- [ ] **Step 5: Commit**

```bash
git add src/prismql/backends/tantivy.py src/prismql/backends/semantic.py src/prismql/server/app.py tests/test_server_app.py tests/test_tantivy_backend.py tests/test_semantic.py
git commit -m "Scouting keeps its hits to a depth and reports how many matched in all"
```

---

### Task 7: `/corpora` names each corpus's board fields; the MCP shim pages

**Files:**
- Modify: `src/prismql/server/app.py` (`/corpora`)
- Modify: `src/prismql/server/mcp.py` (shared HTTP helper, `result_page` tool, tool description)
- Test: `tests/test_server_app.py`, `tests/test_server_mcp.py`

**Interfaces:**
- Produces: `/corpora` → `{"corpora": [...], "default": ..., "board": {name: {"kind": ..., "actor": ...}}}` (empty dict per corpus when unset); `mcp.page_via_http(result_id: str, offset: int = 0, limit: int = 20, base_url: str | None = None) -> dict`; MCP tool `result_page(result_id, offset=0, limit=20)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_corpora_names_board_fields(tmp_path):
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    from prismql.server.config import CorpusConfig

    cfg = ServerConfig(
        corpora={"v": CorpusConfig(data=str(data), board_fields={"actor": "user"})},
        default_corpus="v",
    )
    body = TestClient(create_app(cfg)).get("/corpora").json()
    assert body["board"] == {"v": {"actor": "user"}}
```

In `tests/test_server_mcp.py`, extend `test_round_trip_against_app` (it already runs the app behind a real port; read it first). After its evaluate call, take `result_id` from the payload and assert `page_via_http(rid, offset=1, limit=1, base_url=...)["count"] == 1`. Extend `test_server_object_registers_tool_and_resource` to expect the tool names `{"evaluate", "result_page"}`.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_server_app.py tests/test_server_mcp.py -k "board_fields or round_trip or registers" -v`
Expected: FAIL (`KeyError: 'board'`, `ImportError: page_via_http`).

- [ ] **Step 3: Implement**

`/corpora` adds `"board": {n: config.corpus(n).board_fields for n in config.corpus_names()}`.

`mcp.py`: extract the `urlopen` / error handling of `evaluate_via_http` into `_call(method: str, path: str, payload: dict | None, base_url: str | None) -> dict`. Keep its error shapes byte-identical. `evaluate_via_http` calls `_call("POST", "/evaluate", payload, base_url)`. Add:

```python
def page_via_http(
    result_id: str, offset: int = 0, limit: int = 20, base_url: str | None = None
) -> dict[str, Any]:
    """GET one page of a kept result; structured errors, never raises."""
    query = urllib.parse.urlencode({"offset": offset, "limit": limit})
    return _call("GET", f"/results/{result_id}?{query}", None, base_url)
```

Register the `result_page` tool in `build_server`, returning `json.dumps(page_via_http(...))`. In `_TOOL_DESCRIPTION`, replace the paragraph that begins "For large result sets pass output="file"" with:

```
Every result is kept on the server: the reply carries `total`, the first
`max_results` groups and a `result_id`. Page on with result_page(result_id,
offset, limit) instead of re-running the query. For a whole result on disk
pass output="file" (server-side [server] enable_file_output).
```

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_server_app.py tests/test_server_mcp.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/prismql/server/app.py src/prismql/server/mcp.py tests/test_server_app.py tests/test_server_mcp.py
git commit -m "Corpora name their board fields; the MCP shim pages kept results"
```

---

### Task 8: Docs, the gate, reality, review, the graph

**Files:**
- Modify: `docs/USER-GUIDE.md`, `docs/AGENT-USE.md`, `skills/prismql/SKILL.md`, `README.md`, `CHANGELOG.md`, `STATE.md`

- [ ] **Step 1: Docs.** Run `grep -n "max_results\|truncated\|output=\"file\"\|output: \"file\"\|hydrate" docs/USER-GUIDE.md docs/AGENT-USE.md skills/prismql/SKILL.md README.md`. At each hit, describe the new contract in the file's own voice:
  - every non-aggregate result is kept and has a `result_id`;
  - `max_results` is the page size;
  - `total` is what was found, `kept` what is stored (scouting), and `truncated` means paging further returns more;
  - `GET /results/{id}` pages (`offset`, `limit`, `hydrate`, `fields`) and `GET /results/{id}.jsonl` streams;
  - scouting reports `total` and `kept` (`scout_depth`);
  - `[server] results_memory_mb`, `scout_depth`, `[corpora.X.board]`;
  - kept results are lost on `/reload` and on restart.

  In `SKILL.md`, the scout-then-query flow tells the agent to page by `result_id` rather than re-run. `CHANGELOG.md` gets an "Unreleased → Changed" entry that names the semantic change of scouting's `truncated`. `STATE.md` gets the shipped line. Also check `demo/web/app.js` lines 282–353. It reads `results`, `count` and `truncated` with unchanged meanings. Add nothing there unless the live run in Step 3 shows a difference.

- [ ] **Step 2: Gate.** `make check > "$SCRATCH/gate.log" 2>&1; echo "exit=$?"; tail -30 "$SCRATCH/gate.log"` (`$SCRATCH` = the session scratchpad). Expected: `exit=0`.

- [ ] **Step 3: Reality (the *Reality* table's carriers).**
  - Demo: `uv run prismql-server --config demo/prismql.toml` in the background, then `uv run python demo/verify_examples.py`. Expected: `failures: 0`. Then one `curl -s localhost:8901/evaluate -d '{"query":"…"}' -H 'content-type: application/json'` with an example query, and a `GET /results/<rid>?offset=…` on its `result_id`.
  - Workspace server: restart the swarmchasing server on port 8931 against its `prismql.toml`. Run one `/evaluate` with a chain query and page it. Run one `/similar` and check that `total` is at least `kept`.
  - Falsifier: a page whose `ids` differ from the same slice of an un-paged `max_results=50` response to the same query means a silent-wrong result. Compare the two by script.

- [ ] **Step 4: Commit docs.**

```bash
git add docs/USER-GUIDE.md docs/AGENT-USE.md skills/prismql/SKILL.md README.md CHANGELOG.md STATE.md
git commit -m "Docs: results are kept and paged by id; truncated means more beyond this page"
```

- [ ] **Step 5: Stage self-review, then cold review.** Re-read `git diff origin/main...HEAD -- src tests` for the AGENTS.md list (bugs, fragile spots, files over 150 lines, missing tests). Then spawn the `reviewer` sub-agent in a worktree with: the branch diff against `origin/main`, the repo, focus contour #1 and steward #3, and graph nodes #65, #63, #64, #58, #21. Fix findings in place, or record a rejection with its reason.

- [ ] **Step 6: The graph.** Update #65's modes to what the commits made true (on `main` locally, the owner has not pushed yet: ontic stays `anagata` until `gp`). Weave the result store: a phenomenon for the kept result (ding, context #1) produced by the evaluate and scouting path, read by the board. Put open follow-ups on #65 as questions, for example persisting kept results across restarts, and pagination in the demo page. After the owner's `gp`, move modes to `vartamana`.

---

## Next plan (not this one)

Part B: port the Claude Design board (canvas `D4CtpixVTZ42RAfnKLDgS3`, nine artboards of one component) into `src/prismql/server/board/`. It consumes this plan's `result_id`, `total`, `positions`, `times`, `/results` paging and `/corpora` board fields. It is written after Part A lands, against the real payloads.
