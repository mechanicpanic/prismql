---
name: prismql
description: Run PrismQL pattern-matching queries over sequential data (conversations, logs, events, transactions) — via a local prismql-server if one is running, else directly via Python. Use when the user wants to find sequential/co-occurrence/temporal patterns in ordered records ("X followed by Y", "A and B within N messages", repeated behavior by the same entity), or asks to "seed"/set up PrismQL for a specific dataset.
---

# PrismQL — executable pattern queries over sequential data

PrismQL is "regex for event sequences": a query language over ordered
records. A query names a shape in the stream and returns every instance of
it — the events themselves, grouped, never a summary.

**Read `LANGUAGE_REFERENCE.md` in this directory before your first query**,
then the Pitfalls section below.

## Start here: is a server running?

**`8901` is only the default port — use the port the person gave you, and
ask if they did not.** On any other port the probe below answers
connection-refused, and you would wrongly conclude there is no server.

```bash
curl -s localhost:8901/health    # anything but connection-refused → up
```

If it is up, that is the whole interface — no Python, no data loading.

```bash
curl -s localhost:8901/schema    # do this before writing any query
```

`/schema` describes the loaded corpus: fields with coverage and types,
example values for categorical fields (your `from()` / `field()` targets),
the configured dictionaries, the timestamp field, the text-match mode.
Read it instead of guessing field names. Two things it does not say
outright:

- `fields[].type` is the type of the value as it was loaded — a timestamp
  read from JSON or CSV shows as `"str"` even though the engine parsed it.
  That field does not tell you whether the time axis works.
- the top-level `timestamp_field` is the axis `DURING` measures on, and it
  must name a field that appears in `fields`. When it names one that is
  absent — its default is `timestamp`, so a corpus whose column is `time`
  plus a half-written config shows exactly that — every `DURING` query
  answers zero groups and no error. Say that to the person rather than
  reporting "no matches".

```bash
curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
  -d '{"query": "SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 5", "max_results": 20}'
```

Body fields, all optional but `query`: `max_results` (the inline cap, see
below), `hydrate` (`true` by default; `false` returns ids only),
`dictionaries` (term lists for this request), `output` (`"inline"` or
`"file"`), `corpus` (a name from `GET /corpora`), `label` (a slug for the
results file).

The response carries hydrated event groups (`results[].events`). A bad
query comes back as a structured 422 whose `error.message` says what to
change — read it and retry rather than guessing again. One case the
message does not name: **every query begins with `SELECT`**; leave it out
and the 422 reports the operator it tripped on (`Unexpected 'FOLLOWED_BY'
after query`), not the missing keyword.

Other endpoints: `GET /reference` (the full language doc), `GET /corpora`
(named corpora; pass `"corpus": "<name>"` in the request to pick one),
`POST /reload` (off unless the server enables it).

### Three things about the server that will bite you

1. **The group cap.** `count` in a response is the number of groups *in
   that response*, capped by the server's `max_results` (default 50); a
   larger `max_results` in your request is silently clamped down to it.
   `"truncated": true` is the only signal that more existed. For a real
   total append `AGGREGATE count()` — it counts every group, uncapped.
2. **Enumerating past the cap needs permission.** `"output": "file"`
   writes every group as JSONL server-side and returns `{count, path,
   preview}`; on a server without `[server] enable_file_output = true` it
   answers 403. Do not work around it by paging — use `AGGREGATE count()`
   or a narrower query, or ask the person to enable it.
3. **Dictionaries are per-request.** Add `"dictionaries": {"name":
   ["term", …]}` to the body to define or override term lists for that
   query only. Iterate there; ask for stable ones to be persisted into the
   server's `prismql.toml`.

## Starting a server yourself

One JSON object per line; `id` and a timestamp field are the only fields
the engine needs named, everything else is queryable with `field()`:

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
failures = ["failed", "error", "timeout"]   # stemmed whole words: "fail" ~ "failed"
```

```bash
uv sync --extra server                  # from a clone; not on PyPI yet
uv run --extra server prismql-server --config prismql.toml
```

**Both timestamp keys are required.** Without `[engine].timestamp_field` a
`DURING` query returns an empty result, not an error. Stream order is the
file order; ids are labels and may be strings.

A table in the wrong order or shape, or a harness log folder, becomes that
file through `prismql ingest`: `prismql ingest table SRC DST.parquet --id COL
--time COL [--sort COL] [--keep a,b] [--embed text --model M]`;
`prismql ingest claude-code ~/.claude/projects/<project> DST.parquet` and
`prismql ingest codex ~/.codex/sessions DST.parquet` give one event per
prompt / thought / tool call / tool result (`kind`, `tool`, `error`,
`session`, `model`, `text`). Point `data` at the Parquet, `time` is the
timestamp field. With `--embed`, `similar_to()` works without any
`[semantic]` config: the file carries the vectors and the model name.

Keep `--extra server` on `uv run` too: `uv run` re-syncs the environment to
the project defaults first, and a bare `uv run prismql-server` in a fresh
clone drops FastAPI and fails with `ModuleNotFoundError`.

## The language, and what its text matching is

Every leg of a pattern is a filter on one event; the operators between legs
are the language. Text matching exists only to name such a filter, and it
is deliberately narrow — **no ranking, no relevance, a set of ids in, a set
of ids out**:

| Predicate | Matches | Backed by |
|---|---|---|
| `field(name, value)` | a field equals a value (case-insensitive); `from(x)` = `field(user, x)` | field index |
| `contains(dict)` | the `text` field holds any term of a named dictionary | inverted token index (memory) / tantivy FTS |
| `contains_tokens(dict)` | same, whole tokens only (keeps `C++`, emails) | same |
| `contains_phrase("…")` | one exact phrase | same |
| `similar_to("…", 0.7)` | embedding cosine ≥ threshold | semantic index, if configured |

Only the `text` field is indexed for the text predicates (memory backend;
tantivy takes `text_fields`). A dictionary is the semantic layer: invest
there, and pass it in-band while iterating.

What you can rely on, because every sequence and window operator is one
implementation over the ordered corpus:

- positional distance is stream distance — ids are labels, string ids fine;
- `A, B INWINDOW n` is unordered and commutes; `FOLLOWED_BY` is ordered and
  takes the nearest eligible match per left-hand event;
- a group never holds the same event twice; slots come back in stream
  order;
- `{n,m}` enumerates every size in the range, one group per set;
- pattern variables are held while the nearest candidate is chosen, so two
  variables on one leg, or a variable that skips a leg, both work;
- a subquery stage merges as one group per stage, the union's span counting
  toward the outer window;
- backends with no order axis (OpenSearch; a tantivy index opened from
  disk) refuse sequence operators instead of guessing.

## Pitfalls

1. **A chain's final link must carry a window.** One trailing window covers
   every windowless link (per link, not whole-chain span); links may also
   mix `INWINDOW` and `DURING` individually.
   - ✅ `SELECT a FOLLOWED_BY b FOLLOWED_BY c INWINDOW 2`
   - ✅ `SELECT a FOLLOWED_BY b INWINDOW 2 FOLLOWED_BY c DURING 1 minute`
   - ❌ `SELECT a FOLLOWED_BY b INWINDOW 2 FOLLOWED_BY c` (no window on final link)
2. **Precedence: `NOT` > `AND` > `OR` > sequential operators.** Compound
   conditions next to `FOLLOWED_BY` need no parentheses:
   `SELECT from(alice) AND is_question() FOLLOWED_BY from(bob) INWINDOW 5`
   means `(alice ∧ question) FOLLOWED_BY bob`. Use parens only to override.
3. **Use the subquery form only to sequence multi-event stages.** For
   simple sequences plain `a FOLLOWED_BY b INWINDOW n` is equivalent and
   simpler. `SELECT (SELECT a, b INWINDOW 3) FOLLOWED_BY (SELECT c)
   INWINDOW 8` matches whole groups (all of stage 1 before stage 2, gap
   measured from the stage's last event to the next stage's first) and
   concatenates them. Three rules, all of them enforced:
   - **the outer `SELECT` is not optional** — a query that starts with
     `(SELECT …)` is a syntax error (`Expected '(' after select`). The
     reference's Subqueries section shows one without the outer `SELECT`
     as valid; it is not — this rule wins;
   - **every link carries its own window**, including the last one;
   - **an extra trailing positional window is rejected** (runtime error
     naming this rule) — use `DURING <time>` for an overall time bound.
4. **`contains(x)` takes a dictionary NAME**, never a literal word. For a
   literal use `contains_phrase("exact phrase")`, or define a dictionary.
5. **`INWINDOW` is unordered; `FOLLOWED_BY` is ordered.** "A then B" →
   `FOLLOWED_BY`; "A and B near each other" → comma + `INWINDOW`.
6. **Don't flatten multi-stage patterns.** `SELECT (SELECT a, b INWINDOW
   3) FOLLOWED_BY (SELECT c) INWINDOW 8` keeps a+b grouped; `SELECT a, b,
   c INWINDOW 8` does not mean the same thing.
7. **Same entity twice → a pattern variable**, not two literals:
   `from($u) AND is_question(), from($u) INWINDOW 5`. `!$u` is "a
   *different* one". The excluded side of a negated operator takes no
   variable — that event is not in the group. A variable binds the value
   slot of `field()` too, not only `from()`. "The same page deleted and
   then saved again":
   - ✅ `SELECT field(kind, delete) AND field(page, $p) FOLLOWED_BY field(kind, save) AND field(page, $p) DURING 10 minutes`
   - ❌ the same query without `$p` — it runs, and returns pairs where one
     page was deleted and a different one saved. Dropping the variable
     does not fail, it answers another question.
8. **`{n,}` is rejected** unless the server or engine sets
   `quantifier_ceiling` — there is no upper bound to enumerate to. The
   validator's code is `OPEN_QUANTIFIER`; over HTTP it is a 422 naming
   `quantifier_ceiling`. Write `{n,m}`, or ask for the ceiling to be set.

## Validate before executing (Python path)

```python
from prismql import QueryValidator
v = QueryValidator(user_dictionaries=dicts)   # same dicts as the engine
r = v.validate(query)
if not r.valid:
    feedback = [(i.message, i.suggestion) for i in r.errors]  # → fix and retry
```

Over HTTP the 422 body does the same job; feed the message back and retry,
at most three attempts before asking the person.

## No server: inline Python

From a clone `uv sync`, or in another project `uv add --editable
/path/to/prismql`. If `import prismql` already works, skip both.

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
    print(group)   # e.g. [1, 2]  — matching record ids, in stream order
EOF
```

Backends: `MemoryBackend` (< ~100K rows), `TantivyBackend` (`[tantivy]`
extra, real full-text), `DuckDBBackend` / `PostgresBackend` (data already
there). Documents are dicts with `id`, `text` (for text predicates), `user`
(for `from()`), `timestamp` (for `DURING`); other fields allowed and
queryable with `field()`.

Result shapes:

- `engine.execute(q)` → `list[list[id]]`, one inner list per match group;
- `AGGREGATE count()` → `AggregateResult`; `.to_dict()` →
  `{'function': 'count', 'field': None, 'value': N}`;
- `AS "name"` → `NamedQueryResult`; `.get_named_group(i)` → `{name: id}`;
- full records for a group: `backend.get_documents(group)` (the server
  hydrates them for you).

## Seeding an application-specific spec

Asked to "set up / seed PrismQL for <dataset>", write a project skill so
future sessions query it without rediscovery:

1. Sample ~20 records; find the ordering; map columns → `id` / `text` /
   `user` / `timestamp`. Pick the backend from size and format.
2. Draft 5–15 domain dictionaries from the sampled vocabulary (trading
   news: `earnings_beat`, `sanctions_new`). This is the semantic layer.
3. Write the loader, or a `prismql.toml` if the project runs the server.
4. Smoke-test three queries — one filter, one `INWINDOW`, one
   `FOLLOWED_BY` — and paste the real output in.
5. Write `.claude/skills/prismql-<dataset>/SKILL.md` from
   `SEED_TEMPLATE.md` (in this directory) and copy this directory's
   `LANGUAGE_REFERENCE.md` alongside it (`cp -L`: it is a symlink).

The seeded skill must stand alone: loader or config, field mapping, full
dictionary definitions, example queries with their actual output, and the
quirks found while smoke-testing.
