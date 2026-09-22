# PrismQL — in one page

*Orientation for a reader (or agent) who knows nothing. Long version with
every diagram and table: `ARCHITECTURE.md`. Status: `STATE.md`. Language:
`LANGUAGE_REFERENCE.md` / `PIPE_REFERENCE.md`. Last update: 2026-09-19.*

## What

A declarative language for **retrieving temporal/sequential patterns** in
ordered event data — chat logs, agent traces, crime records. Predicates
select messages (`from(alice)`, `contains(crisis)`, `field(type, THEFT)`,
`similar_to("oil sanctions", 0.7)`); operators compose them in time:
ordered sequences (`FOLLOWED_BY`, `PRECEDED_BY`, negated forms), unordered
co-occurrence (`INWINDOW`), temporal windows (`DURING`), pattern variables
(`$k` same value across legs; `!$k` different — landing), quantifiers. Two
surface syntaxes, one IR:

```
SELECT field(type, ROBBERY) AND field(cell, $c)
       FOLLOWED_BY field(type, BATTERY) AND field(cell, $c) DURING 30 minutes
```
```
field(type, ROBBERY) and field(cell, $c) ~>(30m) field(type, BATTERY) and field(cell, $c)
```

Lineage: Matcher (PANDL 2022) → Chat-Corpora-Annotator (C#) → this engine.
The bet: the human states intent, an agent authors the query, the human
verifies at the evidence level; experiments are cheap, so hypotheses are
swept.

## How (five layers, bottom up)

| # | Layer | Today | Target (spec 2026-09-18 rev. 2) |
|---|---|---|---|
| 1 | Storage / ingest | one flat JSON, re-indexed on every start; `load_table()` → ordered Arrow table (P1a) | corpus = **Arrow table**, `position` = row index; ingest = "anything → Arrow" (DuckDB/Polars for joins) |
| 2 | Search backend ("give me the id set for a predicate") | memory, rust_memory, tantivy, opensearch, postgres, duckdb | 2a text search (tantivy) · 2b **order axis**: position / timestamp columns |
| 3 | Language | parse → IR → executor → **one operator layer emitting a Polars plan** (P3, 2026-09-22): asof / offset equi-joins / anti-asof, bindings inside selection; results as a `(group, slot, position, id)` table | same; next: frame cost on the full tier, positional benchmark |
| 4 | Server | FastAPI, multi-corpus from `prismql.toml`, locks, rate limit, gates | same |
| 5 | Surfaces | demo page, REPL, MCP shim (`evaluate`) | skill + scriptable API with table results; workbench; thin MCP |

Why the change: an inverted index has no notion of order; order was smuggled
in through id values, giving three definitions of "position", dual-path
divergences, a silent 1M-id cap and id-sorted groups. Making order a column
and merges a relational plan removes the bug class. Evidence: the Polars
plan reproduces the engine tuple-for-tuple on 8.47M events (372 = 372) at
5–80× the speed; the hand-written kernels (the PANDL merge algorithms in
Rust) retire after P3 and survive as semantics and benchmark baselines.

## Numbers that matter

| | |
|---|---|
| Chicago benchmark (VLDB'23 Fig. 1, 8.47M events) | 372 matches; Rust kernels 3.4 s, Polars plan 0.043 s; naive SQL DNF |
| Tests | ~980 (both execution paths byte-identical; IR equality across dialects); CI 3.12/3.13 |
| Known silent-correctness holes | pinned `xfail(strict)`, all fixed by construction in P3 |
| Deadlines | paper EDBT'27 EA&B 2026-10-07; swarmchasing hackathon Oct 3–4 (agent traces; needs `!$k`) |

## Where

`~/Projects/vibes/prismql` (engine, server, demo) · `../prismql-rust`
(kernels, retiring) · `~/Projects/research/prismql-research` (benchmarks,
paper, eval, diary, spike) · Obsidian `~/Vaults/prismql` · Iskron realm
`@aleph/prismql`.

## Reading order for the implementation (P3, 2026-09-22)

| # | Read | What it gives |
|---|---|---|
| 1 | `docs/MENTAL_MODEL.md` (+ `.ru.md`) | what the language promises, twelve shapes, self-test |
| 2 | `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` | why a plan, audit A1–A10, review amendments |
| 3 | `src/prismql/backends/order.py` | the order axis: `OrderIndex`, positions, epoch microseconds |
| 4 | `src/prismql/plan/frames.py` | the per-query frame: only the participating rows |
| 5 | `src/prismql/plan/primitives.py` | asof and bucket joins, `extend_link`, `cooccur`, `quantify`, group-level links |
| 6 | `src/prismql/plan/operators.py` | `Leg`, `_v_` bindings, key vs eligible |
| 7 | `src/prismql/plan/bridge.py` | executor state → operator layer → id groups |
| 8 | `src/prismql/ir/nodes.py` → `ir/lower.py` → `dialects/pipe.py` | two dialects, one IR |
| 9 | `src/prismql/ir/executor.py`, `src/prismql/visitors/query_visitor.py` | both paths: `execute_body`, `execute_restriction`, the four shared helpers |
| 10 | `tests/plan/`, `tests/test_p3_review_regressions.py`, `tests/test_ordinal_axis_contract.py` | what is proven and by which oracle |
| 11 | `docs/superpowers/plans/2026-09-21-ordinal-axis-p3-operator-layer.md` | how it went, task by task |
