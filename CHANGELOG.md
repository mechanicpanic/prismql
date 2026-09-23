## Unreleased

### Added (query line breaks)
- The board shows a query with a line per link, window, clause and pipe stage (top level only; an author's own line breaks are kept), and the editor's *Format* button does the same on demand (graph @aleph/prismql, #84). Copy still copies the query as sent.

### Fixed (memory)
- An ingested `emb` column loads as one float32 numpy matrix, normalized in place, not as Python lists of floats: loading peaked at ~13x the matrix, now ~3x (20k x 64 test: 69 MB → 15 MB) (graph @aleph/prismql, #95).

### Changed (the query frame reads by position)
- The per-query frame no longer fetches whole documents it does not need (graph @aleph/prismql, #14): positions and times come from the order axis, field values from the backend's new `values_at(positions, field)`; only a field a backend cannot read by position falls back to documents. `TantivyBackend` keeps its metadata fields by position in a `fields.parquet` sidecar (index layout 4 — an index of layout 3 or older is refused with rebuild instructions; a text index at `text_index_path` rebuilds itself). Chicago demo (50k), tantivy backend, identical groups: a two-leg chain 44 → 10 ms, a chain with a `$k` variable 42 → 23 ms (memory: 16 / 15 ms).

### Added (the corpus on the board)
- The board's rail lists every corpus with its event count and what it can answer; its card in the new *Corpus* tab shows each field's type, coverage and ten most frequent values with counts, the role fields and the dictionaries' words (graph @aleph/prismql, #86). `GET /schema` is computed once per load over every event (was: the first 1,000 on every call, behind the corpus lock) and gains `distinct`, `top`, `complete`, `capabilities`, `dictionary_terms`, `board` and `text_search`; the old keys keep their shape.
- The inspector's header names a request by its `#seq`, the result id in the tooltip (as the full view already did).

### Changed (text search runs on a full-text index)
- A `memory` corpus answers `contains()`, phrases and `/search` from one tantivy index per corpus (graph @aleph/prismql, #91): `[corpora.<name>] text_index = "tantivy" | "memory"` (default tantivy when the extra is installed; `text_match = "substring"` stays in Python), `text_index_path` keeps it on disk with a fingerprint of the loaded text and the tokenizing code and rebuilds it when either differs; a folder that is not a text index (including a tantivy backend's own index) is never overwritten. Same sets as before (two tokenizer differences, Greek final sigma and superscript digits, are pinned), verified on Village: a phrase query 10 s → 0.18 s, `contains(outreach)` in a chain 20 s → 0.07 s, `/search` on a memory corpus no longer builds a second index (75 s on first use → 1.5 ms). `/schema` reports `text_search`.
- `TantivyBackend` reads match sets from a position fast field instead of each hit's stored document (index layout 3; an index of layout 2 is refused with rebuild instructions): a common word 1.2 s → 81 ms on Village.

### Fixed (text)
- A dictionary term the tokenizer splits (`sign-in`, `hello!`) matched nothing on the memory backend; it now matches the phrase of its tokens, as on tantivy (Village `contains(signin)`: 9,561 → 10,350 events).
- `contains_phrase` and multi-word dictionary entries on memory without n-grams no longer re-tokenize the whole corpus per call.

### Added (GROUP BY ... AGGREGATE answers page)
- A `GROUP BY ... AGGREGATE` answer (`grouped_values`) is now additionally kept on the server as a pageable `"rows"` result (graph @aleph/prismql, node #90, extends #65): the inline `/evaluate` response is unchanged apart from a new `result_id`/`total`, and `GET /results/{id}` (and `.jsonl`) page the same key/value pairs, in the engine's order. Plain aggregates and a `GROUP BY` without `AGGREGATE` are unchanged — still small and inline, no id. The board's inspector and full view show these as a two-column, paged table instead of the "per group" placeholder; old journal entries without a `result_id` keep the placeholder.

### Fixed (the board, final fix wave)
- The full view's paging skipped groups whenever `[server] max_results` capped a page below 50: it advanced the offset by a fixed 50 instead of the page's own returned count. It now advances by what each page actually returned, so every kept group loads, correctly numbered, even under a low cap.
- "Capped" now means cut off, not "there are more pages": the journal's new `capped` field is true only when scouting kept fewer hits than it found, or file output holds fewer than what was kept — an inline `/evaluate` page is never capped by itself, since the board can still page through the rest of what the store kept. The board's status pill and result label read this field instead of a page's own `truncated` bit.
- "Run again" now replays a request by its own kind: `search`/`similar` post straight back to `POST /search`/`POST /similar`, never through `/evaluate`; "Open in editor" is offered only for `evaluate` requests. A request that carried its own request-scoped dictionaries can't be replayed (the board never held their terms) — "Run again" is disabled with a visible note; "Open in editor" stays offered, with the same note.
- `GET /corpora` now also reports each corpus's `id_field`; the board pairs a group's events back to its ids/positions by that field instead of assuming `"id"`.
- The timeline's group range now uses the earliest/latest of a group's non-null times (`INWINDOW` groups are unordered — the times list isn't guaranteed chronological) instead of the filtered array's first/last element; a named result's event cards show their own slot labels instead of a generic "event n"; the journal's "N of M requests" count is drawn from one consistent set (the range+search-filtered set, not the journal's whole lifetime count); a live journal arrival no longer rebuilds the open full view — it patches only the header's "k of n" nav, so scroll/filter/table selection survive it.
- Every empty state on the board (the journal's "Nothing asked yet"/"No requests match" and the inspector's "Nothing selected") now shares one component and one vertical rhythm — same icon slot, same top offset below the header row — instead of the inspector's pane padding pushing its title 16px below the journal's.

### Removed (breaking — backends)
- The OpenSearch/Elasticsearch, PostgreSQL and DuckDB backends and their extras. None carried an order axis (so no sequence operators since P3) and two had no tests. A database or a search cluster is not a backend: make a table, `prismql ingest table` it, the engine reads the Arrow stream (graph #53). The remaining backends — memory, tantivy, rust_memory — all carry the axis.

### Removed
- The legacy Streamlit demo app (`demo/app.py`, `demo/pages/`, `demo/generate_demo_data.py`, `demo/requirements.txt`) and the `demo` extra. The web demo (FastAPI + static frontend) stays; it's the one that gets deployed.

### Changed (breaking — text matching)
- `contains()` stems by default: single-word dictionary terms match whole words folded by a Snowball stemmer in the corpus's `text_language` (`english` unless set), on the memory and tantivy backends alike, so `fail` finds `failed` and `hi` no longer finds `this`. The old default, substring matching, is now an explicit choice (`text_match = "substring"` or `match = "substring"` on a dictionary), as is whole-token matching. A backend that cannot honour a mode refuses at load or at the first `contains()` instead of silently answering with another meaning (tantivy has no substring mode; the memory backend has all three). Phrases (multi-word terms) match plain adjacent tokens in order, unstemmed, on both backends. `snowballstemmer` is a core dependency.

### Changed (semantic index)
- `SemanticIndex` runs on numpy when installed (one matrix product per query; 381k rows in milliseconds) and gains `rank(text, limit)`; the pure-Python path remains. `similar_to()` works on the tantivy backend (`semantic_index=`), and the server builds the index for tantivy corpora from `emb` or from the documents.

### Changed (tantivy)
- A tantivy index built with `index_path` writes its order axis beside the index (`order.parquet`: ids in load order, configured `timestamp_fields` as UTC microseconds) and reads it back when opened, so an index opened from disk supports sequence operators. Both backends carry every configured timestamp field on the axis, not only `timestamp`. Tantivy tokenizes with the memory backend's token shapes (one shared regex). The index layout is versioned: an index built by an earlier prismql is refused on open with rebuild instructions instead of failing on the first token search.

### Changed (scouting's `truncated`, and its file output)
- `truncated` on `POST /search` and `POST /similar` no longer says whether the cap on `limit` bit; it now says whether paging the *kept* result further would return more (`offset + count < kept`). Scouting keeps only its best `[server] scout_depth` hits (default 1000) out of everything that matched — the response reports both: `total` (how many matched) and `kept` (how many were stored and are pageable), and `kept` can be less than `total`. `"output": "file"` for scouting now always writes up to `scout_depth` hits (capped by `file_output_max_groups`); the request's own `limit` no longer narrows the file, so a small `limit` with `output: "file"` gets more rows than before, not fewer (graph @aleph/prismql, node #65).

### Added (the board)
- `/board/`: a page served by the server itself (whatever `static_dir` says) with a live feed of every request — `/evaluate`, `/search`, `/similar`, successes and errors — as `{who, corpus, query, outcome, elapsed, label, file}` summaries, the query highlighted, and an editor to re-run or change any of them with a chosen `max_results` and hydration. Backed by `GET /activity?since=` and the event stream `GET /activity/stream`; a ring of `[server] activity_max` entries (500) in memory and `activity.jsonl` beside the results when file output is on. Clients name themselves with the `X-PrismQL-Client` header. The demo page now loads the same lexer (`/board/prismql-lexer.js`).

### Changed (the board, rebuilt from the design canvas)
- The board was rebuilt end to end (graph @aleph/prismql, node #76): rail filters (time/kind/source/corpus/status) with live counts, a day-grouped journal, a Request pane showing each request's real output — chains with "+Δt · K events between" gap lines from the positions and times between two matched events, scored hits with a bar for `/similar` and highlighted matched terms for `/search`, plain aggregate values, and errors with their line/column — an Editor tab that reruns or edits any request (identifying itself as `board`), and a full view (Timeline/Table/Raw JSON, paged 50 at a time). Keyboard: ↑/↓, Enter, Esc, ←/→, ⌘⏎; dark/light theme is remembered per browser. The board notices a stopped server and rebases its journal after a restart instead of mixing the two.

### Added
- `[corpora.<name>.board]` (`[board]` on a single-corpus file) names which fields the board reads as an event's `kind` and `actor`; `GET /corpora` echoes the mapping back per corpus. Left unset, the board still shows the request and its output, just without a kind/actor line on each event.

### Changed (kept groups, board journal fields)
- Kept groups from `/evaluate` now come back in stream order (by each group's first matched position), not the engine's own internal order (graph @aleph/prismql, node #73). The scouting journal (`/search`, `/similar`) now records the request's `threshold`; every `/activity` entry carries the server's `boot` id, so a client can tell a restarted process from the one it was already following.

### Fixed
- A plain `GROUP BY` (no `AGGREGATE`) journaled its `count` as the raw groups dict, not a number — the board (and anything else reading `/activity`) now sees the group count like every other kind of result.

### Added (scouting)
- `POST /search` (ranked full-text hits in tantivy query syntax over the corpus's text fields; an in-process tantivy index is built once per corpus on first use when the query backend is not tantivy) and `POST /similar` (ranked nearest events by cosine over the embedding index). Both take `corpus`, `limit`, `hydrate` and `output: "file"` like `/evaluate`; `limit` is capped by `max_results` (inline) or `file_output_max_groups` (file) and `truncated` says when the cap bit; hits are `{id, score[, event]}`. Ranking lives only here; the language stays set-in, set-out.

### Added (results kept as server objects)
- A non-aggregate answer from `POST /evaluate` (match groups, named groups) or from `POST /search` / `POST /similar` (ranked hits) is kept on the server under an opaque `result_id` ("r<N>-<8 lowercase hex>", e.g. `r12-3fa9c1d0` — treat it as an unparsed token, not "r" plus a counter: the counter alone repeats from 1 in every process, so the hex half is what keeps an id held from before a restart from matching a different result on the new one); an aggregate or `GROUP BY` answer stays small, inline, and carries no id. The response is the first page: `max_results` is the page size, `count` is how many items this page carries, `total` is how many were found, `truncated` means paging further returns more. `GET /results/{id}?offset=&limit=&hydrate=&fields=` pages a kept result (`limit` capped by `max_results`, rate-limited like `/evaluate`); `GET /results/{id}.jsonl?hydrate=&fields=` streams every kept item, one JSON object per line, also rate-limited, with an `X-PrismQL-Total` response header carrying the number of lines the stream will send; a new `fields` (a list on `POST /evaluate`, comma-separated on `GET /results`) projects hydrated events down to those fields plus the id. An unknown, evicted, or reload-stale id answers 404 with `error.type == "gone"` ("run the query again") instead of an empty page. Kept results live in memory only, under a `[server] results_memory_mb` byte budget (default 256; oldest evicted first) — they do not survive `/reload` or a restart. `[corpora.<name>.board]` (flat `[board]` on a single-corpus file) names the fields the board shows as an event's `kind` and `actor`; `GET /corpora` echoes it back. The MCP shim gains `result_page(result_id, offset, limit)`; the `/activity` journal now carries `result_id` and `total` per summary, and a syntax-error entry carries `line`/`column` (graph @aleph/prismql, node #65).

### Added (ingest toolkit)
- `prismql ingest table SRC DST --id --time [--sort] [--keep] [--embed COL --model M]` writes the ordered Parquet stream the engine loads without config (`position`, `id`, `time` as UTC microseconds, kept fields, optional `emb` vectors); `prismql ingest claude-code DIR DST` turns a Claude Code project's transcripts, and `prismql ingest codex DIR DST` the Codex CLI rollouts, into one event per content block with the same columns (`kind`, `tool`, `error`, `session`, `model`, `text`). Rows without text carry zero vectors (a null in a fixed-size Array column does not survive Parquet). `--time-unit` states the unit of a numeric time column (otherwise classified per value by magnitude). New extra `[ingest]` for `--embed`. The server reads `emb` from such a Parquet file into the semantic index instead of encoding the corpus at start; the embedding model is taken from the file's metadata (a differing `[semantic].model` is an error).

### Added (P3)
- `!$k` in both dialects: "unequal to the value an earlier leg bound to `$k`", chosen inside candidate selection; `UNBOUND_NEGATED_VARIABLE` when nothing bound it.

### Changed (P3 — one operator layer)
- Every sequence/window operator executes through `prismql.plan` on both execution paths: FOLLOWED_BY / PRECEDED_BY and their negations, chains, INWINDOW / DURING comma rows, quantifiers, subquery stages. The Python builders, the backtracking window merger, the post-hoc variable validator and the Rust operator kernels are deleted; `RustMemoryBackend` remains as a search-only backend. Semantics now match the language reference where the engine used to diverge (audit A1–A10, D2): stream distance on gapped and string ids, unordered co-occurrence, no message reuse across axes, ranges enumerated, slots in axis order, variables held inside candidate selection, one group per subquery stage with the union's span in the window. Backends without an order axis (OpenSearch) raise `PositionalUnsupportedError` on sequence operators.
- `polars` and `pyarrow` are core dependencies: the operator layer is a Polars plan over an Arrow table and every sequence/window query needs it. `[plan]` and `[arrow]` remain as empty aliases for one release.
- An open quantifier range `{n,}` is rejected (`OPEN_QUANTIFIER`, both dialects, validator and runtime) unless `quantifier_ceiling = m` is configured (engine argument; `[engine] quantifier_ceiling` in `prismql.toml`, reported by `GET /schema`), in which case it reads as `{n,m}` (a minimum above the ceiling is rejected). Enumeration itself still runs as the minimum until the operator layer lands (A8). The plan enumerates groups up to an explicit size and never truncates silently (graph #46).

### Fixed (installation from a fresh clone)
- `uv sync` no longer requires the sibling `../prismql-rust` checkout: the Rust kernels left the declared dependency groups (they are installed by hand by the owner, `uv pip install ../prismql-rust`, and kept with `uv sync --inexact`). Any fresh clone resolves now; the test suite skips the Rust parametrizations when the crate is absent.
- CI workflow was invalid YAML since June (`env` nested under `with`) and never ran a job; fixed, and it installs the way a clone does.
- README: honest install (not on PyPI yet) and a "try it on your own events" walkthrough with the two timestamp keys a `DURING` query needs.

### Added (P2 — sequence primitives as a Polars plan, `[plan]` extra)
- `prismql.plan`: `corpus_frame` (ordered Arrow table → LazyFrame with `position` and `<field>_us`), and the primitives `nearest_link`, `extend_link`, `body_span_filter`, `anti_link`, `cooccur`, `quantify`, plus `inequality(key)` (the `!$k` eligibility). One implementation per operator, both axes, string ids, eligibility inside candidate selection, distinctness across axes, unordered co-occurrence and quantifier enumeration by construction. Not wired into the executor yet (P3); proven tuple-for-tuple against the engine where it is a valid oracle and against exhaustive oracles elsewhere, and on the Chicago 100k/1m tiers (`tests/plan/test_chicago_tiers.py`, slow).

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
