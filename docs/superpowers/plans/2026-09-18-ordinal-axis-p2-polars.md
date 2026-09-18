# Ordinal Axis P2 — sequence primitives as a Polars plan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement every sequence/window primitive once, as Polars LazyFrame operations over the ordered Arrow corpus table, proven tuple-for-tuple against the current engine (the oracle) — without wiring them into the executor yet (that is P3).

**Architecture:** A new package `prismql/plan/` holds pure functions from `(corpus LazyFrame, predicate frames, parameters)` to a result frame `(group, slot, position, id)`. Each primitive is one function; each is tested against `PrismQLEngine` on seeded random corpora and on the Chicago tiers. Polars is an optional extra (`[plan]`); the engine keeps working without it.

**Tech Stack:** Python 3.9+, polars ≥ 1.44, pyarrow (`[arrow]` extra, P1a), pytest. No Rust.

**Spec:** `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` — "P2 — primitives as a relational plan"; evidence: `prismql-research/experiments/polars-spike/RESULTS.md`.

## Global Constraints

- Semantics replicated are the engine's CURRENT ones for everything EXCEPT co-occurrence, which is implemented UNORDERED (spec D2); the co-occurrence test therefore compares against the engine on inputs where slot order and position order coincide (lhs group ids all < rhs group ids) and separately asserts commutativity.
- Greedy nearest match, strict `>` on the axis, distinct messages, one match per left row, right rows reusable.
- No `join_where`. No Rust. Nothing in `executor.py` / `query_visitor.py` changes.
- `polars` and `pyarrow` are optional: `prismql/plan/__init__.py` imports lazily; tests `pytest.importorskip("polars")`.
- Gate per commit: `uv run ruff format . && uv run ruff check . --fix && uv run mypy src/prismql` (11 baseline) and `uv run pytest -m "not slow"`. Commits: imperative subject, explicit paths, trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; never push.

---

## File map

- Create `src/prismql/plan/__init__.py` — lazy import guard, `PlanUnavailableError`.
- Create `src/prismql/plan/corpus.py` — `corpus_frame(table_or_backend) -> pl.LazyFrame` with `position`, `id`, timestamp columns as int64 micros.
- Create `src/prismql/plan/primitives.py` — `nearest_link`, `extend_link`, `anti_link`, `cooccur`, `quantify`, `body_span_filter`, `variable_filter`.
- Test `tests/plan/conftest.py` — seeded random corpora + engine oracle helpers; `tests/plan/test_primitives_vs_engine.py`.
- Modify `pyproject.toml` — extra `plan = ["polars>=1.44", "pyarrow>=15"]`, add to `all`.

Result frame schema (every primitive returns it): columns `group: u32`, `slot: u32`, `position: i64`, `id: i64|str`, sorted by `(group, slot)`. Helper `to_groups(frame) -> list[list[MessageId]]` for oracle comparison.

---

### Task 1: package skeleton, corpus frame, oracle fixtures

**Files:**
- Create: `src/prismql/plan/__init__.py`, `src/prismql/plan/corpus.py`
- Create: `tests/plan/__init__.py`, `tests/plan/conftest.py`, `tests/plan/test_corpus.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `corpus_frame(source: pyarrow.Table | SearchBackend, *, timestamp_fields=("timestamp",)) -> pl.LazyFrame` with columns `position (i64)`, `id`, all document fields, and `<field>_us (i64, nullable)` per timestamp field (UTC micros, via `prismql.backends.order.epoch_micros` semantics); `to_groups(result: pl.DataFrame) -> list[list[MessageId]]`; conftest fixtures `random_corpus(seed, n, users, kinds) -> list[dict]`, `oracle(docs) -> PrismQLEngine`.

- [ ] **Step 1: extra**

`pyproject.toml`: `plan = ["polars>=1.44", "pyarrow>=15"]`; add `plan` to `all`. Run the full-extras `uv sync ... --extra arrow --extra plan`.

- [ ] **Step 2: failing tests**

```python
# tests/plan/conftest.py
import random

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine


def random_corpus(seed: int, n: int = 200, users=("a", "b", "c"), kinds=("X", "Y", "Z")):
    rng = random.Random(seed)
    t = 1_000_000
    docs = []
    for i in range(n):
        t += rng.choice([1, 5, 30, 120, 3600])  # seconds; irregular gaps
        docs.append({"id": i, "user": rng.choice(users), "kind": rng.choice(kinds),
                     "text": "x", "timestamp": t})
    return docs


@pytest.fixture
def oracle():
    return lambda docs: PrismQLEngine(MemoryBackend(documents=docs), timestamp_field="timestamp")
```

```python
# tests/plan/test_corpus.py
import pytest

pl = pytest.importorskip("polars")
pa = pytest.importorskip("pyarrow")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from tests.plan.conftest import random_corpus  # noqa: E402


def test_corpus_frame_has_position_and_micros():
    docs = random_corpus(1, n=5)
    lf = corpus_frame(pa.Table.from_pylist(docs))
    df = lf.collect()
    assert df["position"].to_list() == [0, 1, 2, 3, 4]
    assert df["timestamp_us"].to_list() == [d["timestamp"] * 1_000_000 for d in docs]


def test_to_groups_orders_by_group_then_slot():
    res = pl.DataFrame({"group": [1, 0, 0], "slot": [0, 1, 0], "position": [9, 5, 4], "id": [9, 5, 4]})
    assert to_groups(res) == [[4, 5], [9]]
```

Run: `uv run pytest tests/plan -q` → FAIL (`ModuleNotFoundError: prismql.plan`).

- [ ] **Step 3: implement**

```python
# src/prismql/plan/__init__.py
"""Sequence/window primitives as a Polars plan (spec 2026-09-18, P2).

Optional: requires the [plan] extra. Nothing here is wired into the
executor yet; the engine is the oracle these primitives are tested
against.
"""

from ..exceptions import PrismQLRuntimeError


class PlanUnavailableError(PrismQLRuntimeError):
    """polars/pyarrow are not installed: uv pip install 'prismql[plan]'."""


def _pl():  # noqa: ANN202 - lazy import guard
    try:
        import polars as pl

        return pl
    except ImportError as e:
        raise PlanUnavailableError(str(__doc__)) from e
```

```python
# src/prismql/plan/corpus.py
from __future__ import annotations

from typing import Any

from ..backends.order import epoch_micros
from ..types import MessageId
from . import _pl


def corpus_frame(source: Any, *, timestamp_fields: tuple[str, ...] = ("timestamp",)) -> Any:
    """Ordered corpus as a LazyFrame: position = row index, <f>_us per timestamp field."""
    pl = _pl()
    if hasattr(source, "documents"):  # a SearchBackend built from a document list
        rows = list(source.documents)
    elif hasattr(source, "to_pylist"):
        rows = source.to_pylist()
    else:
        rows = list(source)
    df = pl.DataFrame(rows).with_row_index("position").with_columns(pl.col("position").cast(pl.Int64))
    for f in timestamp_fields:
        if f in df.columns:
            df = df.with_columns(pl.Series(f"{f}_us", [epoch_micros(v) for v in df[f].to_list()], dtype=pl.Int64))
    return df.lazy()


def to_groups(result: Any) -> list[list[MessageId]]:
    df = result.sort(["group", "slot"])
    out: list[list[MessageId]] = []
    for g, sub in df.group_by("group", maintain_order=True):
        out.append(sub["id"].to_list())
    return out
```

Run: `uv run pytest tests/plan -q` → PASS. Gate, commit: `Add prismql.plan: corpus frame and oracle fixtures`.

---

### Task 2: `nearest_link` — FOLLOWED_BY / PRECEDED_BY, positional and temporal, with `$k`

**Files:**
- Create: `src/prismql/plan/primitives.py`
- Test: `tests/plan/test_primitives_vs_engine.py`

**Interfaces:**
- Produces: `nearest_link(corpus: LazyFrame, lhs: LazyFrame, rhs: LazyFrame, *, axis: str, window: int, forward: bool, key: str | None = None) -> LazyFrame` where `lhs`/`rhs` are frames with at least `position`, `id` and (if `key`) the key column; `axis` is `"position"` or `"<field>_us"`; `window` in axis units (positions, or micros). Returns the result-frame schema with `slot 0 = earlier element` (i.e. `[rhs, lhs]` for backward, matching the engine's chronological order).

- [ ] **Step 1: failing tests**

```python
# tests/plan/test_primitives_vs_engine.py
import pytest

pl = pytest.importorskip("polars")

from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import nearest_link  # noqa: E402
from tests.plan.conftest import random_corpus  # noqa: E402


def _pred(lf, **eq):
    out = lf
    for k, v in eq.items():
        out = out.filter(pl.col(k) == v)
    return out


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("window", [1, 3, 10])
def test_followed_by_positional_matches_engine(oracle, seed, window):
    docs = random_corpus(seed)
    lf = corpus_frame(docs)
    got = to_groups(nearest_link(lf, _pred(lf, user="a"), _pred(lf, user="b"),
                                 axis="position", window=window, forward=True).collect())
    want = oracle(docs).execute(f"SELECT from(a) FOLLOWED_BY from(b) INWINDOW {window}")
    assert got == want


@pytest.mark.parametrize("seed", range(5))
def test_preceded_by_positional_matches_engine(oracle, seed):
    docs = random_corpus(seed)
    lf = corpus_frame(docs)
    got = to_groups(nearest_link(lf, _pred(lf, user="a"), _pred(lf, user="b"),
                                 axis="position", window=3, forward=False).collect())
    assert got == oracle(docs).execute("SELECT from(a) PRECEDED_BY from(b) INWINDOW 3")


@pytest.mark.parametrize("seed", range(5))
def test_followed_by_temporal_with_key_matches_engine(oracle, seed):
    docs = random_corpus(seed)
    lf = corpus_frame(docs)
    got = to_groups(nearest_link(lf, _pred(lf, kind="X"), _pred(lf, kind="Y"),
                                 axis="timestamp_us", window=60 * 1_000_000, forward=True, key="user").collect())
    want = oracle(docs).execute(
        "SELECT field(kind, X) AND field(user, $u) FOLLOWED_BY field(kind, Y) AND field(user, $u) DURING 1 minute"
    )
    assert got == want
```

Run → FAIL (`ImportError: nearest_link`).

- [ ] **Step 2: implement**

```python
# src/prismql/plan/primitives.py
"""Sequence/window primitives as Polars operations (spec 2026-09-18, P2).

Each function is ONE mathematical statement over the ordered corpus; the
operator layer (P3) composes them. Semantics: greedy nearest match per
left row, strict '>' on the axis, distinct messages, right rows reusable.
"""

from __future__ import annotations

from typing import Any

from . import _pl

RESULT_COLS = ("group", "slot", "position", "id")


def _result(frame: Any, legs: list[tuple[str, str]]) -> Any:
    """Explode leg columns [(position_col, id_col), ...] into the result schema."""
    pl = _pl()
    frame = frame.with_row_index("group")
    parts = [
        frame.select(pl.col("group"), pl.lit(i, dtype=pl.UInt32).alias("slot"),
                     pl.col(pcol).alias("position"), pl.col(icol).alias("id"))
        for i, (pcol, icol) in enumerate(legs)
    ]
    return pl.concat(parts).sort(["group", "slot"])


def nearest_link(corpus: Any, lhs: Any, rhs: Any, *, axis: str, window: int,
                 forward: bool, key: str | None = None) -> Any:
    """Greedy nearest rhs strictly after (forward) / before (backward) each
    lhs, within `window` on `axis`; optional equality on `key`."""
    pl = _pl()
    unit = 1  # both axes are integers (positions, micros)
    l = lhs.select(pl.col("position").alias("l_pos"), pl.col("id").alias("l_id"),
                   pl.col(axis).alias("l_ax"), *( [pl.col(key).alias("l_key")] if key else [] ))
    r = rhs.select(pl.col("position").alias("r_pos"), pl.col("id").alias("r_id"),
                   pl.col(axis).alias("r_ax"), *( [pl.col(key).alias("r_key")] if key else [] ))
    shift = unit if forward else -unit
    l = l.with_columns((pl.col("l_ax") + shift).alias("k")).sort("k")
    r = r.with_columns(pl.col("r_ax").alias("k")).sort("k")
    kw = dict(on="k", strategy="forward" if forward else "backward", tolerance=window - unit)
    if key:
        kw.update(by_left="l_key", by_right="r_key")
    j = l.join_asof(r, **kw).drop_nulls("r_id")
    legs = [("l_pos", "l_id"), ("r_pos", "r_id")] if forward else [("r_pos", "r_id"), ("l_pos", "l_id")]
    return _result(j.sort("l_pos"), legs)
```

Run → PASS on all seeds. If a seed fails, the diff IS the finding: record it in the spec's audit before touching either side. Gate, commit: `Add nearest_link: FOLLOWED_BY/PRECEDED_BY as an asof join`.

---

### Task 3: `extend_link` (chains) and `body_span_filter`

**Interfaces:** `extend_link(corpus, seqs: LazyFrame, rhs, *, axis, window, forward, key=None) -> LazyFrame` where `seqs` is a result frame; anchors on the last (forward) / first (backward) slot; appends/prepends one slot. `body_span_filter(result, corpus, *, axis, span) -> LazyFrame` keeps groups whose `max(axis) − min(axis) ≤ span`.

- [ ] Tests: 3-leg chain `a ~> b ~> c` positional windows 2 and 5 vs engine; the Chicago-shaped `X/$u ~> Y/$u DURING 1m ~> Z/$u DURING 1m` + body `DURING 1m` vs engine on random corpora (5 seeds).
- [ ] Implement: pivot `seqs` to one row per group with the anchor's `(position, axis, key)`; reuse `nearest_link`'s asof on the anchor; re-explode with the new slot appended. `body_span_filter`: group_by(group).agg(max−min) join back and filter.
- [ ] Gate, commit: `Add extend_link and body_span_filter for chains`.

### Task 4: `anti_link` — NOT_FOLLOWED_BY / NOT_PRECEDED_BY

- [ ] Tests vs engine: `SELECT from(a) NOT_FOLLOWED_BY from(b) INWINDOW 3` and the backward form, 5 seeds.
- [ ] Implement: same asof as `nearest_link`, keep rows where the match is null; result has one slot.
- [ ] Gate, commit.

### Task 5: `cooccur` — unordered co-occurrence, positional and temporal

- [ ] Tests: (a) engine parity on inputs where slot order = position order (build lhs from ids < 100, rhs from ids ≥ 100 in a 200-doc corpus) for positional windows 2, 5 and temporal 1 minute; (b) commutativity `cooccur(A,B) == cooccur(B,A)` as sets of frozensets; (c) distinctness (no group contains the same position twice); (d) k = 3 groups against a brute-force Python oracle in the test file (all combinations, one per group, span ≤ window).
- [ ] Implement: positional window ≤ 64 → union of offset equi-joins on `position + d`, `d ∈ [1, window]`, both directions folded into unordered by keeping `min < max`; temporal or larger windows → bucketize `axis // window`, join on `(key, bucket)` and `(key, bucket ± 1)`, then exact `|a − b| ≤ window` filter, dedupe by frozenset; k > 2 by iterated joins with the running `min/max` span check.
- [ ] Gate, commit: `Add cooccur: unordered co-occurrence, positional and temporal`.

### Task 6: `quantify` and `variable_filter` (`!$k`)

- [ ] `quantify(frame, *, n_min, n_max)` = window function `count over group ≥ n_min` (and `≤ n_max`); test vs engine `from(a){2,} INWINDOW 5`.
- [ ] `variable_filter(joined, left_col, right_col, equal: bool)` — the `!$k` inequality is `equal=False`; test: `a/$u ~> !$u` yields only different-user pairs on random corpora, and equals `nearest_link` with `key` when `equal=True`. This is diary gap #1 landing as one filter.
- [ ] Gate, commit.

### Task 7: Chicago tiers as a gate

- [ ] `tests/plan/test_chicago_tiers.py` (marked `slow`, skipped when `prismql-research/benchmarks/chicago-crime/data/tier_100k.parquet` is absent): rebuild the spike's Q1–Q3 through the primitives and assert tuple equality vs the engine on 100k (and 1m under `PRISMQL_TIERS=1m`).
- [ ] Gate, commit: `Gate plan primitives on Chicago tiers`.

### Task 8: docs

- [ ] CHANGELOG (Unreleased): P2 primitives, `[plan]` extra, `!$k` primitive (not yet exposed in syntax — P3 exposes it). AGENTS.md: structure line for `src/prismql/plan/`, install command `--extra plan`.
- [ ] Commit.

## Not in this plan
P3 (wire the executor to the plan, delete both merge paths, expose `!$k` in both dialects with an IR-equality test, drop the xfail markers), P4 gates, tantivy axis, zero-copy Arrow ingest (P1b, now low priority — Polars builds from Arrow directly).
