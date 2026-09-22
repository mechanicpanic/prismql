// Pins fix round 2, #1: a failed /corpora used to make ensure()'s .catch
// call PrismQLBoard.render(), whose render dispatcher calls ensure()
// again — an unthrottled loop (measured ~2000 req/s against a failing
// /corpora live). At most one request in flight; a failure schedules a
// real 5 s retry timer, and the failure's own render must not start a
// second request before that timer fires. Fake window, fake timers — no
// real network, no real clock — same pattern as board-stream.test.mjs.
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

function freshState() {
  return { corpora: null, corporaFailed: false };
}

test("ensure(): only one request in flight, even across many render-driven calls", async () => {
  let calls = 0;
  const api = { corpora: async () => { calls++; return new Promise(() => {}); } }; // never resolves
  const renders = [];
  setWindow(api, renders);
  const C = freshCorpora();
  const state = freshState();

  C.ensure(state);
  C.ensure(state);
  C.ensure(state);
  await flush();
  assert.equal(calls, 1, "a second ensure() call while one is still in flight must not fetch again");
});

test("ensure(): a failure's own render() must not trigger an immediate second request", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "Date"] });
  let calls = 0;
  const api = { corpora: async () => { calls++; throw new Error("502"); } };
  const renders = [];
  setWindow(api, renders);
  const C = freshCorpora();
  const state = freshState();

  C.ensure(state);
  await flush();
  assert.equal(calls, 1);
  assert.equal(state.corporaFailed, true);
  assert.ok(renders.length >= 1, "a render was triggered so the UI can show the failure");

  // Simulate what the real board does on every render: call ensure()
  // again. Before fix round 2 this alone re-triggered a fetch.
  for (let i = 0; i < 50; i++) {
    C.ensure(state);
    await flush();
  }
  assert.equal(calls, 1, "no new request before the 5s retry timer, however many renders happen");
});

test("ensure(): retries no sooner than 5s after a failure, then succeeds", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "Date"] });
  let calls = 0;
  const api = {
    corpora: async () => {
      calls++;
      if (calls === 1) throw new Error("502");
      return { corpora: ["demo"], default: "demo", board: { demo: {} } };
    },
  };
  const renders = [];
  setWindow(api, renders);
  const C = freshCorpora();
  const state = freshState();

  C.ensure(state);
  await flush();
  assert.equal(calls, 1);

  t.mock.timers.tick(4999);
  await flush();
  assert.equal(calls, 1, "still short of the 5s backoff");

  t.mock.timers.tick(2);
  await flush();
  assert.equal(calls, 2, "the timer itself retried, no render() call needed");
  assert.deepEqual(state.corpora, { corpora: ["demo"], default: "demo", board: { demo: {} } });
  assert.equal(state.corporaFailed, true, "left true from the earlier failure — render() reads state.corpora first anyway");
});

test("ensure(): a resolved state.corpora short-circuits — never fetches again", async () => {
  let calls = 0;
  const api = { corpora: async () => { calls++; return { corpora: [], default: null, board: {} }; } };
  const renders = [];
  setWindow(api, renders);
  const C = freshCorpora();
  const state = freshState();
  state.corpora = { corpora: ["x"], default: "x", board: {} };

  C.ensure(state);
  await flush();
  assert.equal(calls, 0);
});

test("reset(): clears corpora/corporaFailed and cancels a pending retry timer", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "Date"] });
  let calls = 0;
  const api = { corpora: async () => { calls++; throw new Error("502"); } };
  const renders = [];
  setWindow(api, renders);
  const C = freshCorpora();
  const state = freshState();
  state.corpora = { corpora: ["old"], default: "old", board: {} };

  C.reset(state);
  assert.equal(state.corpora, null);
  assert.equal(state.corporaFailed, false);

  // A stream reset while a retry timer from an earlier failure was
  // pending must not let that timer fire a stale attempt later.
  C.ensure(state);
  await flush();
  assert.equal(calls, 1);
  C.reset(state);
  t.mock.timers.tick(6000);
  await flush();
  assert.equal(calls, 1, "the cancelled retry timer never fired");
});
