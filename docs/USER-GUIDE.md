# PrismQL for your own events — from a link to the first query

For someone who has a file of events and a question about their order. You
do not need to read the source, the project state, or anything about how the
engine works. Everything below was run on the six-line file in section 2 —
twice: once against this repository's working tree, and once against the
build the install commands in section 1 actually give you. The outputs are
copied from those runs, and section 1 names the one place where the two
builds disagree.

If you want the model behind the language rather than the recipe, read
`MENTAL_MODEL.md` after this page.

---

## 1. Install

PrismQL is **not on PyPI**: `pip install prismql` does not work yet. The
repository is private, so all three routes below need access to it (an
invitation from the owner and an SSH key on GitHub).

**A. As a tool, no clone, no virtualenv.** This is the shortest path.

```bash
uv tool install "prismql[repl,server] @ git+ssh://git@github.com/mechanicpanic/prismql"
```

You get three commands on your PATH: `prismql` (the REPL), `prismql-server`
(HTTP), `prismql-mcp`. Add `,highlighting` to the extras for colour in the
REPL. This installs whatever is on `main` on GitHub at that moment; re-run
with `--force` to update.

**B. From a clone**, if you also want the examples and the references at
hand:

```bash
git clone git@github.com:mechanicpanic/prismql.git && cd prismql
uv sync --extra repl --extra server --extra highlighting
uv run prismql --config /path/to/your/prismql.toml
```

**C. Into a virtualenv you own**, if PrismQL is one library among others in
your own project:

```bash
uv venv
uv pip install "prismql[repl,server] @ git+ssh://git@github.com/mechanicpanic/prismql"
```

Nothing here edits the repository, and nothing needs a Rust toolchain: the
query engine is Python plus Polars, both installed for you.

### Which build you get, and the one thing that differs

All three routes take GitHub `main` as it stands at that moment. As of
**2026-09-22** the owner's working tree is a few commits ahead of that, and
one construct on this page lives only in the newer tree:

- **`!$k`** — "a different value from the bound `$k`" (section 5, pitfall 4).
  On the GitHub `main` build it is not in the grammar at all, so you get
  `Syntax Error: Syntax error: token recognition error at: '!'` instead of
  an answer.

Everything else on this page — every query, every error message, the server
responses — was run on both builds and came back identical.

To find out which build you have, run one query:

```
prismql[1]> SELECT field(user, $u) FOLLOWED_BY field(user, !$u) INWINDOW 2
```

Groups back: you have the newer build. `token recognition error at: '!'`:
you have GitHub `main`, and everything on this page except that one
construct still holds.

(The same gap is why a fresh clone may not carry this page yet: it is in the
working tree until the owner pushes. If you were handed this file rather
than finding it in `docs/`, that is why.)

---

## 2. Your data: one file, an id and a time

One event per record. Four formats are read directly: `.jsonl`, `.json` (a
single array), `.csv`, `.parquet`. The file used throughout this page is
`events.jsonl`:

```jsonl
{"id": "e1", "time": "2026-06-18T18:24:12Z", "user": "alice", "kind": "login",  "page": "P1", "text": "session opened"}
{"id": "e2", "time": "2026-06-18T18:24:31Z", "user": "alice", "kind": "delete", "page": "P1", "text": "removed the paragraph"}
{"id": "e3", "time": "2026-06-18T18:25:56Z", "user": "bob",   "kind": "save",   "page": "P1", "text": "restored the paragraph"}
{"id": "e4", "time": "2026-06-18T19:02:10Z", "user": "carol", "kind": "delete", "page": "P2", "text": "removed a table"}
{"id": "e5", "time": "2026-06-18T19:04:44Z", "user": "carol", "kind": "save",   "page": "P2", "text": "put the table back"}
{"id": "e6", "time": "2026-06-18T21:40:00Z", "user": "dave",  "kind": "delete", "page": "P3", "text": "removed an image"}
```

Four things decide whether your file will work:

- **`id` must be unique.** It is a label, not a coordinate — strings are
  fine, gaps are fine, it does not have to be sorted.
- **Order is file order.** Row 1 is position 1. If your records are not
  already in the order you want to reason about, sort the file before
  loading; the engine will not sort it for you.
- **One timestamp field**, named however you like (`time` here). It is what
  time windows are measured on. Without it you can still ask positional
  questions.
- **Everything else is queryable as it is** — `field(kind, delete)`,
  `field(page, P1)`. The field called `text` is the one the text predicates
  (`contains`, `contains_phrase`) search.

A CSV needs the same columns and a header row; a Parquet file and a JSON
array the same columns. All four were loaded from the same six records and
answered the section 5 queries identically.

### When the file is not in that shape: `prismql ingest`

If the table has the right rows but the wrong order, an odd timestamp
format, or twenty columns you do not need, let the ingest command write the
stream for you instead of editing the file by hand:

```
$ uv run prismql ingest table export.csv events.parquet --id rev_id --time created --sort created --keep user,kind,page,text
events.parquet: 6 rows, 2026-06-18 18:24:12+00:00 … 2026-06-18 21:40:00+00:00
  columns: position, id, time, user, kind, page, text
```

It sorts, renames the id and time columns to `id` and `time`, parses the
timestamps (ISO strings, `YYYY-MM-DD HH:MM:SS` without a zone, date-only
strings, epoch seconds / milliseconds / microseconds / nanoseconds told
apart by magnitude — all become UTC; anything unparseable stays as a null
and is counted in the summary; `--time-unit ms` states the unit when the
guess would be wrong, e.g. milliseconds before 1973), and keeps only what
you asked for.
Point the config at `events.parquet`, `timestamp_field = "time"`, done.

Add `--embed text --model all-MiniLM-L6-v2` (extra `ingest`) and the file
also carries one embedding per row; the server then answers
`similar_to("…", 0.7)` without encoding the corpus at start, and it knows
which model to encode the query with because the file says so.

The same command reads a Claude Code project's transcripts —
`prismql ingest claude-code ~/.claude/projects/<your-project> sessions.parquet`
— one event per prompt, thought, tool call and tool result, with `kind`,
`tool`, `error`, `session` and `model` fields (`error` is true only where the
harness itself reports a failure: `is_error` in Claude Code, a non-zero exit
of the exec tool in Codex); the questions in section 5 work on it unchanged ("a tool failed, then the same tool was retried within
three events"). `prismql ingest codex ~/.codex/sessions sessions.parquet`
does the same for Codex CLI rollouts, with the same columns, so one query
runs over both harnesses.

---

## 3. The config file

Everything the engine needs lives in one `prismql.toml` next to your data:

```toml
[backend]
type = "memory"              # in-process, fine up to ~100K events
data = "events.jsonl"        # .jsonl / .json / .csv / .parquet
timestamp_fields = ["time"]  # parsed into real timestamps on load

[engine]
timestamp_field = "time"     # the axis DURING measures on

[dictionaries]
removal = ["removed"]        # named word lists; see contains() below
```

**Both timestamp keys are needed, and they are not the same key.**
`[backend].timestamp_fields` says which columns to parse; `[engine].timestamp_field`
says which parsed column time windows use. With the first and without the
second, a `DURING` query returns **no results and no error** — verified:
the identical `INWINDOW` query still answers. If a time query comes back
empty, check this first.

Relative paths inside the file resolve against the file's own directory, so
you can keep config and data together and point at them from anywhere.

---

## 4. The first query

```
$ prismql --config prismql.toml
```

(from a clone: `uv run prismql --config prismql.toml`)

```
PrismQL Interactive REPL
Type \help for help, \schema to inspect the corpus, \quit to exit
Loaded: 6 documents via MemoryBackend from events.jsonl · 1 dictionary
Features: history

prismql[0]> \schema
Corpus: 6 documents (sampled 6) · backend MemoryBackend
  data: events.jsonl
  id_field: id · timestamp_field: time · text_match: substring

Fields:
  id    str     100.0%
  kind  str     100.0%  e.g. delete, login, save
  page  str     100.0%  e.g. P1, P2, P3
  text  str     100.0%
  time  str     100.0%
  user  str     100.0%  e.g. alice, bob, carol, dave

Dictionaries:
  removal (1 term)
```

`Features:` lists what your extras bought: `history` for `[repl]`,
`history, syntax highlighting` when `highlighting` is installed too. Every
query also prints a timing line — `(Query executed in 0.003s)` — after its
groups; the transcripts below leave it out.

`\schema` first, always: it prints the field names and real example values,
so you write `field(kind, delete)` instead of guessing. `\quit` exits.
`\help` lists the commands, but its example queries come from the chat
corpus this project started on (`from(alice)`, `is_question()`, …) — they
will match nothing in a file of your own fields. Take the examples from this
page and the field names from `\schema`.

The REPL is built for a person at a terminal. Piping queries into it works
(`printf 'SELECT ...\n\\quit\n' | prismql --config prismql.toml`) but warns
that input is not a terminal and echoes your lines back; for anything
scripted use the server in section 7 instead.

---

## 5. The three questions

Almost every investigation is one of three shapes. Learn these and the rest
of the language is detail.

### "Then" — one thing after another

```
prismql[1]> SELECT field(kind, delete) FOLLOWED_BY field(kind, save) DURING 10 minutes
Found 2 result(s):

  Group 1:
    [e2] alice: removed the paragraph
    [e3] bob: restored the paragraph
  Group 2:
    [e4] carol: removed a table
    [e5] carol: put the table back
```

A deletion, then a save within ten minutes. `e6` is missing because nothing
saved after it. Each `delete` takes its **nearest** eligible `save`; a save
is not used up and may answer for several deletions.

Swap the window for `INWINDOW 3` to count in events instead of minutes.
Positional windows survive missing or coarse timestamps; time windows
survive bursts. `PRECEDED_BY` asks the same question backwards.

### "Near" — two things close together, either order

```
prismql[2]> SELECT field(kind, delete), field(kind, save) INWINDOW 2
Found 4 result(s):

  Group 1:
    [e2] alice: removed the paragraph
    [e3] bob: restored the paragraph
  Group 2:
    [e3] bob: restored the paragraph
    [e4] carol: removed a table
  Group 3:
    [e4] carol: removed a table
    [e5] carol: put the table back
  Group 4:
    [e5] carol: put the table back
    [e6] dave: removed an image
```

The comma is co-occurrence, and it is **unordered**: group 2 is a save with
a delete after it, which `FOLLOWED_BY` would never return. Use the comma
when you mean "these things happen around each other" and the arrow when
the order is the point. More than two members is allowed
(`A, B, C INWINDOW 5` — all pairwise within 5, all distinct).

### "Same entity" — the same page, the same user, twice

Write `$name` where you would otherwise repeat a value. It binds on the
first leg that mentions it and must match on every later leg:

```
prismql[3]> SELECT field(kind, delete) AND field(page, $p) FOLLOWED_BY field(kind, save) AND field(page, $p) DURING 10 minutes
Found 2 result(s):

  Group 1:
    [e2] alice: removed the paragraph
    [e3] bob: restored the paragraph
  Group 2:
    [e4] carol: removed a table
    [e5] carol: put the table back
```

"Something was deleted on a page and *that same page* was saved within ten
minutes." Several variables can run side by side (`field(page,$p) AND field(user,$u)`).

`!$u` is the opposite: a **different** value from the one already bound.
**This one needs a build newer than GitHub `main`** — see section 1; on the
`main` build the `!` is a syntax error.

```
prismql[4]> SELECT field(user, $u) FOLLOWED_BY field(user, !$u) INWINDOW 2
Found 5 result(s):

  Group 1:
    [e1] alice: session opened
    [e3] bob: restored the paragraph
  Group 2:
    [e2] alice: removed the paragraph
    [e3] bob: restored the paragraph
  Group 3:
    [e3] bob: restored the paragraph
    [e4] carol: removed a table
  Group 4:
    [e4] carol: removed a table
    [e6] dave: removed an image
  Group 5:
    [e5] carol: put the table back
    [e6] dave: removed an image
```

"Someone acts, then somebody else acts within two events." Note that
`!$u` only means anything once `$u` is bound by an earlier leg — on its own
it is an error (see the pitfalls).

### And the fourth question, which is really the first one negated

```
prismql[5]> SELECT field(kind, delete) NOT_FOLLOWED_BY field(kind, save) DURING 10 minutes
Found 1 result(s):

  Group 1:
    [e6] dave: removed an image
```

Deletions nobody undid. The group holds only the deletion: the event that
did *not* happen is not in the answer, which is also why the excluded side
cannot carry a variable.

---

## 6. Reading what comes back

A result is a list of **groups**, and a group is the actual events, in
stream order, one per slot of the pattern — never a count, never a summary.
That is the whole point: you can open every match and look at it.

Two things worth knowing:

- **`AGGREGATE count()`** turns the answer into a single number over every
  group, uncapped: `SELECT ... INWINDOW 3 AGGREGATE count()` → `Aggregated
  result: 2`. It is the honest way to a total, because listings are capped
  (the HTTP server sends at most `[server] max_results` groups, 50 by
  default, and says `"truncated": true` when it cut).
- **`GROUP BY`** splits that count: `SELECT field(kind, delete) GROUP BY user
  AGGREGATE count()` → `alice: 1`, `carol: 1`, `dave: 1`. Fields and time
  buckets (`day(time)`, `hour(time)`) both work.

**`AS "name"` is narrower than it looks.** It attaches to members of the
comma form only, and the quotes are required:

```
prismql[6]> SELECT field(kind, delete) AS "del", field(kind, save) AS "undo" INWINDOW 2
Found 4 result(s):

  Group 1:
    del: [e2] alice: removed the paragraph
    undo: [e3] bob: restored the paragraph
  ...
```

On a chain it does not parse at all — `field(kind, delete) AS "del"
FOLLOWED_BY ...` gives *"mismatched input 'FOLLOWED_BY' expecting `<EOF>`"*,
and `AS del` without quotes gives *"mismatched input 'del' expecting
QUOTED_STRING"*. And the names are handed out **by position**: the group
prints in stream order and takes your names in the order you wrote them, so
on an unordered comma set the name can land on the other event —
`field(kind, save) AS "the save", field(kind, login) AS "the login"
INWINDOW 3` prints `the save:` in front of the login. Read the ids; treat
the names as slot numbers with words on them.

---

## 7. Out of the REPL: the server

When something other than you is asking — a script, a notebook, an agent —
run the same config as an HTTP server instead:

```bash
prismql-server --config prismql.toml     # http://127.0.0.1:8901
```

```bash
curl -s localhost:8901/health
# {"status":"ok","backend":"MemoryBackend","documents":6,"loaded_at":"..."}

curl -s -X POST localhost:8901/evaluate -H 'Content-Type: application/json' \
  -d '{"query":"SELECT field(kind, delete) FOLLOWED_BY field(kind, save) DURING 10 minutes","max_results":5}'
# {"kind":"groups","count":2,"truncated":false,"results":[{"ids":["e2","e3"],"events":[{...full records...}]}, ...]}
```

`GET /schema` is `\schema` as JSON. A bad query comes back as a 422 whose
body says what to fix — `{"ok":false,"error":{"type":"syntax","message":"...","line":1,"column":27}}` —
rather than as an empty list. `AGGREGATE count()` answers as
`{"kind":"aggregate","function":"count","field":null,"value":2, ...}`. You
can also pass word lists per request — `"dictionaries": {"undo": ["restored","back"]}` — which
is the fast way to try a vocabulary before writing it into the config.

Two more endpoints are for looking around, not for asking: `POST /search`
with `{"query": "restored OR \"put back\""}` returns the best-matching
events ranked (full-text, tantivy syntax), and `POST /similar` with
`{"text": "someone undid a deletion"}` returns the nearest events by
embedding when the corpus carries one. Read a few hits, learn the words,
put them in a dictionary, then ask the real question with `/evaluate`.

If you want an agent to drive this, hand it the folder `skills/prismql/`
from a clone: it is self-contained (how to call the server, the language
reference, the traps) and needs no Python on the agent's side.

---

## 8. Naming words: dictionaries

`contains(removal)` does not search for the word "removal". It takes the
**name** of a dictionary — a list of terms you define in the config (or per
request) — and matches any of them against the `text` field:

```toml
[dictionaries]
removal = ["removed", "deleted", "took down"]
```

This is deliberate. The interesting part of most questions is the
vocabulary, and putting it in one named place means you can revise the
question by revising the list instead of rewriting queries. For a single
literal string use `contains_phrase("exact phrase")`.

Single words match **stemmed whole words** by default: `removed` finds
"removed", "remove", "removing", and `hi` does not find "this". The stemmer's
language is the corpus's `text_language` (`english` unless you set it;
`german`, `russian`, … work the same way on both backends). Two other modes
exist and are chosen explicitly, per corpus (`text_match`) or per dictionary
(`match`): `token` (whole words, no stemming) and `substring` (`ERR` finds
`ERR_TIMEOUT`, and `hi` finds `this` — right for logs and identifiers, wrong
for prose). Multi-word entries always match as a phrase, in that order.

Text matching here has no ranking and no scores: a set of events in, a set
of events out. (With the `semantic` extra installed and a model configured,
`similar_to("...", 0.7)` adds an embedding-threshold predicate — still a
set, not a ranking. Nothing on this page exercises it.)

---

## 9. Is the pattern real? The null twin

A query that returns 47 chains is not yet a finding. Busy entities produce
sequences by being busy: if one user edits constantly, "user deletes, then
the same user saves" will fire often with no coordination behind it. The
cheap check is a **null twin** — build a copy of your data with the
timestamps (or the order) shuffled *within* each entity, so every entity
keeps its own activity level and loses only the alignment between entities;
run the identical query against it a couple of hundred times; and compare
your real count with that distribution. If the real number sits inside the
shuffled 95th percentile, what you found is the activity level, not the
pattern — and that is a result worth recording. Nothing in the library does
this for you; it is a loop over shuffled copies of your file, and it is the
difference between a query result and a claim.

---

## 10. Pitfalls, with the exact message you will see

The REPL prefixes these with `Runtime Error: Error executing query:` or
`Syntax Error:`; quoted below is the message itself, in full.

1. **The last link of a chain must carry a window.** One trailing window
   covers every windowless link before it.
   `SELECT field(kind, delete) FOLLOWED_BY field(kind, save) INWINDOW 2
   FOLLOWED_BY field(kind, login)` →
   *"Sequential chain is missing a window constraint on its final link. Add
   `INWINDOW <n>` or `DURING <time>` at the end of the chain — a trailing
   window applies to every windowless link."*
2. **`contains(x)` wants a dictionary name, not a word.**
   `SELECT contains(deleted)` → *"Dictionary 'deleted' not found"*. Define
   it in `[dictionaries]`, or use `contains_phrase("deleted")`.
3. **`{n,}` needs a ceiling.** An open range has nothing to enumerate to.
   `SELECT field(kind, delete){2,} INWINDOW 5` → *"{2,} has no upper bound and no
   quantifier_ceiling is configured. Write {2,m} with an explicit upper
   bound, or set quantifier_ceiling (engine argument; [engine]
   quantifier_ceiling in prismql.toml) to close every open range at m."*
4. **`!$k` needs a `$k` bound on an earlier leg.**
   `SELECT field(user, !$u)` → *"!$u refers to a variable no earlier leg
   binds"*. Bind it first: `field(user,$u) FOLLOWED_BY field(user,!$u)`.
   On the GitHub `main` build (section 1) you get
   *"token recognition error at: '!'"* instead, for any use of `!$k`.
5. **A backend without an order axis says so.** `memory`, `rust_memory` and
   a tantivy index built by this version carry one (tantivy keeps it on disk
   next to the index). A tantivy index built by an older version does not,
   and is refused on open with rebuild instructions; filters would still
   work, order would not. *"TantivyBackend has no stream-order axis: positional
   (INWINDOW, FOLLOWED_BY, ...) and temporal-sequence operators cannot run
   on it. Use a backend with an OrderIndex (memory, rust_memory) or load the
   corpus with a persisted position column."* For sequence questions use
   `memory`, or let tantivy rebuild the index from the data file.
6. **A time query that returns nothing** — check `[engine].timestamp_field`
   (section 3) before suspecting your data.
7. **Booleans join filters, not patterns.** `AND`, `OR`, `NOT` combine
   conditions on a single event. Once you have groups there is nothing left
   to intersect, so `SELECT field(kind, delete), field(kind, save) INWINDOW 5
   AND field(page, P1)` →
   *"Syntax error: mismatched input 'AND' expecting `<EOF>`"*. Put the
   condition on one of the legs instead.

---

## 11. Where to go next

- **`MENTAL_MODEL.md`** (`MENTAL_MODEL.ru.md` in Russian) — the model behind
  the syntax in one sitting, with a self-test. Read it once and you will
  stop looking things up. If its section 7 still lists engine defects as
  true "until P3 lands", that section predates the current operator layer:
  those defects are closed in the build this page describes.
- **`../LANGUAGE_REFERENCE.md`** — every operator of the `SELECT` dialect
  used on this page.
- **`../PIPE_REFERENCE.md`** — the same language in a shorter, pipe-shaped
  syntax: `field(kind,delete) ~>(10m) field(kind,save)` returns exactly the
  two groups of section 5. Both dialects are accepted everywhere, including
  the REPL and the server; the REPL tells them apart by the leading
  `SELECT`.
- **`REPL.md`** — the REPL's own commands in full.
- **`../skills/prismql/`** — the folder to hand an agent.

*Where this documentation will finally live — a package on PyPI, a
published site, an installable agent skill — is the owner's call and is
open (graph `@aleph/prismql`, #49 agent delivery, #50 the human path).*
