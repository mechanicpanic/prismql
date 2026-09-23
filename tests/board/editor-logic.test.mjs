// Pins the editor's pure helpers (graph @aleph/prismql, node #63; task-6
// brief): max-groups clamping, the /evaluate body it actually sends, the
// 422 → inline-error shape (line:column for syntax, message-only for
// runtime), which journal entry a finished run resolves to, and the
// recent-queries list.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const L = require("../../src/prismql/server/board/editor-logic.js");

test("clampMax: blank or unset sends nothing — the server's own default applies", () => {
  assert.equal(L.clampMax(""), null);
  assert.equal(L.clampMax(null), null);
  assert.equal(L.clampMax(undefined), null);
});

test("clampMax: garbage input sends nothing", () => {
  assert.equal(L.clampMax("abc"), null);
  assert.equal(L.clampMax(NaN), null);
});

test("clampMax: clamps below 1 up to 1, never below", () => {
  assert.equal(L.clampMax("0"), 1);
  assert.equal(L.clampMax("-5"), 1);
});

test("clampMax: a valid count is floored and passed through", () => {
  assert.equal(L.clampMax("12"), 12);
  assert.equal(L.clampMax(7.9), 7);
});

test("buildEvaluateBody: omits corpus and max_results the user never set", () => {
  const body = L.buildEvaluateBody({ query: "SELECT $a", corpus: "", max: "", hydrate: false });
  assert.deepEqual(body, { query: "SELECT $a", hydrate: false });
});

test("buildEvaluateBody: carries corpus, clamped max and hydrate through", () => {
  const body = L.buildEvaluateBody({ query: "SELECT $a", corpus: "village", max: "0", hydrate: true });
  assert.deepEqual(body, { query: "SELECT $a", hydrate: true, corpus: "village", max_results: 1 });
});

test("describeError: a syntax 422 carries line:column", () => {
  const d = L.describeError(422, { error: { type: "syntax", message: "unexpected token", line: 3, column: 12 } });
  assert.deepEqual(d, { pos: "3:12", message: "unexpected token" });
});

test("describeError: a runtime 422 has no position", () => {
  const d = L.describeError(422, { error: { type: "runtime", message: "unknown corpus 'x'" } });
  assert.deepEqual(d, { pos: null, message: "unknown corpus 'x'" });
});

test("describeError: any other status describes itself with status + message", () => {
  const d = L.describeError(429, { error: { type: "rate_limit", message: "Too many queries — try again in a minute." } });
  assert.equal(d.pos, null);
  assert.equal(d.message, "HTTP 429 · Too many queries — try again in a minute.");
});

test("describeError: no body at all (network failure) still describes itself", () => {
  const d = L.describeError(0, null);
  assert.equal(d.pos, null);
  assert.match(d.message, /request failed/);
});

test("findPendingMatch: matches by result_id, ignoring who !== board and other result_ids", () => {
  const entries = [
    { who: "10.0.0.1", result_id: "r1", ts: "2026-01-01T00:00:02Z" },
    { who: "board", result_id: "r2", ts: "2026-01-01T00:00:01Z" },
    { who: "board", result_id: "r1", ts: "2026-01-01T00:00:00Z" },
  ];
  const found = L.findPendingMatch(entries, { resultId: "r1", query: "x", sinceMs: 0 });
  assert.equal(found, entries[2]);
});

test("findPendingMatch: an aggregate (no result_id) matches by query + timing", () => {
  const sinceMs = Date.parse("2026-01-01T00:00:00Z");
  const entries = [
    { who: "board", result_id: null, query: "SELECT count($a)", ts: "2026-01-01T00:00:05Z" },
    { who: "board", result_id: null, query: "SELECT count($a)", ts: "2025-12-31T23:59:00Z" }, // before the run — not it
  ];
  const found = L.findPendingMatch(entries, { resultId: null, query: "SELECT count($a)", sinceMs: sinceMs });
  assert.equal(found, entries[0]);
});

test("findPendingMatch: no pending run means no match", () => {
  assert.equal(L.findPendingMatch([{ who: "board" }], null), null);
});

test("recentQueries: only who === board, newest first, capped at 5", () => {
  const entries = [
    { who: "board", seq: 6 }, { who: "agent-1", seq: 5 }, { who: "board", seq: 4 },
    { who: "board", seq: 3 }, { who: "board", seq: 2 }, { who: "board", seq: 1 }, { who: "board", seq: 0 },
  ];
  const rec = L.recentQueries(entries);
  assert.deepEqual(rec.map((e) => e.seq), [6, 4, 3, 2, 1]);
});

test("singleLine: collapses a multi-line query for the compact list", () => {
  assert.equal(L.singleLine("SELECT $a\n  FOLLOWED_BY $b\nWITHIN 5m"), "SELECT $a FOLLOWED_BY $b WITHIN 5m");
});
