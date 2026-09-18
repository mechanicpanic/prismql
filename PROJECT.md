# PrismQL — the project in one page

*Orientation for a reader (or agent) who knows nothing. For current status see `STATE.md`; for the language see `LANGUAGE_REFERENCE.md` / `PIPE_REFERENCE.md`. Last update: 2026-09-18.*

## What it is

A declarative language for **retrieving temporal/sequential patterns** in ordered event data — chat logs, agent traces, crime records, news. Predicates select messages (`from(alice)`, `contains(crisis)`, `field(type, THEFT)`, `similar_to("oil sanctions", 0.7)`); operators compose them in time: ordered sequences (`FOLLOWED_BY`, `PRECEDED_BY`, negative forms), unordered co-occurrence (`INWINDOW`), temporal windows (`DURING`), pattern variables (`$k` — same key across legs), quantifiers. Two surface syntaxes, one IR:

```
SELECT field(type, ROBBERY) AND field(cell, $c)
       FOLLOWED_BY field(type, BATTERY) AND field(cell, $c) DURING 30 minutes
```
```
field(type, ROBBERY) and field(cell, $c) ~>(30m) field(type, BATTERY) and field(cell, $c)
```

Lineage: Chat-Corpora-Annotator (C#, the original annotation workbench) → this engine. Bet: the human states intent, an agent authors the query, the human verifies at the evidence level.

## Architecture — today and target

```
                 TODAY (2026-09-18)                          TARGET (spec 2026-09-18, rev. 2)
 ┌──────────────────────────────────────┐        ┌──────────────────────────────────────┐
 │ 5  demo page · REPL · MCP shim       │        │ 5  skill + scriptable API (table     │
 │                                      │        │    results) · workbench · thin MCP   │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 4  FastAPI server (multi-corpus)     │        │ 4  same                              │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 3  parse → IR → executor             │        │ 3  parse → IR → ONE operator layer   │
 │    merges: Python fallback ∥ Rust    │        │    emitting a Polars plan             │
 │    kernels (two owners of semantics) │        │    (one owner; asof / equi-joins)     │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 2  search backends: memory,          │        │ 2a text search: tantivy              │
 │    rust_memory, tantivy, opensearch, │        │ 2b order axis: position/timestamp    │
 │    postgres, duckdb (id sets)        │        │    columns (fast fields / Arrow)     │
 ├──────────────────────────────────────┤        ├──────────────────────────────────────┤
 │ 1  — none — (list[dict] from JSON)   │        │ 1  ordered Arrow table; ingest =     │
 │                                      │        │    "anything → Arrow" (DuckDB…)      │
 └──────────────────────────────────────┘        └──────────────────────────────────────┘
```

Data flow, target:

```
tables (parquet / DB) ─DuckDB/Polars: join, order, bucket─▶ Arrow table (position = row)
   ─▶ predicates → position sets ─▶ Polars plan (asof, equi-joins, filters)
   ─▶ result table (group, slot, position, id) ─▶ Python view / parquet / workbench diff
```

Why the change: an inverted index has no notion of order; order was smuggled in through id values, which produced three definitions of "position", dual-path divergences and a silent 1M-id cap. Making order a column and merges a relational plan removes the bug class instead of relocating it. Evidence: the Polars spike reproduces the engine tuple-for-tuple on 8.47M events (372 = 372) at 5–80× the speed.

## Numbers that matter

| | |
|---|---|
| Chicago benchmark (VLDB'23 Fig. 1 pattern, 8.47M events) | 372 matches; engine 3.4 s (Rust kernels), Polars plan 0.043 s; naive SQL DNF |
| Test suite | 826 (+ slow), both execution paths byte-identical, IR equality across dialects |
| Known silent-correctness holes | 2 pinned as `xfail(strict)`, both fixed by construction in P3 |
| Mismatch diary (expressibility study) | 8/18 questions attempted; top gap: variable inequality `!$k` (lands in P2) |

## Repos and reading

- `~/Projects/vibes/prismql` — engine, server, demo (this repo). `../prismql-rust` — kernels (retiring). `~/Projects/research/prismql-research` — benchmarks, paper (EDBT'27 EA&B, 2026-10-07), eval, diary, spike, workbench scope.
- Obsidian: `~/Vaults/prismql` (symlink vault over all docs + agent memory).
- Conventions for agents: `AGENTS.md`. State: `STATE.md`.
