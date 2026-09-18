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

| Site                                                                                                          | Definition of distance                                                                          |
| ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Rust `merge_followed_by` / `merge_preceded_by` (`algorithms.rs:506,535`) — the path that runs for all-int ids | `rhs_id - lhs_id` (id arithmetic)                                                               |
| Rust `merge_histogram_pruned` (INWINDOW co-occurrence) and `window.py` int branch (`:98`)                     | `abs(id1 - id2)` (id arithmetic)                                                                |
| Python fallback for FB/PB and chain extension (`query_visitor.py:~1514,1567`)                                 | index in `sorted(get_all_document_ids())` (ordinal over ALL docs)                               |
| `window.py` string-id branch (`:99-102, :233`)                                                                | index in the sorted list of *matched* ids only (ordinal over the match set — a third semantics) |

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

## Design (revision 2 — one owner of merge semantics)

Revision 1 proposed an explicit ordinal axis and migrating *both*
execution paths onto it. Review and the owner's question ("isn't this a
crutch?") exposed the structural cause behind every divergence found in
the audit: **each merge has two implementations** — a Python fallback and
a Rust kernel — and semantics live in both. Three definitions of
"position", nearest-vs-earliest PRECEDED_BY, differing tie-breaks, and the
ordered-INWINDOW defect are all the same bug: two owners. Migrating both
paths would move the class, not remove it. Revision 2 removes it.

### Principles

1. **One ordinal axis.** `order` = load order, full stop. The loader (the
   future ingest layer) delivers documents in stream order; the backend
   validates against the configured timestamp field and *warns* when
   positional and temporal order disagree. No `order="id"` switch: ids
   are labels (`int | str`, unique — duplicates are a load error). A
   corpus where id gaps mean deleted messages encodes that in the loader
   (placeholder positions) or asks with DURING. `tests/test_basic.py:98`
   changes meaning and is rewritten.
2. **One owner of merge semantics: Python, over position arrays.** Every
   sequence/window operator — FOLLOWED_BY, PRECEDED_BY (and their NOT
   forms), chain extension, INWINDOW co-occurrence, DURING links, DURING
   co-occurrence, subquery boundaries, final group normalization — is
   implemented exactly once, in `prismql/processors/`, on sorted
   position arrays and a parallel timestamp array. There is no "Rust
   path" and no "Python fallback" for an operator.
3. **Rust accelerates primitives, not operators.** The Rust crate exposes
   only leaf primitives whose contract is one sentence and testable by
   property tests against the Python reference:
   - `nearest_after(sorted: &[u64], xs: &[u64]) -> Vec<Option<usize>>`
     (first element strictly greater), `nearest_before` (last strictly
     smaller) — the bisect that FOLLOWED_BY/PRECEDED_BY/temporal links
     are made of;
   - `window_product(groups: &[&[u64]], span: u64) -> Vec<Vec<u64>>` —
     unordered co-occurrence: combinations of one element per group, all
     within `span` of the minimum, distinct elements (the corrected
     INWINDOW/DURING co-occurrence, written once for both axes);
   - `positions(ids) / ids_at(positions) / timestamps_at(positions)` on
     the backend.
   Rust cannot disagree with Python about what FOLLOWED_BY means because
   it does not know FOLLOWED_BY exists.

   **What "retiring the operator-shaped kernels" means — and does not.**
   The heavy loops do not leave Rust. `merge_followed_by` *is* sort +
   `partition_point` per lhs + a distance check: that is
   `nearest_after_within`. `merge_histogram_pruned` *is* the pruned
   combinatorial product: that is `window_product`. `merge_temporal_link`
   is the same bisect over the timestamp cache. The bodies survive as
   primitives, together with the timestamp cache and the no-document-
   materialization projection that bought Chicago's 7.5 s → 3.8 s. What
   is removed is the **semantics** each kernel currently carries — which
   axis, how a window distributes, how ties break, id-as-position — and
   its duplicate in the Python fallback. The difference is not how much
   runs in Rust but who owns meaning: a primitive's contract is one
   mathematical sentence, tested against a Python reference; the
   operator is composed once in Python. A pure-Python install runs the
   same operator layer over the reference primitives (`bisect`) —
   slower, never semantically different.

   **Performance risk, stated honestly.** Costs that move to the Python
   side: pair assembly from returned index arrays (a `zip` over a
   million elements, ~0.1 s), FFI array conversion per chain link (tens
   of ms per million), and sorting positions if it were done in Python
   (~0.3 s per million — so `sorted_positions()` is served by the Rust
   backend, not Python). Expected: within ±20 % of today's 3.8 s on
   Chicago, plausibly faster (the current Python path re-sorts ids and
   materializes documents). This is a hypothesis; P4 measures it. The
   fallback that keeps the principle intact if index shipping proves
   expensive: a fatter primitive, `nearest_pairs(xs, sorted_ys, d)`,
   returning the pairs themselves — still one sentence of mathematics,
   still property-tested, just more work on the Rust side of the
   boundary.
4. **Positional and temporal are the same algorithm on different axes.**
   INWINDOW = `window_product` over positions; DURING co-occurrence =
   `window_product` over timestamps. FOLLOWED_BY INWINDOW n =
   `nearest_after` on positions with distance ≤ n; FOLLOWED_BY DURING t =
   `nearest_after` on timestamps with distance ≤ t (strict inequality on
   equal timestamps preserved). One implementation each, parameterized
   by axis. This is where the DST/tie-break class of bugs also dies:
   the tie-break is `(axis value, position)` by construction.

### Layer 1 — the corpus is an ordered Arrow table

There is no ingest layer today: `load_documents` reads json/jsonl/csv/
parquet and immediately turns everything into `list[dict]` (parquet is
read through pyarrow and the table is thrown away with `to_pylist()`);
every backend takes `list[dict]`, and `RustMemoryBackend` receives one
Python dict per document across PyO3 — the single most expensive step
of loading. Results are `list[list[MessageId]]` and JSONL on disk. The
many backends are many *search* backends (layer 2); the interchange
format between layers is one, and it is the wrong one.

**Decision: the contract between layers is Arrow, not JSON.**

- **A corpus is an ordered Arrow table** (in memory, or parquet on disk):
  one row per document, field columns, and `position` = row index.
  This *is* the ordinal axis as data — load order becomes explicit,
  portable and checkable instead of a property of whoever iterated a
  list. `id` is an ordinary column (`int64` or `utf8`, unique).
- **Ingest = "anything → Arrow".** Joining the six AI Village tables,
  bucketing numeric fields, incremental appends, timestamp-monotone
  validation — all happen in whatever produces the table: DuckDB (the
  zero-ops default and the recommended tool), Polars, Postgres, pandas.
  None of them is a dependency of the engine. The engine never joins.
- **Backends ingest Arrow.** `RustMemoryBackend` takes the table
  directly (arrow-rs, zero-copy for numeric columns; strings without
  per-document dict construction) and builds `id_to_index` and the
  timestamp caches from columns. `MemoryBackend` may keep `to_pylist()`
  internally — it is the reference, not the fast path. `load_documents`
  returns an Arrow table; the `list[dict]` constructors survive as a
  convenience wrapper for tests and tiny corpora.
- **Results are a table too**: `(group, slot, position, id)`. Result-set
  diffs (workbench), sweep curves and null twins (harness), `output=
  "file"` (parquet instead of JSONL), and any external tool become
  table operations rather than nested-list walks. `QueryResult` as
  `list[list[MessageId]]` remains the *Python-facing view*, produced
  from the table at the edge, so the public API does not break.
- **Hydration is a column gather**, not `get_documents(ids)` returning
  dicts: take rows at positions.

**The data plane, stated as a principle.** Python stays the control
plane (parser, IR, the single operator layer, server, MCP). The data
plane — documents, id sets, positions, results — is contiguous memory:
Arrow columns and position arrays, never `list[dict]`, `set[int]` or
`list[list]` on the hot path. The heavy work runs where the memory is
(Rust primitives over buffers); Python orchestrates over result-sized
arrays. This is the numpy/polars lesson, and it is what makes "Python is
slow" stop being true for this engine without rewriting it.

**Follow-on for layer 2a (not this spec, recorded so it is not lost):**
predicate postings as bitmaps over positions (roaring). Boolean AND/OR/
NOT become SIMD bitmap operations in Rust instead of Python `set`
algebra over boxed ints, and a predicate's result is already a sorted
position array — the exact input the primitives want. At that point no
Python container touches the hot path anywhere.

### Backend contract (layer 2b)

Built once at load, immutable afterwards:
- `positions(ids: Iterable[MessageId]) -> list[int]` — order-preserving
  (NOT sorted; sorting is the caller's business), unknown ids raise;
- `sorted_positions(ids) -> list[int]` — the set projection used by
  merges;
- `ids_at(positions) -> list[MessageId]`;
- `timestamps_at(positions, field) -> list[int | None]` (epoch micros,
  UTC; per configured field);
- `size() -> int`.
`RustMemoryBackend` already holds `id_to_index` and per-field timestamp
caches: it exposes them under this contract and its id ingress/egress
translate `int | str` labels at the wrapper. Remote backends
(OpenSearch, Postgres, DuckDB) implement the contract from a persisted
`position` column or **raise `PositionalUnsupported`** — positional and
temporal-sequence queries fail explicitly there; boolean/set queries
keep working. No silent reconstruction of order from ids anywhere.

### What this removes

- Both `_apply_followed_by/_preceded_by` builders and both chain
  extenders in `query_visitor.py`; `window.py`'s backtracking and its
  int/str branches; the `RUST_*_AVAILABLE` dispatch (14 sites); the
  `MAX_MESSAGES_NOT` positional universe (boolean NOT keeps a separate,
  explicitly documented cap);
- the documented "Rust tie-break differs" divergence, the "Rust only for
  numeric ids" limitation, and the dual-path test matrix for merges
  (replaced by property tests of three primitives + one reference).

### Performance

The expensive parts of Chicago (nearest-next over millions of sorted
positions/timestamps, the co-occurrence product with pruning) are
exactly the primitives, so they stay in Rust; the Python operator layer
does O(k) work over result-sized arrays. Must be measured, not assumed:
Chicago tuple-equality and time on both `nearest_*` implementations
(Rust vs `bisect`) is the gate.

## Migration (revision 2; each step leaves the suite green)

- **P0** (done + expanded): contract tests as xfail(strict) —
  gapped-id adjacency, load-order string ids, PRECEDED_BY nearest,
  INWINDOW commutativity — plus the review's additions: chains, negative
  operators, reversed-load ids, string ids separated by unmatched docs,
  subquery boundaries, duplicate-id rejection, 1M boundary.
- **P1 — the axis and the table.** `load_documents` returns an ordered Arrow table (`position` = row index); `RustMemoryBackend` ingests Arrow (arrow-rs), no per-document dicts across FFI; `OrderIndex` in Python for MemoryBackend;
  `RustMemoryBackend` exposes the same contract; `PositionalUnsupported`
  on remote backends; duplicate-id rejection at load. Nothing else
  changes yet.
- **P2 — primitives.** Python reference implementations of
  `nearest_after/before` (bisect) and `window_product`; Rust twins in
  `prismql-rust` with the same signatures; hypothesis-style property
  tests asserting Rust == reference on random sorted arrays. Old kernels
  untouched.
- **P3 — the single operator layer.** `processors/sequence.py`: every
  operator once, over positions/timestamps, using the primitives.
  INWINDOW/DURING co-occurrence become unordered here (D2 fixed once).
  Executors (both `use_ir` paths — they share the helpers) call only
  this layer. The old builders, `window.py` backtracking and dispatch
  flags are deleted in the same series; the operator-shaped Rust
  kernels are re-exported as the primitives (bodies kept, semantics
  stripped) and their old entry points removed.
  Subquery boundaries and final normalization operate on positions and
  map back to ids at the edge.
- **P4 — gates.** Classic/pipe IR equality (unchanged); `use_ir` on/off
  equality (unchanged); Rust-primitives vs reference-primitives on the
  full suite (env flag forcing the reference); Chicago full-tuple
  equality vs the committed 372 result plus a positional benchmark
  query; relabeled corpora (gapped numeric, non-lexical strings).
- **P5 — docs with each phase**: both references, gotchas, CHANGELOG
  (semantic changes: INWINDOW truly unordered; gapped-id distance is
  stream distance; string ids everywhere; PositionalUnsupported).

Estimate: P1 one day, P2 one day, P3 two to three days, P4 one day.
Grammar and IR untouched throughout.

## Review amendments (GPT-6 Astra via Codex, 2026-09-18)

The review confirmed A1–A5 with file:line evidence, refuted three
overstatements, and found two defects that are independent of the
ordinal axis. Amendments, in severity order:

**Refuted / qualified.**
- "Dual-path equality held only because test corpora are dense" — wrong
  on both counts: existing tests do use gapped ids
  (`tests/test_basic.py:98` asserts id-distance semantics: `[1,3]` and
  `[10,11]` pair, "2 apart") and string ids; and dense ids do NOT
  guarantee equality (see D1). The gapped-id test is itself a decision
  input: it encodes "an id gap is real distance" (e.g. deleted messages
  in a chat export keep their original positions).
- "Any string-id corpus is silently wrong" → wrong only when lexical
  order differs from stream order.
- "Only the non-Rust path hits the 1M cap" → chain extensions and
  subquery positional merges build the capped universe regardless of
  Rust availability.
- "Python parses timestamps per query" → only on the document-fetch
  fallback; `get_timestamps` projections are used when available.

**D1 — new defect (fixed same day).** `PRECEDED_BY` picked the NEAREST
predecessor on the Rust kernel but the EARLIEST-in-window on the Python
builders (pair and chain extension) — divergence on dense ids. Pinned in
`tests/test_positional_path_parity.py`; Python builders now scan nearest
first.

**D2 — new defect, decision pending.** `INWINDOW` is documented UNORDERED
(`A, B ≡ B, A`, LANGUAGE_REFERENCE §INWINDOW) but BOTH kernels enforce
restriction order: Rust `extend_partial` requires strictly ascending
positions across group slots (`algorithms.rs:371–381`), the Python
backtracker only searches forward from the last pick (`window.py`).
`SELECT from(b), from(a) INWINDOW 3` returns `[]` where the reverse
returns `[[1,2]]`. Pinned as `xfail(strict)` in the same test file.
Either the kernels change (anchor = minimum position of the combination,
every other slot within `[anchor, anchor+window]`, distinct messages) or
the documentation and the language story change. This is a release
blocker independent of everything else in this spec.

**Design corrections.**
- Mapping ids → positions does not by itself unify operator semantics
  (D1, D2): P2 must fix operator rules explicitly, not just coordinates.
- P2 must migrate EVERY consumer of order, not only the merge helpers:
  subquery boundary selection by label `max`/`min`
  (`query_visitor.py:1322–1329`), subquery concatenation sorts
  (`:1383,1395`), and both executors' final group normalization
  (`query_visitor.py:493,499`, `ir/executor.py:381,386`). Unordered
  predicate sets and ordered sequence tuples must be distinguished — a
  sorted `positions()` API must never be applied to tuples.
- `MAX_MESSAGES_NOT` also bounds boolean NOT in both executors; removing
  positional enumeration and changing complement semantics are separate
  changes.
- "Optional capability, free for every backend" is not implementable:
  OpenSearch receives a client, not an ordered list, and the base
  enumeration API returns a set. Remote backends need a persisted order
  source; positional queries must FAIL explicitly where absent.
- The bijection needs a duplicate-id policy (both MemoryBackend and Rust
  currently overwrite mappings silently), unknown-id and bounds rules,
  and an immutability statement. Keep `MessageId = int | str`, not "any
  hashable".
- Backend temporal methods take ids and resolve through `id_to_index`;
  passing positions there would resolve wrong documents silently. Keep
  backend temporal APIs id-based; feed positions only to the stateless
  positional kernels. Full Rust string-id support (P4) is a real project
  — constructor, search egress, `get_documents`, `get_timestamps` all
  translate — not a "surface" change.
- Multiple configured timestamp fields exist; `ts_at` must be per field.
- P3 must keep strict temporal inequality (no same-timestamp links);
  `(ts, pos)` only orders candidates.

**Benchmark gate corrections.** Chicago's query is DURING-only — it does
not exercise positional merges and its runner compares counts, not
tuples. Keep it as the temporal gate; add positional benchmark queries,
compare full tuples with leg order, and run relabeled copies (gapped
numeric, non-lexical strings) translating labels back.

**The open decision (owner):** *ordinal = load order* (ids are labels;
`test_basic.py:98` changes meaning) vs *ordinal = id* (gaps are real
distance, as today's Rust path and that test assume). A per-corpus
`order = "load" | "id"` setting with an explicit default is the honest
option; the reviewer and the author both lean to load order as default.

**Amended migration order.** P0 expanded (PB nearest, chains, negative
operators, reversed-load numeric ids, string ids separated by unmatched
docs, subquery boundaries, duplicate ids, 1M boundary) → P1 ordinal
contract (uniqueness, snapshot, global vs partition positions, missing
ids, unsupported-backend error; order-preserving lookup separate from
sorted projection) → P2 all positional consumers together, D2 resolved,
backend temporal APIs untouched → gate on three axes (classic/pipe IR,
use_ir on/off, native/forced-Python) → Chicago tuple equality +
positional scale tests → P3 temporal tie-break → P4 Rust string ids as
its own project → docs shipped with each phase, not at the end.
