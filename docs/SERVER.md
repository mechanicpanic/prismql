# Running the PrismQL server

One page, from a table of events to a running server with the board, text
search and `similar_to()`. For the language itself see
[USER-GUIDE.md](USER-GUIDE.md); for how an agent drives the server,
[AGENT-USE.md](AGENT-USE.md).

What you get from `prismql-server --config prismql.toml`:

- an HTTP API — `POST /evaluate` (the language), `POST /search` (ranked
  full-text), `POST /similar` (ranked by meaning), `GET /schema`,
  `GET /corpora`, `GET /reference`, `GET /health`, result pages under
  `GET /results/<id>`, and `GET /context` — the events around one event
  (`id`, `before`/`after` or `minutes`, `same=<field>`). `"explain": true`
  on `/evaluate` (`?explain=true` on a result page) says per event which
  conditions it satisfies: matched terms with offsets, similarity scores —
  and per group what each `$variable` stood for (`bindings`);
- the board at `/board/` — every request anyone sends, live, with an editor;
- any number of corpora, each loaded once at start and held in memory.

## 1. Install

From a clone:

```bash
uv sync --extra server --extra tantivy --extra semantic
```

| Extra | What it brings | Without it |
|---|---|---|
| `server` | FastAPI + uvicorn: `prismql-server` | no server |
| `tantivy` | the full-text index behind `contains()`, phrases and `/search` | text predicates fall back to Python's own index — same sets, far slower on a large corpus |
| `semantic` | sentence-transformers + numpy: encodes query text for `similar_to()` and `/similar` | no `similar_to()` |
| `ingest` | the same model stack, for `prismql ingest --embed` | no `--embed` |
| `nlp` | spaCy, for `--annotate entities` (then `python -m spacy download en_core_web_sm`) | no `mentions_org()` and kin |
| `mcp` | `prismql-mcp`, an MCP front for the server | no MCP |

`all` does not include `tantivy`: add it explicitly.

As a tool, with no clone:
`uv tool install "prismql[server,tantivy,semantic] @ git+ssh://git@github.com/mechanicpanic/prismql"`
(the repository is private; see USER-GUIDE §1).

## 2. Prepare the corpus

The server reads `.jsonl`, `.json`, `.csv` or `.parquet`. The stream order
is the order of the rows, and ids are labels. The way to get a clean file is
`prismql ingest`. It sorts, parses time into UTC, keeps the columns you name,
and can annotate and embed in the same pass:

```bash
prismql ingest table raw_events.parquet events.parquet \
  --id event_id --time created_at --sort seq \
  --keep kind,agent,room,text \
  --annotate questions,links
```

The output has `position`, `id`, `time` and the kept columns. The time
column is called **`time`**, which matters in the config (§3).

Several streams become one corpus, since a query reads one corpus:

```bash
prismql ingest table urlquery.csv wiki=revisions.jsonl union.parquet \
  --id id --time time --sort time --source-col source
```

Each row gets `source` (the `LABEL=` given, else the file's stem), ids
become `LABEL:id` so they cannot collide, and a column one file lacks is
empty on the other's rows. The time column must have one name in every
file. Then `field(source, urlquery) … FOLLOWED_BY field(source, wiki) …`
asks across them.

- `--sort COL` orders the stream by that column. Without it the source
  order stands. `--time-unit s|ms|us|ns` states the unit of a numeric time
  column when guessing by magnitude would be wrong.
- `--annotate questions` writes `is_question` for `is_question()`.
  `--annotate links` writes `has_link` for `contains_link()`: a link is
  `http://` or `https://` up to whitespace, the same rule that keeps a link
  one token in the text index. `--annotate entities` writes spaCy labels for
  `mentions_org()` and kin. `--annotate mentions --actor agent` writes
  `mentions` for `mentions_user()`: `@` and a name from the `agent` column.
  Without an annotation column, questions, links and mentions are
  annotated once at load by the same rules (mentions against the corpus's
  `board.actor` field). Entities are never annotated at load.
- `prismql ingest claude-code <project dir> out.parquet` and
  `prismql ingest codex <sessions dir> out.parquet` read agent harness logs.
  A tool call is one event with its program, file, host, kind of action and
  outcome (`cmd`, `path`, `host`, `action`, `outcome`, `duration_ms`,
  `duration_bucket`, `output_chars`, `output_bucket`); the agent skill
  (`skills/prismql/SKILL.md`) lists the values.

### Embeddings: `similar_to()` and `/similar`

The corpus is encoded once and the vectors are stored in the file, in a
column `emb`. At start the server reads them and encodes only the query
text, with the model the file names.

**Encode with ingest:**

```bash
prismql ingest table raw.parquet events.parquet --id id --time time \
  --keep kind,agent,text \
  --embed text --model google/embeddinggemma-300m \
  --doc-prompt 'title: none | text: ' \
  --query-prompt 'task: search result | query: '
```

Models that encode a query and a document differently (embeddinggemma,
Qwen3, nomic, bge) need both prompts. They are written into the file
beside the model, and the server puts the query prompt in front of every
query. Leave them out and the query is encoded like a document: it runs,
and it ranks worse. A file with a document prompt and no query prompt
loads with a warning. For a symmetric model (all-MiniLM, granite) leave
both out.

**Or bring vectors from elsewhere** (vLLM on a GPU box, an API). Write the
Parquet yourself; the server holds you to this contract:

| What | Value |
|---|---|
| column `emb` | `FixedSizeList<float32, d>`, **no nulls**, one row per event, in the file's row order |
| a row with no text | an all-zero vector (not indexed) |
| `prismql.embed_model` | the sentence-transformers name the server will encode queries with |
| `prismql.embed_text` | the text column that was encoded |
| `prismql.embed_doc_prompt` | the prefix the documents were encoded with (omit if none) |
| `prismql.embed_query_prompt` | the prefix for query text (omit if none) |

The four `prismql.*` keys are Parquet schema metadata. Before trusting
outside vectors, compare a few rows against
`SentenceTransformer(model).encode(texts, prompt=doc_prompt)` (the cosine
should be about 1.0). A pipeline that drops a model's final layers puts
the corpus and the queries in different spaces. Every `similar_to()` then
returns plausible, wrong sets.

Without an `emb` column, `[corpora.<name>.semantic] model = "…"` (§3)
encodes the whole corpus at every start. That is fine for a few thousand
events and slow for more.

## 3. The config: `prismql.toml`

Relative paths resolve against the config file's own directory.

```toml
[server]
port = 8901
default_corpus = "events"
enable_file_output = true        # the board's journal survives a restart
results_dir = "results"

[corpora.events]
data = "events.parquet"
# timestamp_fields / timestamp_field: found in the file when left out (§3)
text_index_path = "index/events" # keep the text index on disk

[corpora.events.dictionaries]
signin = ["sign in", "sign-in", "login", "password"]
failure = ["failed", "error", "timeout"]

[corpora.events.board]
kind = "kind"                    # the board shows these as an event's kind
actor = "agent"                  # and who did it
```

**The time keys.** `timestamp_fields` lists the columns parsed as time;
`timestamp_field` is the one `DURING`, `BEFORE`, `AFTER` and `BETWEEN`
measure on. Set neither and the server takes `timestamp` if the file has
that column, else `time` (what `prismql ingest` writes). Set one and the
other follows from it. A query that measures time on a corpus where no
event has a time in that field is refused with an error naming the field
and the columns that do hold times. It is never answered empty.

### `[server]`

| Key | Default | Meaning |
|---|---|---|
| `host` | `127.0.0.1` | address to bind |
| `port` | `8901` | port; `prismql-server --port N` overrides it |
| `default_corpus` | first corpus by name | the corpus a request without `corpus` goes to; must name one |
| `max_results` | `50` | largest page a response carries; the whole result is kept and paged by id |
| `hydrate` | `true` | responses carry the events' fields, not only ids |
| `scout_depth` | `1000` | how many best hits `/search` and `/similar` keep |
| `results_memory_mb` | `256` | memory for kept results; oldest evicted first |
| `enable_file_output` | `false` | allow `"output": "file"` (whole result sets as JSONL) and write the board's journal to `activity.jsonl` |
| `results_dir` | `prismql-results` (in the working directory) | where file output and `activity.jsonl` go |
| `file_output_max_groups` | `100000` | cap on one file output |
| `activity_max` | `500` | how many requests the board's journal holds |
| `enable_reload` | `false` | allow `POST /reload` (rebuilds every corpus from disk) |
| `rate_limit_per_minute` | off | per-client request limit |
| `max_request_dictionary_terms` | `2000` | cap on dictionaries sent inside a request |
| `static_dir` | none | a static site served at `/` (the demo uses it) |

### `[corpora.<name>]`

| Key | Default | Meaning |
|---|---|---|
| `data` | — | the corpus file |
| `type` | `memory` | `memory` (recommended), `tantivy` (a persisted tantivy backend; with `index_path`), `rust_memory` (needs the optional Rust build) |
| `index_path` | none | `type = "tantivy"`: the index folder, opened if it exists |
| `id_field` | `id` | the id column |
| `timestamp_fields` | `[timestamp_field]`, or `timestamp` / `time` from the file | columns parsed as time |
| `timestamp_field` | the first of `timestamp_fields`, or `timestamp` / `time` from the file | the column `DURING` and time filters measure on |
| `text_match` | `stem` | single-word `contains()`: `stem` (fail/failed/failing are one), `token` (whole word), `substring` |
| `text_language` | `english` | stemmer language |
| `text_index` | `tantivy` if installed | `tantivy` or `memory` (Python's own; the only one that answers `substring`) |
| `text_index_path` | none (in RAM) | keep the tantivy text index on disk: the next start opens it; it is rebuilt, never reused, when the text or the tokenizer changed |
| `quantifier_ceiling` | none | upper bound for an open quantifier `{n,}` |

Sub-tables of a corpus:

- `[corpora.<name>.dictionaries]` holds named word lists for `contains(name)`.
  The long form `[corpora.<name>.dictionaries.<dict>]` takes
  `terms = [...]` and `match = "token"`. Multi-word terms always match as a
  phrase.
- `[corpora.<name>.semantic]` has `model = "…"` (and `text_field`, default
  `text`). You need it only for a corpus without a stamped `emb` column; a
  model that differs from the file's stamp is an error.
- `[corpora.<name>.board]` has `kind` and `actor`, the fields the board shows
  for an event; `actor` is also whose names an `@mention` can be.

A single-corpus config may instead use the older flat form: `[backend]`
(`type`, `data`, `index_path`, `id_field`, `timestamp_fields`,
`text_index`, `text_index_path`), `[engine]` (`timestamp_field`,
`text_match`, `text_language`, `quantifier_ceiling`), `[dictionaries]`
(inline or `file = "dicts.json"`), `[semantic]` and `[board]`. Its corpus is
named `default`.

## 4. Start

```bash
prismql-server --config prismql.toml
curl -s localhost:8901/health
```

At start every corpus is loaded, the text index is built (or opened from
`text_index_path`), `emb` becomes one float32 matrix, and the schema the
board shows is computed. Until all of that finishes, nothing answers.
Measured on this machine:

| Corpus | Start | Memory |
|---|---|---|
| Village, 381k events, 384-d vectors, text index in RAM | ~60 s (43 s from `text_index_path`) | ~4.3 GB |
| Village, 569k events, 768-d embeddinggemma vectors | ~45 s | ~12 GB |

The vectors cost `events × dimensions × 4` bytes once loaded (569k × 768 is
1.75 GB). Loading peaks at about three times that.

On an ingested file, `similar_to("…", 0.6)` runs in well under a second.
Encoding the query dominates `/similar` (under 1 s on a laptop CPU).

## 5. The board, and who is asking

Open `http://127.0.0.1:8901/board/`. Every request anyone sends appears
there. The editor runs a query, a search or a similar. *context* on an
event lists its neighbours within ten minutes, the same actor's (the
corpus's `board.actor` field) or every event. In a chain, ①② in front of
each link of the query say which event of every group it gave; each group
shows what the engine bound its `$variables` to; *Copy finding* puts the
request in Markdown — corpus, query, how many groups, a `curl` that
reruns it against `$PRISMQL_SERVER_URL`, and the request's own board
address, `/board/#q<seq>` — on the clipboard. A request's own
`dictionaries` are kept in the journal with their terms, so *Run again*
and a copied finding replay them.

A client names itself with the header `X-PrismQL-Client: <name>`. The
board's own editor sends `board`. A request without the header shows as its
address, labelled *unnamed client*. Scripts and agents should always send
the header:

```bash
curl -s -X POST localhost:8901/evaluate -H 'content-type: application/json' \
  -H 'X-PrismQL-Client: my-script' \
  -d '{"query": "SELECT contains(signin)", "corpus": "events"}'
```

Every `/evaluate` answer carries `warnings`, a list that is usually empty.
A warning names a query that runs without an error but answers another
question than it seems to ask: a chain of three or more identical links
(one overlapping group per starting event — `RUN` counts runs), one
variable in sibling subqueries (each subquery binds its own), a quantifier
under `AGGREGATE` or `GROUP BY`, or listed with 1,000 groups or more (its
groups are combinations — to count events drop the quantifier). Each has a
`code`, a `message` and a `suggestion`; the board shows them in the
request's inspector, and MCP passes them through.

## 6. Restart and reload

Restarting the process reloads every corpus. Two things differ:

- **Kept results do not survive**: their positions belong to one load.
  Opening an old one on the board says *no longer kept* and offers *Run
  again*.
- **The journal survives only with `enable_file_output = true`.** The server
  then reads `activity.jsonl` back at start and numbers on from its last
  entry. Without file output the board starts empty.

`POST /reload` does the same without a restart. It is available only with
`enable_reload = true`.

## 7. MCP

`prismql-mcp` is a stdio MCP server that forwards to a running
`prismql-server`. Point it with `PRISMQL_SERVER_URL`
(default `http://127.0.0.1:8901`):

```json
{"mcpServers": {"prismql": {"command": "prismql-mcp",
  "env": {"PRISMQL_SERVER_URL": "http://127.0.0.1:8901"}}}}
```

## 8. When something is off

| You see | Likely cause |
|---|---|
| `This query measures time on the field '…', but no event in the corpus has a time there` | `timestamp_field` names a column without times; the message lists the ones that have them (§3) |
| `similar_to()`: no semantic index | no stamped `emb` column and no `[corpora.<name>.semantic] model` |
| `[prismql] … doc_prompt but no query_prompt` at start | the file was embedded with a document prompt only; re-ingest with `--query-prompt` |
| `[semantic].model = … but the corpus was embedded with …` | the config names another model than the file's stamp; drop the config line |
| `emb column ignored on backend …` | the corpus `type` cannot hold a semantic index; use `memory` |
| `is_question()` / `contains_link()`: no backing | an index that stores no documents to annotate; annotate at ingest (`--annotate questions,links`) |
| start takes minutes and memory climbs | vectors plus text index on a large corpus (§4); keep the index on disk with `text_index_path` |
| a `contains()` word inside a link is not found | a link is one token by design; search for the whole link, or for words outside it |
