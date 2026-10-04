# Handing PrismQL to an agent

For the person who sets this up. You have a file of events and an agent
(Claude Code, Codex, any harness that can run `curl`). You start a PrismQL
server on your data; the agent reads the folder `skills/prismql/` and asks
questions over HTTP. The agent needs no Python, no MCP and no copy of your
data — only the port.

Every command below was run against a live server before it was written
here; the sample outputs are real.

## 1. Your events

One JSON object per line. The engine needs two things named: an id field
and a timestamp field. Everything else is queryable with `field(name, value)`. **Stream order is file order** — ids are labels, not coordinates,
and may be strings.

```jsonl
{"id": "e1", "time": "2026-06-18T18:24:12Z", "kind": "save", "page": "P1", "who": "ann"}
```

`.json`, `.jsonl`, `.csv` and `.parquet` all load.

Text search (`contains()`, `contains_phrase()`) reads only the columns named
`text`, `content` or `message`. Words that live in another column (`body`,
`title`) are found by `field()` but never by the text predicates, and the
query does not fail — it just returns less. Put the text an agent should
search into a `text` column.

Agent harness logs become such a file with `prismql ingest claude-code` or
`prismql ingest codex`: one event per prompt, thought, tool call and result,
and each call carries what it ran and how it ended — `cmd`, `path`, `host`,
`action` (`destructive` for recursive deletes, hard resets, force pushes),
`outcome`, `duration_bucket`, `output_bucket` (the agent skill lists the
values). "A command failed and was retried" is then
`field(outcome, error) AND field(cmd, $c) FOLLOWED_BY field(cmd, $c) INWINDOW 5`,
not a text search.

## 2. `prismql.toml`

```toml
[server]
port = 8901
max_results = 50             # page size for a match response
# results_memory_mb = 256    # kept results, in-memory budget; oldest evicted first
# scout_depth = 1000         # best hits /search and /similar keep

[backend]
type = "memory"              # under ~100K rows; "tantivy" for real full-text
data = "events.jsonl"        # relative paths resolve against this file
timestamp_fields = ["time"]  # parsed on load

[engine]
timestamp_field = "time"     # the axis DURING measures on

[dictionaries]               # optional; the semantic layer for contains()
failures = ["failed", "error", "timeout"]
```

**The time keys.** `[backend].timestamp_fields` says what to parse;
`[engine].timestamp_field` says which parsed field `DURING` measures on.
One is enough: the other follows, and with neither the server takes
`timestamp` if the file has it, else `time`. A time query on a corpus with
no time in that field stops with an error naming the columns that hold
times — it is never answered empty.

`GET /schema` shows what the server made of the config, and the check is
one line: `timestamp_field` must name a field that appears in the same
response's `fields` block. Its default is `timestamp`, so a config that
omits the `[engine]` key on events carrying `time` reports
`"timestamp_field": "timestamp"` — a field nothing has — and from then on
every `DURING` query answers zero groups and no error.

## 3. Start the server

PrismQL is not on PyPI. Today the install is a clone:

```bash
git clone git@github.com:mechanicpanic/prismql.git && cd prismql
uv sync --extra server
uv run --extra server prismql-server --config /path/to/prismql.toml
```

Keep `--extra server` on `uv run` as well. `uv run` re-syncs the
environment to the project's defaults first, so a bare `uv run prismql-server` in a fresh clone uninstalls FastAPI and then fails with
`ModuleNotFoundError: No module named 'fastapi'`.

Check it is up:

```console
$ curl -s localhost:8901/health
{"status":"ok","backend":"MemoryBackend","documents":13,"loaded_at":"..."}
```

The server binds `127.0.0.1` by default — it is local, not exposed.

## 4. Hand the agent the folder

```bash
cp -rL /path/to/prismql/skills/prismql <your-project>/.claude/skills/prismql
```

**The `-L` matters.** `skills/prismql/LANGUAGE_REFERENCE.md` is a symlink
to the repo root. Without `-L` you copy the link instead of the file, and
outside the repo it points at nothing — the agent loses the one document
it is told to read first. Which flag does that is platform business: on
macOS `cp -R` copies the link (`cp -r` there happens to follow it), while
GNU coreutils copies the link under both `-r` and `-R`. So keep the `-L`,
and check after copying:

```bash
head -1 <your-project>/.claude/skills/prismql/LANGUAGE_REFERENCE.md
```

If the harness has no skills folder, give the agent the directory path and
tell it to read `SKILL.md` first. Either way, tell it the port if it is not
8901.

## 5. What the agent can and cannot do

Can:

- read `GET /schema` — fields, coverage, example values, configured
  dictionaries — so it writes `field()` targets instead of guessing them;
- run `POST /evaluate` and get back whole events, grouped, not a summary;
- define or override dictionaries for one query by putting
  `"dictionaries": {"name": ["term", …]}` in the request body;
- get a total with `AGGREGATE count()`;
- read `warnings` on every answer: a query that ran but answers another
  question (identical links repeated, a variable shared by subqueries,
  counted quantifier combinations) says so, with what to write instead;
- count repeats in a row with `RUN(X){n,m}` — one group per run (retry
  loops, the same request again and again), where `X{n}` would give every
  combination and a chain one overlapping group per starting event;
- fix its own broken query: a bad query comes back as a 422 whose
  `error.message` says what to change;
- scout first: `POST /search` (ranked full-text hits, tantivy syntax) and
  `POST /similar` (ranked nearest events by embedding, when the corpus has
  one) show what is where before it writes a query — with `hydrate: false`
  for ids and scores only, or `output: "file"` to keep the hits out of its
  context entirely (scouting to a file writes up to `scout_depth` hits; the
  request's own `limit` no longer narrows that file);
- see why each event is there: `"explain": true` on `/evaluate` gives, per
  event, the conditions it satisfies with the matched terms and their
  offsets, and the `similar_to` score — and, for a query with `$variables`,
  what each variable stood for in that group (`bindings`);
- read around a finding: `GET /context?id=<id>&minutes=10&same=agent` gives
  the events before and after one event (the same agent's, or every event
  without `same`), so it can check a hit before calling it anything;
- page past the cap without re-running anything: a match response is kept
  server-side under a `result_id`; `GET /results/{result_id}?offset=…&limit=…`
  fetches more of it, `GET /results/{result_id}.jsonl` streams all of it. A
  plain aggregate (no `GROUP BY`, or `GROUP BY` without `AGGREGATE`) carries
  no id — it stays small and inline. `GROUP BY ... AGGREGATE` is the one
  exception that gets both: inline in full AND kept as a `"rows"` result
  with a `result_id`/`total`, pageable the same way.

The request body is `query` plus, all optional, `max_results`, `hydrate`
(ids without events when `false`), `fields` (project hydrated events down
to these plus the id), `dictionaries`, `output`, `corpus` and `label`.
`skills/prismql/SKILL.md` says what each one does; the agent does not have
to guess them from the examples.

Cannot, on a default server:

- change the corpus — `POST /reload` needs `enable_reload = true`;
- write anything to disk — see the second limit below;
- rank or score *query* results. The language is set-in, set-out: no
  relevance, no top-k (ranking lives only in the two scouting endpoints
  above). `contains(x)` takes a **dictionary name**, never a literal word
  (`contains_phrase("…")` is the literal form);
- use sequence operators on a backend with no order axis — a tantivy index
  built before this version refuses them instead of guessing (rebuild it;
  indexes built now keep their axis on disk).

## 6. The two limits to tell the agent about

**The inline cap — now a page, not a wall.** `[server] max_results`
(default 50) is the size of one *page* of a match response; `count` is how
many groups this page carries, `total` is how many the query found, and
`"truncated": true` means paging further returns more (a larger
`max_results` in the request is clamped down to the configured value
without saying so). The agent does not need to shrink its query to see the
rest — it pages the kept result by the `result_id` the response carries:

```console
$ curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
    -d '{"query": "SELECT field(kind, save)", "max_results": 2, "hydrate": false}'
{"kind":"groups","count":2,"total":8,"truncated":true,"result_id":"r12-3fa9c1d0","results":[{"ids":["e1"]},{"ids":["e12"]}], …}

$ curl -s "localhost:8901/results/r12-3fa9c1d0?offset=2&limit=2"
{"ok":true,"result_id":"r12-3fa9c1d0","kind":"groups","total":8,"offset":2,"count":2,"truncated":true,"results":[…]}

$ curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
    -d '{"query": "SELECT field(kind, save) AGGREGATE count()"}'
{"kind":"aggregate","function":"count","field":null,"value":8, …}
```

`result_id` is opaque — treat it as an unparsed token, not "r" plus a
counter: the numeric part alone can repeat across a server restart, so the
hex suffix is what makes an id from before a restart practically never
collide with a live one. `GET /results/{id}` and `/results/{id}.jsonl` are
rate-limited the same way `/evaluate` is. `GET /results/{id}.jsonl` also
carries an `X-PrismQL-Total` response header: the number of lines the
stream will send, so the agent can check it received the whole thing
without buffering it first.

`/search` and `/similar` are paged the same way, but their `total` can run
ahead of what the server kept: it holds only the best `[server] scout_depth` hits (default 1000) and reports that count as `kept` — more
matched than were kept when `kept < total`, and `truncated` turns false
once the agent has paged through `kept`.

A kept result lives in memory only: it does not survive `/reload` or a
restart, and the oldest are dropped first once `[server] results_memory_mb`
fills up. Either way a stale id comes back `{"ok":false,"error":{"type": "gone",...}}` — tell the agent to run the query again, not to treat it as
a bug.

**`AGGREGATE count()` is still the only honest total** for the number
itself — reading `total` off a match response works too, but an aggregate
is the one shape built to answer "how many" and nothing else.

It counts **match groups**. For `A FOLLOWED_BY B` that is one per start
event, so a page deleted twice and then saved once is two matches. If the
question is "how many pages", say `count(DISTINCT page)` (the field both
legs share); for matches per page `GROUP BY page AGGREGATE count()`. The
language has no stage that keeps one group per page — an agent that needs
that takes the groups and deduplicates them itself. The agent skill's
pitfall 10 has the worked example.

**File output is off.** To enumerate more groups than the cap, the agent
asks for `"output": "file"`, and on a default server gets:

```json
{"ok":false,"error":{"type":"forbidden","message":"output='file' is disabled on this server; set [server] enable_file_output = true to allow it."}}
```

Turn it on only if you want the server writing to your disk:

```toml
[server]
enable_file_output = true
results_dir = "results"      # resolved against prismql.toml's directory
```

Then every group goes to a JSONL file server-side and the response carries
only `{count, path, preview}` — the agent reads the file selectively
instead of pulling thousands of groups into its context. The file is on the
server's machine; if the agent runs elsewhere it can see the path but not
the file.

## 7. Check the agent got it right

Open `http://127.0.0.1:8901/board/` while the agent works. Every request the
server answers — queries, scouting, file outputs, errors — appears there as
it happens, with the query highlighted, who asked (the agent's
`X-PrismQL-Client` name), how many groups came back and how long it took.
Click a row to see its label and file path, **open** to re-run it with your
own `max` and with or without events, **edit** to change it and run it
yourself; your runs land in the same feed as `board`. The server keeps
summaries only (last 500 in memory; `results/activity.jsonl` when file
output is on, read back after a restart), never the results.


Save these 13 lines as `events.jsonl` and the config from section 2 beside
it, start the server, and ask the agent the three questions in plain words
— do not give it the queries.

```jsonl
{"id": "e1",  "time": "2026-06-18T18:24:12Z", "kind": "save",   "page": "P1", "who": "ann"}
{"id": "e2",  "time": "2026-06-18T18:24:31Z", "kind": "delete", "page": "P1", "who": "admin"}
{"id": "e3",  "time": "2026-06-18T18:25:56Z", "kind": "save",   "page": "P1", "who": "ann"}
{"id": "e4",  "time": "2026-06-18T18:31:02Z", "kind": "save",   "page": "P2", "who": "bo"}
{"id": "e5",  "time": "2026-06-18T18:33:40Z", "kind": "delete", "page": "P2", "who": "admin"}
{"id": "e6",  "time": "2026-06-18T18:35:10Z", "kind": "save",   "page": "P4", "who": "ann"}
{"id": "e7",  "time": "2026-06-18T19:10:05Z", "kind": "save",   "page": "P2", "who": "bo"}
{"id": "e8",  "time": "2026-06-18T19:12:20Z", "kind": "delete", "page": "P3", "who": "admin"}
{"id": "e9",  "time": "2026-06-18T19:13:01Z", "kind": "save",   "page": "P3", "who": "cai"}
{"id": "e10", "time": "2026-06-18T19:20:44Z", "kind": "login",  "page": "-",  "who": "cai"}
{"id": "e11", "time": "2026-06-18T19:21:02Z", "kind": "delete", "page": "P3", "who": "cai"}
{"id": "e12", "time": "2026-06-18T19:22:15Z", "kind": "save",   "page": "P3", "who": "cai"}
{"id": "e13", "time": "2026-06-18T19:40:00Z", "kind": "save",   "page": "P4", "who": "ann"}
```

**Question 1 — "Which events are deletions?"**

Four one-event groups: `e2`, `e5`, `e8`, `e11`. Compare them as a set;
which group comes first is not part of the answer.

**Question 2 — "Find a page that was deleted and then saved again within
ten minutes."**

Exactly three pairs: `[e2, e3]`, `[e8, e9]`, `[e11, e12]`, each hydrated
with both events. The query that produces them:

```
SELECT field(kind, delete) AND field(page, $p)
       FOLLOWED_BY field(kind, save) AND field(page, $p) DURING 10 minutes
```

This is the question that separates an agent that read the reference from
one that did not:

- **Four pairs, with `[e5, e6]` among them** — it dropped the `$p`
  variable and matched a delete of P2 against a save of P4. Same shape,
  wrong question. Send it back to the pattern-variable section.
- **A 422 saying the chain is missing a window on its final link** — it
  forgot the trailing `DURING`/`INWINDOW`. The message tells it exactly
  that, so a competent agent retries and lands on the right answer; only
  count this as a failure if it does not recover.
- **`[e5, e7]` in the list** — it ignored the time window; those two are
  36 minutes apart.

**Question 3 — "How many such repairs are there in total?"**

`3`, from an `AGGREGATE count()` response (`{"kind":"aggregate", …, "value":3}`). An agent that reports the number of groups it happened to
receive inline has not understood the cap — on your real data that number
will be 50 and wrong.

The same three, as curl, if you want to see them yourself:

```bash
curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
  -d '{"query": "SELECT field(kind, delete)", "hydrate": false}'

curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
  -d '{"query": "SELECT field(kind, delete) AND field(page, $p) FOLLOWED_BY field(kind, save) AND field(page, $p) DURING 10 minutes"}'

curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
  -d '{"query": "SELECT field(kind, delete) AND field(page, $p) FOLLOWED_BY field(kind, save) AND field(page, $p) DURING 10 minutes AGGREGATE count()"}'
```

## 8. Still open

How an agent gets this pack **without cloning the repository** — a
marketplace plugin, a skills package, a file shipped inside the wheel — is
not decided (graph `@aleph/prismql` #49), and neither is where the
human-facing documentation is published (#50). Today the answer is the one
above: clone, then copy the folder with `-L`.

## Further reading

- `skills/prismql/SKILL.md` — what the agent reads.
- `LANGUAGE_REFERENCE.md` / `PIPE_REFERENCE.md` — the two dialects.
- `docs/MENTAL_MODEL.md` — the language in one sitting, with a self-test.
