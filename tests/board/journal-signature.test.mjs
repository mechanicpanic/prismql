// Pins fix round 2, #2: the periodic 5 s beat used to only patch ".rel"
// text, never re-checking the time-range filter or day labels — so a row
// aged out of "15m"/"1h" stayed visible forever, and "Today" never rolled
// to "Yesterday" at midnight. journal.js now computes a signature (which
// seqs are visible, and what day label each carries) and only takes the
// cheap patch path when it hasn't moved; otherwise it does a full render.
// These tests pin the signature itself — pure logic, no DOM — via
// PrismQLJournal._visibleEntries/_signatureOf (exposed for exactly this).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const F = require("../../src/prismql/server/board/format.js");
const U = require("../../src/prismql/server/board/board-util.js");
const JOURNAL_PATH = require.resolve("../../src/prismql/server/board/journal.js");

function freshJournal() {
  globalThis.window = { PrismQLFormat: F, PrismQLBoardUtil: U };
  delete require.cache[JOURNAL_PATH];
  return require(JOURNAL_PATH);
}

function stateWithRange(range, entries) {
  return {
    entries: entries,
    filters: { range: range, search: "", kinds: {}, srcs: {}, corpora: {}, statuses: {} },
  };
}

test("a row aged out of the time range disappears from the visible set", () => {
  const J = freshJournal();
  const t0 = Date.parse("2026-09-23T12:00:00.000Z");
  const entry = { seq: 1, ts: new Date(t0 - 10 * 60 * 1000).toISOString(), kind: "evaluate", ok: true }; // 10 min old
  const state = stateWithRange("15m", [entry]);

  const stillWithin = J._visibleEntries(state, t0); // now 10 min after ts — still under 15m
  assert.equal(stillWithin.length, 1);

  const later = t0 + 10 * 60 * 1000; // now 20 min after ts — past 15m
  const agedOut = J._visibleEntries(state, later);
  assert.equal(agedOut.length, 0, "a row must age out of the visible set, not linger forever");
});

test("signatureOf changes when a row ages out, even with the same entries array", () => {
  const J = freshJournal();
  const t0 = Date.parse("2026-09-23T12:00:00.000Z");
  const entry = { seq: 1, ts: new Date(t0 - 10 * 60 * 1000).toISOString(), kind: "evaluate", ok: true };
  const state = stateWithRange("15m", [entry]);

  const sigNow = J._signatureOf(J._visibleEntries(state, t0), t0);
  const later = t0 + 10 * 60 * 1000;
  const sigLater = J._signatureOf(J._visibleEntries(state, later), later);

  assert.notEqual(sigNow, sigLater, "the tick must see this as a change and re-render");
});

test("signatureOf changes across a midnight rollover even though the row stays visible", () => {
  const J = freshJournal();
  // 2026-09-22 23:59:00 local — "Today" while nowMs is still the 22nd.
  const entryTs = new Date(2026, 8, 22, 23, 59, 0).toISOString();
  const entry = { seq: 1, ts: entryTs, kind: "evaluate", ok: true };
  const state = stateWithRange("7d", [entry]); // wide enough range: still visible either way

  const beforeMidnight = new Date(2026, 8, 22, 23, 59, 30).getTime();
  const afterMidnight = new Date(2026, 8, 23, 0, 0, 30).getTime();

  const visBefore = J._visibleEntries(state, beforeMidnight);
  const visAfter = J._visibleEntries(state, afterMidnight);
  assert.equal(visBefore.length, 1);
  assert.equal(visAfter.length, 1, "still in range — the row itself doesn't disappear");

  const sigBefore = J._signatureOf(visBefore, beforeMidnight);
  const sigAfter = J._signatureOf(visAfter, afterMidnight);
  assert.notEqual(sigBefore, sigAfter, "the day label rolled from Today to Yesterday — tick must catch it");
});

test("signatureOf is stable when nothing relevant changed (a few seconds later)", () => {
  const J = freshJournal();
  const t0 = Date.parse("2026-09-23T12:00:00.000Z");
  const entry = { seq: 1, ts: new Date(t0 - 5 * 60 * 1000).toISOString(), kind: "evaluate", ok: true };
  const state = stateWithRange("1h", [entry]);

  const sig1 = J._signatureOf(J._visibleEntries(state, t0), t0);
  const t1 = t0 + 5000; // 5 s later, the normal tick cadence
  const sig2 = J._signatureOf(J._visibleEntries(state, t1), t1);

  assert.equal(sig1, sig2, "a plain 5 s beat with nothing crossing a boundary must not force a rebuild");
});
