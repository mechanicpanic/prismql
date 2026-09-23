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

function fakeEl() {
  return {
    children: [], style: {},
    appendChild(c) { this.children.push(c); return c; },
    addEventListener() {},
    setAttribute() {},
  };
}

function freshModules(pageImpl) {
  globalThis.document = { createElement: () => fakeEl() };
  globalThis.window = {
    PrismQLBoardUtil: BoardUtil,
    PrismQLInspectorUI: { emptyBlock: () => fakeEl(), ICON_FULL: "" },
    PrismQLInspectorPageLogic: PageLogic,
    PrismQLFullLogic: FullLogic,
    PrismQLFormat: Format,
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
