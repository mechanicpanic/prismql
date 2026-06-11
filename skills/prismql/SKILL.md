---
name: prismql
description: Run PrismQL pattern-matching queries over sequential data (conversations, logs, events, transactions) — via a local prismql-server if one is running, else directly via Python. Use when the user wants to find sequential/co-occurrence/temporal patterns in ordered records ("X followed by Y", "A and B within N messages", repeated behavior by the same entity), or asks to "seed"/set up PrismQL for a specific dataset.
---

# PrismQL — executable pattern queries over sequential data

PrismQL is "regex for event sequences": a query language over ordered records.
Two ways to run queries: a local **prismql-server** (preferred when running —
warm engine, plain HTTP) or **inline Python** (no server needed).
**Read `LANGUAGE_REFERENCE.md` in this skill directory before writing your
first query**, then check the Pitfalls section below for the errors agents
most commonly make.

## Server mode (check this first)

```bash
curl -s localhost:8901/health    # anything but connection-refused → server is up
```

If up, query over HTTP — no Python, no data loading:

```bash
curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
  -d '{"query": "SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 5", "max_results": 20}'
```

Responses carry hydrated event groups (`results[].events`); query errors are
structured 422s whose `error.message` tells you how to fix the query.
Iterate on dictionaries in-band — add `"dictionaries": {"name": ["term", …]}`
to the request to define/override term lists for that query only; persist
stable ones into the server's `prismql.toml` when done.
For large result sets add `"output": "file"` (+ optional `"label"`): every
group is written server-side as JSONL and the response carries only
`{count, path, preview}` — read the file selectively, never inline it all.
`GET /reference` serves the full language doc; `POST /reload` re-reads the
data file. To start a server: `prismql-server --config prismql.toml` (config
holds backend, data path, dictionaries — see the repo README).

## Inline Python (no server)

Not yet on PyPI — install from the local repo (or a git URL):

```bash
uv add --editable ~/Projects/vibes/prismql     # adjust path to your checkout
# or: uv pip install ~/Projects/vibes/prismql/dist/prismql-0.1.0-py3-none-any.whl
```

If `import prismql` already works in the project (check first!), skip setup.
Optional extras: `prismql[nlp]` (spaCy), `prismql[server,mcp]` (the server
and MCP shim), `prismql[all]`.

## Execution recipe

Run queries inline via Bash. This snippet is verified working (2026-06-10):

```bash
uv run python - <<'EOF'
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

docs = [  # any ordered records; load yours from JSON/CSV/parquet here
    {"id": 1, "text": "can you help me with an error?", "user": "alice", "timestamp": 1000},
    {"id": 2, "text": "try clearing the cache, that fixes it", "user": "bob", "timestamp": 1001},
]

engine = PrismQLEngine(
    search_backend=MemoryBackend(docs, id_field="id"),
    user_dictionaries={
        "problems":  ["error", "broken", "bug", "issue"],
        "solutions": ["fix", "fixes", "solve", "works"],
    },
)

for group in engine.execute("SELECT contains(problems) FOLLOWED_BY contains(solutions) INWINDOW 5"):
    print(group)   # e.g. [1, 2]  — list of matching record ids, in pattern order
EOF
```

### Backend selection (by dataset size)

| Backend | Import | When |
|---|---|---|
| `MemoryBackend(docs, id_field="id")` | `prismql.backends.memory` | < ~10K records, quick analysis |
| `RustMemoryBackend(docs, id_field="id")` | `prismql.backends.rust_memory` | 10K–1M records (10–100x faster; needs `prismql_rust`) |
| `DuckDBBackend(database, table_name, field_mappings)` | `prismql.backends.duckdb` | Parquet/CSV/larger-than-RAM analytics |
| `PostgresBackend` | `prismql.backends.postgres` | Data already in Postgres |

Document format: dicts with `id` (required), `text` (required for text ops),
`user` (for `from()`), `timestamp` (for `DURING`). Other fields allowed.
Records are matched by **positional distance = abs(id1 − id2)** for `INWINDOW`,
so ids should be sequential integers in stream order.

## Result shapes (verified)

- `engine.execute(q)` → `list[list[id]]` — each inner list is one match group.
  Sequential queries return ordered tuples: `[[problem_id, solution_id], ...]`.
- `AGGREGATE count()` → `AggregateResult`; call `.to_dict()` →
  `{'function': 'count', 'field': None, 'value': N}`.
- `AS "name"` groups → `NamedQueryResult`; `.get_named_group(i)` → `{name: id}`.
- Full records for a group: `backend.get_documents(group)`.

## Pitfalls (verified against implementation)

1. **A chain's final link must carry a window.** One trailing window covers
   every windowless link (per link, not whole-chain span); links may also mix
   `INWINDOW` and `DURING` individually.
   - ✅ `SELECT a FOLLOWED_BY b FOLLOWED_BY c INWINDOW 2`
   - ✅ `SELECT a FOLLOWED_BY b INWINDOW 2 FOLLOWED_BY c DURING 1 minute`
   - ❌ `SELECT a FOLLOWED_BY b INWINDOW 2 FOLLOWED_BY c` (no window on final link)
2. **Precedence: `NOT` > `AND` > `OR` > sequential operators.** Compound
   conditions next to `FOLLOWED_BY` need no parentheses:
   `SELECT from(alice) AND is_question() FOLLOWED_BY from(bob) INWINDOW 5`
   means `(alice ∧ question) FOLLOWED_BY bob`. Use parens only to override.
3. **Avoid the subquery form for simple sequences.** `a FOLLOWED_BY (SELECT b)`
   goes through a different code path and can return wrong results *silently*.
   Plain `a FOLLOWED_BY b INWINDOW n` is correct and simpler.
4. **`contains(x)` takes a dictionary NAME**, never a literal word. For a
   literal use `contains_phrase("exact phrase")`, or define a dictionary.
5. **`INWINDOW` is unordered; `FOLLOWED_BY` is ordered.** "A then B" →
   `FOLLOWED_BY`; "A and B near each other" → comma + `INWINDOW`.
6. **Don't flatten multi-stage patterns.** `(SELECT a, b INWINDOW 3) ;
   (SELECT c) INWINDOW 8` keeps a+b grouped; `SELECT a, b, c INWINDOW 8`
   does not mean the same thing.
7. **Same-entity repetition** uses pattern variables:
   `from($u) AND is_question(), from($u) INWINDOW 5` — not two literals.

## Validate before executing

Always validate generated queries; feed errors back and retry (≤3 attempts):

```python
from prismql import QueryValidator
v = QueryValidator(user_dictionaries=dicts)   # same dicts as the engine
r = v.validate(query)
if not r.valid:
    feedback = [(i.message, i.suggestion) for i in r.errors]  # → fix and retry
```

## Seeding an application-specific spec

When asked to "set up / seed PrismQL for <dataset>", generate a project skill
so future sessions can query that dataset without rediscovery:

1. **Explore the data**: find the files/table, sample ~20 records, identify the
   ordering, and map columns → `id` / `text` / `user` / `timestamp`. If ids are
   not sequential ints, assign `enumerate()` positions at load time.
2. **Pick the backend** from the table above (size + format).
3. **Draft dictionaries**: 5–15 domain term-lists from the sampled vocabulary
   (e.g. for trading news: `earnings_beat`, `sanctions_new`, `oil_positive`).
   Dictionaries are the semantic layer — invest here.
4. **Write the loader** as a small, importable snippet (file path → docs list →
   backend → engine).
5. **Smoke-test 3 queries**: one filter, one `INWINDOW` co-occurrence, one
   `FOLLOWED_BY` sequence. Paste real output into the seeded skill.
6. **Write the skill** to `.claude/skills/prismql-<dataset>/SKILL.md` in the
   target project using `SEED_TEMPLATE.md` (in this directory) as the skeleton,
   and copy this skill's `LANGUAGE_REFERENCE.md` alongside it.

The seeded skill must stand alone: loader code, field mapping, full dictionary
definitions, verified example queries with their actual output, and any
dataset-specific quirks discovered during smoke-testing.
