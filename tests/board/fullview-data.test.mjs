// Pins fix round 1's #1 (the "actors"/"sources" tile counts the SAME list
// the chips show, never a wider all-events count) and #2 (no invented
// tiles/numbers while nothing is loaded or the body shows a blocker — a
// gone result renders no tiles and the canvas's "result no longer kept"
// note, never a fabricated "0.000 top score"). Fake window + a minimal
// fake DOM (goneBlock/mk touch `document`), same fake-window pattern as
// inspector-fetch.test.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const FETCH_PATH = require.resolve("../../src/prismql/server/board/inspector-fetch.js");
const LOAD_PATH = require.resolve("../../src/prismql/server/board/fullview-load.js");
const ROWSCTX_PATH = require.resolve("../../src/prismql/server/board/fullview-rows-context.js");
const DATA_PATH = require.resolve("../../src/prismql/server/board/fullview-data.js");
const BoardUtil = require("../../src/prismql/server/board/board-util.js");
const PageLogic = require("../../src/prismql/server/board/inspector-page-logic.js");
const FullLogic = require("../../src/prismql/server/board/fullview-logic.js");
const FullNav = require("../../src/prismql/server/board/fullview-nav-logic.js");
const Format = require("../../src/prismql/server/board/format.js");
const EditorLogic = require("../../src/prismql/server/board/editor-logic.js");

// dispatch() lets a test fire the click a real goneBlock button wired via
// addEventListener; emptyBlock's stub actually appends `opts.action` (the
// real goneBlock passes its "Run again" button there) so it's reachable.
function fakeEl() {
  var listeners = {};
  return {
    children: [], style: {}, textContent: "", className: "",
    appendChild(c) { this.children.push(c); return c; },
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    dispatch(type) { (listeners[type] || []).forEach(function (fn) { fn({}); }); },
    setAttribute() {},
  };
}
function fakeEmptyBlock(title, detail, opts) {
  var el = fakeEl();
  if (opts && opts.action) el.appendChild(opts.action);
  return el;
}

function freshModules(pageImpl) {
  globalThis.document = { createElement: () => fakeEl() };
  globalThis.window = {
    PrismQLBoardUtil: BoardUtil,
    PrismQLInspectorUI: { emptyBlock: fakeEmptyBlock, ICON_FULL: "" },
    PrismQLInspectorPageLogic: PageLogic,
    PrismQLFullLogic: FullLogic,
    PrismQLFullNav: FullNav,
    PrismQLFormat: Format,
    PrismQLEditorLogic: EditorLogic,
    PrismQLApi: { page: pageImpl },
    PrismQLBoard: { render: function () {} },
  };
  delete require.cache[FETCH_PATH];
  delete require.cache[DATA_PATH];
  delete require.cache[LOAD_PATH];
  delete require.cache[ROWSCTX_PATH];
  const PF = require(FETCH_PATH);
  globalThis.window.PrismQLInspectorFetch = PF;
  const Data = require(DATA_PATH);
  return Data;
}

function flush() {
  return new Promise((resolve) => setImmediate(resolve));
}

const board = { kind: "kind", actor: "agent" };
const actions = {};
const vs = () => Object.assign({ q: "", agents: {}, group: 0 }, FullNav.initial(50));

test("fix round 1, #1: the actors tile counts the chip list — distinct FIRST-slot actors, not every event's actor", async () => {
  const Data = freshModules(async () => ({
    kind: "groups", total: 2,
    results: [
      { ids: ["a", "b"], positions: [1, 2], times: [null, null], events: [
        { id: "a", agent: "A", kind: "K1" }, { id: "b", agent: "B", kind: "K2" },
      ] },
      { ids: ["c", "d"], positions: [3, 4], times: [null, null], events: [
        { id: "c", agent: "A", kind: "K1" }, { id: "d", agent: "C", kind: "K2" },
      ] },
    ],
  }));
  const entry = { result_id: "r1", total: 2, kind: "evaluate", result: "groups" };
  Data.buildContext(entry, board, "groups", vs(), actions); // first call: still pending
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", vs(), actions);

  assert.equal(ctx.agents.length, 1, "both groups lead with actor A — one chip");
  const actorsTile = ctx.tiles.find((t) => t.l === "actors");
  assert.equal(actorsTile.v, String(ctx.agents.length), "the tile must equal the chip list's own length");
  assert.equal(actorsTile.v, "1", "not 3 — never counted via every event's actor (B and C are never leads)");
});

test("fix round 1, #2: nothing loaded yet (still pending) renders no tiles", async () => {
  const Data = freshModules(() => new Promise(() => {})); // never resolves
  const entry = { result_id: "r2", total: 5, kind: "evaluate", result: "groups" };
  const ctx = Data.buildContext(entry, board, "groups", vs(), actions);
  assert.deepEqual(ctx.tiles, []);
  assert.equal(ctx.pending, true);
});

test("fix round 1, #2: a gone result renders no tiles, carries a blocker, and the canvas's own note", async () => {
  const Data = freshModules(async () => ({ gone: true }));
  const entry = { result_id: "r3", total: 5, kind: "evaluate", result: "groups" };
  Data.buildContext(entry, board, "groups", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", vs(), actions);
  assert.deepEqual(ctx.tiles, []);
  assert.ok(ctx.blocker, "a gone result renders a blocker instead of a view");
  assert.equal(ctx.gone, true);
  assert.equal(ctx.note, "result no longer kept");
});

test("fix round 1, #2: hits never show a fabricated '0.000 top score' when nothing scored is loaded yet", async () => {
  const Data = freshModules(() => new Promise(() => {}));
  const entry = { result_id: "r4", total: 5, kind: "similar", result: "hits" };
  const ctx = Data.buildContext(entry, board, "hits", vs(), actions);
  assert.deepEqual(ctx.tiles, []);
});

test("fix round 1, #12: hits with kept < total show it in the note, never as a 5th tile", async () => {
  const Data = freshModules(async () => ({
    kind: "hits", total: 3, kept: 2,
    hits: [
      { id: "a", position: 1, score: 0.9, time: null, event: { agent: "A", text: "hi" } },
      { id: "b", position: 2, score: 0.8, time: null, event: { agent: "B", text: "bye" } },
    ],
  }));
  const entry = { result_id: "r5", total: 3, kind: "similar", result: "hits" };
  Data.buildContext(entry, board, "hits", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "hits", vs(), actions);
  assert.equal(ctx.tiles.some((t) => t.l === "kept"), false);
  assert.equal(ctx.tiles.length, 4);
  assert.equal(ctx.note, "1–2 of 2 · 3 found", "kept 2 of the 3 found");
});

// --- fix round 2 ---

test("fix round 2, #1: 'Run again' on a gone result closes the full view before rerunning", async () => {
  const Data = freshModules(async () => ({ gone: true }));
  const entry = { result_id: "r6", total: 5, kind: "evaluate", result: "groups" };
  const calls = [];
  const actionsWithRerun = { closeFull: () => calls.push("close"), rerun: (e) => calls.push("rerun:" + e.result_id) };
  Data.buildContext(entry, board, "groups", vs(), actionsWithRerun);
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", vs(), actionsWithRerun);

  const btn = ctx.blocker.children[0].children.find((c) => c.textContent === "Run again");
  assert.ok(btn, "the gone block must contain a Run again button");
  btn.dispatch("click");
  assert.deepEqual(calls, ["close", "rerun:r6"], "closeFull must run, then rerun — never the other order or neither");
});

test("finding 1: a server cap below the page size steps offsets by what came back — no page skips items", async () => {
  const N = 80, CAP = 25;
  const all = [];
  for (let i = 0; i < N; i++) {
    all.push({ ids: ["g" + i], positions: [i], times: [null], events: [{ id: "g" + i, agent: "A", kind: "K" }] });
  }
  const asked = [];
  const Data = freshModules(async (rid, opts) => {
    asked.push([opts.offset, opts.limit]);
    const off = opts.offset;
    return { kind: "groups", total: N, count: Math.min(CAP, N - off), truncated: off + CAP < N, offset: off, results: all.slice(off, off + CAP) };
  });
  const entry = { result_id: "rN", total: N, kind: "evaluate", result: "groups" };
  const view = vs();
  const seen = [];
  for (let page = 0; page < 4; page++) {
    view.page = page;
    let ctx;
    for (let i = 0; i < 5; i++) {
      ctx = Data.buildContext(entry, board, "groups", view, actions);
      if (!ctx.pending) break;
      await flush();
    }
    assert.equal(ctx.pending, false);
    seen.push(...ctx.loaded.map((g) => g.n));
    assert.equal(ctx.nav.pageCount, 4, "80 items at 25 a page");
  }
  assert.deepEqual(seen, Array.from({ length: N }, (_, i) => i + 1), "every group exactly once, none skipped");
  assert.deepEqual(asked.map((a) => a[0]), [0, 25, 50, 75]);
  assert.ok(asked.every((a) => a[1] === 50), "every request asks for one PAGE, never a growing limit");
});

test("paging fetches one page and never accumulates the earlier ones", async () => {
  const N = 120;
  const all = [];
  for (let i = 0; i < N; i++) all.push({ ids: ["g" + i], positions: [i], times: [null], events: [{ id: "g" + i, agent: "A", kind: "K" }] });
  const Data = freshModules(async (rid, opts) => ({
    kind: "groups", total: N, offset: opts.offset, count: Math.min(50, N - opts.offset),
    truncated: opts.offset + 50 < N, results: all.slice(opts.offset, opts.offset + 50),
  }));
  const entry = { result_id: "rP", total: N, kind: "evaluate", result: "groups" };
  const view = vs();
  async function load() {
    let ctx = Data.buildContext(entry, board, "groups", view, actions);
    if (ctx.pending) { await flush(); ctx = Data.buildContext(entry, board, "groups", view, actions); }
    return ctx;
  }
  await load();
  view.page = 2;
  const ctx = await load();
  assert.equal(ctx.loaded.length, 20, "page 3 of 120 holds its own last 20, not 120");
  assert.equal(ctx.loaded[0].n, 101);
  assert.match(ctx.note, /101–120 of 120/);
});

test("a sorted page numbers each group by its place in the STORED result", async () => {
  const Data = freshModules(async (rid, opts) => ({
    kind: "groups", total: 6, offset: 0, count: 2, truncated: true, order: opts.order, reverse: !!opts.reverse,
    indices: [5, 1],
    results: [
      { ids: ["a", "b", "c", "d"], positions: [4, 5, 6, 7], times: [null, null, null, null], events: [] },
      { ids: ["x", "y", "z"], positions: [1, 2, 3], times: [null, null, null], events: [] },
    ],
  }));
  const entry = { result_id: "rS", total: 6, kind: "evaluate", result: "groups" };
  const view = vs();
  view.order = "size";
  Data.buildContext(entry, board, "groups", view, actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", view, actions);
  assert.deepEqual(ctx.loaded.map((g) => g.n), [6, 2]);
  assert.deepEqual(ctx.loaded.map((g) => g.idx), [5, 1]);
});

test("the view reaches the request: default sends no order, a view sends order and reverse", async () => {
  const calls = [];
  const Data = freshModules(async (rid, opts) => {
    calls.push({ order: opts.order, reverse: opts.reverse });
    return { kind: "groups", total: 1, offset: 0, count: 1, truncated: false, results: [{ ids: ["a"], positions: [0], times: [null], events: [] }] };
  });
  const entry = { result_id: "rV", total: 1, kind: "evaluate", result: "groups" };
  const view = vs();
  Data.buildContext(entry, board, "groups", view, actions);
  view.order = "size"; view.reverse = true;
  Data.buildContext(entry, board, "groups", view, actions);
  assert.deepEqual(calls, [{ order: undefined, reverse: undefined }, { order: "size", reverse: true }]);
});

test("a selected agent chip survives a page that has none of its groups", async () => {
  const Data = freshModules(async () => ({
    kind: "groups", total: 1, offset: 0, count: 1, truncated: false,
    results: [{ ids: ["a"], positions: [0], times: [null], events: [{ id: "a", agent: "B", kind: "K" }] }],
  }));
  const entry = { result_id: "rC", total: 1, kind: "evaluate", result: "groups" };
  const view = vs();
  view.agents = { A: true };
  Data.buildContext(entry, board, "groups", view, actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", view, actions);
  assert.deepEqual(ctx.agents, [{ label: "B", on: false }, { label: "A", on: true }]);
  assert.equal(ctx.filtered.length, 0, "the filter still applies, and its chip is there to undo it");
});

test("finding 4: buildContext threads idField through to pairEventsToSlots for groups", async () => {
  const Data = freshModules(async () => ({
    kind: "groups", total: 1,
    results: [{ ids: ["x"], positions: [1], times: [null], events: [{ event_id: "x", agent: "A", kind: "K" }] }],
  }));
  const entry = { result_id: "rid", total: 1, kind: "evaluate", result: "groups" };
  Data.buildContext(entry, board, "groups", vs(), actions, "event_id");
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", vs(), actions, "event_id");
  assert.equal(ctx.loaded[0].slots[0].agent, "A", "the event must be paired by event_id, not the default 'id'");
});

test("finding 3 round 2, #5: goneBlock disables Run again (with the dictionaries note) for an entry that carried request dictionaries", async () => {
  const Data = freshModules(async () => ({ gone: true }));
  const entry = { result_id: "r8", total: 5, kind: "evaluate", result: "groups", dictionaries: ["spikes"] };
  Data.buildContext(entry, board, "groups", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", vs(), actions);

  const btn = ctx.blocker.children[0].children.find((c) => c.textContent === "Run again");
  assert.equal(btn.disabled, true, "Run again must be disabled — the board never held the request's dictionary terms");
});

test("fix round 2, #4: a blocked (gone) result hides the filter box and chips", async () => {
  const Data = freshModules(async () => ({ gone: true }));
  const entry = { result_id: "r7", total: 5, kind: "evaluate", result: "groups" };
  Data.buildContext(entry, board, "groups", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "groups", vs(), actions);
  assert.equal(ctx.canFilter, false);
  assert.deepEqual(ctx.agents, []);
});

// --- rows (GROUP BY ... AGGREGATE answer, graph @aleph/prismql, #90) ---

test("rowsContext: loads the flat key/value list and reports it as groups loaded/total", async () => {
  const Data = freshModules(async () => ({
    kind: "rows", function: "count", field: null, total: 2, offset: 0,
    count: 2, truncated: false,
    rows: [{ key: "tick_a", value: 3 }, { key: "tick_b", value: 1 }],
  }));
  const entry = { result_id: "r9", total: 2, kind: "evaluate", result: "aggregate" };
  Data.buildContext(entry, board, "rows", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "rows", vs(), actions);
  assert.equal(ctx.kind, "rows");
  assert.deepEqual(ctx.loaded, [{ key: "tick_a", value: 3 }, { key: "tick_b", value: 1 }]);
  assert.deepEqual(ctx.filtered, ctx.loaded);
  assert.deepEqual(ctx.tiles, [{ v: "2 / 2", l: "groups loaded" }]);
  assert.equal(ctx.note, "1–2 of 2");
  assert.equal(ctx.canFilter, true);
});

test("rowsContext: the text filter matches the key or the value", async () => {
  const Data = freshModules(async () => ({
    kind: "rows", total: 2, offset: 0, count: 2, truncated: false,
    rows: [{ key: "tick_a", value: 3 }, { key: "tick_b", value: 1 }],
  }));
  const entry = { result_id: "r10", total: 2, kind: "evaluate", result: "aggregate" };
  const filterVs = vs();
  filterVs.q = "tick_a";
  Data.buildContext(entry, board, "rows", filterVs, actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "rows", filterVs, actions);
  assert.deepEqual(ctx.filtered, [{ key: "tick_a", value: 3 }]);
});

test("rowsContext: the filter matches the DISPLAYED text — a list joined with ', ', not String() of the array", async () => {
  const Data = freshModules(async () => ({
    kind: "rows", total: 2, offset: 0, count: 2, truncated: false,
    rows: [{ key: "tick_a", value: ["x", "y"] }, { key: "tick_b", value: 3 }],
  }));
  const entry = { result_id: "r12", total: 2, kind: "evaluate", result: "aggregate" };
  const filterVs = vs();
  filterVs.q = "x, y";
  Data.buildContext(entry, board, "rows", filterVs, actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "rows", filterVs, actions);
  assert.deepEqual(ctx.filtered, [{ key: "tick_a", value: ["x", "y"] }]);
});

test("rowsContext: a null value is findable by '—', the text the cell actually shows", async () => {
  const Data = freshModules(async () => ({
    kind: "rows", total: 2, offset: 0, count: 2, truncated: false,
    rows: [{ key: "tick_a", value: null }, { key: "tick_b", value: 3 }],
  }));
  const entry = { result_id: "r13", total: 2, kind: "evaluate", result: "aggregate" };
  const filterVs = vs();
  filterVs.q = "—";
  Data.buildContext(entry, board, "rows", filterVs, actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "rows", filterVs, actions);
  assert.deepEqual(ctx.filtered, [{ key: "tick_a", value: null }]);
});

test("rowsContext: a gone result renders no tiles and the canvas's own note", async () => {
  const Data = freshModules(async () => ({ gone: true }));
  const entry = { result_id: "r11", total: 2, kind: "evaluate", result: "aggregate" };
  Data.buildContext(entry, board, "rows", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "rows", vs(), actions);
  assert.deepEqual(ctx.tiles, []);
  assert.equal(ctx.note, "result no longer kept");
});

test("a failed page keeps its nav (the way back); a gone result has none", async () => {
  const bad = freshModules(async () => ({ error: { message: "boom" } }));
  const entry = { result_id: "rE", total: 130, kind: "evaluate", result: "groups" };
  const view = vs();
  view.page = 2;
  bad.buildContext(entry, board, "groups", view, actions);
  await flush();
  const failed = bad.buildContext(entry, board, "groups", view, actions);
  assert.ok(failed.blocker && !failed.gone);
  assert.deepEqual([failed.nav.page, failed.nav.pageCount], [2, 3]);
  const gone = freshModules(async () => ({ gone: true }));
  gone.buildContext({ ...entry, result_id: "rG" }, board, "groups", view, actions);
  await flush();
  assert.equal(gone.buildContext({ ...entry, result_id: "rG" }, board, "groups", view, actions).nav, null);
});
