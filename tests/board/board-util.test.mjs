// Pins findEntry (graph @aleph/prismql, node #63; task-6 fix round 2, #1):
// a selection (state.sel) can point at an entry that only ever landed in
// state.pending — a match found while paused never merges into entries —
// so any lookup by seq must check both, in that order, or a paused run's
// own Request tab renders empty.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const U = require("../../src/prismql/server/board/board-util.js");

test("findEntry: found in entries", () => {
  const state = { entries: [{ seq: 5, who: "board" }], pending: [] };
  assert.equal(U.findEntry(state, 5), state.entries[0]);
});

test("findEntry: found only in pending (a paused run's own entry)", () => {
  const state = { entries: [{ seq: 1 }], pending: [{ seq: 5, who: "board" }] };
  assert.equal(U.findEntry(state, 5), state.pending[0]);
});

test("findEntry: entries wins when the same seq is somehow in both", () => {
  const inEntries = { seq: 5, tag: "entries" };
  const inPending = { seq: 5, tag: "pending" };
  const state = { entries: [inEntries], pending: [inPending] };
  assert.equal(U.findEntry(state, 5), inEntries);
});

test("findEntry: not found anywhere returns null", () => {
  const state = { entries: [{ seq: 1 }], pending: [{ seq: 2 }] };
  assert.equal(U.findEntry(state, 99), null);
});

test("findEntry: a null/undefined seq is never a match", () => {
  const state = { entries: [{ seq: null }], pending: [] };
  assert.equal(U.findEntry(state, null), null);
});
