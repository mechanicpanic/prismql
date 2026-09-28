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
  must name a field that appears in `fields`. When no event has a time in
  it, a time query stops with an error that names the columns that do hold
  times: say that to the person and fix the config, rather than rewriting
  the query.

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
`GET /results/{result_id}` / `GET /results/{result_id}.jsonl` (page or
stream a kept match or scout result — rate-limited like the endpoints
above; the `.jsonl` response carries an `X-PrismQL-Total` header with the
number of lines the stream will send), `POST /reload` (off unless the
server enables it).

**Scout before you query.** Two endpoints answer "what is where" with
ranked hits — outside the language, which never ranks:

- `POST /search` `{"query": "timeout OR \"rate limit\" OR fail*", "limit": 20}` —
  full-text over the `text` field in tantivy syntax (`AND`/`OR`/`NOT`,
  quoted phrases, `field:term`, `prefix*`), stemmed, BM25 best first.
- `POST /similar` `{"text": "the agent gave up on the task", "limit": 20}` —
  nearest events by cosine over the corpus's embedding index (needs an
  ingested `emb` column or `[semantic].model`; 422 otherwise). Optional
  `threshold`.

Both take `corpus`, `hydrate` (`false` = ids and scores only, no events)
and `output: "file"` (all hits to a JSONL file, a five-row preview back —
up to `scout_depth` hits; your request's own `limit` does not narrow that
file), exactly like `/evaluate`. Send `X-PrismQL-Client: <your name>` on every
request: the server keeps a journal of requests (`GET /activity`) and shows
it to the person on `/board/` — with your name, they can follow what you
asked and open any of it themselves — use them to read a few hits, learn the words
people actually wrote, then put those words in a dictionary and ask the
real question with `/evaluate`. Hits are `{"id", "score"[, "event"]}`, kept
server-side under a `result_id` exactly like a match result — page them the
same way.

**Who addresses whom.** `mentions_user("Claude Opus 4.5")` finds messages
that `@mention` that author; `mentions_user($y)` binds each mentioned name,
so `SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) DURING 10
minutes` is "addressed, then answered by the one addressed" and
`field(agent, !$y)` "answered by someone else". A mention is `@` plus an
author name that exists in the corpus — e-mail addresses do not count.

**Ask why an event is there.** `"explain": true` on `/evaluate` (or
`?explain=true` on `GET /results/<id>`) adds `explain` to each group: per
event, the conditions it satisfies — `{"predicate": "contains(evalaware)",
"matches": [{"term", "field", "start", "end"}]}` with character offsets
into that field, `{"predicate": "similar_to(…)", "score": 0.61}`, or just
the name for `field(…)`. Conditions under `NOT` never appear. Use it to
tell a dictionary that is too broad from a hit whose word sits past what
you read — before you narrow the dictionary.

**Read around an event before you name what it is.** `GET /context?id=<id>&
minutes=10&same=agent` returns the events around one event in stream order
— within ten minutes before and after, only those with the same `agent` —
each with its `offset` from the event (`0`), time and fields. Without
`minutes` it takes `before`/`after` events (10 each, at most 200); `same` is
any field. One call instead of two queries and a join.

### Four things about the server that will bite you

1. **A match or scout result is kept, not just returned — page it, don't
   re-run it.** `result_id` is opaque — treat it as an unparsed token, not
   "r" plus a counter; the hex suffix is what keeps an id held from before a
   restart from matching a different result on the new process, where the
   counter alone repeats from 1. A plain aggregate (no `GROUP BY`, or
   `GROUP BY` without `AGGREGATE`) is small and returned inline only — no
   `result_id`, not kept. `GROUP BY ... AGGREGATE` is the one exception
   that gets both: it answers inline in full (its `grouped_values`) AND is
   kept as a `"rows"` result with a `result_id`/`total`, pageable the same
   way. `count` is how many items
   *this response* carries,
   `max_results` is the page size, `total` is how many the query found, and
   `"truncated": true` means paging further returns more. Fetch the rest
   with `GET /results/{result_id}?offset=…&limit=…&hydrate=…&fields=…` (the
   MCP shim's `result_page(result_id, offset, limit)` does the same), or
   stream every kept item at once with `GET /results/{result_id}.jsonl`.
   Scouting keeps only its best `scout_depth` hits and reports that as
   `kept` — `total` can exceed `kept`, and then `truncated` turns false at
   `kept`, not `total`. A stale id (server restarted, `/reload` ran, or the
   result aged out of the memory budget) comes back as a 404 with
   `error.type == "gone"` — run the query again, do not retry the page.
   For a real total regardless of paging, `AGGREGATE count()` still counts
   every group, uncapped.
2. **Enumerating past the cap in one shot needs permission.** `"output":
   "file"` writes every kept group (or up to `scout_depth` hits for
   scouting) as JSONL server-side and returns `{count, path, preview}`; on a
   server without `[server] enable_file_output = true` it answers 403. For
   a match result, paging by `result_id` works either way and needs no
   permission — use it instead of asking to enable file output.
3. **Dictionaries are per-request.** Add `"dictionaries": {"name":
   ["term", …]}` to the body to define or override term lists for that
   query only. Iterate there; ask for stable ones to be persisted into the
   server's `prismql.toml`.
4. **Kept results do not survive a reload or a restart.** They live only in
   memory, on the load they were computed on; the person restarting the
   server or reloading corpora mid-conversation means your next page comes
   back `gone` — that is expected, not a bug to report.

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

One timestamp key is enough: the other follows, and with neither the server
takes `timestamp` if the file has it, else `time`; a time query over a field
without times is an error, not an empty answer. Stream order is the file
order; ids are labels and may be strings.

A table in the wrong order or shape, or a harness log folder, becomes that
file through `prismql ingest`: `prismql ingest table SRC DST.parquet --id COL
--time COL [--sort COL] [--keep a,b] [--embed text --model M]`;
`prismql ingest claude-code ~/.claude/projects/<project> DST.parquet` and
`prismql ingest codex ~/.codex/sessions DST.parquet` give one event per
prompt / thought / tool call / tool result (`kind`, `tool`, `error`,
`session`, `model`, `text`). A call carries its structure and its end:
`cmd` (the first program a shell command runs: `git`, `curl`, `rm` — past
`cd`, `sudo`, assignments, loop headers; quoted text and heredocs are not
programs), `path` (the file read or written), `host` (from a URL a network
program or fetch is given), `action` (`read`, `write`, `exec`, `network`,
`destructive` — recursive rm, `git reset --hard`, force push, `git clean
-f`, `find -delete`, `dd of=`, DROP/TRUNCATE through a SQL client),
`outcome` (`ok`, `error`, `none` — no result), `duration_ms` (call to
result, so a wait for the user's approval counts), `output_chars`, and the
words `duration_bucket` (`instant` < 1s, `short` < 10s, `medium` < 1m,
`long` < 10m, `very_long`) and `output_bucket` (`empty`, `small` < 1k
chars, `medium`, `large`, `huge` ≥ 100k); `call` joins a call to its
result. Codex marks `error` only for a non-zero exit of its exec tool and
reads files through the shell, so its failure and read counts are not
comparable with Claude Code's. Claude Code sub-agent events carry `agent`,
and the call that started one carries it as `spawned`:
`field(spawned, $g) FOLLOWED_BY field(agent, $g) DURING 1 hour`. Point `data` at the
Parquet, `time` is the timestamp field. With `--embed`, `similar_to()` works without any
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
- a backend with no order axis (a tantivy index built before the axis
  sidecar) refuses sequence operators instead of guessing.

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
9. **"N times in a row" is a run, not a quantifier or a chain.** `X{7}`
   counts every combination of 7 (20 repeats → 77,520 groups); a chain of
   7 links gives one overlapping group per starting event. `RUN(X){7,}`
   gives one group per maximal run, split by the variables in X, the first
   window the step, a second the whole run:
   - ✅ `SELECT RUN(field(kind, retry) AND field(agent, $a)){7,} DURING 1 hour DURING 1 day`
   - pipe: `run(field(kind, retry) and field(agent, $a)){7,} |> during(1h) |> during(1d)`
   - for now RUN is the whole query (no comma, AND/OR or chain around it).

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
extra, real full-text, persisted with `index_path`). Data in a database
becomes a corpus through `prismql ingest table`, not through a backend. Documents are dicts with `id`, `text` (for text predicates), `user`
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
