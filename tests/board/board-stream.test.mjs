// Pins fix-round-1 rulings #1 (one backfill call, not a page-until-short
// loop that silently drops everything but the newest page), #3 (a restart
// reset clears sel/full/freshSeq/pending) and #4 (one retry timer, a
// generation token so a superseded attempt is a no-op, the previous stream
// handle closed before a new one opens, a successful backfill clears
// pending) against a fake PrismQLApi — no real network, no real timers.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const MODPATH = require.resolve("../../src/prismql/server/board/board-stream.js");

function freshStream() {
  delete require.cache[MODPATH];
  return require(MODPATH);
}

function freshState(overrides) {
  return Object.assign(
    {
      entries: [], seq: 0, boot: null, live: true, pending: [], down: false,
      freshSeq: null, sel: null, full: null,
      filters: { range: "24h", search: "", kinds: {}, srcs: {}, corpora: {}, statuses: {} },
    },
    overrides || {},
  );
}

function entry(seq) {
  return { seq: seq, ts: new Date(2026, 0, 1, 0, 0, seq).toISOString(), kind: "evaluate", ok: true };
}

// setImmediate, never setTimeout: the retry-timer test mocks setTimeout
// itself, and a flush built on the very API under mock would never settle.
function flush() {
  return new Promise((resolve) => setImmediate(resolve));
}

function fakeApi(opts) {
  opts = opts || {};
  const activityCalls = [];
  const streamCalls = [];
  const order = []; // "open1", "close1", "open2", ... — real event ordering
  let activityN = 0;
  return {
    activityCalls, streamCalls, order,
    activity: async (since, limit) => {
      activityN++;
      activityCalls.push({ since: since, limit: limit });
      if (opts.activityImpl) return opts.activityImpl(since, limit, activityN);
      return { ok: true, seq: 0, boot: "boot-1", entries: opts.entries || [] };
    },
    stream: (since, onEntry, onState, knownBoot) => {
      const n = streamCalls.length + 1;
      order.push("open" + n);
      const closeSpy = { closed: false };
      const call = { since: since, onEntry: onEntry, onState: onState, knownBoot: knownBoot, closeSpy: closeSpy };
      streamCalls.push(call);
      return { close: () => { closeSpy.closed = true; order.push("close" + n); } };
    },
  };
}

// --- #1: single backfill call ---

test("connect: backfills with one activity(0, 1000) call, never a paging loop", async (t) => {
  const api = fakeApi({ entries: [entry(1), entry(2)] });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState();

  await new Promise((resolve) => {
    stream.connect(state, () => resolve());
  });
  await flush();

  assert.equal(api.activityCalls.length, 1, "exactly one activity() call");
  assert.deepEqual(api.activityCalls[0], { since: 0, limit: 1000 });
  assert.equal(state.entries.length, 2, "both entries kept, not just a short page");
  assert.equal(state.entries[0].seq, 2, "newest first");
});

test("connect: state.seq is the max of since and the last delivered row's seq, not body.seq", async () => {
  const api = fakeApi({
    activityImpl: async () => ({ ok: true, seq: 999, boot: "boot-1", entries: [entry(1), entry(2)] }),
  });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState();

  await new Promise((resolve) => { stream.connect(state, () => resolve()); });
  await flush();

  assert.equal(state.seq, 2, "seq tracks what was actually delivered, not the server's own counter");
});

// --- #3: reset clears selection state too ---

test("a boot-mismatch reset clears sel, full, freshSeq and pending, then backfills again", async () => {
  const api = fakeApi({ entries: [entry(1)] });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState({ sel: 1, full: 1, freshSeq: 1, pending: [entry(2)] });

  let renders = 0;
  await new Promise((resolve) => {
    stream.connect(state, () => { renders++; if (renders === 1) resolve(); });
  });
  await flush();

  assert.equal(api.streamCalls.length, 1);
  const firstStreamCall = api.streamCalls[0];
  // Simulate the boot changing under us.
  firstStreamCall.onState("reset", "boot-2");
  await flush();

  assert.equal(state.sel, null);
  assert.equal(state.full, null);
  assert.equal(state.freshSeq, null);
  assert.deepEqual(state.pending, []);
  assert.equal(api.activityCalls.length, 2, "reset re-backfills");
  assert.equal(api.streamCalls.length, 2, "and reopens a stream");
  assert.equal(firstStreamCall.closeSpy.closed, true, "the pre-reset handle was closed, not just abandoned");
});

// --- #4: one retry timer, a generation token, no overlap ---

test("reconnect() cancels a pending 4s retry timer instead of layering a second attempt", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  let n = 0;
  const api = fakeApi({
    activityImpl: async () => {
      n++;
      if (n === 1) throw new Error("boom");
      return { ok: true, seq: 0, boot: "boot-1", entries: [entry(1)] };
    },
  });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState();
  const render = () => {};

  stream.connect(state, render);
  await flush();
  assert.equal(state.down, true, "first attempt failed, marked down");
  assert.equal(api.activityCalls.length, 1);

  // Retry now, before the scheduled 4s timer fires.
  stream.reconnect(state, render);
  await flush();
  assert.equal(api.activityCalls.length, 2, "reconnect tried again immediately");
  assert.equal(state.down, false);

  // Advance past where the original (should-be-cancelled) timer would have
  // fired. If it wasn't cancelled, this fires a THIRD overlapping attempt.
  t.mock.timers.tick(5000);
  await flush();
  assert.equal(api.activityCalls.length, 2, "the superseded retry timer never fired");
});

test("connect: a stale (superseded) backfill never applies its result", async () => {
  let resolveFirst;
  const first = new Promise((resolve) => { resolveFirst = resolve; });
  let call = 0;
  const api = fakeApi({
    activityImpl: async (since, limit, n) => {
      call = n;
      if (n === 1) { await first; return { ok: true, seq: 0, boot: "boot-1", entries: [entry(1)] }; }
      return { ok: true, seq: 0, boot: "boot-1", entries: [entry(2), entry(3)] };
    },
  });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState();
  const renders = [];

  stream.connect(state, () => renders.push(state.entries.map((e) => e.seq)));
  await flush();
  // A second connect (e.g. via reconnect) starts and finishes before the
  // first backfill resolves.
  stream.reconnect(state, () => renders.push(state.entries.map((e) => e.seq)));
  await flush();
  assert.deepEqual(state.entries.map((e) => e.seq), [3, 2], "the second (newer) attempt won");

  resolveFirst();
  await flush();
  assert.deepEqual(state.entries.map((e) => e.seq), [3, 2], "the stale first attempt changed nothing");
});

test("connect: closes the previous stream handle before opening a new one", async () => {
  const api = fakeApi({ entries: [entry(1)] });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState();

  await new Promise((resolve) => { stream.connect(state, () => resolve()); });
  await flush();

  stream.reconnect(state, () => {});
  await flush();

  assert.equal(api.streamCalls.length, 2);
  assert.deepEqual(api.order, ["open1", "close1", "open2"], "close1 must land before open2, not after");
});

test("a successful full backfill replaces entries and clears pending", async () => {
  const api = fakeApi({ entries: [entry(1), entry(2)] });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState({ entries: [entry(99)], pending: [entry(100), entry(101)] });

  await new Promise((resolve) => { stream.connect(state, () => resolve()); });
  await flush();

  assert.deepEqual(state.entries.map((e) => e.seq), [2, 1]);
  assert.deepEqual(state.pending, []);
});

// --- #7: entries cap ---

test("connect: caps state.entries at 1000, newest kept", async () => {
  const many = [];
  for (let i = 1; i <= 1200; i++) many.push(entry(i));
  const api = fakeApi({ entries: many });
  globalThis.window = { PrismQLApi: api };
  const stream = freshStream();
  const state = freshState();

  await new Promise((resolve) => { stream.connect(state, () => resolve()); });
  await flush();

  assert.equal(state.entries.length, 1000);
  assert.equal(state.entries[0].seq, 1200, "newest first");
  assert.equal(state.entries[999].seq, 201, "oldest beyond the cap dropped");
});
