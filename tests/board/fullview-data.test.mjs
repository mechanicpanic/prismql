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
const DATA_PATH = require.resolve("../../src/prismql/server/board/fullview-data.js");
const BoardUtil = require("../../src/prismql/server/board/board-util.js");
const PageLogic = require("../../src/prismql/server/board/inspector-page-logic.js");
const FullLogic = require("../../src/prismql/server/board/fullview-logic.js");
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
    PrismQLFormat: Format,
    PrismQLEditorLogic: EditorLogic,
    PrismQLApi: { page: pageImpl },
    PrismQLBoard: { render: function () {} },
  };
  delete require.cache[FETCH_PATH];
  delete require.cache[DATA_PATH];
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
const vs = () => ({ loadTo: 50, q: "", agents: {} });

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
  assert.match(ctx.note, /kept 2/);
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

test("finding 1: full view paging advances by the page's own count, not a fixed PAGE, when the server caps below it", async () => {
  const N = 80, CAP = 25;
  const all = [];
  for (let i = 0; i < N; i++) {
    all.push({ ids: ["g" + i], positions: [i], times: [null], events: [{ id: "g" + i, agent: "A", kind: "K" }] });
  }
  const Data = freshModules(async (rid, opts) => {
    const off = opts.offset;
    return { kind: "groups", total: N, results: all.slice(off, off + CAP) };
  });
  const entry = { result_id: "rN", total: N, kind: "evaluate", result: "groups" };
  let ctx;
  for (let i = 0; i < 10; i++) {
    ctx = Data.buildContext(entry, board, "groups", { loadTo: N, q: "", agents: {} }, actions);
    if (!ctx.pending) break;
    await flush();
  }
  assert.equal(ctx.pending, false, "loading must finish within a handful of page fetches");
  assert.equal(ctx.loaded.length, N, "all 80 groups must load despite the 25-item server cap");
  assert.deepEqual(ctx.loaded.map((g) => g.n), Array.from({ length: N }, (_, i) => i + 1));
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
  assert.equal(ctx.note, "2 of 2 loaded");
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

test("rowsContext: a gone result renders no tiles and the canvas's own note", async () => {
  const Data = freshModules(async () => ({ gone: true }));
  const entry = { result_id: "r11", total: 2, kind: "evaluate", result: "aggregate" };
  Data.buildContext(entry, board, "rows", vs(), actions);
  await flush();
  const ctx = Data.buildContext(entry, board, "rows", vs(), actions);
  assert.deepEqual(ctx.tiles, []);
  assert.equal(ctx.note, "result no longer kept");
});
