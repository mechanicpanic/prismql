# prismql
Backend-agnostic query language for temporal/sequential pattern retrieval in conversational and event data; Python library + FastAPI server + live demo.

## What this project is
- **Nature**: production (pre-release library, 0.1.0 unreleased; full discipline, no relaxations).
- **NKS realm**: `prismql` — not yet created (NKS server unavailable at bootstrap, 2026-07-12); create + add focus holon on the first NKS-connected session, then update this line.
- **Focus holon**: none yet (see above).
- **Stack**: Python 3.9–3.12 (uv), ANTLR4 parse + hand-written pipe-dialect parser over a shared frozen-dataclass IR; optional Rust kernels (PyO3/maturin, sibling repo); FastAPI server extra.
- **Production statement**: private repo backing a submission-track paper (EDBT'27 EA&B, due 2026-10-07) and a public demo (Railway deploy pending owner go-ahead). Breakage cost = wrong query results silently corrupting benchmark/paper claims; correctness regressions matter more than downtime.

## Persistence rules
Sanctioned deviation from the verstak standard (owner decision, 2026-07-12): the local agent memory dir (`~/.claude/projects/-Users-aleph-Projects-vibes-prismql/memory/`) **remains the cross-session store** for project state (paper status, benchmark results, release rules) — it has survived multi-week access gaps and is load-bearing. Revisit once the NKS realm exists and holds this state.
- **Repo**: code, configs, conventions, code-level gotchas — this file.
- **Memory dir**: paper/venue state, benchmark numbers, release cautions, cross-repo status. Read `MEMORY.md` index at session start.
- **Fetch state; never reconstruct from recall.** No source for a "we decided…"? Read memory or the repo before acting.

## Session lifecycle
- **Start:** read the memory index (`MEMORY.md`), `git status`, and the task board before acting. (Once the NKS realm exists: `nks_orient` on `prismql` first.)
- **Pushing is the owner's move.** Never `git push`, tag, or publish this repo (or PyPI) without explicit per-conversation go-ahead; the owner pushes via `gp`. Committing locally is normal work.
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
| Install (full local dev) | `uv sync --dev --extra server --extra repl --extra highlighting --extra mcp --extra tantivy` |
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
- Sibling repos: `../prismql-rust` (kernels), `~/Projects/research/prismql-research` (benchmarks, paper, eval), `../prismql-mcp`, `Chat-Corpora-Annotator` (original C# — consult for original algorithm semantics).

## Code conventions
- Python 3.9 floor: module-level runtime type aliases use `Union[...]`; `X | None` in annotations is fine (`from __future__ import annotations`).
- Two surface dialects, one IR: any semantics change must keep `parse_pipe(pipe) == lower_query(classic)` equality tests green and both dialect references (`LANGUAGE_REFERENCE.md`, `PIPE_REFERENCE.md`) in sync.
- **Test discipline**: unit + integration (backend matrix); dialect equivalence via node-for-node IR equality; coverage uploaded to Codecov (no enforced threshold).
- **Gotchas**:
  - `INWINDOW` is UNORDERED co-occurrence; `FOLLOWED_BY`/`PRECEDED_BY` are ordered and return complete sequences (`[[lhs, rhs], …]`). Boolean ops need `set`s — AND/OR on a completed sequence result is an error. Canonical: `INWINDOW`/`DURING`; `INWIN`/`WITHIN` deprecated.
  - The final link of a sequential chain must carry a window; one trailing window distributes per link (not whole-chain span). Quantifiers cannot appear inside chains (use explicit chaining).
  - `contains(x)` resolves `x` as a **dictionary name**, not a word; undefined dictionary = validator error.
  - Rust kernels run only for numeric message ids; string ids fall back to Python. Timestamp tie-break differs (rust: ascending id; python: set order) — documented, acceptable.
  - `uv run mypy src/prismql` shows ~11 errors locally in `repl.py`/`tantivy.py` that CI doesn't (optional extras installed locally, absent in CI). Baseline — do not "fix" with ignores; zero NEW errors is the bar.
  - Plain `uv sync` strips extras and drops the suite to ~675 tests — reinstall with the full extras command above.
  - Window merge pairs DISTINCT messages, greedy-forward; a message satisfying two restrictions can't pair with itself (matters when authoring corpora/examples).
  - Demo eval corpora dictionary names collide across test cases — last definition wins in the union (see research repo eval).
- Stage commits with explicit paths only — never `git add -A` (untracked handoffs/scratch live at repo root). Leave `uv.lock` changes uncommitted unless the change is dependency work.

## What to update when
- `AGENTS.md` — commands, structure, conventions, or stack change.
- Memory dir — paper/venue/benchmark/release state changes (until the NKS realm takes over).
- `PIPE_REFERENCE.md` + `LANGUAGE_REFERENCE.md` — any surface-syntax change (both, same commit).

## Git workflow
- Commit subjects: plain imperative sentence (existing house style — not conventional-commit prefixes). Body explains the why when non-obvious.
- Trailer on every commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` (established project convention).
- Work lands on `main` directly; **the owner pushes** (see Session lifecycle). No PR flow.
- Local gate: pre-commit runs ruff format/check + mypy on staged files; CI (push + PR, py 3.9–3.12) enforces format/lint/mypy/tests.
- **Never** `--no-verify`, `--force`, `git reset --hard`, or history rewrites without explicit user instruction.
