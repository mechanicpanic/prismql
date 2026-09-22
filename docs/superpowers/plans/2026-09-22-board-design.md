# The board, by the Claude Design canvas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/board/` becomes the page drawn on the Claude Design canvas: a filter rail, a journal grouped by day, an inspector with each request's real output, an editor, and a full-screen output view (Timeline / Table / Raw JSON). Everything is fed by the server's journal, kept results (`/results`) and `/corpora`.

**Architecture:** No framework and no build step, as today. The canvas component (`docs/superpowers/specs/board-design/Main.dc.html`) is the spec: its `<style>` block is ported as the stylesheet, and its markup and `renderVals()` logic are ported to plain DOM render functions over one state object. Pure logic (statuses, labels, gaps, filters, highlighting) goes in `format.js`, which runs in the browser and under `node --test`. Networking goes in `api.js`. Each UI region is its own file under 150 lines.

**Tech Stack:** HTML/CSS/vanilla JS (ES2020, classic scripts exposing `window.PrismQL*` globals, like `prismql-lexer.js`); node ≥ 18 for the JS unit tests (a pytest wrapper skips them where node is absent); FastAPI server (Python ≥ 3.12).

**Spec:** the design canvas, copied into the repo: `docs/superpowers/specs/board-design/Main.dc.html` (one component, nine scenarios; `canvas.json` names them). The record is graph `@aleph/prismql` #76 (this change), anga to #63 (the board). #73 (group order) is answered in Task 1.

## Global Constraints

- The canvas is the look. Port `.t-dark` / `.t-light` tokens and the component CSS **as they are**. Class names in the port match the canvas's, so a later canvas revision ports 1:1.
- **No fake data.** Every number, label and row comes from the server. A field the server does not send is left out, never invented. The canvas's `timeout` error, "time range, 2026" tile suffix and `NOW0` clock are mock-only.
- Data sources, and only these:
  - `GET /activity?since=&limit=` for backfill.
  - `GET /activity/stream?since=` (SSE) for live updates.
  - `GET /results/{id}?offset=&limit=&hydrate=&fields=` for pages.
  - `GET /results/{id}.jsonl` for downloads.
  - `GET /corpora` for names, the default corpus and board fields.
  - `POST /evaluate` for the editor. It sends header `X-PrismQL-Client: board`.
- Per corpus, the fields shown as an event's kind and actor come from `/corpora` → `board[corpus]` (`{"kind": "...", "actor": "..."}`). The text field is always `text`. If one of the two is unset, show only what is set; never guess a column.
- Statuses of a journal entry:
  - `error` when `ok` is false.
  - `empty` when `ok` and (`total === 0`, or a hits `count === 0`).
  - `capped` when `ok` and `truncated`.
  - `ok` otherwise. Aggregates are `ok`.
- Gap between two consecutive slots of a group: `+<Δt> · <Δpos − 1> events between`. Δt comes from `times` and Δpos from `positions`. If either time is `null`, show only the events part.
- A human's source is `board`. Every other `who` is shown as it arrives. The "agent" tag goes on anything that is not `board` and not an IP address.
- Theme: dark by default. The toggle is remembered in `localStorage`, with every access wrapped in try/catch.
- Files under `src/prismql/server/board/` stay under 150 lines each. The page must work with the server's `static_dir` unset.
- Gate: `make check`. Commit with explicit paths only. Commit trailer per the session's attribution lines. Never push. Never kill processes you did not start, and never bind ports 8901 or 8931.

## File Structure

- Modify `src/prismql/server/app.py`: kept groups are sorted by the position of their first slot (#73); the scouting journal records `threshold`.
- Create `src/prismql/server/board/format.js`: pure helpers (UMD: `window.PrismQLFormat` / `module.exports`).
- Create `src/prismql/server/board/api.js`: fetch/SSE wrappers (`window.PrismQLApi`).
- Rewrite `src/prismql/server/board/index.html`: the canvas skeleton (topbar, rail, journal, inspector, full-view host).
- Rewrite `src/prismql/server/board/board.css`: the canvas `<style>`, ported.
- Create `src/prismql/server/board/journal.js`: the rail and the journal (`window.PrismQLJournal`).
- Create `src/prismql/server/board/inspector.js`: the request pane (`window.PrismQLInspector`).
- Create `src/prismql/server/board/editor.js`: the editor pane (`window.PrismQLEditor`).
- Create `src/prismql/server/board/fullview.js`: the full-screen output (`window.PrismQLFull`).
- Rewrite `src/prismql/server/board/board.js`: state, wiring, keyboard, theme.
- Tests: `tests/board/format.test.mjs` (node), `tests/test_board_js.py` (pytest wrapper), `tests/test_server_app.py` (order, threshold, board assets served).
- Docs: the board section in `docs/USER-GUIDE.md`, and `STATE.md`.

---

### Task 1: The server sends groups in stream order and records the scouting threshold

**Files:**
- Modify: `src/prismql/server/app.py` (where `/evaluate` builds `StoredResult.from_groups`; `_record_scout`)
- Test: `tests/test_server_app.py`

**Interfaces:**
- Produces: kept `groups` / `named` results are ordered by the position of each group's first slot, ascending. Ties keep the engine's order (stable sort). Scouting journal entries gain `"threshold"` (the request's threshold, or `null`; `/search` always `null`).

- [ ] **Step 1: Write the failing tests**

```python
def test_kept_groups_come_in_stream_order(tmp_path):
    # ids whose string order differs from load order: e1, e11, e2 loaded as e2, e11, e1
    docs = [
        {"id": "e2", "user": "u", "text": "spike", "timestamp": 1000},
        {"id": "e11", "user": "u", "text": "spike", "timestamp": 1010},
        {"id": "e1", "user": "u", "text": "spike", "timestamp": 1020},
    ]
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in docs))
    c = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data))))
    body = c.post("/evaluate", json={"query": "SELECT from(u)", "hydrate": False}).json()
    assert [g["positions"][0] for g in body["results"]] == [0, 1, 2]
    assert [g["ids"] for g in body["results"]] == [["e2"], ["e11"], ["e1"]]


def test_similar_journal_records_the_threshold(tmp_path, monkeypatch):
    from prismql.backends import semantic as semantic_module

    class Fake:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts: list[str]) -> list[list[float]]:
            return [[1.0 if "spike" in t else 0.0, 0.1] for t in texts]

    monkeypatch.setattr(semantic_module, "SentenceTransformerEmbedder", Fake)
    data = tmp_path / "e.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    c = TestClient(create_app(ServerConfig(backend_type="memory", data=str(data), semantic_model="fake")))
    c.post("/similar", json={"text": "spike", "threshold": 0.5, "hydrate": False})
    entry = c.get("/activity").json()["entries"][-1]
    assert entry["kind"] == "similar" and entry["threshold"] == 0.5
```

(Reuse the file's `DOCS`. Adjust the fake embedder's shape if `test_similar_ranks_by_cosine` in the same file uses a different one, and keep the two consistent.)

- [ ] **Step 2: Run the tests to see them fail.** `uv run pytest tests/test_server_app.py -k "stream_order or records_the_threshold" -v`. Expected: the first fails on order ([2,1,0] or id order), the second fails with `KeyError: 'threshold'`.

- [ ] **Step 3: Implement.** In `/evaluate`, sort the groups before building the stored result:

```python
                positions = [backend.positions(g) for g in groups]
                order = sorted(range(len(groups)), key=lambda i: positions[i][0] if positions[i] else -1)
                stored = StoredResult.from_groups(
                    kind,
                    req.corpus or config.default_corpus,
                    [positions[i] for i in order],
                    labels,
                    load=load,
                )
```

(Follow the variable names the handler really uses. `sorted` is stable. Only the stored order changes. Every page, the JSONL stream and file output read from the stored result, so they all follow it.) In `_record_scout`, add `"threshold": getattr(req, "threshold", None)`.

- [ ] **Step 4: Run the server suite.** `uv run pytest tests/test_server_app.py tests/test_server_mcp.py -q`. Expected: all pass. If an existing test asserted the old id order, it was asserting the defect #73 names: update it to stream order and say so in the report.

- [ ] **Step 5: Commit** `Server: kept groups come in stream order; the scouting journal records its threshold`.

---

### Task 2: `format.js`, the board's pure logic, under node tests

**Files:**
- Create: `src/prismql/server/board/format.js`
- Create: `tests/board/format.test.mjs`
- Create: `tests/test_board_js.py`

**Interfaces:**
- Produces `PrismQLFormat` with:
  - `status(entry) -> "ok"|"capped"|"empty"|"error"` (rules in Global Constraints)
  - `resultLabel(entry) -> string`. For errors, the error type in words: `"syntax error"`, `"runtime error"`, `"rate limited"`, else the type. For aggregates: `"= <value>"`. For groups and named: `"<total> groups"`, and if capped also `" · capped"`. For hits: `"<total> hits"`, plus `" ≥ <threshold>"` when a threshold is set. File output adds `" → file"`.
  - `rel(seconds) -> "just now"|"N s ago"|"N min ago"|"N h ago"|"N d ago"`
  - `dur(ms) -> "212 ms"|"1.2 s"|"30 s"`
  - `hms(iso) -> "15:41:02"` (local time)
  - `dayLabel(iso, nowMs) -> {key, label, sub}`. `label` is `Today`, `Yesterday` or the weekday; `sub` looks like `Tue 22 Sep`.
  - `gapLabel(prevPos, pos, prevTime, time) -> {plus, label}`. For example `{plus: "+17 min", label: "41 events between"}`; `plus` is `""` when a time is null. Δt is rendered as `s` / `min` / `h` / `d`, rounded down, and a zero gap reads `0 events between`.
  - `span(times) -> "17 min"` (last minus first; `"—"` if none)
  - `isAgent(who) -> boolean`
  - `highlightParts(text, terms) -> [{t, m}]` (case-insensitive, regex-escaped terms)
  - `searchTerms(query) -> string[]`: the quoted phrases plus the bare words of a tantivy query, dropping `AND` / `OR` / `NOT` and `field:` prefixes.
  - `matches(entry, filters, nowMs) -> boolean` and `facetCounts(entries, filters, nowMs, key, values) -> {value: n}`. These are the canvas's `pass()` / `facet()` logic; `filters = {range, search, kinds, srcs, corpora, statuses}`.
  - `lexJson(text) -> [{t, c}]` (ported from the canvas)

- [ ] **Step 1: Write the failing node tests** (`tests/board/format.test.mjs`). Load the file with `createRequire(import.meta.url)("../../src/prismql/server/board/format.js")`. Cover at least:
  - every `status` branch (error, empty by total 0, empty by hits count 0, capped, aggregate ok);
  - `resultLabel` for groups (capped and not), hits with a threshold, aggregate, a syntax error, file output;
  - `gapLabel(57592, 57603, "2025-09-03T19:30:48+00:00", "2025-09-03T19:32:31+00:00")` → `{plus: "+1 min", label: "10 events between"}`, and with a null time → `plus: ""`;
  - `rel` boundaries (9, 10, 59, 60, 3599, 3600, 86400);
  - `dur(212)`, `dur(1234)`, `dur(30000)`;
  - `searchTerms('"verification code" OR password AND text:spike')` → `["verification code", "password", "spike"]`;
  - `highlightParts` with a regex metacharacter in a term;
  - `matches` with each filter kind and the range cut-off;
  - `facetCounts` excluding its own key (the canvas `pass(r, skip)` rule);
  - `isAgent("board") === false`, `isAgent("127.0.0.1") === false`, `isAgent("codex") === true`.

- [ ] **Step 2: Write the pytest wrapper** (`tests/test_board_js.py`):

```python
"""Runs the board's pure-JS unit tests under node (skipped where node is absent)."""

import shutil
import subprocess
from pathlib import Path

import pytest

NODE = shutil.which("node")
TESTS = Path(__file__).parent / "board"


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_board_format_js() -> None:
    proc = subprocess.run(
        [NODE, "--test", str(TESTS / "format.test.mjs")],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
```

Run `uv run pytest tests/test_board_js.py -v`. Expected: FAIL (module not found).

- [ ] **Step 3: Implement `format.js`.** Wrap it as `(function (root) { … const api = {…}; if (typeof module === "object" && module.exports) module.exports = api; else root.PrismQLFormat = api; })(typeof window !== "undefined" ? window : globalThis);`. Port `rel`, `durFmt`, `highlight`, `lexJson` and the filter logic from the canvas script (`Main.dc.html`, lines ≈504–700), adapted to real journal entries (`ts`, `kind`, `who`, `corpus`, `ok`, `result`, `count`, `total`, `truncated`, `value`, `path`, `threshold`, `error`, `elapsed_ms`).

- [ ] **Step 4: Run the tests to see them pass.** `uv run pytest tests/test_board_js.py -v`, then `node --test tests/board/format.test.mjs`.

- [ ] **Step 5: Commit** `Board: the pure logic — statuses, labels, gaps, filters — under node tests`.

---

### Task 3: The shell — skeleton, stylesheet, API client

**Files:**
- Rewrite: `src/prismql/server/board/index.html`, `src/prismql/server/board/board.css`
- Create: `src/prismql/server/board/api.js`
- Modify: `tests/test_server_app.py` (the board-served test)

**Interfaces:**
- `index.html` has the canvas's static skeleton, with these element ids: `#app`, `#topbar`, `#rail`, `#journal`, `#inspector`, `#full`. It loads, in order: `board.css`, `prismql-lexer.js`, `format.js`, `api.js`, `journal.js`, `inspector.js`, `editor.js`, `fullview.js`, `board.js`. The static markup comes from canvas lines ≈253–300 and 330–334: the topbar (logo, live button, search, theme toggle, "New query"), the empty rail sections, the journal head, and the inspector tabs.
- `board.css` is the canvas `<style>` (lines ≈13–249) plus `body{margin:0}` and a full-viewport layout: the canvas's fixed 1440×900 becomes `100vw × 100vh`, keeping `grid-template-columns: 232px minmax(0,1fr) 520px`. Below 1100px wide the rail hides. Drop only the `.sc-interp` selectors.
- `PrismQLApi`:
  - `activity(since) -> Promise<{seq, entries}>`
  - `stream(since, onEntry, onState) -> {close()}` (EventSource; `onState("live"|"down")`; it reconnects from the last seq after 4 s on error)
  - `page(rid, {offset, limit, hydrate, fields}) -> Promise<payload>` (`gone` → resolves with `{gone: true}`)
  - `jsonlUrl(rid, hydrate) -> string`
  - `corpora() -> Promise<{corpora, default, board}>`
  - `evaluate(body) -> Promise<{status, body}>`, sending `X-PrismQL-Client: board`

- [ ] **Step 1: Update the board-served test** (`test_board_page_and_lexer_are_served_from_the_package`). Assert that `/board/` returns HTML containing `id="journal"`, and that each of `format.js`, `api.js`, `journal.js`, `inspector.js`, `editor.js`, `fullview.js`, `board.js`, `board.css` and `prismql-lexer.js` returns 200. Run it: FAIL.
- [ ] **Step 2: Write `index.html`, `board.css` and `api.js`,** plus empty-but-valid stubs for `journal.js`, `inspector.js`, `editor.js` and `fullview.js` (each exposes its global with no-op functions) and a `board.js` that only sets the theme class. Run the test: PASS.
- [ ] **Step 3: Commit** `Board: the canvas shell — skeleton, tokens and components, API client`.

---

### Task 4: The rail and the journal

**Files:**
- Rewrite: `src/prismql/server/board/journal.js`, `src/prismql/server/board/board.js` (state and wiring)

**Interfaces:**
- `board.js` owns `state`:
  ```js
  {
    entries: [], seq: 0, live: true, pending: [], down: false,
    filters: {range: "24h", search: "", kinds: {}, srcs: {}, corpora: {}, statuses: {}},
    sel: null, tab: "details", theme,
    corpora: {names: [], default: null, board: {}},
    full: null,
  }
  ```
  It also owns `render()`, which calls `PrismQLJournal.render(state, actions)`, `PrismQLInspector.render(...)`, `PrismQLEditor.render(...)` and `PrismQLFull.render(...)`.
- `PrismQLJournal.render(state, actions)` draws:
  - the rail: time segments `15m 1h 24h 7d all`; facets for kind, source (sources are the distinct `who` values present, each with an agent tag), corpus and status, each with counts from `PrismQLFormat.facetCounts`; and "Reset all filters";
  - the journal head: a count label, the "N errors" pill, and chips;
  - the list: days, newest first, and rows (canvas markup lines ≈307–318) with the query highlighted by `PrismQLLexer` for `evaluate`;
  - the offline banner, the new-requests pill while paused, and the empty states (canvas "Nothing asked yet" / "No requests match").
- Keyboard: ↑/↓ move the selection in the list; Enter opens the full view.

- [ ] **Step 1:** Implement the backfill: `activity(0)` in a loop until fewer than the limit come back. Then the stream from the last seq. Incoming entries prepend while live and go to `pending` while paused. Mark the freshest row `.fresh`.
- [ ] **Step 2:** Implement the rail and the list exactly per the canvas, fed by real entries. Relative times refresh every 5 s.
- [ ] **Step 3:** Check it by hand against the live server. Start a scratch server on a port above 20000 with the workspace config, or ask the controller to point you at 8931 (read-only). The journal must show real entries with correct statuses. Take one screenshot and put its path in the report.
- [ ] **Step 4:** Run `uv run pytest tests/test_board_js.py tests/test_server_app.py -q` and `make check`. Commit `Board: the rail and the journal, live, with filters and counts`.

---

### Task 5: The inspector — a request and its real output

**Files:**
- Rewrite: `src/prismql/server/board/inspector.js`

**Interfaces:**
- `PrismQLInspector.render(state, actions)`. For the selected entry it draws:
  - the header: kind, status badge, id (`result_id` or `#seq`), and when (absolute and relative);
  - the highlighted query with a copy button;
  - the actions: Full view, Open in editor, Run again, and `.jsonl` (a link to `jsonlUrl(result_id, true)`, only when `result_id` is set);
  - the key/value list: source (with the agent / person-via-board tag), corpus, received, duration, result;
  - the output section, by type:
    - **groups / named:** fetch `page(rid, {offset: 0, limit: 2, hydrate: true, fields: [text, kind field, actor field]})`, then "Show 2 more", which fetches the next page. Draw chains per the canvas (`.chain`, `.ev`, `.gapl`). The group title reads `group N · span <span(times)>`. Gap lines come from `gapLabel` over consecutive slots. Each slot shows the kind and actor fields from `board[corpus]` and the time, plus the text when present. `moreLabel` reads `showing k of total`.
    - **hits:** a page of 3, with scores and bars for `similar` and the `highlightParts(text, searchTerms(query))` marks for `search`.
    - **aggregate:** the big value.
    - **file:** "Written to `<path>`".
    - **error:** the message, plus `line L, column C` when present.
    - **empty:** "No matches — the request ran cleanly and found nothing."
    - **gone** (the page came back `{gone: true}`): "This result is no longer kept (evicted, reloaded or restarted)", with a Run again button.
- Page fetches are cached per `result_id` and offset, so re-renders don't refetch.

- [ ] **Step 1:** Implement it, porting the canvas markup (lines ≈336–397) and `renderVals` detail logic (≈734–764).
- [ ] **Step 2:** Check by hand on the live server. Make sure these all render correctly: a chain query (gaps must read like `+1 min · 10 events between`), a `similar`, a `search` with marks, an aggregate, a syntax error with its position, and an empty result. Screenshots go in the report.
- [ ] **Step 3:** Run the gate, then commit `Board: the inspector draws each request's real output — chains with gaps, hits, values, errors`.

---

### Task 6: The editor

**Files:**
- Rewrite: `src/prismql/server/board/editor.js`

**Interfaces:**
- `PrismQLEditor.render(state, actions)` draws the canvas editor (lines ≈399–418):
  - a highlighted overlay (`pre`) under a transparent `textarea`, highlighted with `PrismQLLexer`;
  - a corpus select filled from `/corpora`;
  - `max groups` (becomes `max_results`) and `with event text` (becomes `hydrate`);
  - Run with ⌘⏎ / Ctrl⏎;
  - a skeleton while running;
  - an inline error with `line:column` from the 422 body;
  - "Your recent queries": the last 5 journal entries whose `who === "board"`, loadable with a click.
- A successful run selects its own journal entry when it arrives: match on `seq` from the stream, or on the query plus `result_id`, and switch to the Request tab.
- "Open in editor" and "Run again" from the inspector load the query and corpus. Run again also runs it.
- "New query" loads `SELECT `.

- [ ] **Step 1:** Implement it. Check by hand: run a query, see it appear in the journal and get selected, and see the output. Run a bad query and see the error position.
- [ ] **Step 2:** Run the gate, then commit `Board: the editor — highlighted, runs as board, errors with their position`.

---

### Task 7: The full-screen output view

**Files:**
- Rewrite: `src/prismql/server/board/fullview.js`

**Interfaces:**
- `PrismQLFull.render(state, actions)`, per the canvas (lines ≈421–499 and 766–859).
- Header: back (Esc), kind, status, when, meta, `k of n` with ←/→ between visible requests, Open in editor, Download `.jsonl`.
- Summary: the query, plus tiles:
  - for groups: `loaded / total groups`, events, distinct actors, and the time range from the loaded times;
  - for hits: `loaded / total hits` (plus `kept` when it is smaller than total), top score or "exact", sources, time range.
- Views:
  - **Timeline** (groups): a nav list of loaded groups on the left; on the right, the selected group's vertical timeline with `.tgap` gaps from `gapLabel`.
  - **Table**, for both groups and hits.
  - **Raw JSON**: the loaded items, one per line, via `lexJson`.
  - **Summary**, for aggregate, error, file and empty results.
- Loading: the view fetches pages of 50 as the nav scrolls, or through a "Load more" button, never more than `total`. Text filtering and actor chips apply to what is loaded, and a note says how many are loaded and how many exist.

- [ ] **Step 1:** Implement it, then check by hand. Open a chain result, move between groups with ↑/↓ and between requests with ←/→, switch to Table and Raw, and press Esc to go back.
- [ ] **Step 2:** Run the gate, then commit `Board: the full view — timeline, table and raw output of any request`.

---

### Task 8: Reality, docs, reviews, graph (controller)

- [ ] **Step 1: Workspace board fields.** In `~/Projects/research/swarmchasing/prismql.toml`, add `[corpora.village.board]` with `kind = "kind"` and `actor = "agent"`. (The owner's workspace: say so in the report; leave wiki and revisions unset unless their columns are obvious from the data.)
- [ ] **Step 2: Live walk-through** on the workspace server (8931, restarted by the controller only if the owner agrees; otherwise a scratch server on a free port with the same config). Use the browser tools to go through the nine canvas scenarios with real data:
  - live dark;
  - light;
  - full view in timeline and in table;
  - a failed request selected;
  - a query running;
  - filters that match nothing;
  - a lost stream (stop the scratch server);
  - an empty journal (a fresh server).

  Take a screenshot of each. **Falsifier:** any number on the page that differs from the same request's `/results` page or journal entry.
- [ ] **Step 3: Docs.** The board section in `docs/USER-GUIDE.md` (what it shows, where the data comes from, `[corpora.X.board]`), plus the `STATE.md` line.
- [ ] **Step 4:** Gate, stage self-review, then a cold review on Opus with graph nodes #76, #63, #64, #67, #68, #71 and #73.
- [ ] **Step 5: Graph.** Answer #73 with Task 1, move #76 to what was delivered, and update the seed #43.
