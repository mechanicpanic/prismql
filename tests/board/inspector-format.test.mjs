// Pins the inspector's pure helpers (graph @aleph/prismql, node #63):
// outputKind's type resolution (task-5 brief's exhaustive list), srcKind's
// three-way split (global-constraints.md: board / agent / IP), and
// gapText's "+<Δt> · <Δpos-1> events between" combination.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const IF = require("../../src/prismql/server/board/inspector-format.js");

test("outputKind: a failed request is always an error, regardless of result", () => {
  assert.equal(IF.outputKind({ ok: false, result: "groups" }), "error");
});

test("outputKind: output=file wins over the underlying result kind", () => {
  assert.equal(IF.outputKind({ ok: true, output: "file", result: "groups", path: "x.jsonl" }), "file");
});

test("outputKind: aggregate", () => {
  assert.equal(IF.outputKind({ ok: true, result: "aggregate", value: 5 }), "aggregate");
});

test("outputKind: hits with count 0 is empty, not hits", () => {
  assert.equal(IF.outputKind({ ok: true, result: "hits", count: 0, total: 12 }), "empty");
});

test("outputKind: hits with a positive count", () => {
  assert.equal(IF.outputKind({ ok: true, result: "hits", count: 3, total: 12 }), "hits");
});

test("outputKind: groups/named with total 0 is empty", () => {
  assert.equal(IF.outputKind({ ok: true, result: "groups", total: 0 }), "empty");
  assert.equal(IF.outputKind({ ok: true, result: "named", total: 0 }), "empty");
});

test("outputKind: groups/named with a positive total", () => {
  assert.equal(IF.outputKind({ ok: true, result: "groups", total: 4 }), "groups");
  assert.equal(IF.outputKind({ ok: true, result: "named", total: 4 }), "groups");
});

test("outputKind: grouped (GROUP BY) falls back to its own case", () => {
  assert.equal(IF.outputKind({ ok: true, result: "grouped", count: 3 }), "grouped");
});

test("srcKind: board is a person via the board", () => {
  assert.equal(IF.srcKind("board"), "person, via board");
});

test("srcKind: a non-board, non-IP who is an agent", () => {
  assert.equal(IF.srcKind("codex"), "agent");
});

test("srcKind: an IP address is a person, not an agent", () => {
  assert.equal(IF.srcKind("10.0.0.1"), "person");
});

test("gapText: both halves present", () => {
  assert.equal(
    IF.gapText(1, 12, "2026-09-23T12:00:00Z", "2026-09-23T12:01:00Z"),
    "+1 min · 10 events between",
  );
});

test("gapText: null time drops the '+<Δt>' half", () => {
  assert.equal(IF.gapText(1, 3, null, "2026-09-23T12:01:00Z"), "1 events between");
});

test("gapText: null position drops the 'events between' half", () => {
  assert.equal(IF.gapText(null, null, "2026-09-23T12:00:00Z", "2026-09-23T12:01:00Z"), "+1 min");
});

test("statusLabel maps the four journal statuses", () => {
  assert.equal(IF.statusLabel("ok"), "ok");
  assert.equal(IF.statusLabel("capped"), "capped");
  assert.equal(IF.statusLabel("error"), "failed");
  assert.equal(IF.statusLabel("empty"), "no matches");
});

test("localDateTime: local YYYY-MM-DD HH:MM:SS", () => {
  const iso = new Date(2026, 8, 23, 14, 34, 56).toISOString();
  assert.equal(IF.localDateTime(iso), "2026-09-23 14:34:56");
});

test("whenAbs: day label plus hms, comma-joined", () => {
  const iso = new Date(2026, 8, 23, 14, 34, 56).toISOString();
  const nowMs = new Date(2026, 8, 23, 15, 0, 0).getTime();
  assert.equal(IF.whenAbs(iso, nowMs), "Wed 23 Sep, 14:34:56");
});
