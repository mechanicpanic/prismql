# Ordinal axis: making stream order a first-class index

*Spec + migration plan, 2026-09-18. Status: proposed, awaiting review.*

## Why

PrismQL is a DSL over an inverted index: every leaf predicate yields a
set of message ids, and boolean composition is set algebra. That half is
right. The other half — `FOLLOWED_BY`/`PRECEDED_BY`, `INWINDOW`,
`DURING` — is about **order**, and an inverted index has no notion of
order. Order was smuggled in through the id values themselves. The audit
below shows that this smuggling is now the engine's main correctness
liability, and that the two execution paths already disagree on it.

## Audit (2026-09-18, all findings reproduced on the live engine)

**A1. "Position" has three different definitions in the codebase.**

| Site | Definition of distance |
|---|---|
| Rust `merge_followed_by` / `merge_preceded_by` (`algorithms.rs:506,535`) — the path that runs for all-int ids | `rhs_id - lhs_id` (id arithmetic) |
| Rust `merge_histogram_pruned` (INWINDOW co-occurrence) and `window.py` int branch (`:98`) | `abs(id1 - id2)` (id arithmetic) |
| Python fallback for FB/PB and chain extension (`query_visitor.py:~1514,1567`) | index in `sorted(get_all_document_ids())` (ordinal over ALL docs) |
| `window.py` string-id branch (`:99-102, :233`) | index in the sorted list of *matched* ids only (ordinal over the match set — a third semantics) |

**A2. Dual-path divergence, reproduced.** Corpus with ids `{1, 10}` (adjacent
in the stream, 9 apart in id space), query
`SELECT from(a) FOLLOWED_BY from(b) INWINDOW 3`:
Rust kernels → `[]`; Python fallback → `[[1, 10]]`. The dual-path
equality guarantee holds only because every test corpus has dense ids.

**A3. String ids are ordered lexicographically.** `sorted(...)` on
`"m1","m2","m10"` yields `m1 < m10 < m2`, so `FOLLOWED_BY` picks `m10` as
the message "after" `m1` and INWINDOW pairs across the wrong neighbours
(reproduced). Any corpus with UUID/string ids gets silently wrong
sequence results on every backend that accepts strings.

**A4. Silent truncation above 1M documents.** The Python positional
fallback materializes `get_all_document_ids(limit=MAX_MESSAGES_NOT)` with
`MAX_MESSAGES_NOT = 1_000_000` per query; larger corpora (AI Village:
1.14M turns) lose positions past the cap. Only the string-id / non-Rust
path hits this, i.e. exactly the corpora that also hit A3.

**A5. Temporal tie-break differs by path** (known, documented): Rust sorts
`(timestamp, id)`, Python sorts by timestamp with stable set-iteration
order. Rust caches parsed UTC micros at ingest; Python parses per query.

**A6. Fixed today (7d18c43):** `id_field` was hard-coded to `"id"` on
the pattern-variable and temporal-fallback paths — empty results on any
corpus with another id field.

**The implicit contract today:** ids must be non-negative integers,
dense, and monotone in stream order. Nothing enforces or documents it;
Chicago and FCC satisfy it by construction.

## Design

Introduce **layer 2b, the ordinal axis**, next to the inverted index
(layer 2a). Built once at load, owned by the backend:

- `order`: the stream order of documents. **Decision: ordinal = load
  order.** No hidden sort — the loader (the future ingest layer) is
  responsible for delivering documents in stream order, and the backend
  validates (warning when the configured timestamp field is not
  monotone in load order). This keeps the axis deterministic, makes the
  two execution paths trivially consistent, and matches the documented
  meaning of INWINDOW ("distance in the source stream").
- `pos: id -> int` (dense, 0..n-1) and `id_at: int -> id`.
- `ts_at: int -> epoch micros | None`, the existing timestamp cache
  re-keyed by position.

Backend API (optional capability, default implementation in a small
`OrderIndex` helper so every backend gets it for free from its
document list):

```python
positions(ids: Iterable[MessageId]) -> list[int]      # sorted ascending
ids_at(positions: Iterable[int]) -> list[MessageId]
timestamps_at(positions) -> list[int | None]
```

`RustMemoryBackend` already holds `id_to_index` (id → load index) and a
timestamp cache indexed the same way: it IS the ordinal axis, exposed
under the wrong name. Only the surface changes.

Merges then operate on positions:

- Positional FB/PB/extend and INWINDOW: id sets → position arrays →
  the **existing** kernels (they are id-agnostic `usize` nearest-next /
  histogram algorithms) → map back to ids. `window.py`'s int/str
  branches collapse into one; the per-query `all_ids`/`id_to_pos`
  materialization and the 1M cap disappear.
- Temporal links: unchanged algorithm; tie-break becomes `(ts, pos)`
  on both paths (closes A5).
- Ids become labels: any hashable, on every backend, including Rust
  (the wrapper maps ids ↔ positions before the FFI boundary; Rust sees
  positions only).

Semantic change to call out: on corpora with gapped ids, INWINDOW
distance becomes stream distance (today: id distance on the Rust path).
That is the fix, not a regression, but it is a behaviour change and goes
in the CHANGELOG and both references.

## Migration (each phase leaves the suite green)

- **P0 (this commit):** `tests/test_ordinal_axis_contract.py` — the
  target semantics as `xfail(strict=True)` tests: gapped ids agree on
  both paths; string ids follow load order; no lexicographic ordering.
  They flip to passing as phases land, and fail loudly if a phase
  regresses them.
- **P1: `OrderIndex`** (`src/prismql/backends/order.py`): built from the
  document list in `MemoryBackend`; `RustMemoryBackend` exposes
  `id_to_index` + timestamp cache through the same three methods.
  Monotone-timestamp validation with a warning.
- **P2: positional merges on positions.** FB/PB/extend in the visitor
  (both paths share the helpers, so one change), `window.py` merge
  through positions, remove `MAX_MESSAGES_NOT`. Dual-path equality
  tests on gapped and string-id corpora. Chicago 372 must reproduce on
  both paths (benchmark gate).
- **P3: temporal tie-break `(ts, pos)`** on both paths; drop the
  "documented divergence" note.
- **P4: string ids on Rust.** Wrapper-side id ↔ position mapping;
  remove the "Rust kernels only for numeric ids" limitation.
- **P5: docs.** Both references, gotchas in AGENTS.md, CHANGELOG entry
  for the gapped-id semantic change; delete the implicit id contract.

Estimate: P1–P2 two to three days, P3–P4 one to two, P5 hours. Nothing
here touches the grammar or IR.

## Risks and open questions for review

1. **Load order vs timestamp-sorted axis.** Load order is explicit and
   cheap but pushes ordering responsibility to the loader. The
   alternative (sort by configured timestamp field at load, tie-break
   by load index) is friendlier for ad-hoc corpora but hides a sort and
   must decide where unparseable timestamps go. Which contract?
2. **FFI boundary.** Positions across the boundary (Rust never sees
   ids) vs. teaching Rust about string ids. The former keeps Rust
   untouched but adds two O(k) mappings per merge.
3. **Perf.** id ↔ position mapping per merge over result-sized sets;
   expected negligible vs merge cost, must be measured on Chicago.
4. **Did anything rely on id-distance semantics?** The Chicago
   benchmark's ids are dense, so 372 should hold; needs the re-run.
5. **Interaction with the planned ingest layer** (DuckDB → flat stream):
   the loader becomes the single place that defines stream order — is
   that the right home, or should the backend always re-sort by time?
