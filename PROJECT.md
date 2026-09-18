# PrismQL — the project, explained

*Orientation for a reader (or agent) who knows nothing. This file explains
**what the pieces are and why they are shaped this way**; it does not track
progress. For current status see `STATE.md`; for the language see
`LANGUAGE_REFERENCE.md` / `PIPE_REFERENCE.md`; for agent conventions see
`AGENTS.md`. Last update: 2026-09-19.*

**Contents:** 1 What it is · 2 The language in one table · 3 Five layers ·
4 Python vs Rust · 5 Search backends · 6 The order axis (and the three
"positions") · 7 Layer 1: Arrow · 8 Polars as the executor · 9 Migration
timeline · 10 Server, MCP, agent surface · 11 Semantic join and multi-corpus ·
12 Agent traces and trees · 13 Numbers that matter · 14 Repos and reading

---

## 1. What it is

A declarative language for **retrieving temporal/sequential patterns** in
ordered event data — chat logs, agent traces, crime records, news. Predicates
select messages; operators compose them in time. Two surface syntaxes lower to
one IR; the same query written twice:

```
SELECT field(type, ROBBERY) AND field(cell, $c)
       FOLLOWED_BY field(type, BATTERY) AND field(cell, $c) DURING 30 minutes
```
```
field(type, ROBBERY) and field(cell, $c) ~>(30m) field(type, BATTERY) and field(cell, $c)
```

Lineage: Chat-Corpora-Annotator (C#, the original annotation workbench) → this
engine. The bet: the human states intent, an agent authors the query, the
human verifies at the evidence level. Experiments are cheap, so hypotheses are
swept, not hand-picked.

## 2. The language in one table

| Layer | Constructs | Result type |
|---|---|---|
| Predicates (leaves) | `from(x)` / `field(name, value)`, `contains(dict)`, `contains_tokens`, `contains_phrase("…")`, `mentions_user`, `is_question()`, `mentions_date/time/place/org`, `contains_link`, `has_feature(f)`, `similar_to("text", θ)` | `set[MessageId]` |
| Boolean | `AND`, `OR`, `NOT` | set |
| Ordered sequence | `A FOLLOWED_BY B`, `A PRECEDED_BY B`, `NOT_FOLLOWED_BY`, `NOT_PRECEDED_BY`; chains nest left; pipe: `~>`, `<~`, `!~>`, `!<~` | complete groups `[[a, b, …]]` |
| Windows | `INWINDOW n` (positional, distance on the order axis), `DURING n unit` (temporal); one trailing window distributes per link | — |
| Unordered co-occurrence | `A, B, C INWINDOW n` — restrictions in one window, **order-free by definition** | groups |
| Pattern variables | `$k` — same value across legs (`field(cell, $c) … field(cell, $c)`); `!$k` — *different* value (the top expressibility gap; lands with P2/P3) | — |
| Quantifiers | `{n}`, `{n,}`, `{n,m}` on a restriction (not inside chains) | groups |
| Subqueries | `(query) ; (query)` unordered; positional continuation `(q) FOLLOWED_BY (q) INWINDOW n` | groups |
| Clauses | `BEFORE / AFTER / BETWEEN` timestamps (absolute or `n unit AGO`), `GROUP BY`, aggregations, `ORDER BY`, `LIMIT/OFFSET` | — |

Semantics worth knowing: sequence matching is **greedy nearest** with strict
`>` on the axis; a message never pairs with itself; a group is a complete,
distinct sequence. Any construct that runs without error and returns wrong or
empty results is a release blocker (rule 5 in `AGENTS.md`).

## 3. Five layers — today and target

The word "backend" in this codebase means only **one** of these layers (the
search layer), which is the usual source of confusion.

```
                 TODAY (2026-09-19)                          TARGET (spec 2026-09-18, rev. 2)
 ┌──────────────────────────────────────┐        ┌──────────────────────────────────────┐
 │ 5  SURFACES                          │        │ 5  skill + scriptable API (table     │
 │    demo page · REPL · MCP shim       │        │    results) · workbench · thin MCP   │
 │    (evaluate, reference)             │        │                                      │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 4  SERVER  FastAPI: multi-corpus     │        │ 4  same                              │
 │    from prismql.toml, per-corpus     │        │                                      │
 │    exec locks, rate limit, gates     │        │                                      │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 3  LANGUAGE (engine)                 │        │ 3  parse → IR → ONE operator layer   │
 │    classic ⇄ pipe → one IR →         │        │    emitting a Polars LazyFrame plan  │
 │    executor; boolean algebra on id   │        │    (asof / offset equi-joins /       │
 │    sets, sequence merge, windows,    │        │    anti-asof); one owner of          │
 │    $k, quantifiers, aggregates       │        │    semantics; results as a table     │
 │    ┆ hot merges = Rust kernels,      │        │                                      │
 │    ┆ reachable ONLY via rust_memory  │        │                                      │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 2  SEARCH BACKEND                    │        │ 2a text search: tantivy (or any      │
 │    "give me the id set for a         │        │    predicate → position set)         │
 │    predicate": memory, rust_memory,  │        │ 2b order axis: position / timestamp  │
 │    tantivy, opensearch, postgres,    │        │    columns (fast fields / Arrow)     │
 │    duckdb                            │        │                                      │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 1  STORAGE / INGEST  — did not exist │        │ 1  ordered Arrow table               │
 │    one flat JSON, loaded and         │        │    (position = row index);           │
 │    re-indexed on every start;        │        │    ingest = "anything → Arrow"       │
 │    P1a added load_table() → Arrow    │        │    (DuckDB/Polars: join, order,      │
 │                                      │        │    bucketize)                        │
 └──────────────────────────────────────┘        └──────────────────────────────────────┘
```

Three things that mislead:

1. **Layer 2 is not a database**, even when it is called `postgres` or
   `duckdb`. Every backend there answers one question — "which ids match this
   leaf predicate" — plus "return documents by id". The Postgres backend is
   Postgres *in the role of an inverted index*, not a store with joins.
2. **Layer 3 is always Python, except in one case.** Sequence merge, windows
   and temporal kernels were accelerated in Rust, but those kernels are
   methods of `rust_memory`, so "fast prismql" = rust_memory. Every other
   backend gets the slow Python merge over `get_documents`.
3. **Layer 1 did not exist** — that is what "we have no DB we live with" meant.
   Table joins, incremental ingest, integer ids, bucketizing numbers, storing
   results and investigations are layer-1 work. DuckDB/Polars are proposed to
   *create* layer 1, not to replace layer 2; they live under it and emit one
   flat ordered stream.

Target data flow:

```
tables (parquet / DB) ─DuckDB or Polars: join, order, bucketize─▶ Arrow table (position = row)
   ─▶ predicates → position sets ─▶ Polars plan (asof, equi-joins, filters)
   ─▶ result table (group, slot, position, id) ─▶ Python view / parquet / workbench diff
```

## 4. Python vs Rust — today's split and why it is crooked

| Where | What runs there |
|---|---|
| **Python only** (control plane, and rightly so) | ANTLR-runtime parser + hand-written pipe parser, IR, lowering, validator, executor/visitor as orchestrator, server, MCP, aggregates/grouping, `BEFORE/AFTER/BETWEEN` (`TemporalProcessor`), pattern variables (`VariableValidator`, on every backend), quantifiers, subquery boundaries |
| **Rust, only on `rust_memory`, only for integer ids** | Search: inverted index, `search_text/tokens/phrase/by_field`, n-grams, timestamp cache. Kernels: `merge_followed_by/preceded_by`, `merge_histogram_pruned` (INWINDOW co-occurrence), `merge_temporal_link/extend_temporal_link` (DURING chains), `merge_within_time_window`, `filter_by_time_range/window`, `group_by_temporal_unit`, `get_timestamps` |
| **Python twins of every kernel** | `_apply_followed_by`, `_extend_sequences_*`, backtracking in `window.py`, bisect-based temporal builders — used when the backend is not rust, ids are strings, or a kernel raised (`except Exception: pass`, silently). **The second owner of semantics** — the source of every dual-path divergence |
| **Dispatch** | 14 sites in Python, each with its own condition (`RUST_*_AVAILABLE and all ints`, `hasattr(backend, …)`) and its own fallback behaviour |

The border is crooked in three ways:

1. **Rust receives ids, not positions**, and decides that an id is a
   coordinate. Hence "distance = id difference" lives in Rust while Python has
   its own "index in a list".
2. **Data crosses the border as Python objects**: a list of dicts at load, lists
   of boxed ints per merge, lists of lists back.
3. **Acceleration is per backend, not per operation**: tantivy, postgres and
   duckdb get the slow path entirely, although nothing in a merge depends on
   the search backend. Tantivy was adopted *for* native Rust and got it only in
   search — worst of both worlds.

Target split (rev. 2): **by role, not by operation**. Python owns meaning
(parser → IR → the single operator layer); the executor is a Polars plan over
Arrow buffers; Rust remains for tantivy (text) only. `rust_memory` and its
kernels retire after P3 — their bodies survive as the *definitions* the plan
reproduces, not as code.

## 5. Search backends

| Backend | Index | Persistent | Sequence path today | Text match | Notes |
|---|---|---|---|---|---|
| `memory` | Python dicts | no | Python | substring | the **reference**; deliberately `list[dict]`, never the fast path |
| `rust_memory` | Rust inverted index (PyO3) | no | **Rust kernels** (integer ids only) | substring | the only fast path; requires dict-per-document FFI at load |
| `tantivy` | Lucene-style, Rust | **yes** (`index_path`, opens without re-indexing) | Python fallback | **stemmed** (`work` finds `working`; `hi` does not find `this`) | tokenizers are per field: raw / simple / n-gram / language stemmer — substring mode is an n-gram field |
| `opensearch` / `elasticsearch` | remote FTS | remote | Python | analyzer-dependent | client-side search only |
| `postgres`, `duckdb` | FTS in the DB | in the DB | Python | FTS | **not** used as a store with joins; only as an id-set oracle |
| `spacy` | NLP backend (entities), not a search backend | — | — | — | feeds `mentions_*` |

Order contract (P1a, every backend): `positions / sorted_positions / ids_at /
timestamps_at / has_order_axis`; a backend without an axis raises
`PositionalUnsupportedError` instead of silently falling back.

## 6. The order axis — and the three "positions"

A DSL over an inverted index is the right choice for **half** the language:
every leaf is an id set, boolean algebra over sets is free, compositional, and
trivially understood by an LLM (no state, no evaluation order). But an inverted
index has **no notion of order**, and the other half of the language —
`FOLLOWED_BY`, `INWINDOW`, `DURING` — is entirely about order. Order was
smuggled in: position = the id's numeric value; time = a timestamp cache
beside the index. The Rust kernels sped the smuggling up without changing its
nature. The audit (2026-09-18) found "position" defined **three** incompatible
ways:

| Path | Distance = |
|---|---|
| Rust `merge_followed_by/preceded_by`, histogram merge, `window.py` for integer ids | arithmetic on id values |
| Python fallback for FB/PB and chain extension | index in the sorted list of **all** documents |
| `window.py` for string ids | index among the **matched** documents |

Consequences: on corpus `{1, 10}` the query `from(a) FOLLOWED_BY from(b)
INWINDOW 3` returns `[]` on Rust and `[[1, 10]]` on Python; string ids sort
lexicographically (`m10` "follows" `m1` before `m2`) — any UUID corpus gets
silently wrong sequences; the Python path capped the universe at 1 000 000
documents (88 % of pairs lost on the full Chicago tier — fixed); tie-breaks
differed (Rust `(ts, id)`, Python set order). Chicago and FCC happen to have
dense, time-monotone integer ids, so nothing ever surfaced.

The lineage that fixes it is old: Lucene **span queries**, CEP engines (SASE,
Esper), kdb `asof` — everywhere an explicit ordered axis separate from
identifiers. Hence the design (spec `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md`):

```
 2a  inverted index      predicate ─▶ set of ids                     (as today)
 2b  order axis          position = load order (dense, 0..n-1), ids are labels,
                         timestamps_at[position]; built once by the loader
 3   merges on 2b        id sets ─▶ positions ─▶ sorted-array operations
                         INWINDOW = distance on the position axis
                         DURING   = distance on the timestamp axis
```

**Stream order is the load order.** The loader owns ordering; no hidden sort;
duplicate ids are a load error. Until P3 lands the old semantics still run and
are pinned as `xfail(strict)` contract tests — do not "fix" them piecemeal.

## 7. Layer 1 is Arrow

**What Arrow is.** Not a database and not a library: a **specification of the
in-memory layout** of columnar data. A table = schema + columns; each column
is one contiguous typed buffer (strings: offsets + bytes, plus a null bitmap).
Plus the **C Data Interface**: two libraries in different languages hand each
other a pointer to those buffers *without copying or serialising*. Parquet is
the same columnar idea on disk with compression; Arrow IPC is the same format
as a file/stream. Everything we need speaks it: DuckDB in/out zero-copy,
Polars is built on it, pyarrow in Python, arrow-rs in Rust, pyo3-arrow between
them.

**How it lives between DuckDB and tantivy** — Arrow is the **bus, not the
store**:

```
Village tables (parquet)
   │  DuckDB / Polars: joins, bucketizing, ORDER BY ts
   ▼
Arrow table in memory              ← position = row number, id, timestamp, text, agent, …
   │  pyo3-arrow: same buffers, no copy
   ▼
tantivy indexing (Rust)            ← text → tokenizer → inverted index
   │                                  id, position, timestamp → fast fields (columns inside the index)
   ▼
tantivy index on disk              ← persistent; opens without re-indexing
```

and back, at query time:

```
predicate → tantivy → DocIds → fast field → position array (Arrow u32/u64 buffer)
        → Polars plan (asof, offset equi-joins, filters) over position/timestamp columns
        → result: Arrow table (group, slot, position, id)
        → Python view list[list] / parquet on disk / back into DuckDB for diffs and sweeps
```

Two real stores: **DuckDB/parquet** for data and joins, **tantivy** for the
index and axis. Arrow is what they hand each other, and what Python and Rust
exchange positions in. No `dict` and no `list[int]` on the border.

The contract, as decided: corpus = an ordered Arrow table with `position` =
row index (`prismql.loaders.load_table`, `[arrow]` extra); ingest =
"anything → Arrow" (DuckDB recommended, not required — it is layer-1 tooling,
not a dependency of the engine); results = a `(group, slot, position, id)`
table with `list[list[MessageId]]` kept as the Python-facing view. This *is*
the native ingest; there is no per-dataset adapter.

## 8. Polars as the executor

**Why a relational plan at all.** The Rust kernels bought less than it seemed:
on Chicago, Python 5.1 s vs Rust 3.8 s — 25 %; the real win was algorithmic
(partition by correlation key + bisect). `MemoryBackend` is slow not because
of Python but because of `list[dict]`, sets of boxed ints and document
materialisation — which Arrow fixes, not Rust. Meanwhile every operator has a
relational form that already exists, is parallel, and is debugged by someone
else:

| Operator | Relational form |
|---|---|
| `FOLLOWED_BY` (greedy nearest, strict `>`) | `join_asof(forward)` with the key shifted by +1, `tolerance = window − 1` |
| `PRECEDED_BY` | the same, backward |
| `$k` correlation | `by=` on the asof join (better than the partition hack) |
| `!$k` | a post-join filter `r.k != l.k` — one line; why it lands in P2 |
| chains | successive asof joins; window distributes per link |
| `NOT_FOLLOWED_BY` / `NOT_PRECEDED_BY` | anti-asof |
| `INWINDOW` co-occurrence (small windows) | offset equi-joins (`position + d`, `d ∈ 1..w`) — **not** a generic range join |
| `DURING` co-occurrence | bucketization on the timestamp column |
| quantifiers `{n,m}` | enumeration checked against an exhaustive oracle |
| `DURING` vs `INWINDOW` | the same operation on the `timestamp` or `position` column |

The spike (`prismql-research/experiments/polars-spike/RESULTS.md`) turned
the reasoning into tuples: 100k, 1m and the full 8.47M tier reproduce the
engine **tuple-for-tuple**, including the benchmark's 372; Polars is 5–80×
faster on merges and ~65× on build. It also found that a generic
`join_where` is the wrong primitive (did not finish in 120 s on 1m) and that
the full tier exposed a silent-wrong in the engine (the 1M cap).

**Polars vs DuckDB** — one job, two philosophies:

| | DuckDB | Polars |
|---|---|---|
| What it is | embedded analytical **DBMS**, SQL engine in C++ | **dataframe library** in Rust with a lazy planner |
| How you drive it | SQL strings (or relational API) | expression chains → `LazyFrame` — the plan is an object |
| Data | own columnar store; reads parquet/Arrow/Postgres/csv directly; persistent DB file | in memory (or streaming from disk); persist = "write parquet" |
| Joins | full SQL: `ASOF JOIN`, range joins, window functions, recursive CTEs | `join_asof`, equi-joins, window expressions; range join via `join_where` (newer, weaker) |
| Resources | takes all cores and much memory by default; capped via `SET memory_limit/threads` | multithreaded too; streaming engine keeps memory more predictable |
| As a compile target | generate SQL strings from the IR | build the plan as objects — closer to what the IR already is |

For the "DB we live with" role (joining Village's six tables, persistence,
increments) DuckDB is objectively stronger — that is its job. For the
"executor of sequence primitives" role both have `asof`; Polars gives a plan
instead of strings, Rust instead of C++, and stays inside a bounded memory
protocol (the owner's laptop is the benchmark machine). So: **Polars is the
executor; DuckDB is optional layer-1 tooling.**

## 9. Migration timeline — where each Python container disappears

| Today | Becomes | When |
|---|---|---|
| `list[dict]` documents at load | Arrow table with `position` (accepted since P1a, still converted via `to_pylist()`) | **P1a** format exists → **P2/P3** consumed directly |
| one `dict` per document across PyO3 (the most expensive part of loading) | `pl.from_arrow(table)`, no copies of numeric columns | **P2** (plan side); dict-FFI dies with `rust_memory` |
| `list[int]` positions across FFI, `set[int]` matches in operators | position columns; primitives `nearest_link`, `cooccur`, `anti_link`, `quantify` over frames | **P2** (primitives) → **P3** (operators move; both old paths deleted) |
| `list[list[MessageId]]` results, JSONL to file | `(group, slot, position, id)` table; `list[list]` only as an edge view; `output=file` → parquet | **P3** |
| `get_documents(ids)` → dicts at hydration | gather rows by position from the table | **P3** |
| `set[MessageId]` in predicate boolean algebra | bitmaps / sorted position arrays as predicate results | **after P4** — a follow-on for layer 2a, own plan |

Phases (spec §Migration): **P0** pins (xfail contracts) → **P1a** order
contract + `load_table` (done) → **P2** primitives as a Polars plan against
oracles → **P3** single operator layer, delete both merge paths, `!$k` in both
dialects → **P4** gates: Chicago full-tuple equality, positional benchmark,
relabeled corpora → **P5** tantivy order axis (fast fields), retire
`rust_memory`. `MemoryBackend` stays on `list[dict]` on purpose: it is the
reference, not a fast path.

## 10. Server, MCP, agent surface

The "language server" (design 2026-06-10, research repo
`docs/development/2026-06-10-prismql-server-design.md`) exists so that
**anything can call PrismQL over HTTP/JSON** — agent loops, `curl`, other
systems — with all state in a config file, and MCP as a thin adapter rather
than the core:

```
prismql.toml ──> prismql-server  (FastAPI + uvicorn, warm engines, one per corpus)
                   │  POST /evaluate {query, corpus}  → hydrated results (honest `truncated`)
                   │  GET  /reference                 → packaged LANGUAGE_REFERENCE.md
                   │  GET  /corpora · /health          → corpus + backend status
                   │  POST /reload                     → gated (`enable_reload`)
                   │  GET  /openapi.json               → free schema for non-MCP agents
                   ▲
        ┌──────────┼──────────────┐
      curl    custom agent    prismql-mcp (stdio shim: `evaluate` tool + reference resource)
```

Hardening (review 2026-07-12): identity from `X-Real-IP`, pruned rate-limit
state, gates for reload / file output / dictionary size, per-corpus execution
locks, `default_corpus` validated at boot. **Multi-corpus lives here, not in
the engine**: `[corpora.<name>]` tables in the config, `corpus` in
`/evaluate` and in the MCP tool. The engine is single-corpus by design — one
query, one ordered stream; Village's six tables are flattened into one stream
with a `kind` column at layer 1.

**Agent surface direction** (decided 2026-09-18): an MCP tool that returns
JSON is the wrong interface for an agent — the whole result lands in its
context. Target = a **skill + scriptable API with table results** (the
code-execution model: the agent writes a short script that queries, filters
and aggregates, and reads only what it needs). The MCP shim stays as a thin
adapter. Own track after P3, together with the workbench (four surfaces,
agent-authors-queries; scope in the research repo).

## 11. Semantic join and multi-corpus

- **v1 shipped** (2026-07-16): `similar_to("text", θ)` in both dialects,
  threshold **required** (no default — owner decision), no `top_k`. Semantics:
  threshold-to-set — cosine is computed and *discarded*; what remains is an id
  set, so composition with `AND`/`FOLLOWED_BY`/`DURING` is free. Out-of-range
  θ fails loudly at parse, validation and runtime.
- Engine is deliberately commodity: an `Embedder` protocol, a pure-Python
  `SemanticIndex` (brute-force cosine, no numpy in the core),
  `SentenceTransformerEmbedder` behind the `[semantic]` extra; memory backend
  only, others raise a teachable error. Server config: `[semantic]` /
  `[corpora.<name>.semantic]`.
- Demo corpora have no semantic index yet (diary Q17).
- **v2 — scores-first ranking algebra** (t-norms, HRJN-style joins, ranked
  negation as an open problem) is the *paper contribution* and is not
  started. It needs results that carry a score — with results as an Arrow
  table that is a column, not a data-model rewrite. The novelty claim rests on
  2026 preprints (VectraFlow verified: threshold join, code closed; HiMu not
  verified) — not to be claimed publicly until checked.

## 12. Agent traces and trees (the hackathon use)

Target data: swarms of agents (AI Village style — chat, events, sessions,
turns, memory, goals). What the language is strong at, and where it is not:

| Question class | Expressible? | How |
|---|---|---|
| Failure shapes: retry loops, `call NOT_FOLLOWED_BY result`, `error ~> fallback ~> escalate` | **now** | quantifiers, negative links, windows |
| Correlation within one run/agent under interleaving | **now** | `field(run, $r)` on every leg (the mandatory idiom for traces) |
| Precursors of failure (contrast-set mining: same sweep on successful vs failed runs) | now / partly | PrismQL as the verifier; "retry with the *same* args" needs `$a`, "with *different* args" needs `!$a` |
| Silent abandonment: work produced and never consumed | **now** | `call NOT_FOLLOWED_BY consumed DURING …` with `$r` |
| Hand-off ping-pong `A→B→A`, "switched to a *different* tool" | **only with `!$k`** | variable inequality (P2/P3) |
| Latency cascades, "calls longer than 5 s" | with a workaround | no numeric predicates — bucketize at ingest (`latency_bucket=slow`) or `has_feature` |
| Idioms vs anomalies (n-grams frequent overall vs beating the null twin only in failed runs) | now, with a sweep harness | null-twin methodology from the research repo |
| Behavioural: escape genesis (frustration → boundary probing), side channels, dialect birth, norms and sanctions, claim → challenge → retraction, leadership | now / needs `!$k` | sequences over chat + events, `similar_to` for drift |

**Trees.** A trace is a tree, but serialised in pre-order (by start time, as
OTel spans are) it becomes a sequence in which **a node's whole subtree lies
in the contiguous segment between its start and end**. So ingest emits two
events per span — `start` and `end` (a Dyck / bracket encoding) — plus `run,
span, parent, depth, agent`. Then:

- "an error happened inside sub-agent X" is a sandwich:
  `field(kind, start) AND field(span, $x) FOLLOWED_BY field(status, error)
  FOLLOWED_BY field(kind, end) AND field(span, $x) DURING 1 hour` — correct
  *because* matching is greedy: if the error came after X's end, no `end(X)`
  exists after it, so no match. Brackets + greediness = a nesting check.
- "error at depth ≥ 3" — `field(depth, …)`; "a sub-agent that never returned"
  — `start(X) NOT_FOLLOWED_BY end(X)`; sibling order is preserved;
  interleaving from other runs is cut by `$r`.
- What is lost, honestly: aggregates *over a subtree* (cost of a whole
  sub-agent), and "nearest child" vs "any descendant" are indistinguishable.
  Whatever breaks there becomes a native operator (`inside($x)`) — and a
  paragraph for the paper.

## 13. Numbers that matter

| | |
|---|---|
| Chicago benchmark (VLDB'23 Fig. 1 pattern, 8.47M events) | 372 matches; Python path 5.1 s, Rust kernels 3.4–3.8 s, Polars plan 0.043 s; build 27.7 s (dict-FFI) vs 0.15 s (`from_arrow`); naive SQL DNF |
| Test suite | ~860 collected (incl. slow), both execution paths byte-identical, IR equality across dialects; CI 3.12 / 3.13 |
| Known silent-correctness holes | pinned `xfail(strict)`: three "position" semantics, INWINDOW enforcing order, cross-axis message reuse, quantifier ranges executed as minimum — all fixed by construction in P3 |
| Mismatch diary (expressibility study) | 8/18 questions attempted; top gap: variable inequality `!$k` |
| Paper | EDBT'27 EA&B, due 2026-10-07; hackathon (swarmchasing) Oct 3–4 |

## 14. Repos and reading

- `~/Projects/vibes/prismql` — engine, server, demo (this repo).
  `../prismql-rust` — kernels (retiring). `../prismql-mcp` — stdio shim.
  `~/Projects/research/prismql-research` — benchmarks, paper, eval, mismatch
  diary, Polars spike, workbench scope, server design.
  `Chat-Corpora-Annotator` — the original C#; consult for original semantics.
- Specs and plans: `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md`
  (audit, design rev. 2, Arrow contract, migration),
  `docs/superpowers/plans/2026-09-18-ordinal-axis-p2-polars.md` (P2, rev. 2
  after the Astra review).
- Obsidian: `~/Vaults/prismql` (symlink vault over all docs + agent memory).
- Conventions for agents: `AGENTS.md`. State: `STATE.md`. Knowledge graph:
  Iskron realm `@aleph/prismql` (holon #1, kriya relay P1a → P2 → P3).
