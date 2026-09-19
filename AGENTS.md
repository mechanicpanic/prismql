# prismql
Backend-agnostic query language for temporal/sequential pattern retrieval in conversational and event data; Python library + FastAPI server + live demo.

## What this project is
- **Nature**: production (pre-release library, 0.1.0 unreleased; full discipline, no relaxations). CI matrix: 3.12, 3.13.
- **NKS realm**: `prismql` (aleph/prismql, r72) — every session starts with `nks_orient` here.
- **Focus holon**: `#1 «🔺 PrismQL engine contour»`.
- **Stack**: Python ≥ 3.12 (uv), ANTLR4 parse + hand-written pipe-dialect parser over a shared frozen-dataclass IR; Polars plan for sequence primitives (P2, `[plan]` extra); Rust kernels (PyO3/maturin, sibling repo) retiring after P3; FastAPI server extra.
- **Production statement**: private repo backing a submission-track paper (EDBT'27 EA&B, due 2026-10-07) and a public demo (Railway deploy pending owner go-ahead). Breakage cost = wrong query results silently corrupting benchmark/paper claims; correctness regressions matter more than downtime.

## Persistence rules
State lives in four places, each with one job; the local agent memory dir is **frozen** (evacuated 2026-09-19; `MEMORY.md` there is a stub that says so — never write to it).
- **Repo** — code, configs, conventions, code-level gotchas: this file. Shipped / decided / open: `STATE.md` (updated in the same commit as the change). Orientation: `PROJECT.md`, `ARCHITECTURE.md`.
- **Graph `@aleph/prismql`** — structure: what each phase consumes/produces, open inquiries and who answers, the paper and benchmark artifacts, transformations. Update it in the session that moves a phase.
- **Owner** — facts about Aleph, their machine and tool surfaces: graph `@aleph/mind` (skill minding); global `~/.claude/CLAUDE.md` for how to work with them.
- **Open items Aleph looks at**: Todoist project `prismql` (`td task list --project prismql`) — flat, plain language, no phase jargon. Reconcile at session end (skill `desk`).
- **Fetch state; never reconstruct from recall.** No source for a "we decided…"? Read `STATE.md`, the graph or git before acting.

## Session lifecycle
- **Start:** `iskron_orient` on `@aleph/prismql` (focus holon #1), `STATE.md`, `git status`, Todoist project `prismql`.
- **Pushing is the owner's move.** Never `git push`, tag, create a GitHub release or upload to PyPI without explicit per-conversation go-ahead; the owner pushes via `gp`. Committing locally is normal work. "Prepare a release" means do the prep and **stop before** any public artifact; a CHANGELOG entry framed as a release is a draft, not authorization. The remote is private — verify with `gh repo view --json isPrivate` if asked.
- **After a green commit run: self-review.** Re-read the diff for bugs, fragile spots, missing tests, god-files; fix in the same series or state plainly that nothing surfaced.

## Working principles
1. **Think before coding.** State assumptions; ask when uncertain — name *what's* unclear. Check repo + memory before writing; fetch, don't recall. Hit the live engine before trusting a doc claim.
2. **Simplicity first.** Minimum code for the task; no speculative abstractions; validate at boundaries, trust internal invariants.
3. **Surgical changes.** Touch only what the task needs; match existing style; ruff is authoritative.
4. **Goal-driven execution.** Bugs: pin with a failing test before patching. Semantics changes: prove with IR-equality or dual-path execution tests, not by eye.
5. **Silent-wrong-results are the enemy.** Any construct that executes without error but returns incorrect/empty results is a release blocker — file it immediately (pattern: tasks #18/#21/#23/#41).

## Commands
| Action | Command |
|---|---|
| Install (full local dev) | `uv sync --dev --extra server --extra repl --extra highlighting --extra mcp --extra tantivy --extra arrow --extra plan` |
| Test | `uv run pytest` (~735 tests; `-m "not slow"` to skip slow) |
| Lint + format | `uv run ruff format . && uv run ruff check . --fix` |
| Typecheck | `uv run mypy src/prismql` |
| Regenerate parser (after grammar edits) | `./scripts/generate_parser.sh` |
| Rebuild Rust backend | `uv sync --reinstall-package prismql-rust` (CI: `uv sync --no-group rust`) |
| Demo server | `uv run prismql-server --config demo/prismql.toml` → localhost:8901 |
| Verify demo examples | `uv run python demo/verify_examples.py` |
| Demo container E2E | `docker build -t prismql-demo . && uv run python demo/e2e_container.py` |

## Project structure
- `src/prismql/grammar/` — ANTLR4 grammar + generated parser (regenerate, never hand-edit; excluded from lint/mypy).
- `src/prismql/ir/` — the IR: `nodes.py` (frozen dataclasses), `lower.py` (only module touching ANTLR contexts), `executor.py` (subclasses the visitor).
- `src/prismql/dialects/pipe.py` — pipe-dialect tokenizer + recursive-descent parser → same IR.
- `src/prismql/visitors/` — legacy parse-tree executor (`use_ir=False`); shared helpers live here, `IRExecutor` inherits them.
- `src/prismql/processors/`, `aggregators/` — window merging, temporal filtering, aggregation.
- `src/prismql/backends/` — memory, rust_memory, tantivy, opensearch, spacy + factory.
- `src/prismql/server/` — FastAPI app (multi-corpus, static mount, rate limit), MCP, config.
- `demo/` — live web demo (web/, data/, prismql.toml, verify/e2e scripts) + legacy Streamlit app.
- `docs/superpowers/` — specs and plans; `PIPE_REFERENCE.md` / `LANGUAGE_REFERENCE.md` at root are the LLM-facing dialect references (symlinked into the research repo's eval).
- Sibling repos: `../prismql-rust` (kernels, retiring after P3), `~/Projects/research/prismql-research` (benchmarks, paper, eval, diary, spike), `../prismql-mcp` (superseded by the `[mcp]` extra), `Chat-Corpora-Annotator` (original 2020 C# — `Infrastructure/Helpers/WindowIndexer.cs`, `Model/Parsers/Macther/`). Naming: the language in the 2022 PANDL paper is **Matcher**; "Macther" is a typo that lives only in code paths — write "Matcher" in prose.
- Reading surface: Obsidian symlink vault `~/Vaults/prismql` (`docs/` dirs are live; new root `*.md` need `sync.sh`).

## Code conventions
- Python ≥ 3.12 (raised from 3.9 on 2026-09-19: Polars needs ≥ 3.10, 3.9 is EOL). Use `X | None` and PEP 604/585 syntax everywhere; `Union[...]` only survives in untouched legacy lines.
- Two surface dialects, one IR: any semantics change must keep `parse_pipe(pipe) == lower_query(classic)` equality tests green and both dialect references (`LANGUAGE_REFERENCE.md`, `PIPE_REFERENCE.md`) in sync.
- **Test discipline**: unit + integration (backend matrix); dialect equivalence via node-for-node IR equality; coverage uploaded to Codecov (no enforced threshold).
- **Gotchas**:
  - Rust toolchain is brew rustup and `cargo` is NOT on PATH — prefix `PATH="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH"`.
  - Heavy benchmark runs (full Chicago tier) only on the owner's word; the laptop is the bench machine — keep a thermal watchdog (`macmon pipe -s 1 | jq .temp.cpu_temp_avg`, stop sustained-parallel work at ≥85 °C).
  - `INWINDOW` is UNORDERED co-occurrence; `FOLLOWED_BY`/`PRECEDED_BY` are ordered and return complete sequences (`[[lhs, rhs], …]`). Boolean ops need `set`s — AND/OR on a completed sequence result is an error. Canonical: `INWINDOW`/`DURING`; `INWIN`/`WITHIN` deprecated.
  - The final link of a sequential chain must carry a window; one trailing window distributes per link (not whole-chain span). Quantifiers cannot appear inside chains (use explicit chaining).
  - `contains(x)` resolves `x` as a **dictionary name**, not a word; undefined dictionary = validator error.
  - **Stream order is the load order** (spec `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md`). Ids are labels and must be unique (duplicates are a load error). Backends expose `positions/sorted_positions/ids_at/timestamps_at/has_order_axis`; backends without an axis raise `PositionalUnsupportedError`. Until P3 lands, positional operators still measure id distance on the Rust path and list index on the Python fallback — pinned as xfail(strict) contract tests; do not "fix" them piecemeal. INWINDOW is documented UNORDERED but both kernels still enforce restriction order (blocker, fixed by design in P3).
  - Rust kernels run only for numeric message ids; string ids fall back to Python (until P3/P4). Timestamp tie-break differs (rust: ascending id; python: set order) until P3.
  - A corpus can be loaded as an ordered Arrow table (`prismql.loaders.load_table`, `[arrow]` extra, `position` = row index); the Polars spike (`prismql-research/experiments/polars-spike/RESULTS.md`) showed a relational plan reproduces the engine tuple-for-tuple incl. Chicago 372 — P2 = Polars plan, Rust stays for tantivy.
  - `uv run mypy src/prismql` shows ~11 errors locally in `repl.py`/`tantivy.py` that CI doesn't (optional extras installed locally, absent in CI). Baseline — do not "fix" with ignores; zero NEW errors is the bar. mypy checks at `python_version = 3.12`, matching the floor.
  - Plain `uv sync` strips extras and drops the suite to ~675 tests — reinstall with the full extras command above.
  - Window merge pairs DISTINCT messages, greedy-forward; a message satisfying two restrictions can't pair with itself (matters when authoring corpora/examples).
  - Demo eval corpora dictionary names collide across test cases — last definition wins in the union (see research repo eval).
- Stage commits with explicit paths only — never `git add -A` (untracked handoffs/scratch live at repo root). `uv.lock` is gitignored in this repo; dependency changes are carried by the constraints in `pyproject.toml`.

## What to update when
- `AGENTS.md` — commands, structure, conventions, or stack change.
- `STATE.md` + graph — paper/venue/benchmark/release state changes.
- `PIPE_REFERENCE.md` + `LANGUAGE_REFERENCE.md` — any surface-syntax change (both, same commit).

## Git workflow
- Commit subjects: plain imperative sentence (existing house style — not conventional-commit prefixes). Body explains the why when non-obvious.
- Trailer on every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` (established project convention).
- Work lands on `main` directly; **the owner pushes** (see Session lifecycle). No PR flow.
- Local gate: pre-commit runs ruff format/check + mypy on staged files; CI (push + PR, py 3.9–3.12) enforces format/lint/mypy/tests.
- **Never** `--no-verify`, `--force`, `git reset --hard`, or history rewrites without explicit user instruction.
