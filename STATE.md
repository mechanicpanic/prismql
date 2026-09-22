# STATE — what is shipped, decided, and open

*The one place project state lives. Updated in the same commit as the change
it describes. Agent memory points here; it does not duplicate this.*
*Last update: 2026-09-22 (P3 complete; documentation packs; ingest toolkit).*

## Shipped (newest first)

| Date | What | Where |
|---|---|---|
| 2026-09-22 | **Ingest toolkit (P1b, stage 1)** — `prismql ingest table SRC DST --id --time [--sort] [--keep] [--embed COL --model M]` `prismql ingest claude-code DIR DST` and `prismql ingest codex DIR DST`: any table, a Claude Code project folder or the Codex sessions folder → Parquet with `position`, `id`, `time` (Arrow `timestamp[us, UTC]`, null when unparseable, reported), kept fields, optional `emb` (`FixedSizeList<float32,d>`, one model pass; the model name is stamped in the Parquet metadata and the server reads the vectors into `SemanticIndex.from_vectors` instead of re-encoding at start, refusing loudly on a model mismatch). Dataset-specific joins stay outside the package (workspace Makefile → one table → `table`); harness-log adapters live in `prismql.ingest.sources` because the format is shared by every user of that harness (graph #54, #56, #57). Checked on this machine: this repo's Claude Code transcripts (14,746 events, engine up in 0.6 s) and every Codex rollout (36,253 events); "tool failed then the same tool retried within 3 events" = 107 and 149 chains. `--embed` end-to-end with a real model is not yet observed (sentence-transformers not installed here) — verified on the Village corpus next. | `src/prismql/ingest/`, plan `docs/superpowers/plans/2026-09-22-ingest-p1b.md` |
| 2026-09-22 | **P3 complete — one operator layer.** Both execution paths run every sequence/window operator through `prismql.plan` (`plan/operators.py` over the P2 primitives, `plan/bridge.py` from the executors' state, `plan/frames.py` per-query frame from the backend's order axis). Deleted: the Python builders, the backtracking window merger, the post-hoc variable validator, the Rust operator kernels (`RustMemoryBackend` stays search-only, graph #51). Audit A1–A10 and D2 closed by construction; every `xfail(strict)` contract passes and its marker is gone. `!$k` in both dialects; `{n,}` needs `quantifier_ceiling` (graph #46); polars/pyarrow core. Real-data check: collusion.wiki three-leg same-label restore 0 → 47 chains. Codex adversarial reviews of the plan and of tasks 2–3 found seven real defects before merge (binding from the wrong member, global slot maximum, key path swallowing a cross-field equality, …), all fixed with regressions. | plan `docs/superpowers/plans/2026-09-21-ordinal-axis-p3-operator-layer.md` |
| 2026-09-21 | **P2 complete**: all sequence primitives as a Polars plan in `prismql.plan` (tasks 3–8: chains with distinctness across axes, anti-links, unordered k-way co-occurrence, quantifier enumeration, `!$k` helper, Chicago 100k/1m gate). Engine divergences recorded: A9 (groups sorted by id), null-timestamp lhs kept by the engine on negative links. | `ad3c8dd`…`2523df4` + this commit |
| 2026-09-21 | **Audit A10** (silent-wrong, both paths): two variables on one leg, or a variable that skips a leg of a chain, fall back to nearest-then-filter, so any other-key event in between empties the result (a single `$k` on a two-leg link is fine); found by running the P2 primitives against HEAD on the collusion.wiki export (3-leg same-label restore: HEAD 0, plan 9). Pinned xfail(strict); the plan primitives are correct by construction; P3 fixes it by routing `$k` links through them. Cold-clone check the same day: `uv sync` on a fresh clone fails on the `../prismql-rust` path source (any group, any flags) — see open items. | `tests/test_ordinal_axis_contract.py`, spec A10 |
| 2026-09-19 | **P2 tasks 1–2**: `prismql.plan` (Arrow-native `corpus_frame`, hostile fixtures) and `nearest_link` — FOLLOWED_BY/PRECEDED_BY as a Polars plan, asof path + candidate path with eligibility inside selection (`!$k` works as a primitive), `(axis, position)` tie-break, proven vs HEAD where valid and vs a brute-force oracle elsewhere. New audit finding A9. `PROJECT.md` rewritten as the full project description. | `7ac4c81`, `526f37e`, `3152246`; plan `docs/superpowers/plans/2026-09-18-ordinal-axis-p2-polars.md` |
| 2026-09-18 | **Ordinal axis P1a**: `OrderIndex`, backend order contract (`positions / sorted_positions / ids_at / timestamps_at / has_order_axis`), `PositionalUnsupportedError`, duplicate ids rejected at load, `load_table()` + `[arrow]` extra (corpus as ordered Arrow table, `position` = row index). Semantics unchanged. | `916d10e`…`2c1b52a`; spec `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` |
| 2026-09-18 | **Polars spike**: relational plan reproduces the engine tuple-for-tuple on Chicago 100k/1m/full incl. the benchmark's 372; 5–80× faster than the Rust kernels, ~65× on build. | `prismql-research/experiments/polars-spike/RESULTS.md` |
| 2026-09-18 | Three silent-wrong fixes: 1M-id universe cap on positional paths and NOT (88% of pairs lost on 8.5M); PRECEDED_BY earliest-vs-nearest divergence; `id_field ≠ "id"` emptied `$k` and temporal results. Pipe-validator holes (#43). Deps upgraded (mcp 2, mypy 2), `prismql-mcp` ported to `MCPServer`. | `7d18c43`, `2b48a7c`, `d2c20f7`, `d732692`, `df71db0` |
| 2026-07-17 | Review 2026-07-12 remediated (4 clusters, 19 defects); mismatch diary started (8/18 questions); workbench scoped; MCP `evaluate` corpus-aware. | `REVIEW-2026-07-12.md`; `prismql-research/use-cases/mismatch-diary/`; `…/docs/development/WORKBENCH_SCOPE.md` |
| 2026-07-16 | `similar_to("text", threshold)` v1 (threshold-to-set) in both dialects; `[semantic]` extra; server `[semantic]` config. | `a02f105`, `139cf84` |
| 2026-07 | IR layer (parse → lower → execute, both paths byte-identical) and the pipe dialect on top; Rust temporal kernels (Chicago 3.8 s / 372). | memory notes `ir_layer`, `chicago_benchmark` |
| 2026-06 | Grammar stratification; correctness cluster #18/#21/#23; tantivy backend; DURING. | `ef6eed8`, `#20` |

## Decided

- **Stream order = load order; ids are labels** (unique; no `order="id"` switch). Loader owns ordering. — 2026-09-18
- **One owner of merge semantics**: every operator implemented once; executor = **Polars plan** over the per-query frame from the order axis. Rust stays for tantivy (text) only; `rust_memory` is search-only, its kernels are gone. — 2026-09-18, done 2026-09-22
- **Layer 1 contract is Arrow**, not JSON: corpus = ordered Arrow table; ingest = "anything → Arrow" (DuckDB recommended, not required); results = `(group, slot, position, id)` table; `list[list[MessageId]]` stays as the Python-facing view. — 2026-09-18
- **Agent surface**: MCP-tool-returning-JSON is the wrong interface (whole output lands in context); target = skill + scriptable API with table results (code-execution model). MCP shim stays as a thin adapter. Own track, after P3. — 2026-09-18
- **Python floor is 3.12** (from 3.9): Polars needs ≥ 3.10, 3.9 is EOL; CI matrix 3.12/3.13; polars + pyarrow are core since P3 (`[plan]`/`[arrow]` empty aliases for one release). — 2026-09-19, 2026-09-22
- `similar_to` threshold required, no default, no top_k; v2 (scores-first ranking algebra) is the paper contribution. — 2026-07-16
- INWINDOW is UNORDERED by definition (language reference); kernels that enforce order are defects. — reaffirmed 2026-09-18

## Open

**Blockers (silent-wrong class)**
- None open. The audit defects A1–A10 and D2 (2026-09-18/21) are closed by the operator layer and stand as ordinary contract tests (`tests/test_ordinal_axis_contract.py`, `tests/test_engine_defects_pinned.py`, `tests/test_positional_path_parity.py`).

**Next work, in order**
0. **P1b ingest toolkit, remaining stages** (plan `docs/superpowers/plans/2026-09-22-ingest-p1b.md`): Village through `table` in the hackathon workspace; `query_frame` from the Arrow table only if the frame cost shows on Village (#14). Then the semantic leg: similarity as `eligible` inside candidate selection, embeddings as a column, no pairwise matrix (graph: the vimarsha on #8; scope before the hackathon is the owner's).
1. **P4 gates** — Chicago full-tuple equality on the tiers is in `tests/plan/test_chicago_tiers.py` (100k/1m via `PRISMQL_TIERS`; full tier on the owner's word); still to add: a positional benchmark query on the full tier, relabeled corpora (gapped numeric, non-lexical strings) on the tiers.
2. **Frame cost** — the per-link frame (`get_documents` of the participating ids per call) is the known cost of the bridge; measure on the full tier before optimizing (risk #14: 1m tier Q2 0.41 s vs the spike's 0.012 s direct).
3. Tantivy order axis from fast fields for indexes opened from disk (today: only when built from documents); remote backends (OpenSearch) need an order contract or stay set-only.
4. Agent surface track; workbench M0–M3; mismatch diary Q04–Q18; `similar_to` v2.

**Not decided / to verify**
- Novelty claim for the ranked semantic join rests on 2026 preprints (HiMu unverified; VectraFlow verified).
- Railway XFF/X-Real-IP behaviour on the live deploy; Chicago 372 re-run after the DST fixes (done implicitly by the spike: 372 reproduced on both sides).
- swarmchasing hackathon (Oct 3–4, AI Village dataset, gated — access requested? not yet): language is strong for failure-shape questions; needs `!$k`; native ingest is layer 1.

## Paper and studies

- **Paper #1 "Same Pattern, Seven Engines"** — DRAFT v0.1 (`prismql-research/papers/prismql-workshop-paper/DRAFT.md`, SKELETON, VENUES, prior-art). Contributions are findings (engine camps, portability traps, counting-unfalsifiable, ground truth); PrismQL is the instrument. Venue: **EDBT 2027 EA&B, deadline 2026-10-07**, 12 pp, single-anonymous, byline Anna Smirnova. To fix before submission: the "Rust kernels = fastest row" claim (now the Polars plan), tied-timestamp figure, BibTeX, page trim.
- **Paper #2 (ranked semantic join)** — prior art verified 2026-07-07: VectraFlow (CIDR'25) is the closest, a windowed threshold join with private code; HiMu was a citation error. Delta open: score algebra through boolean + temporal composition. Not started; competes with #3 for the post-EDBT slot.
- **Paper #3 idea (Aleph, 2026-07-08): agentic TPM** — invert exhaustive temporal-pattern mining into an agent hypothesis → query → instances loop. `prismql-research/papers/agentic-tpm/IDEA.md`.
- **Benchmarks**: Chicago crime (VLDB'23 Fig. 1, 8.47M events: 372 exact; naive SQL DNF; Flink/EQL in the stream-order tie camp; portability findings in the draft), fcc-situations (ground truth: 236 hand-annotated situations, cluster key = (topic, SId); per-situation macro-F1 0.754 vs ML 0.664; disentanglement DURING 600 → pairwise F1 0.795). Both in `prismql-research/benchmarks/`; data gitignored, refetchable.
- **Next study (data located, not started)**: Reuters × WSJ stale-news lag — see `prismql-research/docs/development/NEXT-STUDY-reuters-wsj.md`.
- **Eval re-score (#17)** still owed: the March 2026 LLM eval penalized query forms that are valid again; A/B harness ready, blocked on API keys.

## History and lessons (why things are the way they are)

- **Grammar precedence (2026-06-10, `ef6eed8`)**: ANTLR gives the FIRST alternative of a left-recursive rule the HIGHEST precedence, and only alternatives ending in the recursive ref get left-associativity — the Nov-2025 grammar got both wrong (sequential ops bound tightest, chains nested right). Fix = stratified `restriction` over `bool_restriction`. Lesson: prove precedence with IR-equality tests, not by reading the grammar.
- **UNR dropped (2026-06-11, `c23ae36`)**: the paper said UNR "removes the match-order constraint"; the implementation did a Cartesian product ignoring the window. Kept only as reviewer history.
- **Correctness cluster #18/#21/#23 (2026-06-11)**: positional subqueries group-wise, per-leg variable buckets, teachable errors for unbacked ops — the origin of rule 5 (silent-wrong = blocker).
- **IR layer (2026-07, `52d3abf`)**: `IRExecutor` subclasses the visitor, so both paths are byte-identical by construction; deferred: retire the visitor, static window distribution, static leg buckets. Pipe dialect on top (`a7f085c`).
- **Tantivy (2026-06-15)** locked the search / merge / orchestrate split; **kernels (#25, 2026-07-08)** made Rust the fastest row — superseded by the Polars plan (see Decided).
- **Release plan**: `prismql-research/docs/development/PUBLIC_RELEASE_PLAN.md` is canonical for 0.1.0 (phases, addenda A–C). Remote private; nothing tagged or published.

## Repo standard

iskronify contract 11 applied 2026-09-19: `AGENTS.md` re-projected (cover table, consent node `@aleph/prismql` #23 holds the open authorial slots), `make check` is the single gate and CI calls it, contract-11 hooks in `.claude/settings.json` (start, push, merge, memory-guard), role sub-agents in `.claude/agents/`, gotchas moved to graph nodes #24–#28, the local mypy baseline fixed at the source (0 errors).

## Where things live

- Code: `~/Projects/vibes/prismql` (this repo), `../prismql-rust` (kernels, retiring), `~/Projects/research/prismql-research` (benchmarks, paper, eval, diary, spike, workbench scope).
- Specs/plans: `docs/superpowers/specs/`, `docs/superpowers/plans/`. Reviews: `REVIEW-*.md`. Handoffs: `HANDOFF-*.md` (untracked, repo root).
- Reading: Obsidian symlink vault `~/Vaults/prismql` (`START.md`).
- Owner and machine facts: graph `@aleph/mind`. Open items: Todoist project `prismql`. The local agent memory dir is frozen (evacuated here, into the graphs and AGENTS.md on 2026-09-19).
