# Text modes, backends and scouting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** one meaning of `contains()` on every backend (stemming by default, refusal instead of substitution), a semantic index that scales, tantivy as a full backend from disk, and ranked full-text / semantic scouting in the server with the same `hydrate` and file output as `/evaluate`.

**Architecture:** the match mode is a corpus property (`text_match`, `text_language`); backends declare what they support and the engine refuses at construction or at first use, never falls back. Tantivy indexes each text field twice (stemmed + plain tokens) so per-dictionary overrides work. Memory stems the vocabulary once (unique tokens), not every occurrence. The scout index is the corpus's own tantivy index when the backend is tantivy, otherwise a lazily built in-process one.

**Tech Stack:** snowballstemmer (core), tantivy custom analyzers, numpy (semantic/ingest extras).

**Spec:** graph `@aleph/prismql` #59 (stemming default), #39 (tantivy axis from disk), #58 (scouting), #31 (demo similar_to), STATE open items.

## Global Constraints
- Silent-wrong is the release blocker: a backend that cannot do a mode raises; no fallback.
- Both dialect references change in the same commit as the surface (`text_match` values, `text_language`, `match = "stem"`).
- `STATE.md` and `CHANGELOG.md` (breaking: default changes) in the same commit.

---

### Task 1: `stem` mode, default, refusal
**Files:** `src/prismql/backends/base.py` (`search_stems`, `supports_match`), `memory.py` (stem index over the vocabulary, `text_language`), `tantivy.py` (custom analyzers per language, `<field>__tok` twin fields, `search_text` raises), `rust_memory.py` (`supports_match`), `engine.py` (`text_match="stem"`, `text_language`, validation, refusal), `visitors/query_visitor.py` (`_search_dictionary` routing), `server/{config,app}.py` (`text_language`, `DictSpec.match` accepts stem, `/schema` reports), `backends/factory.py`; docs: `LANGUAGE_REFERENCE.md`, `PIPE_REFERENCE.md`, `docs/USER-GUIDE.md` §8, `README.md`, `skills/prismql/SKILL.md`; tests: `tests/test_text_match_mode.py` (+stem, +refusal), new `tests/test_text_mode_parity.py` (memory vs tantivy, stem and token, same docs, same sets), demo `verify_examples`.
- [ ] failing tests: stem finds fail/failed/failing, "hi" no longer hits "this"; substring on tantivy refused at engine construction; per-dictionary `match="stem"` on memory; parity memory==tantivy in stem and token modes.
- [ ] implement; `make check`; `uv run python demo/verify_examples.py` against the demo config (mode now stem).
- [ ] commit.

### Task 2: numpy semantic index
`SemanticIndex` keeps an (n, d) float32 matrix; `search` is one matmul; `rank(text, limit)` for scouting; pure-Python path stays when numpy is missing. Test: same sets as before on both paths; timing on Village (381k) noted in STATE.

### Task 3: `similar_to` on tantivy
`semantic_index=` on `TantivyBackend`, `search_semantic` there; server allows `[semantic]` / `emb` for tantivy. Test in `tests/test_semantic.py`.

### Task 4: tantivy axis from disk, configured time fields (#39)
`position` and `<field>_us` fast fields at build; `_open_existing` rebuilds `OrderIndex` from them; `timestamp_fields` threaded to both backends. Tests: order contract on an index opened from disk; DURING on a `time`-named field equal on memory and tantivy.

### Task 5: scouting endpoints (#58)
`POST /search` (`query` in tantivy syntax, `limit`, `corpus`, `hydrate`, `output`) and `POST /similar` (`text`, `limit`, `threshold?`, …); hits `[{id, score[, event]}]`; file mode writes JSONL + preview; scout index per corpus built lazily (tantivy backend reused when present). Skill and AGENT-USE: "scout, then query". Tests in `tests/test_server_app.py`.

### Task 6: Codex adversarial review of the whole series; fix; STATE/CHANGELOG; graph reconcile (#59, #39, #58, #31).
