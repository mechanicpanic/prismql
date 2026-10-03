# START HERE — for a collaborator with a clone

You have access to the repository and you are going to change code in it.
This page is the reading path, the commands, and the honest shape of what
the test suite does and does not prove. Every command below was run before
this page was written, and the numbers are what it printed; the install and
gate numbers come from a tracked-files-only copy of the repo, with no `.git`
and a fresh virtualenv.

*Last update: 2026-09-22 (after P3, the single operator layer).*

## 1. Install, and prove the checkout is sound

The repository is private, so you need an invitation first. Then:

```bash
git clone git@github.com:mechanicpanic/prismql.git && cd prismql
uv sync --extra server --extra repl --extra highlighting --extra tantivy --extra mcp
make check-fast
```

`uv sync` with no extras also works and is enough to run the engine — polars
and pyarrow are core dependencies, not optional. Extras only add surfaces:
`server` (the FastAPI HTTP server), `mcp` (the stdio MCP shim — its own
extra, *not* part of `server`; without it `prismql-mcp` stops at
`ModuleNotFoundError: No module named 'mcp'`), `repl`, `highlighting`,
`tantivy` (real full-text search), `nlp` (spaCy), `semantic`
(sentence-transformers). There is no compiler step and nothing to build.

What you should see:

| command | result on a fresh clone (the line pytest prints) |
|---|---|
| `uv sync` then `make check-fast` | `1278 passed, 70 skipped, 6 deselected` in ~8 s |
| with the extras above | `1353 passed, 62 skipped, 6 deselected` in ~10 s |
| `make check` | the same plus the 6 `slow` tests: `1357 passed, 64 skipped` where the benchmark data is present, four fewer passes and four more skips where it is not (§4) |

Nothing fails and nothing xfails. If anything is red on a clean clone, that
is a real defect, not a known one.

**The skips, counted.** On `make check` with the extras above, the 64 skips
are:

| how many | why |
|---|---|
| 52 | `prismql_rust` is not installed |
| 10 | spaCy, or a trained spaCy model, is not installed |
| 1 | `sentence_transformers` is not installed |
| 1 | debris — see below |

`prismql_rust` is the Rust **search** backend in the sibling repo
`../prismql-rust`. It is deliberately *not* a declared dependency (a path
source would break every fresh clone), so it skips for everyone who has not
built it. To build it into the virtualenv of this project:

```bash
# from the prismql clone
uv pip install maturin
VENV="$PWD/.venv"
( cd ../prismql-rust && PATH="$HOME/.cargo/bin:$PATH" \
    VIRTUAL_ENV="$VENV" "$VENV/bin/maturin" develop --release )
```

Capture `$VENV` before the `cd`: maturin installs into whatever
`VIRTUAL_ENV` points at, and a relative `../prismql/.venv` written after the
`cd` resolves against the *physical* path if either repo is reached through
a symlink. It needs a Rust toolchain; the explicit `PATH` is there for the
case where `cargo` is not already on yours. The build writes only into
`../prismql-rust/target/` and the virtualenv — nothing in this repository
changes. With it installed,
`make check-fast` reports `1406 passed, 11 skipped, 6 deselected` — the 52
skips become passes. The Rust *operator* kernels are gone; P3 deleted them,
and `rust_memory` is a search backend only.

The one debris skip is in `tests/test_quantifier_fix.py` —
`test_backtracking_finds_all_combinations`, skipped with the reason
*"Backtracking algorithm still has limitations — see
QUANTIFIER_BUG_ANALYSIS.md"*. Both things it names are gone: there is no
`QUANTIFIER_BUG_ANALYSIS.md` anywhere in the repo, and P3 deleted the
backtracking merger it blames. The test itself is wrong, not the engine: on
five events it asks `SELECT from(alice), from(bob) INWINDOW 2` and demands
five groups including `[1, 4]`, which are three positions apart and so
outside a window of 2. Today's answer is `[[1, 2], [2, 3], [3, 4], [4, 5]]`
— four groups, correct — and `INWINDOW 3` is what returns `[1, 4]`. Read
this skip as debris to delete, not as a live defect record.

`make check` is the whole gate in one call — ruff format, ruff check, mypy
over `src/prismql`, pytest. CI runs the same target on 3.12 and 3.13. Never
assemble the steps by hand. `make check-fast` is the same minus the `slow`
mark (the Chicago tiers, the million-id universe test, the
sentence-transformer smoke test). `make format` fixes what ruff can.

## 2. Read in this order

| # | File | Why | Time |
|---|---|---|---|
| 1 | `README.md` | what the language is, and one query on your own events | 5 min |
| 2 | `docs/MENTAL_MODEL.md` | the model you need to stop looking things up: two axes, three levels, twelve shapes, a self-test | 30 min |
| 2a | `docs/USER-GUIDE.md`, `docs/AGENT-USE.md` | what a user and an agent are handed. Read them once so you know what you are not allowed to break | 20 min |
| 3 | `PROJECT.md` | the project in one page — five layers, what is where, the numbers | 10 min |
| 4 | `STATE.md` | what is shipped, what is decided, what is open. Read the *Decided* section before proposing anything | 15 min |
| 5 | `ARCHITECTURE.md` | the long read: why each piece is shaped this way, the order axis, Polars as the executor | 1 h |
| 6 | `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` and `docs/superpowers/plans/2026-09-21-ordinal-axis-p3-operator-layer.md` | the design and the execution of the work that produced today's engine; the plan's revision notes record seven defects found in review and why the fixes look the way they do | 1 h |
| 7 | `LANGUAGE_REFERENCE.md` / `PIPE_REFERENCE.md` | the two surface dialects, exhaustively | reference |
| 8 | `AGENTS.md` | how work is done here before you open a PR-sized change | 20 min |

Only the classic reference is packaged inside `prismql`
(`src/prismql/LANGUAGE_REFERENCE.md`; the root `LANGUAGE_REFERENCE.md` is a
symlink to it). `PIPE_REFERENCE.md` is a repository file only, so `GET /reference` and the MCP `prismql://reference` resource serve the classic one
alone.

**P1a, P2, P3, P4** are the phases of one piece of work — making stream
order a real column instead of something inferred from id values. P1a
(2026-09-18) added the order axis and the backend order contract; P2
(2026-09-21) built the sequence primitives as a Polars plan; P3 (2026-09-22)
routed *every* operator on both execution paths through that plan and
deleted what it replaced; P4 is the gate work still open (§7). `STATE.md`'s
*Shipped* table is the definition of each.

### Traps in the older text

These files are stamped `2026-09-19`, before P3 landed on 2026-09-22, and
parts of them describe a world that no longer exists. They are still worth
reading — the reasoning is sound, only the "today" is stale.

- **`ARCHITECTURE.md` §4 ("Python vs Rust — today's split")** describes the
  Rust operator kernels, their Python twins, the backtracking `window.py`
  and the dispatch sites as current. P3 deleted all of them. §9's migration
  timeline is likewise a plan that has since executed. §6–§8 (the order
  axis, Arrow, Polars as the executor) are the parts you actually want and
  they are current.
- **`PROJECT.md`, "Numbers that matter"** still says "Rust kernels 3.4 s",
  "~980 tests" and "pinned `xfail(strict)`". There are ~1,420 tests, no
  `xfail` markers remain, and the Rust kernels are gone. Its five-layer
  table (row 3) *is* current.
- **`STATE.md`'s own header** says *"Last update: 2026-09-19 (P2 task 2)"*
  while the first row of its *Shipped* table is 2026-09-22 P3. The body is
  the current one; the stamp is not. On everything else `STATE.md` is the
  authority — in particular on which defects are open.
- **`docs/MENTAL_MODEL.md`** has three stale spots, all about the pre-P3
  engine: §7 ("what is still a lie today") lists A2/D2/A7/A8/A9/A10 as live
  defects and ends "when the engine and the plan disagree, the plan is
  right" — they are closed and the engine *is* the plan; the variables
  section says `!$u`'s "surface syntax arrives with P3" (it has arrived, in
  both dialects); and self-test answer 1 says D2 "is why it is being
  replaced". Everything else on the page is current, including the twelve
  shapes.
- **`docs/legacy/`** holds what predates all of this — `QUICKSTART.md`,
  `QUICK_REFERENCE.md`, `ROADMAP.md`, `MIGRATION_GUIDE.md`, `PUBLISHING.md`,
  `WHY_NOT_SQL.md`, the July review and the semantic-join brief. History,
  not instructions; its own `README.md` says what each was.

### The rest of the root, and what it is for

Not on the reading path, not history either — reach for these when the
question comes up:

| File | For |
|---|---|
| `CHANGELOG.md` | what changed per release; everything is still under `## Unreleased` |
| `demo/README.md` | how the live demo is wired: two corpora, static frontend, the deploy |
| `docs/CHICAGO_BENCHMARK.md` | the cross-engine comparison. Its timing column predates the operator layer and names a Rust execution path that no longer exists |
| `docs/REPL.md`, `docs/SYNTAX_HIGHLIGHTING.md` | the two surfaces in detail |
| `docs/MENTAL_MODEL.ru.md` | the Russian mental model, kept in step with the English one |
| `docs/legacy/` | the pre-P1 documents, the July 2026 review and the semantic-join brief — see its `README.md`. How the project reaches people who cannot clone it is still the owner's open decision (graph #49 for the agent pack, graph #50 for the human path) |

## 3. What the tests prove

About 1,420 tests. They are not uniform — four different kinds of evidence
live in there, and it is worth knowing which is which.

**Two execution paths, and how much of the suite really sees both.** There
are two executors: the IR executor (`src/prismql/ir/executor.py`,
`use_ir=True`, the default) and the legacy parse-tree visitor
(`src/prismql/visitors/`, `use_ir=False`). `IRExecutor` subclasses
`PrismQLVisitor`, so every shared helper is literally the same code; what
differs is only the front end — lowering to the frozen-dataclass IR versus
walking the ANTLR parse tree. Since P3 both call the same operator layer
(`src/prismql/plan/operators.py`) for every sequence, window, co-occurrence
and quantifier operator, there is exactly one owner of merge semantics.

The honest count: **52 of the 1,421 collected test instances run on both
paths**, in seven files — `test_engine_defects_pinned.py`,
`test_negated_variables.py`, `test_no_universe_cap.py`,
`test_ordinal_axis_contract.py`, `test_p3_review_regressions.py`,
`test_quantifier_ceiling.py`, `test_semantic.py`. Some parametrize `use_ir`
directly, some through a `use_ir` fixture with `params=[True, False]`;
grepping for `parametrize` alone will miss the second form. Everything else
runs on the default IR path only. That is the deliberate shape — the dual
coverage is spent on the semantics that once diverged between the paths —
but if you change anything the two front ends share, do not assume the suite
is watching the visitor for you: parametrize your test.

**Both dialects, one IR.** Classic `SELECT …` and the pipe dialect lower to
the same frozen-dataclass IR, and `tests/test_pipe_dialect.py`
(`TestIREquivalence`) asserts `parse_pipe(pipe) == lower_classic(classic)`
— node-for-node IR equality, not a comparison of results, so a difference
shows up as a structural diff instead of as two queries that happen to agree
on one fixture. Any change to surface syntax has to keep that
green *and* update both reference documents in the same commit.
`tests/test_doc_queries.py` additionally runs every ```` ```prismql ````
block in `README.md`, the reference and several other docs through the real
parser, so a broken example in the docs fails the gate.

**Oracles for the operator layer** — `tests/plan/`:

- `test_primitives_vs_engine.py` compares a primitive against the engine
  only where the engine is a valid oracle (dense ids in load order, no known
  divergence). Where it is not, the oracle is brute force.
- `test_anti_link.py`, `test_chains.py`, `test_cooccur.py`,
  `test_quantify.py`, `test_link_groups.py`, `test_operators.py` each carry
  a brute-force oracle: the answer recomputed by an obviously-correct
  nested loop over the fixture, then compared tuple-for-tuple.
- `conftest.py` builds hostile fixtures on purpose — ties on the timestamp,
  nulls, non-monotone time against load order, duplicate labels.
- `test_chicago_tiers.py` is the real-data gate; see §4.

**Contract tests — the defects that must never come back.** These were
`xfail(strict)` pins while the defects were live; P3 fixed them by
construction and the markers are gone, so they are now ordinary tests:

- `tests/test_ordinal_axis_contract.py` — the audit findings A1–A10 and D2,
  each a query that once ran without error and returned a wrong or empty
  answer. That failure class is the project's release blocker.
- `tests/test_engine_defects_pinned.py` — the same, from the engine side.
- `tests/test_p3_review_regressions.py` — seven defects a cold adversarial
  review found in the P3 branch before merge, one test each, every one run
  on both paths.
- `tests/test_backend_order_contract.py` — a backend with no order axis must
  raise `PositionalUnsupportedError` from `positions` / `sorted_positions` /
  `ids_at` / `timestamps_at`, never reconstruct order from id values. Note
  that this is the *backend's* contract: `engine.execute()` wraps everything
  a query raises, so through the public API the same refusal arrives as
  `PrismQLRuntimeError` with the original as `__cause__` and as
  `details["cause_type"]`.
- `tests/test_positional_path_parity.py` — named for a dual-path divergence
  that no longer exists (its docstring is about Rust kernels versus Python
  builders, both deleted in P3). What it pins today is the semantics that
  divergence was about: `PRECEDED_BY` picks the *nearest* predecessor, plain
  and chained. It builds one default engine and does not compare paths.

**What the suite does not prove.** Coverage is uploaded to Codecov with no
enforced threshold. The live Railway deployment, the LLM evaluation, and
anything at the full-corpus scale are outside it — `AGENTS.md` has a table
naming, per claim, what it is checked against and who can observe it.
There is no remote backend any more (OpenSearch, PostgreSQL and DuckDB were
removed: a database feeds the engine through `prismql ingest`).

## 4. The Chicago tiers

The benchmark corpus is the City of Chicago crime dataset (8,473,715
reports, 2001–2026), cut into three tiers. **The data is not in this repo**
— it lives in the sibling research repository, gitignored and refetchable:
`~/Projects/research/prismql-research/benchmarks/chicago-crime/data/`
(`tier_100k.parquet`, `tier_1m.parquet`, `tier_full.parquet`). Without it
`tests/plan/test_chicago_tiers.py` skips with "Chicago tiers absent", and
that is the normal state for a collaborator who only has this repo.

With the data present:

```bash
uv run pytest tests/plan/test_chicago_tiers.py -q          # 100k, 4 passed, ~1 s
PRISMQL_TIERS=100k,1m uv run pytest tests/plan/test_chicago_tiers.py -q   # 8 passed, ~8 s
```

The tiers check two things at once: tuple-for-tuple equality between the
primitives and the engine, and equality with the match counts the Polars
spike committed independently (100k: 1288 / 4 / 1966; 1m: 20831 / 28 /
30832). The second is the one that matters now that the engine *is* the
plan — without it the comparison would be a mirror.

**The full tier is never run without the owner's word.** It is thermally
expensive on a laptop and is the source of the published 372-match figure;
the runner lives in the research repo, not here.

## 5. Running it by hand

Three surfaces, each run before this page was written:

```bash
# REPL over your own events (see "Try it on your own events" in README.md)
uv run prismql --config prismql.toml

# HTTP server: POST /evaluate, GET /schema, GET /reference, GET /health
# (POST /reload exists but answers 403 unless [server] enable_reload = true)
uv run prismql-server --config demo/prismql.toml      # localhost:8901

# the demo's 13 example queries, engine-side, no server needed
uv run python demo/verify_examples.py                 # prints "failures: 0"
```

`demo/verify_examples.py` is worth reading: for each example it asserts the
classic and pipe spellings lower to the same IR *and* that the query still
returns something, which is how the demo page cannot silently rot.

For letting an agent query a corpus, hand it the folder `skills/prismql/` —
the language reference, how to call the server, and the pitfalls agents
actually hit. Copy it with symlinks resolved, `cp -RL skills/prismql <dest>`:
its `LANGUAGE_REFERENCE.md` is a symlink into the package, and a plain
`cp -R` produces a folder whose reference dangles.

## 6. How the work is recorded — and what you can see

Three places, with a clean split:

- **The repo** holds code, commands, conventions (`AGENTS.md`) and state
  (`STATE.md`, updated in the same commit as the change it describes).
- **Git** holds how it got here. Commit subjects are plain imperative
  sentences, not conventional-commit prefixes. Work lands on `main`; the
  owner pushes; there is no PR flow today.
- **A decision graph** (`@aleph/prismql`) holds the reasoning around the
  code: why something was decided, what was rejected, what question is still
  open, who owns what. **You cannot read it** — it is the owner's tool, not
  a repository artifact.

So: when you meet a comment like `(graph #46)` or `(graph #8)` in the source,
it is a pointer to a recorded decision with a number. The code comment next
to it always explains the *mechanics*; the number stands for the *why* and
the alternatives that were discarded. If you need the why, ask the owner and
quote the number — do not reconstruct it, and do not write a paragraph of
rationale into the code to replace it.

What you get from the repo alone, without the graph: every command, every
convention, the full language semantics, the current state, the full history
of the P3 work in `docs/superpowers/`, and the reasoning behind the two big
architectural moves (`ARCHITECTURE.md` §6–§9). That is enough to write code
here. What you do not get: the ranked list of what to do next beyond
`STATE.md`'s "Next work, in order", and the open questions addressed to the
owner.

Conventions you will hit on the first change:

- Python ≥ 3.12, `X | None` everywhere, ruff is authoritative (line length
  88), zero new mypy errors.
- Stage commits with explicit paths — never `git add -A`; untracked drafts
  live at the repo root.
- Never `--no-verify`, `--force` or a history rewrite.
- A semantics change proves itself with an IR-equality or dual-path test,
  not by eye — and updates `LANGUAGE_REFERENCE.md` and `PIPE_REFERENCE.md`
  in the same commit.
- A construct that runs without error and returns a wrong or empty result is
  a release blocker, not a bug to schedule. Pin it with a failing test
  first.

## 7. What is open

From `STATE.md` (read it there; this is only the shape, and `STATE.md` is
what moves):

0. **P1b, the ingest toolkit** — `src/prismql/ingest/` behind an `[ingest]`
   extra, and a `prismql ingest` CLI that turns a source file into the
   ordered Arrow table the engine can read with no config (position, id,
   time in microseconds, kept fields, optional embedding column). It is also
   the intended answer to the frame cost below, because a backend that
   already holds the table can be sliced by position instead of refetched.
1. **P4 gates** — a positional benchmark query on the full tier, and
   relabeled corpora (gapped numeric ids, non-lexical string ids) run
   against the tiers.
2. **Frame cost** — the operator layer builds a per-link frame by fetching
   the participating documents from the backend on each call. That is the
   known cost of the bridge; it is to be measured on the full tier before
   anyone optimizes it. The recorded risk: the 1m tier answers the
   correlated three-leg query in 0.41 s through the bridge against 0.012 s
   for the same plan run directly.
3. **Start-up cost of the memory backend** on large corpora (Village: 21 s
   building the text index); tantivy with `index_path` keeps its axis on disk
   and starts without a rebuild, so the question is whether memory should
   build its text index lazily or large corpora should simply use tantivy.
4. **The agent surface track**, the annotation workbench, the mismatch
   diary, and `similar_to` v2 (ranking, the second paper's contribution).

Not decided, and not yours to decide: **how the agent pack is delivered to
someone who does not clone the repo** (graph #49) and **how a non-collaborator
gets from a link to their first query — PyPI, a plugin marketplace, published
docs** (graph #50). Both are addressed to the owner. Nothing in this repo is
tagged, released or published; `0.1.0` in `pyproject.toml` is unreleased.
