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
