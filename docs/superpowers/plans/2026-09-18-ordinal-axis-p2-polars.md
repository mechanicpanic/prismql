# Ordinal Axis P2 — sequence primitives as a Polars plan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement every sequence/window primitive once, as Polars LazyFrame operations over the ordered Arrow corpus table, proven tuple-for-tuple against the current engine (the oracle) — without wiring them into the executor yet (that is P3).

**Architecture:** A new package `prismql/plan/` holds pure functions from `(corpus LazyFrame, predicate frames, parameters)` to a result frame `(group, slot, position, id)`. Each primitive is one function; each is tested against `PrismQLEngine` on seeded random corpora and on the Chicago tiers. Polars is an optional extra (`[plan]`); the engine keeps working without it.

**Tech Stack:** Python 3.10+ for the plan extra (Polars requires it — see revision note 10), polars pinned to the verified release (1.44.x), pyarrow (`[arrow]` extra, P1a), pytest. No Rust.

**Spec:** `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` — "P2 — primitives as a relational plan"; evidence: `prismql-research/experiments/polars-spike/RESULTS.md`.

> **Revision 2 (2026-09-19), after the GPT-6 Astra review — NO-GO on the
> original Task 1; amendments below supersede the task bodies where they
> conflict.** Review findings, in the order they bind this plan:
>
> 1. **Eligibility before nearest.** `!$k` / `$k` and any leg constraint
>    must participate in *choosing* the nearest candidate, never as a filter
>    after asof (nearest-then-filter drops a later eligible match —
>    reproduced). `nearest_link` takes `eligible: pl.Expr | None` and
>    `exclude_positions` (members already in the group) and selects the
>    nearest candidate satisfying both. Equality keys may still use `by=`
>    (same result, faster); inequality and "not already in group" cannot.
> 2. **Tie-break is `(axis, position)`**, both directions; sort right
>    frames by `[k, position]` (backward: position descending) before asof.
>    `window == 0` is an explicit branch (no shifted-key trick: Polars
>    accepts `tolerance=-1`).
> 3. **Quantifiers are enumeration, not counting.** HEAD executes `{n,}` and
>    `{n,m}` as `{n}` (A8) — define first: `{n,m}` over a restriction =
>    all m′-subsets, n ≤ m′ ≤ m, of that restriction's matches within the
>    window, one group per subset; `{n,}` = m′ up to the window's capacity.
>    Test against an exhaustive Python oracle on tiny corpora, NOT HEAD.
> 4. **Group-preserving contracts.** Every primitive consumes and produces
>    the result-frame schema (whole groups), including subquery chains:
>    `[A] ~>(n) [B]` joins *complete groups*, and when several rhs groups
>    share the nearest boundary all of them expand (HEAD does this —
>    `query_visitor.py:1393`); negation retains the whole lhs group.
> 5. **Distinctness across axes** (A7, reproduced `[[0,0,1]]`): every leg
>    excludes the group's existing positions regardless of axis.
> 6. **Oracle matrix, not "HEAD except co-occurrence"**: HEAD parity only
>    where HEAD is valid; independent (exhaustive, tiny-corpus) oracles for
>    unordered co-occurrence, quantifier ranges, cross-axis distinctness,
>    timestamp ties, relabeled/gapped/string ids. Fixtures must include
>    non-monotone timestamps, ties, nulls and gapped ids — the original
>    `random_corpus` (dense ids, strictly increasing time) masks all of it.
> 7. **Task 1 was wrong on the data path**: `corpus_frame` must be
>    Arrow-native (`pl.from_arrow`), *preserve* an existing `position`
>    column (P1a's `load_table()` already adds it — the original code
>    raised `DuplicateError`), honour a backend's `id_field`, and take an
>    explicit adapter per source instead of duck-typing every backend.
> 8. **Null timestamps**: any group with a missing timestamp on a temporal
>    leg or body span is rejected (`temporal.py:319`), not span 0.
> 9. **k-way co-occurrence**: all-member distinctness (not adjacent),
>    canonicalization *after* variable constraints, equal timestamps allowed
>    for distinct messages; tests over bucket boundaries, overlapping
>    predicates, all restriction permutations, k ≥ 3, vs exhaustive oracle.
> 10. **Python floor.** Polars ≥ 1.44 requires Python ≥ 3.10; the declared
>     floor is 3.9. Decision for the owner (recorded in STATE.md): raise
>     the floor to 3.10 (3.9 is EOL; mypy 2 already targets 3.10) — until
>     then the extra carries `; python_version >= "3.10"`, and the
>     capability policy for installs without Polars is decided with P3.
> 11. **CI must install `[plan]`** and the plan suite must not be
>     skippable there; pin the verified Polars release in the lock/CI env.
> 12. **Benchmark envelope**: LazyFrame path incl. ingest, conversion,
>     result-frame assembly and peak RSS; one subprocess, 4 threads,
>     wall-clock watchdog, explicit memory/thermal stop; 100k → 1m, full
>     tier only on separate authorization.

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


def test_corpus_frame_keeps_load_table_position(tmp_path):
    import json

    from prismql.loaders import load_table

    docs = random_corpus(1, n=5)
    p = tmp_path / "c.jsonl"
    p.write_text("\n".join(json.dumps(d) for d in docs))
    lf = corpus_frame(load_table(p))  # position column already present
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


def corpus_frame(table: Any, *, id_field: str = "id",
                 timestamp_fields: tuple[str, ...] = ("timestamp",)) -> Any:
    """Ordered corpus as a LazyFrame from an Arrow table (P1a `load_table()`).

    Arrow-native (no Python rows). An existing `position` column is kept
    (load_table already adds it); otherwise it is the row index. `id_field`
    is aliased to `id` for the primitives. Each timestamp field gets
    `<f>_us` (UTC epoch micros, null when unparseable) — computed in Polars
    for numeric/temporal columns, via epoch_micros only for string columns.
    """
    pl = _pl()
    df = pl.from_arrow(table)
    if "position" not in df.columns:
        df = df.with_row_index("position")
    df = df.with_columns(pl.col("position").cast(pl.Int64))
    if id_field != "id":
        df = df.rename({id_field: "id"})
    for f in timestamp_fields:
        if f not in df.columns:
            continue
        col = df[f]
        if col.dtype.is_numeric():
            df = df.with_columns((pl.col(f).cast(pl.Float64) * 1_000_000).round().cast(pl.Int64).alias(f"{f}_us"))
        elif col.dtype == pl.Datetime:
            df = df.with_columns(pl.col(f).dt.replace_time_zone("UTC").dt.epoch("us").alias(f"{f}_us"))
        else:
            df = df.with_columns(pl.Series(f"{f}_us", [epoch_micros(v) for v in col.to_list()], dtype=pl.Int64))
    return df.lazy()


def corpus_frame_from_backend(backend: Any, **kw: Any) -> Any:
    """Adapter for the two in-memory backends only (explicit, not duck-typed)."""
    pa = __import__("pyarrow")
    if not hasattr(backend, "documents"):
        raise TypeError(f"{type(backend).__name__} has no document list; pass an Arrow table")
    return corpus_frame(pa.Table.from_pylist(list(backend.documents)), id_field=getattr(backend, "id_field", "id"), **kw)


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

> **Executed 2026-09-19 (commit follows this note).** Landed signature:
> `nearest_link(lhs, rhs, *, axis, window, forward, key=None, eligible=None)`
> — no `corpus` argument (the frames carry the axis); `eligible` is a
> Polars expression over the pair with lhs columns prefixed `l_` and rhs
> columns `r_`, evaluated *before* the nearest candidate is chosen
> (finding 1). Two paths: asof (no `eligible`) and bucketized candidates +
> argmin (with `eligible`); with `eligible=pl.lit(True)` they must agree —
> the candidate path is the asof path's internal oracle. `window == 0` is an
> explicit empty branch. New audit finding A9 (HEAD sorts every group by
> id) narrowed the HEAD oracle for temporal links to monotone-time corpora.

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

> **Executed 2026-09-21.** `extend_link(corpus, seqs, rhs, *, axis, window, forward, key=None, eligible=None)` anchors on the last/first slot, looks the anchor up in `corpus` by position, and excludes the group's members from candidacy (distinctness across axes — A7 fixed by construction; the pinned `[[0,0,1]]` case returns `[]`). `body_span_filter(result, corpus, *, axis, span)` rejects groups with a null axis value. Oracles: HEAD for 3-leg positional chains on dense ids and for the `X/$u ~> Y/$u ~> Z/$u DURING 1h` chain + body `DURING 70 minutes` on monotone tie-free time; brute-force chain oracle on hostile fixtures incl. overlapping legs. `tests/plan/test_chains.py`.

**Interfaces:** `extend_link(corpus, seqs: LazyFrame, rhs, *, axis, window, forward, key=None) -> LazyFrame` where `seqs` is a result frame; anchors on the last (forward) / first (backward) slot; appends/prepends one slot. `body_span_filter(result, corpus, *, axis, span) -> LazyFrame` keeps groups whose `max(axis) − min(axis) ≤ span`.

- [ ] Tests: 3-leg chain `a ~> b ~> c` positional windows 2 and 5 vs engine; the Chicago-shaped `X/$u ~> Y/$u DURING 1m ~> Z/$u DURING 1m` + body `DURING 1m` vs engine on random corpora (5 seeds).
- [ ] Implement: pivot `seqs` to one row per group with the anchor's `(position, axis, key)`; reuse `nearest_link`'s asof on the anchor; re-explode with the new slot appended. `body_span_filter`: group_by(group).agg(max−min) join back and filter.
- [ ] Gate, commit: `Add extend_link and body_span_filter for chains`.

### Task 4: `anti_link` — NOT_FOLLOWED_BY / NOT_PRECEDED_BY

> **Executed 2026-09-21.** `anti_link(lhs, rhs, *, axis, window, forward, key=None, eligible=None)` = lhs rows with no eligible candidate (anti-join on the nearest-link match); one slot; `window == 0` keeps every lhs row. **Divergence recorded:** an lhs row with a null axis value is dropped (finding 8), whereas HEAD keeps a timestamp-less message as "not followed" — pinned in `tests/plan/test_anti_link.py::test_null_timestamp_lhs_is_rejected_unlike_engine`; HEAD parity for temporal anti-links therefore runs on fixtures without nulls.

- [ ] Tests vs engine: `SELECT from(a) NOT_FOLLOWED_BY from(b) INWINDOW 3` and the backward form, 5 seeds.
- [ ] Implement: same asof as `nearest_link`, keep rows where the match is null; result has one slot.
- [ ] Gate, commit.

### Task 5: `cooccur` — unordered co-occurrence, positional and temporal

> **Executed 2026-09-21.** `cooccur(frames, *, axis, window, key=None)` — one uniform implementation for both axes and any k: bucketize by `window` (`max(window, 1)` so ties at window 0 stay joinable), join each next frame on the running group's bucket range `[(hi − w) // w, (lo + w) // w]` (+ `key`), filter `hi − w ≤ a ≤ lo + w` and all-member distinctness, then canonicalize by `(axis, position)`, dedupe as a set, order groups slot by slot. The offset-equi-join branch from the original text was not needed: the bucket join is the same primitive with a 3-bucket fan-out. Oracle = exhaustive combination search in `tests/plan/test_cooccur.py` (pairs and triples, both axes, `$k`, overlapping predicates, ties at window 0, self-pairs excluded, commutativity over all permutations); engine parity only on the ordered subset (a-message first) on dense ids — D2 stays a documented engine defect.

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
