// Pins finding 5 (graph @aleph/prismql, node #76) and its round-2 follow-up
// (#5): a live journal arrival while the full view is open patches only the
// header's nav (Header.patchNav) instead of rebuilding the body
// (Header.build/Summary/Body) — and, specifically, the FIRST such arrival
// right after opening must also take the cheap path: vs.view starts null
// and is resolved to allowed[0] before the body signature is taken, so the
// signature stored on the resolving build matches the very next render's,
// rather than a stale "null" never matching the resolved name. Fake DOM +
// fake sibling modules — no real rendering, just call counts.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const FullNav = require("../../src/prismql/server/board/fullview-nav-logic.js");
const MODPATH = require.resolve("../../src/prismql/server/board/fullview.js");

function fakeEl() {
  return {
    dataset: {}, hidden: true, style: {}, innerHTML: "",
    children: [],
    appendChild(c) { this.children.push(c); return c; },
    addEventListener() {},
    querySelector() { return null; },
    focus() {},
  };
}

function freshFull(calls) {
  const full = fakeEl();
  globalThis.document = {
    getElementById(id) { return id === "full" ? full : fakeEl(); },
  };
  globalThis.window = {
    PrismQLBoardUtil: {
      mk: () => fakeEl(),
      findEntry: (state, seq) => state.entries.find((e) => e.seq === seq) || null,
    },
    PrismQLFormat: { rel: () => "" },
    PrismQLInspectorFormat: { outputKind: () => "groups" },
    PrismQLInspectorFetch: {
      boardFieldsFor: () => ({ board: {}, idField: "id", blocked: false }),
      loadingBlock: () => fakeEl(),
    },
    PrismQLFullNav: FullNav,
    PrismQLFullLogic: { PAGE: 50, viewsFor: () => ["timeline", "table", "raw"] },
    PrismQLFullData: {
      buildContext: () => ({
        kind: "groups", loaded: [{ n: 1 }], filtered: [{ n: 1 }], pending: false,
        blocker: null, gone: false, loadBound: 1, total: 1, tiles: [], agents: [],
      }),
    },
    PrismQLFullHeader: {
      build: (...args) => { calls.push("build"); },
      patchNav: (...args) => { calls.push("patch"); return true; },
    },
    PrismQLFullSummary: { buildSum() {}, buildBar() {} },
    PrismQLFullBody: { build: () => [] },
    PrismQLFullFocus: {
      captureFocus: () => null, captureScroll: () => null,
      restoreFocus() {}, restoreScroll() {},
    },
    PrismQLJournal: { _visibleEntries: (state) => state.entries },
  };
  delete require.cache[MODPATH];
  return require(MODPATH);
}

function freshState() {
  return { full: 1, entries: [{ seq: 1, corpus: "village" }] };
}

test("render(): the first render after open() resolves vs.view before the sig — the next render (a live arrival) patches, it does not rebuild", () => {
  const calls = [];
  const Full = freshFull(calls);
  const state = freshState();
  const actions = {};

  Full.open(state, function () { Full.render(state, actions); }, 1);
  assert.deepEqual(calls, ["build"], "opening always does one real build");

  // Simulate a live journal arrival: nothing about vs/entry/ctx changed,
  // just another render() call (board.js's own render() re-runs every
  // module on any state change, including an unrelated new journal entry).
  Full.render(state, actions);
  assert.deepEqual(calls, ["build", "patch"], "the very next render must patch, not rebuild");
});

test("render(): a real view/group change still rebuilds", () => {
  const calls = [];
  const Full = freshFull(calls);
  const state = freshState();
  const actions = {};

  Full.open(state, function () { Full.render(state, actions); }, 1);
  Full.render(state, actions); // patches
  state.entries.push({ seq: 2, corpus: "village" });
  Full.open(state, function () { Full.render(state, actions); }, 2); // a new entry: real rebuild
  assert.deepEqual(calls, ["build", "patch", "build"]);
});

// The keyboard: a focused Sort select and the pager buttons keep their own
// arrow keys; elsewhere ←/→ still walk the journal and ↑/↓ the groups.
function keyHarness() {
  const calls = [];
  const Full = freshFull(calls);
  const full = globalThis.document.getElementById("full");
  const handlers = [];
  full.addEventListener = (type, fn) => { if (type === "keydown") handlers.push(fn); };
  globalThis.window.PrismQLFullBody.build = () => [{ n: 1 }, { n: 2 }];
  globalThis.window.PrismQLFullLogic.viewsFor = () => ["timeline", "table", "raw"];
  const state = { full: 1, entries: [{ seq: 1, corpus: "v" }, { seq: 2, corpus: "v" }] };
  const opened = [];
  const closed = [];
  const actions = { openFull: (s) => opened.push(s), closeFull: () => closed.push(1) };
  Full.open(state, () => Full.render(state, actions), 1);
  function press(key, target) {
    let prevented = 0;
    handlers[0]({ key, target, preventDefault() { prevented++; } });
    return prevented;
  }
  return { press, opened, closed };
}
const SELECT = { tagName: "SELECT" };
const PAGER_BTN = { tagName: "BUTTON", closest: (sel) => (sel.includes(".fpager") ? {} : null) };
const PLAIN_BTN = { tagName: "BUTTON", closest: () => null };

test("keys: ArrowDown on the focused Sort select is left to the select (no group move, no preventDefault)", () => {
  const k = keyHarness();
  assert.equal(k.press("ArrowDown", SELECT), 0);
  assert.equal(k.press("ArrowUp", SELECT), 0);
  assert.equal(k.press("ArrowRight", SELECT), 0);
  assert.deepEqual(k.opened, []);
});
test("keys: ArrowRight/Left on a pager button does not jump to another journal entry", () => {
  const k = keyHarness();
  assert.equal(k.press("ArrowRight", PAGER_BTN), 0);
  assert.equal(k.press("ArrowLeft", PAGER_BTN), 0);
  assert.deepEqual(k.opened, []);
});
test("keys: elsewhere the shortcuts still work (←/→ entries, ↑/↓ groups, Esc closes)", () => {
  const k = keyHarness();
  assert.equal(k.press("ArrowRight", PLAIN_BTN), 1);
  assert.deepEqual(k.opened, [2]);
  assert.equal(k.press("ArrowDown", PLAIN_BTN), 1, "the group walk takes ↓ off a non-select control");
  assert.equal(k.press("Escape", SELECT), 1);
  assert.equal(k.closed.length, 1, "Esc on the select still closes the view");
});
