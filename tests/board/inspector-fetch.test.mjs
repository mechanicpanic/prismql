// Pins fix round 2, #2 (a failed page heals itself for an idle viewer —
// one deduped setTimeout(bump, FAIL_TTL_MS+1) per key) and #4 (a fetch in
// flight across a stream reset must not write into the fresh caches — a
// generation tag, bumped by clearCache()). Fake window (real board-util.js
// for `mk`, a stub PrismQLInspectorUI since these tests never call
// goneBlock/loadingBlock), fake timers, fake PrismQLApi/PrismQLBoard.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const MODPATH = require.resolve("../../src/prismql/server/board/inspector-fetch.js");
const BoardUtil = require("../../src/prismql/server/board/board-util.js");
const PageLogic = require("../../src/prismql/server/board/inspector-page-logic.js");

function freshFetch() {
  delete require.cache[MODPATH];
  return require(MODPATH);
}

function setWindow(pageImpl, renders) {
  globalThis.window = {
    PrismQLBoardUtil: BoardUtil,
    PrismQLInspectorUI: {}, // unused by these tests (no gone/loading block calls)
    PrismQLInspectorPageLogic: PageLogic,
    PrismQLApi: { page: pageImpl },
    PrismQLBoard: { render: function (nowMs) { renders.push(nowMs); } },
  };
}

function flush() {
  return new Promise((resolve) => setImmediate(resolve));
}

test("fetchPage: a valid page is cached — a second call never refetches", async () => {
  let calls = 0;
  const renders = [];
  setWindow(async () => { calls++; return { kind: "groups", total: 2, results: [] }; }, renders);
  const PF = freshFetch();

  const rec1 = PF.fetchPage("r1", 0, 2, ["text"]);
  assert.equal(rec1.status, "loading");
  await flush();
  assert.equal(calls, 1);
  const rec2 = PF.fetchPage("r1", 0, 2, ["text"]);
  assert.equal(rec2.status, "done");
  assert.equal(calls, 1, "a cached valid page must never be refetched");
});

test("fetchPage: an invalid body (no results/hits/gone) is not cached as the final page", async () => {
  let calls = 0;
  const renders = [];
  setWindow(async () => { calls++; return { detail: "Internal Server Error" }; }, renders);
  const PF = freshFetch();

  PF.fetchPage("r1", 0, 2, ["text"]);
  await flush();
  const rec = PF.fetchPage("r1", 0, 2, ["text"]);
  assert.equal(rec.data.error.message, "the server answered without a page");
});

test("fix round 2, #2: a failed page schedules its own retry render, healing an idle viewer", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "Date"] });
  let calls = 0;
  const renders = [];
  setWindow(async () => {
    calls++;
    if (calls === 1) return { detail: "gateway timeout" };
    return { kind: "groups", total: 2, results: [{ ids: ["a"], positions: [0], times: [null] }] };
  }, renders);
  const PF = freshFetch();

  PF.fetchPage("r1", 0, 2, ["text"]);
  await flush();
  assert.equal(calls, 1);
  const rendersAfterFailure = renders.length;
  assert.ok(rendersAfterFailure >= 1, "the failure itself renders once so it's shown");

  // No click, no reselect — just time passing (FAIL_TTL_MS + 1 = 5001ms).
  t.mock.timers.tick(5001);
  await flush();
  assert.ok(renders.length > rendersAfterFailure, "the expiry timer fired its own render — an idle viewer still heals");

  // That render's inspector-groups/-hits would call fetchPage again; the
  // cache is stale past the TTL, so it retries and now succeeds.
  const rec = PF.fetchPage("r1", 0, 2, ["text"]);
  await flush();
  assert.equal(calls, 2, "the next fetchPage() call past the TTL actually retried");
  assert.equal(rec.status === "done" || rec.status === "loading", true);
});

test("fix round 2, #2: repeated reads of a failed key while pending never stack more than one retry timer", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "Date"] });
  let calls = 0;
  const renders = [];
  setWindow(async () => { calls++; return { detail: "still down" }; }, renders);
  const PF = freshFetch();

  PF.fetchPage("r1", 0, 2, ["text"]);
  await flush();
  const before = renders.length;
  // Simulate several render passes reading the same still-failed key —
  // must not schedule extra timers (each would otherwise add a render).
  PF.fetchPage("r1", 0, 2, ["text"]);
  PF.fetchPage("r1", 0, 2, ["text"]);
  PF.fetchPage("r1", 0, 2, ["text"]);
  t.mock.timers.tick(5001);
  await flush();
  const after = renders.length;
  assert.equal(after - before, 1, "exactly one retry render from the one deduped timer, not several");
});

test("fix round 2, #4: a fetch in flight across clearCache() (a stream reset) is dropped, not written into the fresh cache", async (t) => {
  const renders = [];
  let resolvePage;
  setWindow(() => new Promise((resolve) => { resolvePage = resolve; }), renders);
  const PF = freshFetch();

  const rec = PF.fetchPage("r1", 0, 2, ["text"]);
  assert.equal(rec.status, "loading");

  // The reset happens while the request is still in flight.
  PF.clearCache();

  // The stale request now resolves — after the reset.
  resolvePage({ kind: "groups", total: 1, results: [{ ids: ["a"], positions: [0], times: [null] }] });
  await flush();

  // A fresh fetchPage() call for the same key must see a clean miss, not
  // the stale (pre-reset) result quietly adopted into the new cache.
  let secondCalls = 0;
  globalThis.window.PrismQLApi.page = async () => { secondCalls++; return { kind: "groups", total: 1, results: [] }; };
  const rec2 = PF.fetchPage("r1", 0, 2, ["text"]);
  assert.equal(rec2.status, "loading", "the stale resolution must not have pre-populated the fresh cache");
  await flush();
  assert.equal(secondCalls, 1, "a real new request was made after the reset");
});
