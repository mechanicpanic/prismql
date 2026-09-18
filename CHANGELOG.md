## Unreleased

- **Python floor raised to 3.12** (was 3.9): Polars — the P2 executor — requires ≥ 3.10 and 3.9 is EOL. `tomli` dropped (stdlib `tomllib`), `mcp` no longer gated by version marker. New `[plan]` extra (polars, pyarrow). CI matrix 3.12/3.13 and it now installs the arrow/plan/server/mcp extras so their suites are not skipped.
- Ordinal axis P1a: `OrderIndex`, backend order contract (`positions`, `sorted_positions`, `ids_at`, `timestamps_at`, `has_order_axis`), `PositionalUnsupportedError` for backends without an axis, duplicate ids rejected at load (memory and rust), `load_table()` + `[arrow]` extra (corpus as an ordered Arrow table with `position` = row index). No query semantics changed.
- Fixed: positional FOLLOWED_BY/PRECEDED_BY, chain extension and boolean NOT silently capped the document universe at 1,000,000 ids (88% of pairs lost on the 8.5M Chicago tier). Fixed: PRECEDED_BY picked the earliest predecessor on the Python path (nearest on Rust). Fixed: `id_field` other than `"id"` emptied pattern-variable and temporal results.

# Changelog

All notable changes to PrismQL will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-15

Initial public release.

### Query Language

- ANTLR4-based parser for the PrismQL DSL with comprehensive syntax error
  reporting.
- **Conditions**: fluent operators (`from(...)`, `contains(...)`,
  `is_question()`, `has_entity(...)`, `has_word(...)`) and legacy
  `haswordofdict(...)` syntax.
- **Boolean composition**: `AND`, `OR`, `NOT`.
- **Positional windows**: `INWINDOW N` (canonical), with `INWIN` accepted as a
  deprecated alias.
- **Temporal windows**: `DURING N <unit>` (seconds, minutes, hours, days,
  weeks) with timestamp-based filtering. Supports both top-level queries and
  individual sequential operators.
- **Sequential operators**: `FOLLOWED_BY`, `PRECEDED_BY`, `NOT_FOLLOWED_BY`,
  `NOT_PRECEDED_BY` — combinable with either `INWINDOW` or `DURING`.
- **Sequential chaining**: `A FOLLOWED_BY B FOLLOWED_BY C INWINDOW 10` — a
  single trailing window applies per link to every windowless link, or each
  link carries its own window; positional and temporal windows mix freely
  within one chain.
- **Operator precedence**: `NOT` > `AND` > `OR` > sequential operators, so
  compound conditions compose with `FOLLOWED_BY` without parentheses.
- **Pattern variables**: `$user`-style backreferences enforcing same-value
  constraints across positions, including across `FOLLOWED_BY`/`PRECEDED_BY`
  legs; ill-defined combinations (chain variables with comma restrictions,
  quantifiers, or on a negative lookaround's right-hand side) fail
  loudly instead of silently mismatching. Chains where every leg shares one
  variable on the same field are matched per field-value partition (the
  EQL `sequence by` evaluation shape): interleaved chains from different
  values are all found, and cross-partition candidates never shadow the
  in-partition match.
- **Quantifiers**: regex-style `{n}`, `{n,}`, `{n,m}` on conditions.
- **Named pattern groups**: `AS` keyword for labeling matched positions.
- **Negative patterns**: `NOT` operator inside sequences.
- The Macther-era `UNR` flag is not part of PrismQL: it was defined in the
  2022 paper as "remove the match-order constraint" but implemented as a
  Cartesian product, and the windowing default that motivated it no longer
  exists. Unordered co-occurrence is expressed with comma + `INWINDOW`.
- **Subqueries**: semicolon-separated unordered subqueries and positional
  subquery chains. Positional operators between subqueries act on whole
  groups (all of A before all of B, gap measured between group boundaries,
  greedy closest match), so multi-message stages stay intact; a single
  parenthesized subquery is the identity.
- **Typed IR + dual surface syntax.** Queries lower to a pure-data
  intermediate representation executed by one engine; the parse-tree visitor
  remains as a legacy path (`use_ir=False`). On top of the IR, a second
  **pipe dialect** ships alongside the SQL-flavored surface:
  `from(alice) + contains(solutions){2} |> within(10)`,
  `from($u) ~> from($u) |> during(1h)`,
  `[a] ~>(10) [b]` for subqueries,
  `... |> group(day(ts)) |> count() |> sort(ts, desc) |> top(5)`.
  `engine.execute` auto-detects the dialect (SELECT-prefixed = classic) or
  takes `dialect="classic"|"pipe"`. Both surfaces lower to identical IR
  trees (asserted node-for-node in tests), so semantics are shared by
  construction; the pipe dialect carries no legacy operators.

### Aggregations & Temporal Filters

- `COUNT`, `SUM(field)`, `AVG(field)`, `MIN(field)`, `MAX(field)`,
  `COUNT(DISTINCT field)`, `DISTINCT(field)`.
- `GROUP BY` over plain fields and temporal units
  (`HOUR(timestamp)`, `DAY(timestamp)`, `WEEK`, `MONTH`, `YEAR`).
- `ORDER BY field ASC|DESC`, `LIMIT N`, `OFFSET M`.
- Temporal filters: `BEFORE`, `AFTER`, `BETWEEN` with ISO 8601 / Unix /
  date-only timestamps and timezone normalization.

### Backends

- Pluggable `SearchBackend` and `NLPBackend` abstract base classes.
- In-memory backend for testing and small datasets.
- OpenSearch / Elasticsearch backend (optional `opensearch` / `elasticsearch`
  extras).
- DuckDB and PostgreSQL backends for SQL-shaped corpora.
- Tantivy backend (optional `tantivy` extra): a real inverted-index search
  engine. Unlike the substring-default in-memory backend, it does **stemmed
  token** matching (`contains("running")` also matches "run"/"runs"), native
  phrase search, and supports a **persistent on-disk index** (`index_path`)
  that later runs open without rebuilding. Numeric ids round-trip as ints so
  the Rust window/sequence merge fast paths still apply. Usable via the
  library, `BackendFactory` (`type: "tantivy"`), and `prismql.toml`
  (`[backend] type = "tantivy"`, optional `index_path`).
- spaCy NLP backend (optional `nlp` extra; deprecated in favor of the
  precomputed approach below).
- `PrecomputedIndexes` + `IndexBuilder` for storing NLP features (entities,
  questions, custom labels) computed during ingestion from any source.
- Unbacked vocabulary operators (`mentions_org()`, `is_question()`,
  `has_feature(...)`, ...) raise teachable errors naming the missing index
  and listing what is available — never a silent empty result. An
  explicitly computed empty questions index is authoritative (no fallback
  to backend heuristics).

### Performance

- Optional Rust acceleration via [prismql-rust](https://github.com/mechanicpanic/prismql-rust)
  using PyO3/maturin: 50–100× speedup for `INWINDOW` window-merge and 10–100×
  for `FOLLOWED_BY`/`PRECEDED_BY`. Automatic fallback to Python when the Rust
  module is absent or message IDs are strings.

### Tooling & Examples

- Generic `field(name, value[, partial])` condition: match events where any
  field equals (default) or contains a value — `from(x)` is now documented
  as the alias for `field(user, x)`. Enables cross-corpus legs over merged
  streams, e.g. `field(source, news) AND contains(sanctions) FOLLOWED_BY
  field(source, pulse) AND contains(panic) DURING 4 hours`.
- Engine-level `text_match` mode (`"substring"` default, `"token"`):
  controls whether `contains()` matches dictionary terms as substrings or
  whole tokens; exposed in server configs via `[engine] text_match`.
  `search_tokens()` is now pure token matching on both backends (the
  Python implementation previously mixed in substring matches; the Rust
  backend previously fell back to substring entirely).
- Per-term dictionary routing: multi-word dictionary entries always go
  through the order-sensitive n-gram phrase engine (token mode previously
  matched nothing for them, silently), and single-word matching mode can
  be set per dictionary (`[dictionaries.crisis] match = "token"` /
  `{"terms": [...], "match": "token"}` in the library API and request
  overlays), overriding the engine-wide default.
- HTTP server (`prismql[server]` extra): config-driven `prismql-server`
  with `/evaluate` (hydrated results, structured errors, request-scoped
  dictionary overlays), `/health`, `/reload`, and `/reference`.
- `GET /schema`: corpus self-description — field inventory with coverage
  and inferred types, example values for categorical fields, configured
  dictionaries, id/timestamp fields, text_match mode. PrismQL is
  schema-on-read; this is the live source of truth for query targets.
- File output mode: `/evaluate` with `"output": "file"` writes ALL result
  groups (bypassing the inline `max_results` cap) as JSONL under
  `[server] results_dir`, returning only `{count, path, preview}` — batch
  pattern mining without blowing up agent context or HTTP bodies.
- MCP shim (`prismql[mcp]` extra): `prismql-mcp` exposes a single
  `evaluate()` tool plus the language reference as a resource.
- Interactive REPL (`prismql` entry point, optional `repl` extra): accepts
  the same `prismql.toml` as the server, shows what corpus is loaded at
  startup, and exposes it via `\schema` (same introspection as
  `GET /schema`).
- Pygments lexer for syntax highlighting (optional `highlighting` extra),
  registered as a Pygments plugin.
- Streamlit demo (optional `demo` extra) including an "Understanding
  INWINDOW" walkthrough of common pitfalls.
- Reference examples for every operator family under `examples/`.

### Tests

- 583 tests covering parsing, execution, all operator combinations,
  aggregations, temporal filters, pattern variables, quantifiers, named
  groups, negative patterns, lookahead/lookbehind, custom features, and Rust
  backend parity.

[0.1.0]: https://github.com/mechanicpanic/prismql/releases/tag/v0.1.0
