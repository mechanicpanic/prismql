---
name: prismql
description: Run PrismQL pattern-matching queries over sequential data (conversations, logs, events, transactions) — via a local prismql-server if one is running, else directly via Python. Use when the user wants to find sequential/co-occurrence/temporal patterns in ordered records ("X followed by Y", "A and B within N messages", repeated behavior by the same entity), or asks to "seed"/set up PrismQL for a specific dataset.
---

# PrismQL — executable pattern queries over sequential data

PrismQL is "regex for event sequences": a query language over ordered records.
Two ways to run queries: a local **prismql-server** (preferred — warm
engine, plain HTTP, hydrated results, teachable 422s) or **inline Python**.
**Read `LANGUAGE_REFERENCE.md` in this skill directory before writing your
first query**, then check the Pitfalls section below for the errors agents
most commonly make.

## Server mode (check this first)

```bash
curl -s localhost:8901/health    # port from the server's prismql.toml; anything but connection-refused → up
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
**The server caps groups per response** (`[server] max_results`, default 50;
a larger `max_results` in the request is silently clamped and the response
says `"truncated": true`). For a total, append `AGGREGATE count()` to the
query — it counts every group, uncapped. To enumerate more than the cap add
`"output": "file"` (+ optional `"label"`): every group is written
server-side as JSONL and the response carries only `{count, path, preview}`
— read the file selectively, never inline it all. This needs
`[server] enable_file_output = true`; otherwise the server answers 403.
`GET /schema` describes the loaded corpus — fields with coverage/types,
example values for categorical fields (your `from()`/`field()` targets),
configured dictionaries, and the text_match mode. **Read it before writing
queries against an unfamiliar corpus instead of guessing field names.**
`GET /reference` serves the full language doc; `POST /reload` re-reads the
data file.

## Starting a server on your own events

One JSON object per line; `id` and a timestamp field are the only ones the
engine needs to know about, everything else is queryable with `field()`:

```toml
# prismql.toml
[server]
port = 8901

[backend]
type = "memory"                 # < ~100K rows; "tantivy" for real full-text
data = "events.jsonl"           # .json / .jsonl / .csv / .parquet
timestamp_fields = ["time"]     # parsed on load

[engine]
timestamp_field = "time"        # the axis DURING measures on

[dictionaries]
failures = ["failed", "error", "timeout"]
```

```bash
uv sync --extra server --extra plan    # from a clone; not on PyPI yet
uv run prismql-server --config prismql.toml
```

**Both timestamp keys are required.** Without `[engine].timestamp_field` a
`DURING` query returns an empty result, not an error. Stream order is the
file order; ids are labels and may be strings.

## What the language is — and what its text matching is

PrismQL asks for *sequences*: A then B within a window, A and B near each
other, the same entity twice, A not followed by B. Every leg of a pattern is
a filter on one event; the operators between legs are the language.

Text matching exists only to name such a filter, and it is deliberately
narrow — **no ranking, no relevance, a set of ids in, a set of ids out**:

| Predicate | Matches | Backed by |
|---|---|---|
| `field(name, value)` | a field equals a value (case-insensitive); `from(x)` = `field(user, x)` | field index |
| `contains(dict)` | the `text` field holds any term of a named dictionary | inverted token index (memory) / tantivy FTS |
| `contains_tokens(dict)` | same, whole tokens only (keeps `C++`, emails) | same |
| `contains_phrase("…")` | one exact phrase | same |
| `similar_to("…", 0.7)` | embedding cosine ≥ threshold | semantic index, if configured |

Only the `text` field is indexed for the text predicates (memory backend;
tantivy takes `text_fields`). A dictionary is the semantic layer: invest
there, and pass it in-band via `dictionaries` while iterating.

## Known-wrong today (read before trusting a result)

The legacy execution path is being replaced by a Polars plan (P3). Until
then these return **wrong or empty results without an error**:

- **Two variables on a leg, or a variable that skips a leg (A10).** A
  single `$k` on a two-leg link is fine. `field(page,$p) AND from($u)` on
  one leg, or `from($u) FOLLOWED_BY x FOLLOWED_BY from($u)`, pick the
  nearest candidate first and only then check the variable; any other
  entity's event in between drops the group, so the count is too low,
  often 0. Cross-check by dropping one variable.
- **Positional distance is id arithmetic on the Rust path (A2).** With
  gapped or string ids prefer `DURING`, or assign sequential integer ids.
- **Quantifier ranges run as their minimum (A8).** `{2,5}` means `{2}`.
- **`{n,}` is rejected unless `[engine] quantifier_ceiling = m` is set** (then it
  means `{n,m}`); the 422 says so. Prefer an explicit `{n,m}`.
- **Groups are printed in id order, not stream order (A9).**

## Inline Python (no server)

From a clone: `uv sync --extra plan`, or in another project
`uv add --editable /path/to/prismql`. If `import prismql` already works, skip.

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

Backends: `MemoryBackend` (< ~100K rows), `TantivyBackend` (`[tantivy]`
extra, real full-text), `DuckDBBackend` / `PostgresBackend` (data already
there). Document format: dicts with `id`, `text` (for text ops), `user` (for
`from()`), `timestamp` (for `DURING`); other fields allowed.

## Result shapes

- `engine.execute(q)` → `list[list[id]]` — each inner list is one match group.
- `AGGREGATE count()` → `AggregateResult`; `.to_dict()` →
  `{'function': 'count', 'field': None, 'value': N}`.
- `AS "name"` groups → `NamedQueryResult`; `.get_named_group(i)` → `{name: id}`.
- Full records for a group: `backend.get_documents(group)` (the server
  hydrates them for you).

## Pitfalls

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
3. **Use the subquery form only to sequence multi-message stages.** For
   simple sequences plain `a FOLLOWED_BY b INWINDOW n` is equivalent and
   simpler. `(SELECT a, b INWINDOW 3) FOLLOWED_BY (SELECT c) INWINDOW 8`
   matches whole groups (all of stage 1 before stage 2, gap from the
   stage's last message to the next stage's first within the window) and
   concatenates them. Each link needs its own `INWINDOW`; an extra trailing
   positional window is rejected — use `DURING` for an overall time bound.
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
