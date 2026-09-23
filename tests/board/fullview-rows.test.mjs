// Pins the pure row/item shaping for the full view's table, timeline nav
// and vertical timeline — kept window-free so it is node-testable without
// a fake DOM (task-7 brief; graph @aleph/prismql, node #76). Pairing a
// group's events to its slots by id (not index) is inspector-page-logic's
// job (fix round 1, #7); these builders take already-paired `slots`.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const FR = require("../../src/prismql/server/board/fullview-rows.js");

const board = { kind: "kind", actor: "agent" };

// --- tableHeadsFor ---

test("tableHeadsFor: groups columns", () => {
  const t = FR.tableHeadsFor("groups", false);
  assert.deepEqual(t.heads, ["group", "#", "time", "kind", "agent", "text"]);
  assert.match(t.cols, /^56px 44px/);
});
test("tableHeadsFor: hits columns say 'score' when scored, 'match' otherwise", () => {
  assert.deepEqual(FR.tableHeadsFor("hits", true).heads, ["score", "time", "kind", "agent", "text"]);
  assert.deepEqual(FR.tableHeadsFor("hits", false).heads, ["match", "time", "kind", "agent", "text"]);
});

// --- groupTableRows ---

test("groupTableRows: one row per slot, the group number only on the first row", () => {
  const groups = [
    { n: 1, ids: ["a", "b"], times: ["2026-06-03T18:02:11Z", "2026-06-03T18:19:40Z"], slots: [
      { kind: "K1", agent: "x", text: "hi" },
      { kind: "K2", agent: "y", text: "there" },
    ] },
  ];
  const rows = FR.groupTableRows(groups, board);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].group, 1);
  assert.equal(rows[0].cls, "first");
  assert.equal(rows[1].group, "");
  assert.equal(rows[1].cls, "");
  assert.equal(rows[0].kind, "K1");
  assert.equal(rows[1].text, "there");
});
// A grid cell, not a wrapping one: the server's full ISO instant
// (microseconds, offset) must never reach the DOM as-is — it overruns the
// fixed TIME column into KIND next to it.
test("groupTableRows: ts is the short local form, never the raw ISO instant", () => {
  const groups = [{ n: 1, ids: ["a"], times: ["2026-06-03T18:02:11.429124+00:00"], slots: [{}] }];
  const rows = FR.groupTableRows(groups, board);
  assert.equal(rows[0].ts.indexOf("."), -1, "no fractional seconds leak through");
  assert.equal(rows[0].ts.indexOf("+"), -1, "no UTC offset leaks through");
});
test("groupTableRows: a null time renders without a ts, not a formatted 'Invalid Date'", () => {
  const groups = [{ n: 1, ids: ["a"], times: [null], slots: [{}] }];
  const rows = FR.groupTableRows(groups, board);
  assert.equal(rows[0].ts, null);
});
test("groupTableRows: a slot with no matching event renders without kind/actor/text", () => {
  const groups = [{ n: 1, ids: ["a"], times: [null], slots: [null] }];
  const rows = FR.groupTableRows(groups, board);
  assert.equal(rows[0].kind, null);
  assert.equal(rows[0].actor, null);
  assert.equal(rows[0].text, null);
});
test("groupTableRows: multiple groups concatenate in order", () => {
  const groups = [
    { n: 1, ids: ["a"], times: ["t1"], slots: [{ kind: "A", agent: "x" }] },
    { n: 2, ids: ["b"], times: ["t2"], slots: [{ kind: "B", agent: "y" }] },
  ];
  const rows = FR.groupTableRows(groups, board);
  assert.deepEqual(rows.map((r) => r.group), [1, 2]);
});

// --- hitTableRows ---

test("hitTableRows: scored hits carry a formatted score and a percent bar width", () => {
  const hits = [{ score: 0.8123, time: "2026-06-03T18:02:11.429124+00:00", event: { kind: "K", agent: "a", text: "abc" } }];
  const rows = FR.hitTableRows(hits, board, [], true);
  assert.equal(rows[0].score, "0.812");
  assert.equal(rows[0].pct, "81.23%");
  assert.equal(rows[0].kind, "K");
  assert.equal(rows[0].actor, "a");
  assert.equal(rows[0].ts.indexOf("."), -1, "the table's ts is the short local form, not the raw ISO instant");
});
test("hitTableRows: unscored (search) hits never surface a BM25 number", () => {
  const hits = [{ score: 5.4, time: "t1", event: { text: "abc" } }];
  const rows = FR.hitTableRows(hits, board, [], false);
  assert.equal(rows[0].score, "match");
  assert.equal(rows[0].pct, null);
});
test("hitTableRows: highlight parts come from the search terms", () => {
  const hits = [{ score: 1, time: "t1", event: { text: "the password field" } }];
  const rows = FR.hitTableRows(hits, board, ["password"], false);
  assert.equal(rows[0].parts.some((p) => p.m && p.t === "password"), true);
});

// --- timelineItems ---

test("timelineItems: alternates gap/event, no gap before the first slot", () => {
  const group = {
    ids: ["a", "b"], positions: [10, 41], times: ["2026-06-03T18:02:11Z", "2026-06-03T18:19:40Z"],
    slots: [{ kind: "K1", agent: "x", text: "hi" }, { kind: "K2", agent: "y", text: null }],
  };
  const items = FR.timelineItems(group, board);
  assert.equal(items.length, 3);
  assert.equal(items[0].isGap, false);
  assert.equal(items[0].n, 1);
  assert.equal(items[1].isGap, true);
  assert.ok(items[1].plus);
  assert.equal(items[2].isGap, false);
  assert.equal(items[2].n, 2);
  assert.equal(items[2].kind, "K2");
});
test("timelineItems: a null slot renders without kind/actor/text", () => {
  const group = { ids: ["a"], positions: [0], times: [null], slots: [null] };
  const items = FR.timelineItems(group, board);
  assert.equal(items[0].kind, null);
  assert.equal(items[0].text, null);
});

// --- navItemFor ---

test("navItemFor: snippet prefers the first slot with real text", () => {
  const group = {
    n: 3, times: ["2026-06-03T18:02:11Z", "2026-06-03T18:19:40Z"],
    slots: [{ agent: "gemini", text: "" }, { agent: "gemini", text: "the real text" }],
  };
  const item = FR.navItemFor(group, board);
  assert.equal(item.n, 3);
  assert.equal(item.actor, "gemini");
  assert.equal(item.snip, "the real text");
});
test("navItemFor: no actor field means an empty actor, not a guess", () => {
  const group = { n: 1, times: [], slots: [{ text: "hi" }] };
  const item = FR.navItemFor(group, {});
  assert.equal(item.actor, "");
});

// --- groupHeaderInfo ---

test("groupHeaderInfo: range runs from the first to the last real time", () => {
  const group = {
    n: 2, times: ["2026-06-03T18:02:11Z", "2026-06-03T18:19:40Z"],
    slots: [{ agent: "gemini" }, { agent: "gemini" }],
  };
  const info = FR.groupHeaderInfo(group, 6, board);
  assert.equal(info.n, 2);
  assert.equal(info.total, 6);
  assert.equal(info.actor, "gemini");
  assert.match(info.range, /\d{2}:\d{2}:\d{2} → \d{2}:\d{2}:\d{2}/);
});
