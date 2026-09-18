# STATE — what is shipped, decided, and open

*The one place project state lives. Updated in the same commit as the change
it describes. Agent memory points here; it does not duplicate this.*
*Last update: 2026-09-19.*

## Shipped (newest first)

| Date | What | Where |
|---|---|---|
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

**Next work, in order**
1. **P2** — primitives as a Polars plan: `docs/superpowers/plans/2026-09-18-ordinal-axis-p2-polars.md`, **revision 2 after the Astra review (NO-GO on the original Task 1; 12 binding amendments)**. Eligibility-before-nearest, `(axis, position)` tie-break, quantifiers as enumeration vs exhaustive oracle, group-preserving contracts, oracle matrix. Includes `!$k`.
2. **P3** — single operator layer on the plan; delete both merge paths; expose `!$k` in both dialects; xfails flip.
3. **P4** — gates: Chicago full-tuple equality (Q1–Q3), positional benchmark, relabeled corpora.
4. Tantivy order axis (fast fields) → retire `rust_memory`.
5. Agent surface track; workbench M0–M3; mismatch diary Q04–Q18; `similar_to` v2.

**Not decided / to verify**
- Novelty claim for the ranked semantic join rests on 2026 preprints (HiMu unverified; VectraFlow verified).
- Railway XFF/X-Real-IP behaviour on the live deploy; Chicago 372 re-run after the DST fixes (done implicitly by the spike: 372 reproduced on both sides).
- swarmchasing hackathon (Oct 3–4, AI Village dataset, gated — access requested? not yet): language is strong for failure-shape questions; needs `!$k`; native ingest is layer 1.

## Where things live

- Code: `~/Projects/vibes/prismql` (this repo), `../prismql-rust` (kernels, retiring), `~/Projects/research/prismql-research` (benchmarks, paper, eval, diary, spike, workbench scope).
- Specs/plans: `docs/superpowers/specs/`, `docs/superpowers/plans/`. Reviews: `REVIEW-*.md`. Handoffs: `HANDOFF-*.md` (untracked, repo root).
- Reading: Obsidian symlink vault `~/Vaults/prismql` (`START.md`).
- Agent memory: `~/.claude/projects/-Users-aleph-Projects-vibes-prismql/memory/` — pointers and non-derivable context only.
