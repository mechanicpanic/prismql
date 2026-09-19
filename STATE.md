# STATE — what is shipped, decided, and open

*The one place project state lives. Updated in the same commit as the change
it describes. Agent memory points here; it does not duplicate this.*
*Last update: 2026-09-19 (P2 task 2).*

## Shipped (newest first)

| Date | What | Where |
|---|---|---|
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
- **One owner of merge semantics**: every operator implemented once in Python; executor = **Polars plan** over the Arrow corpus table (not Rust kernels). Rust stays for tantivy (text) only; `rust_memory` and its kernels retire after P3. — 2026-09-18
- **Layer 1 contract is Arrow**, not JSON: corpus = ordered Arrow table; ingest = "anything → Arrow" (DuckDB recommended, not required); results = `(group, slot, position, id)` table; `list[list[MessageId]]` stays as the Python-facing view. — 2026-09-18
- **Agent surface**: MCP-tool-returning-JSON is the wrong interface (whole output lands in context); target = skill + scriptable API with table results (code-execution model). MCP shim stays as a thin adapter. Own track, after P3. — 2026-09-18
- **Python floor is 3.12** (from 3.9): Polars needs ≥ 3.10, 3.9 is EOL; CI matrix 3.12/3.13; `[plan]` extra = polars + pyarrow. — 2026-09-19
- `similar_to` threshold required, no default, no top_k; v2 (scores-first ranking algebra) is the paper contribution. — 2026-07-16
- INWINDOW is UNORDERED by definition (language reference); kernels that enforce order are defects. — reaffirmed 2026-09-18

## Open

**Blockers (silent-wrong class)**
- INWINDOW co-occurrence enforces restriction order in both kernels (`from(b), from(a) INWINDOW 3` → empty). Fixed by construction in P3; pinned `xfail(strict)` in `tests/test_positional_path_parity.py`.
- Position is id-arithmetic on Rust, list-index on Python, lexical for string ids; pinned `xfail(strict)` in `tests/test_ordinal_axis_contract.py`. Fixed in P3.
- A chain mixing positional and temporal links can reuse a message (`[[0,0,1]]`); quantifier ranges `{n,}`/`{n,m}` execute as `{n}`. Pinned `xfail(strict)` in `tests/test_engine_defects_pinned.py` (found by the P2 plan review, 2026-09-19). Fixed by construction in P3; range enumeration must be defined first.
- Every result group is sorted by id (`query_visitor.py:490`, `executor.py:381`): with time non-monotone in id order a temporal link returns the later message first (A9, 2026-09-19). Not pinned separately — covered by the plan tests' oracle matrix; P3 removes the sort.

**Next work, in order**
1. **P2** — primitives as a Polars plan: `docs/superpowers/plans/2026-09-18-ordinal-axis-p2-polars.md`, revision 2 after the Astra review. **Tasks 1–2 done**; next: task 3 `extend_link` + `body_span_filter` (null timestamps reject the group), then `anti_link`, `cooccur` (k-way, exhaustive oracle), `quantify` (enumeration, exhaustive oracle), Chicago tier gates (100k → 1m; full tier only with separate authorization), docs.
2. **P3** — single operator layer on the plan; delete both merge paths; expose `!$k` in both dialects; xfails flip.
3. **P4** — gates: Chicago full-tuple equality (Q1–Q3), positional benchmark, relabeled corpora.
4. Tantivy order axis (fast fields) → retire `rust_memory`.
5. Agent surface track; workbench M0–M3; mismatch diary Q04–Q18; `similar_to` v2.

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
