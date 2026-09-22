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
and a timestamp field. Everything else is queryable with `field(name,
value)`. **Stream order is file order** — ids are labels, not coordinates,
and may be strings.

```jsonl
{"id": "e1", "time": "2026-06-18T18:24:12Z", "kind": "save", "page": "P1", "who": "ann"}
```

`.json`, `.jsonl`, `.csv` and `.parquet` all load.

## 2. `prismql.toml`

```toml
[server]
port = 8901
max_results = 50

[backend]
type = "memory"              # under ~100K rows; "tantivy" for real full-text
data = "events.jsonl"        # relative paths resolve against this file
timestamp_fields = ["time"]  # parsed on load

[engine]
timestamp_field = "time"     # the axis DURING measures on

[dictionaries]               # optional; the semantic layer for contains()
failures = ["failed", "error", "timeout"]
```

**Both timestamp keys are needed.** `[backend].timestamp_fields` says what
to parse; `[engine].timestamp_field` says which parsed field `DURING`
measures on. Without the second one a `DURING` query returns an empty
result rather than an error — the worst kind of wrong answer.

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
environment to the project's defaults first, so a bare `uv run
prismql-server` in a fresh clone uninstalls FastAPI and then fails with
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
- fix its own broken query: a bad query comes back as a 422 whose
  `error.message` says what to change;
- scout first: `POST /search` (ranked full-text hits, tantivy syntax) and
  `POST /similar` (ranked nearest events by embedding, when the corpus has
  one) show what is where before it writes a query — with `hydrate: false`
  for ids and scores only, or `output: "file"` to keep the hits out of its
  context entirely.

The request body is `query` plus, all optional, `max_results`, `hydrate`
(ids without events when `false`), `dictionaries`, `output`, `corpus` and
`label`. `skills/prismql/SKILL.md` says what each one does; the agent does
not have to guess them from the examples.

Cannot, on a default server:

- change the corpus — `POST /reload` needs `enable_reload = true`;
- write anything to disk — see the second limit below;
- rank or score *query* results. The language is set-in, set-out: no
  relevance, no top-k (ranking lives only in the two scouting endpoints
  above). `contains(x)` takes a **dictionary name**, never a literal word
  (`contains_phrase("…")` is the literal form);
- use sequence operators on a backend with no order axis — OpenSearch
  refuses them instead of guessing (a tantivy index built by this version
  keeps its axis on disk).

## 6. The two limits to tell the agent about

**The inline cap.** `[server] max_results` (default 50) caps the groups in
a response. `count` is the number of groups *in this response*, not the
total, and a larger `max_results` in the request is clamped down to the
configured value without saying so. `"truncated": true` is the only signal
that more existed:

```console
$ curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
    -d '{"query": "SELECT field(kind, save)", "max_results": 2, "hydrate": false}'
{"kind":"groups","count":2,"truncated":true,"results":[{"ids":["e1"]},{"ids":["e12"]}], …}

$ curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
    -d '{"query": "SELECT field(kind, save) AGGREGATE count()"}'
{"kind":"aggregate","function":"count","field":null,"value":8, …}
```

Eight, not two. **`AGGREGATE count()` is the only honest total.**

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

`3`, from an `AGGREGATE count()` response (`{"kind":"aggregate", …,
"value":3}`). An agent that reports the number of groups it happened to
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
