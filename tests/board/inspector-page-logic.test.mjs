// Pins the pure page-fetch logic pulled out for fix round 1: which JSON
// shapes count as a real page (#2), the per-group aggregate wording (#6),
// and pairing a group's events to its slots by id rather than index (#7).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const PL = require("../../src/prismql/server/board/inspector-page-logic.js");

// --- fieldsFor ---

test("fieldsFor: text only when the corpus configures neither kind nor actor", () => {
  assert.deepEqual(PL.fieldsFor({}), ["text"]);
});
test("fieldsFor: adds kind/actor when configured", () => {
  assert.deepEqual(PL.fieldsFor({ kind: "kind", actor: "agent" }), ["text", "kind", "agent"]);
});
test("fieldsFor: a falsy board behaves like an empty one", () => {
  assert.deepEqual(PL.fieldsFor(null), ["text"]);
});

// --- cacheKey ---

test("cacheKey: rid|offset|limit|fields, fields sorted regardless of input order", () => {
  assert.equal(PL.cacheKey("r1", 0, 2, ["kind", "actor", "text"]), "r1|0|2|actor,kind,text");
  assert.equal(PL.cacheKey("r1", 0, 2, ["text", "actor", "kind"]), "r1|0|2|actor,kind,text");
});
test("cacheKey: a text-only fetch (corpora not loaded) never collides with a fully-fielded one", () => {
  const before = PL.cacheKey("r1", 0, 2, ["text"]);
  const after = PL.cacheKey("r1", 0, 2, ["text", "kind", "agent"]);
  assert.notEqual(before, after);
});

// --- isValidPage / errorMessageFor (fix round 1, #2) ---

test("isValidPage: a groups/named page (results array, even empty)", () => {
  assert.equal(PL.isValidPage({ results: [] }), true);
  assert.equal(PL.isValidPage({ results: [{ ids: ["a"] }] }), true);
});
test("isValidPage: a hits page", () => {
  assert.equal(PL.isValidPage({ hits: [] }), true);
});
test("isValidPage: a rows page (GROUP BY ... AGGREGATE, graph @aleph/prismql, #90)", () => {
  assert.equal(PL.isValidPage({ rows: [] }), true);
  assert.equal(PL.isValidPage({ rows: [{ key: "a", value: 1 }] }), true);
});
test("isValidPage: a gone page", () => {
  assert.equal(PL.isValidPage({ gone: true }), true);
});
test("isValidPage: a 429/5xx {ok:false,error:{...}} body is not a page", () => {
  assert.equal(PL.isValidPage({ ok: false, error: { type: "rate_limit", message: "slow down" } }), false);
});
test("isValidPage: an unrelated FastAPI {detail:...} body is not a page", () => {
  assert.equal(PL.isValidPage({ detail: "Not Found" }), false);
});
test("isValidPage: null/undefined is not a page", () => {
  assert.equal(PL.isValidPage(null), false);
  assert.equal(PL.isValidPage(undefined), false);
});

test("errorMessageFor: surfaces the server's own error message when present", () => {
  assert.equal(PL.errorMessageFor({ error: { message: "slow down" } }), "slow down");
});
test("errorMessageFor: a generic message for an unrecognized JSON body", () => {
  assert.equal(PL.errorMessageFor({ detail: "Not Found" }), "the server answered without a page");
  assert.equal(PL.errorMessageFor(null), "the server answered without a page");
});

// --- label builders ---

test("groupsMoreLabel: showing k of total", () => {
  assert.equal(PL.groupsMoreLabel(2, 75307), "showing 2 of 75307");
});
test("hitsNote: k of total", () => {
  assert.equal(PL.hitsNote(3, 35), "3 of 35");
});
test("isScored: only similar carries a score", () => {
  assert.equal(PL.isScored("similar"), true);
  assert.equal(PL.isScored("search"), false);
  assert.equal(PL.isScored("evaluate"), false);
});

// --- aggregateValueText (fix round 1, #6) ---

test("aggregateValueText: a real value", () => {
  assert.equal(PL.aggregateValueText(173493), "173493");
  assert.equal(PL.aggregateValueText(0), "0");
});
test("aggregateValueText: null (a per-group aggregate) reads 'per group', not '—'", () => {
  assert.equal(PL.aggregateValueText(null), "per group");
  assert.equal(PL.aggregateValueText(undefined), "per group");
});

// --- rowValueText (graph @aleph/prismql, #90) ---

test("rowValueText: a number renders as-is", () => {
  assert.equal(PL.rowValueText(3), "3");
  assert.equal(PL.rowValueText(0), "0");
});
test("rowValueText: a distinct list joins with ', '", () => {
  assert.equal(PL.rowValueText(["a", "b", "c"]), "a, b, c");
  assert.equal(PL.rowValueText([]), "");
});
// Fix round 1, #5: a null value read as the literal string "null" —
// render it as the board's own empty marker instead.
test("rowValueText: null/undefined renders as '—', not the literal 'null'", () => {
  assert.equal(PL.rowValueText(null), "—");
  assert.equal(PL.rowValueText(undefined), "—");
});

// --- pairEventsToSlots (fix round 1, #7) ---

test("pairEventsToSlots: events already aligned with ids", () => {
  const ids = ["a", "b", "c"];
  const events = [{ id: "a", text: "1" }, { id: "b", text: "2" }, { id: "c", text: "3" }];
  assert.deepEqual(PL.pairEventsToSlots(ids, events).map((e) => e && e.text), ["1", "2", "3"]);
});
test("pairEventsToSlots: a dropped middle id must not shift the later slots", () => {
  const ids = ["a", "b", "c"];
  // the server dropped "b" (couldn't hydrate it) — events is a SHORTER,
  // index-shifted list, not a same-length one with a hole.
  const events = [{ id: "a", text: "1" }, { id: "c", text: "3" }];
  const slots = PL.pairEventsToSlots(ids, events);
  assert.equal(slots[0].text, "1");
  assert.equal(slots[1], null, "the missing id renders the slot without text, not b's neighbor's text");
  assert.equal(slots[2].text, "3");
});
test("pairEventsToSlots: no events at all yields all-null slots", () => {
  assert.deepEqual(PL.pairEventsToSlots(["a", "b"], []), [null, null]);
  assert.deepEqual(PL.pairEventsToSlots(["a", "b"], undefined), [null, null]);
});
test("pairEventsToSlots: no ids yields an empty array", () => {
  assert.deepEqual(PL.pairEventsToSlots([], [{ id: "a" }]), []);
});

test("pairEventsToSlots: pairs by the corpus's own id_field (finding 4), not a hardcoded 'id'", () => {
  const ids = ["a", "b"];
  const events = [{ event_id: "a", text: "1" }, { event_id: "b", text: "2" }];
  const slots = PL.pairEventsToSlots(ids, events, "event_id");
  assert.equal(slots[0].text, "1");
  assert.equal(slots[1].text, "2");
});

test("pairEventsToSlots: idField defaults to 'id' when not given", () => {
  const ids = ["a"];
  const events = [{ id: "a", text: "1" }];
  assert.equal(PL.pairEventsToSlots(ids, events)[0].text, "1");
});

// --- collectRowPages (fix round 1, #1) ---
// The server caps a page's `limit` at `max_results` regardless of what a
// caller requests; the old code fetched growing offset-0 limits (20, 40,
// 60...) and stuck at the server's cap forever. Page in fixed steps from
// growing offsets instead, advancing by the count the server actually
// returned — never the requested step — so a page capped below the step
// never skips or repeats rows.

function fakePage(rows) {
  return { status: "done", data: { rows: rows } };
}

test("collectRowPages: max_results 25, total 60, three clicks (target 20/40/60) load all 60 rows, no repeats", () => {
  const ALL = Array.from({ length: 60 }, (_, i) => ({ key: "k" + i, value: i }));
  const MAX_RESULTS = 25;
  function fetchFn(offset, limit) {
    const capped = Math.min(limit, MAX_RESULTS);
    return fakePage(ALL.slice(offset, offset + capped));
  }
  var seen = [];
  [20, 40, 60].forEach((target) => {
    const res = PL.collectRowPages(60, target, 20, fetchFn);
    assert.equal(res.pending, false);
    seen = res.rows;
  });
  assert.equal(seen.length, 60);
  const keys = seen.map((r) => r.key);
  assert.deepEqual(keys, ALL.map((r) => r.key), "all 60 rows, in order, no repeats");
});

test("collectRowPages: advances by the count actually returned, never the requested step", () => {
  // The first page returns fewer rows than requested (15 of a 20 step) —
  // the next fetch must start at offset 15, not 20, or 5 rows go missing.
  const calls = [];
  function fetchFn(offset, limit) {
    calls.push([offset, limit]);
    if (offset === 0) return fakePage(Array.from({ length: 15 }, (_, i) => ({ key: "k" + i, value: i })));
    return fakePage(Array.from({ length: 10 }, (_, i) => ({ key: "k" + (offset + i), value: offset + i })));
  }
  const res = PL.collectRowPages(25, 25, 20, fetchFn);
  assert.deepEqual(calls, [[0, 20], [15, 20]]);
  assert.equal(res.rows.length, 25);
  assert.deepEqual(res.rows.map((r) => r.key), Array.from({ length: 25 }, (_, i) => "k" + i));
});

test("collectRowPages: a loading page stops and reports pending, keeping rows loaded so far", () => {
  function fetchFn(offset) {
    if (offset === 0) return fakePage([{ key: "a", value: 1 }]);
    return { status: "loading" };
  }
  const res = PL.collectRowPages(10, 10, 1, fetchFn);
  assert.equal(res.pending, true);
  assert.deepEqual(res.rows, [{ key: "a", value: 1 }]);
});

test("collectRowPages: a gone/error page stops and surfaces it", () => {
  function goneFetch() { return { status: "done", data: { gone: true } }; }
  const gone = PL.collectRowPages(10, 10, 5, goneFetch);
  assert.equal(gone.gone, true);

  function errFetch() { return { status: "done", data: { error: { message: "slow down" } } }; }
  const err = PL.collectRowPages(10, 10, 5, errFetch);
  assert.deepEqual(err.error, { message: "slow down" });
});

test("collectRowPages: an empty page before total is reached stops instead of looping forever", () => {
  function fetchFn() { return fakePage([]); }
  const res = PL.collectRowPages(10, 10, 5, fetchFn);
  assert.equal(res.pending, false);
  assert.deepEqual(res.rows, []);
});
