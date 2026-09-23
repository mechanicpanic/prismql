# Full-text index as the primary text path — implementation plan

> Executed inline by the session agent (owner's word: not delegated). Steps use checkboxes.

**Goal:** `contains`, phrases, dictionaries and `/search` on a memory corpus are answered by one tantivy index
per corpus that returns sets of positions without reading stored documents; the memory backend stays.

**Decision:** graph `@aleph/prismql` #91 — candidate B of the measured spike (set-oriented tantivy). Direction:
#39 (one tantivy index per corpus for language and scouting), #92 (why memory drifted into the main path).

**Architecture:** (1) `TantivyBackend` stores each event's stream position as a fast field and collects match
sets through `Searcher.fast_field_values`, mapping positions to ids through its order axis — no stored-document
fetch per hit. (2) `MemoryBackend` accepts a `text_index` and routes the text predicates it can honour (stem,
token, phrase) to it; `substring` mode and everything non-textual stay in Python. (3) The server builds that
index for a memory corpus in load order, optionally persisted with a fingerprint of the data it was built from,
and serves `/search` from the same index.

**Tech:** Python 3.12, tantivy-py 0.26.2 (observed: `Searcher.search(query, limit, count, …)`,
`Searcher.fast_field_values(field_name, doc_addresses)` for u64/i64/f64/bool fast fields), polars/pyarrow.

## Global constraints
- Sets must stay identical to the memory backend's on every mode tantivy serves — parity is a test, not a hope
  (`tests/test_text_mode_parity.py` and new tests); a divergence is a release blocker.
- A persisted index must never answer for data it was not built from (silent-wrong): fingerprint or rebuild.
- `make check-fast` green before each commit; commit by path (`git commit -- <paths>`) while other agents share the tree.
- The owner's server on 8931 is never restarted or bound; live checks run on a scratch port.

## Measured baseline (Village, 381,610 events)
memory: word 0.2–5 ms, phrase 0.8–7.3 s, `outreach` 0.96 s, build 21 s. Spike B: word 1.4–43 ms, phrase ≤ 16 ms,
`outreach` 7 ms, 187 MB, open 9 ms. Current `TantivyBackend` (A): word 58–1237 ms (per-hit stored fetch).

---

### Task 1: TantivyBackend collects sets by position

**Files:** `src/prismql/backends/tantivy.py`; tests in `tests/test_tantivy_backend.py`.

- [ ] Failing test: a spy on `Searcher.doc` (or on the backend's stored-fetch helper) proves `search_stems`,
      `search_tokens`, `search_phrase` and `search_by_field` read no stored document; results equal today's.
- [ ] Schema: add `_pos` (`add_integer_field(..., stored=False, indexed=False, fast=True)`), written as the
      event's position in load order (the same counter as the order axis: documents with an id only).
- [ ] `_ids_for`: `search(query, num_docs, count=False)` → addresses → `fast_field_values("_pos", addrs)` →
      `self.order.ids_at(positions)`. Keep `rank_counted` on the same path for its ids.
- [ ] `_SCHEMA_VERSION` 2 → 3; an index of layout 2 is refused on open with the rebuild message (test it).
- [ ] Measure on Village (scratch script): word/phrase/dictionary times close to spike B; record in #91.

### Task 2: MemoryBackend routes text predicates to a text index

**Files:** `src/prismql/backends/memory.py`; new `tests/test_memory_text_index.py`.

- [ ] Failing parity test: for the corpora and queries of `tests/test_text_mode_parity.py` (English, German,
      tricky tokens), `MemoryBackend(docs, text_index=TantivyBackend(docs, …))` returns the same sets as a plain
      `MemoryBackend(docs)` for stem, token, phrase and dictionary queries, on both execution paths.
- [ ] `text_index` ctor parameter; `search_stems` / `search_tokens` / `search_phrase` delegate when it is set
      and the field is a text field; `substring` (`search_text`) stays Python; `supports_match` unchanged.
- [ ] With a text index, skip building the Python token/stem index (the 21 s of Village's start); keep the field
      indexes and question detection. Test that a text-mode query with neither index fails loudly, not empty.
- [ ] `rank`/`rank_counted` delegate too, so the backend itself can answer `/search`.

### Task 3: The server builds one text index per memory corpus

**Files:** `src/prismql/server/config.py` (`build_engine`, `CorpusConfig`), `src/prismql/server/app.py`
(`scout_for`), `docs/USER-GUIDE.md`, tests in `tests/test_server_config.py`, `tests/test_server_app.py`.

- [ ] Config: `[corpora.X] text_index = "tantivy" | "memory"`; default `"tantivy"` when the extra imports,
      else `"memory"`; `/health` and `/schema` say which one a corpus runs. `text_match = "substring"` forces
      `"memory"` (tantivy cannot honour it).
- [ ] Build in load order (`ids_at(range(n))`), not `sorted(ids, key=str)` as the lazy scout does today.
- [ ] Persistence: when `index_path` is set on a memory corpus, the text index lives there with a fingerprint of
      its source (data path, size, mtime_ns, row count, text fields, language, layout version) in its meta; a
      mismatch rebuilds and says so on stdout. Test: change the data file → rebuilt; same file → reopened.
- [ ] `scout_for` returns the corpus's text index when it has one (one index for language and `/search`).
- [ ] Live check on a scratch port with the swarmchasing config copied to the scratchpad: start time, the
      phrase and `contains(outreach)` queries, `/search`, and set equality with a memory-only run.

### Task 4: Close out
- [ ] `STATE.md` shipped row, `CHANGELOG.md`, USER-GUIDE config section; `ARCHITECTURE.md` if it names the
      text path.
- [ ] Graph: #91 answered by what shipped (after the owner's push), #88 and #92 revisited, #14's text share.
- [ ] Cold review (reviewer role, Opus) and a verifier on the claim "phrase and dictionary queries on Village
      answer in milliseconds with the same sets".
