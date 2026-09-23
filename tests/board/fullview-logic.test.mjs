// Pins the pure logic behind the full-screen output view (task-7 brief):
// time-range labels, the load/match note, which views a result kind gets,
// text/actor filtering of loaded groups and hits, and the summary tiles —
// all derived from real loaded data only, never invented (global-
// constraints.md; graph @aleph/prismql, node #76).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const FL = require("../../src/prismql/server/board/fullview-logic.js");

// --- timeRangeLabel ---

test("timeRangeLabel: no times loaded", () => {
  assert.equal(FL.timeRangeLabel([]), "—");
  assert.equal(FL.timeRangeLabel([null, null]), "—");
});
test("timeRangeLabel: a single day", () => {
  assert.equal(FL.timeRangeLabel(["2026-06-03T18:02:11Z"]), "Jun 3");
});
test("timeRangeLabel: same month, different days", () => {
  assert.equal(FL.timeRangeLabel(["2026-06-08T16:30:02Z", "2026-06-03T18:02:11Z"]), "Jun 3–8");
});
test("timeRangeLabel: crossing months", () => {
  assert.equal(FL.timeRangeLabel(["2026-06-30T00:00:00Z", "2026-07-02T00:00:00Z"]), "Jun 30–Jul 2");
});
test("timeRangeLabel: crossing years shows both years", () => {
  assert.equal(
    FL.timeRangeLabel(["2025-12-31T00:00:00Z", "2026-01-01T00:00:00Z"]),
    "Dec 31 2025–Jan 1 2026",
  );
});
test("timeRangeLabel: null entries are dropped, not treated as a boundary", () => {
  assert.equal(FL.timeRangeLabel([null, "2026-06-03T18:02:11Z", null]), "Jun 3");
});

// --- loadNote ---

test("loadNote: no filter", () => {
  assert.equal(FL.loadNote(50, 371, null), "50 of 371 loaded");
});
test("loadNote: filter narrows the loaded set", () => {
  assert.equal(FL.loadNote(50, 371, 12), "12 of 50 match · 50 of 371 loaded");
});
test("loadNote: a filter matching everything loaded reads as no filter", () => {
  assert.equal(FL.loadNote(50, 371, 50), "50 of 371 loaded");
});
test("loadNote: everything loaded", () => {
  assert.equal(FL.loadNote(6, 6, null), "6 of 6 loaded");
});

// --- viewsFor ---

test("viewsFor: groups get timeline/table/raw", () => {
  assert.deepEqual(FL.viewsFor("groups"), ["timeline", "table", "raw"]);
});
test("viewsFor: hits get table/raw only", () => {
  assert.deepEqual(FL.viewsFor("hits"), ["table", "raw"]);
});
test("viewsFor: aggregate/grouped/file/error/empty get summary/raw", () => {
  ["aggregate", "grouped", "file", "error", "empty"].forEach((k) => {
    assert.deepEqual(FL.viewsFor(k), ["summary", "raw"]);
  });
});

// --- fieldText / actorOf ---

test("fieldText: joins configured kind+actor+text, lowercased", () => {
  const board = { kind: "kind", actor: "agent" };
  const event = { kind: "AGENT_TALK", agent: "Gemini", text: "Hello There" };
  assert.equal(FL.fieldText(event, board), "agent_talk gemini hello there");
});
test("fieldText: an unset field is left out, never guessed", () => {
  assert.equal(FL.fieldText({ text: "hi" }, {}), "hi");
});
test("fieldText: a null event is empty", () => {
  assert.equal(FL.fieldText(null, { kind: "kind" }), "");
});
test("actorOf: reads the configured actor field", () => {
  assert.equal(FL.actorOf({ agent: "Gemini" }, { actor: "agent" }), "Gemini");
});
test("actorOf: null when the corpus has no actor field", () => {
  assert.equal(FL.actorOf({ agent: "Gemini" }, {}), null);
});

// --- groupPassesFilter ---

const board = { kind: "kind", actor: "agent" };

test("groupPassesFilter: no filter always passes", () => {
  const slots = [{ kind: "A", agent: "x", text: "hi" }];
  assert.equal(FL.groupPassesFilter(slots, board, "", {}), true);
});
test("groupPassesFilter: text filter matches any slot", () => {
  const slots = [{ kind: "A", agent: "x", text: "first" }, { kind: "B", agent: "y", text: "second" }];
  assert.equal(FL.groupPassesFilter(slots, board, "second", {}), true);
  assert.equal(FL.groupPassesFilter(slots, board, "third", {}), false);
});
test("groupPassesFilter: agent chip matches only the LEAD (first) slot's actor", () => {
  const slots = [{ kind: "A", agent: "lead" }, { kind: "B", agent: "other" }];
  assert.equal(FL.groupPassesFilter(slots, board, "", { lead: true }), true);
  assert.equal(FL.groupPassesFilter(slots, board, "", { other: true }), false);
});
test("groupPassesFilter: a null lead slot never matches an agent chip", () => {
  const slots = [null, { kind: "B", agent: "other" }];
  assert.equal(FL.groupPassesFilter(slots, board, "", { other: true }), false);
});

// --- hitPassesFilter ---

test("hitPassesFilter: text and agent filters over the hit's event", () => {
  const hit = { event: { kind: "SEARCH", agent: "codex", text: "help me" } };
  assert.equal(FL.hitPassesFilter(hit, board, "help", {}), true);
  assert.equal(FL.hitPassesFilter(hit, board, "nope", {}), false);
  assert.equal(FL.hitPassesFilter(hit, board, "", { codex: true }), true);
  assert.equal(FL.hitPassesFilter(hit, board, "", { other: true }), false);
});
test("hitPassesFilter: a hit with no event never matches an agent chip", () => {
  assert.equal(FL.hitPassesFilter({}, board, "", { x: true }), false);
});

// --- agentChipList ---

test("agentChipList: dedupes, keeps first-seen order, carries selection", () => {
  const chips = FL.agentChipList(["gemini", "codex", "gemini", "opus"], { codex: true });
  assert.deepEqual(chips, [
    { label: "gemini", on: false },
    { label: "codex", on: true },
    { label: "opus", on: false },
  ]);
});
test("agentChipList: null/undefined values are skipped", () => {
  assert.deepEqual(FL.agentChipList([null, "a", undefined], {}), [{ label: "a", on: false }]);
});

// --- countEvents / allTimes / topScore ---

test("countEvents: sums each loaded group's slot count", () => {
  assert.equal(FL.countEvents([{ ids: ["a", "b"] }, { ids: ["c"] }]), 3);
});
test("allTimes: flattens every loaded group's times", () => {
  assert.deepEqual(FL.allTimes([{ times: ["t1", null] }, { times: ["t2"] }]), ["t1", null, "t2"]);
});
test("topScore: the highest score among loaded hits", () => {
  assert.equal(FL.topScore([{ score: 0.5 }, { score: 0.9 }, { score: 0.3 }]), 0.9);
});
test("topScore: null when nothing is loaded", () => {
  assert.equal(FL.topScore([]), null);
});

// --- groupsTiles / hitsTiles ---

test("groupsTiles: with an actor field configured", () => {
  assert.deepEqual(FL.groupsTiles(2, 6, 4, 3, true, "Jun 3–8"), [
    { v: "2 / 6", l: "groups loaded" },
    { v: "4", l: "events" },
    { v: "3", l: "actors" },
    { v: "Jun 3–8", l: "time range" },
  ]);
});
test("groupsTiles: the actors tile is omitted when the corpus has no actor field", () => {
  const tiles = FL.groupsTiles(2, 6, 4, 0, false, "Jun 3–8");
  assert.equal(tiles.some((t) => t.l === "actors"), false);
  assert.equal(tiles.length, 3);
});

// Fix round 1, #12/13: at most 4 tiles (the canvas's fixed 4-column grid)
// — a "kept" tile would make a 5th; "kept" moves to the note instead
// (hitsNote, below), never a tile.
test("hitsTiles: similar shows a top score, not BM25 for search", () => {
  const tiles = FL.hitsTiles(3, 35, true, 0.812, 3, true, "Jun 3–8");
  assert.deepEqual(tiles, [
    { v: "3 / 35", l: "hits loaded" },
    { v: "0.812", l: "top score" },
    { v: "3", l: "sources" },
    { v: "Jun 3–8", l: "time range" },
  ]);
});
test("hitsTiles: search shows 'exact', never a score", () => {
  const tiles = FL.hitsTiles(1, 1, false, null, 1, true, "Jun 5");
  assert.deepEqual(tiles[1], { v: "exact", l: "match type" });
});
test("hitsTiles: never a 'kept' tile, even when the store kept fewer than the total found", () => {
  const tiles = FL.hitsTiles(3, 181, true, 0.9, 2, true, "Jun 3");
  assert.equal(tiles.some((t) => t.l === "kept"), false);
  assert.equal(tiles.length, 4);
});
test("hitsTiles: the sources tile is omitted without an actor field — never more than 3 tiles then", () => {
  const tiles = FL.hitsTiles(3, 35, true, 0.8, 0, false, "Jun 3");
  assert.equal(tiles.some((t) => t.l === "sources"), false);
  assert.equal(tiles.length, 3);
});
// Fix round 1, #2: topScore([]) is null — never render "0.000" as if it
// were a real score.
test("hitsTiles: a null top score (nothing scored yet) reads '—', never '0.000'", () => {
  const tiles = FL.hitsTiles(0, 35, true, null, 0, true, "—");
  assert.equal(tiles[1].v, "—");
});

// --- hitsNote (fix round 1, #5/#12: the Load-more row drops its own
// count — "kept" lives in the note instead, never a 5th tile) ---

test("hitsNote: no filter, kept === total", () => {
  assert.equal(FL.hitsNote(50, 2735, null, 2735), "50 of 2735 loaded");
});
test("hitsNote: kept < total appends 'kept K'", () => {
  assert.equal(FL.hitsNote(50, 2735, null, 1000), "50 of 2735 loaded · kept 1000");
});
test("hitsNote: a filter's match count still comes first", () => {
  assert.equal(FL.hitsNote(50, 2735, 12, 1000), "12 of 50 match · 50 of 2735 loaded · kept 1000");
});
test("hitsNote: kept === null (groups have no kept concept) never appends anything", () => {
  assert.equal(FL.hitsNote(50, 10764, null, null), "50 of 10764 loaded");
});

// --- PAGE (fix round 1, #8: one shared constant, not three literal 50s) ---

test("PAGE is the one page-size constant the whole full view shares", () => {
  assert.equal(FL.PAGE, 50);
});
