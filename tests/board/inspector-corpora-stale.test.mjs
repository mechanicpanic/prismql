// Carry-over from Task 5's review (task-6 brief): a /corpora request in
// flight across a stream reset must neither arm a stale retry nor write
// pre-reset data. reset() bumps a generation counter; ensure()'s own
// then/catch checks it before touching state, fetching or the retry timer
// — a stale settle is a pure no-op. Fake window, fake timers — no real
// network, no real clock — same pattern as inspector-corpora.test.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const MODPATH = require.resolve("../../src/prismql/server/board/inspector-corpora.js");

function freshCorpora() {
  delete require.cache[MODPATH];
  return require(MODPATH);
}

function setWindow(api, renderCalls) {
  globalThis.window = {
    PrismQLApi: api,
    PrismQLBoard: { render: function () { renderCalls.push(1); } },
  };
}

function flush() {
  return new Promise((resolve) => setImmediate(resolve));
}

test("ensure(): a pre-reset in-flight request neither writes stale data nor arms a stale retry", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const pending = [];
  let calls = 0;
  const api = {
    corpora: () => {
      calls++;
      return new Promise((_resolve, reject) => pending.push(reject));
    },
  };
  const renders = [];
  setWindow(api, renders);
  const C = freshCorpora();
  const state = { corpora: null, corporaFailed: false };

  C.ensure(state); // request A (pre-reset generation)
  await flush();
  assert.equal(calls, 1);

  C.reset(state);
  C.ensure(state); // request B (post-reset generation) — A is still outstanding
  await flush();
  assert.equal(calls, 2, "reset() lets a fresh request start even while the stale one is still in flight");

  pending[0](new Error("502")); // A settles late
  await flush();
  assert.equal(state.corpora, null, "a stale settle must never write into post-reset state");
  assert.equal(state.corporaFailed, false, "a stale failure must not be reported as the current one");

  // A's settle must not have armed a retry timer of its own — ticking well
  // past its 5s backoff must not fetch again while B is still pending.
  t.mock.timers.tick(10000);
  await flush();
  assert.equal(calls, 2, "no stale retry chain from the superseded request");

  pending[1](new Error("502")); // B — the real, current failure
  await flush();
  assert.equal(state.corporaFailed, true);

  t.mock.timers.tick(4999);
  await flush();
  assert.equal(calls, 2, "B's own retry hasn't fired yet");

  t.mock.timers.tick(2);
  await flush();
  assert.equal(calls, 3, "B's own retry chain continues on schedule");
});
