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
  constraints across positions.
- **Quantifiers**: regex-style `{n}`, `{n,}`, `{n,m}` on conditions.
- **Named pattern groups**: `AS` keyword for labeling matched positions.
- **Negative patterns**: `NOT` operator inside sequences.
- **Subqueries**: semicolon-separated unordered subqueries and positional
  subquery chains.

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
- spaCy NLP backend (optional `nlp` extra; deprecated in favor of the
  precomputed approach below).
- `PrecomputedIndexes` + `IndexBuilder` for storing NLP features (entities,
  questions, custom labels) computed during ingestion from any source.

### Performance

- Optional Rust acceleration via [prismql-rust](https://github.com/mechanicpanic/prismql-rust)
  using PyO3/maturin: 50–100× speedup for `INWINDOW` window-merge and 10–100×
  for `FOLLOWED_BY`/`PRECEDED_BY`. Automatic fallback to Python when the Rust
  module is absent or message IDs are strings.

### Tooling & Examples

- Interactive REPL (`prismql` entry point, optional `repl` extra).
- Pygments lexer for syntax highlighting (optional `highlighting` extra),
  registered as a Pygments plugin.
- Streamlit demo (optional `demo` extra) including an "Understanding
  INWINDOW" walkthrough of common pitfalls.
- Reference examples for every operator family under `examples/`.

### Tests

- 431 tests covering parsing, execution, all operator combinations,
  aggregations, temporal filters, pattern variables, quantifiers, named
  groups, negative patterns, lookahead/lookbehind, custom features, and Rust
  backend parity.

[0.1.0]: https://github.com/mechanicpanic/prismql/releases/tag/v0.1.0
