// Pins run()'s corpus resolution (graph @aleph/prismql, node #63; task-6
// fix round 3): the server always journals a real corpus name
// (req.corpus or its own default_corpus, app.py) — it never journals a
// null one — so a run whose editor never had a corpus chosen (before
// /corpora loaded, or when it failed) must resolve to state.corpora's own
// default before it goes into editorPending, or findPendingMatch's corpus
// check has nothing real to compare against. Fake window, fake
// PrismQLApi.evaluate — no real network — same pattern as
// board-stream.test.mjs / inspector-corpora.test.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const MODPATH = require.resolve("../../src/prismql/server/board/editor-actions.js");

function freshActions() {
  delete require.cache[MODPATH];
  return require(MODPATH);
}

function flush() {
  return new Promise((resolve) => setImmediate(resolve));
}

function freshState(overrides) {
  return Object.assign(
    {
      seq: 10, boot: "b1", corpora: { corpora: ["wiki", "village"], default: "wiki" },
      editor: { query: "SELECT count($a)", corpus: null, running: false, error: null, rev: 0, focus: false },
    },
    overrides || {},
  );
}

test("run(): a null corpus resolves to state.corpora.default before it's stored in editorPending", async () => {
  const api = { evaluate: async () => ({ status: 200, body: { ok: true, result_id: null } }) };
  globalThis.window = { PrismQLApi: api };
  const A = freshActions();
  const state = freshState();

  A.run(state, function () {});
  await flush();

  assert.equal(state.editorPending.corpus, "wiki", "resolved to the known default, not left null");
});

// --- finding 3: rerun dispatch by kind ---

test("rerun(): a search entry posts straight to /search, never the editor", () => {
  const calls = [];
  globalThis.window = {
    PrismQLApi: {
      search: (body) => { calls.push(["search", body]); return Promise.resolve({}); },
      similar: () => { throw new Error("must not call similar"); },
      evaluate: () => { throw new Error("must not call evaluate"); },
    },
  };
  const A = freshActions();
  const state = freshState({ tab: "details" });
  const entry = { kind: "search", query: "spike", corpus: "wiki", total: 4 };

  A.rerun(state, function () {}, entry);

  assert.deepEqual(calls, [["search", { query: "spike", corpus: "wiki", limit: 4 }]]);
  assert.equal(state.tab, "details", "a search rerun never flips the tab to the editor");
});

test("rerun(): a similar entry posts straight to /similar, never the editor", () => {
  const calls = [];
  globalThis.window = {
    PrismQLApi: {
      similar: (body) => { calls.push(["similar", body]); return Promise.resolve({}); },
      search: () => { throw new Error("must not call search"); },
      evaluate: () => { throw new Error("must not call evaluate"); },
    },
  };
  const A = freshActions();
  const state = freshState({ tab: "details" });
  const entry = { kind: "similar", query: "calm seas", corpus: null, total: 2, threshold: 0.6 };

  A.rerun(state, function () {}, entry);

  assert.deepEqual(calls, [["similar", { text: "calm seas", threshold: 0.6, limit: 2 }]]);
});

test("rerun(): an entry with request dictionaries is not replayed at all", () => {
  globalThis.window = {
    PrismQLApi: {
      evaluate: () => { throw new Error("must not call evaluate"); },
      search: () => { throw new Error("must not call search"); },
      similar: () => { throw new Error("must not call similar"); },
    },
  };
  const A = freshActions();
  const state = freshState({ tab: "details" });
  const entry = { kind: "evaluate", query: "SELECT from(a)", dictionaries: ["spikes"] };

  A.rerun(state, function () {}, entry);

  assert.equal(state.tab, "details", "the editor is never opened for a blocked rerun");
});
