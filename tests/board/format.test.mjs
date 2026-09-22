import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const F = require("../../src/prismql/server/board/format.js");

// --- status ---

test("status: error when ok is false", () => {
  assert.equal(F.status({ ok: false, error: { type: "syntax" } }), "error");
});

test("status: empty by total 0", () => {
  assert.equal(
    F.status({ ok: true, result: "groups", total: 0, truncated: false }),
    "empty",
  );
});

test("status: empty by hits count 0", () => {
  assert.equal(
    F.status({ ok: true, result: "hits", count: 0, total: 5, truncated: false }),
    "empty",
  );
});

test("status: capped when ok and truncated", () => {
  assert.equal(
    F.status({ ok: true, result: "groups", total: 3, truncated: true }),
    "capped",
  );
});

test("status: aggregate is ok", () => {
  assert.equal(
    F.status({
      ok: true,
      result: "aggregate",
      value: 50,
      count: null,
      total: null,
      truncated: false,
    }),
    "ok",
  );
});

// --- resultLabel ---

test("resultLabel: groups, not capped", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "groups", total: 6, truncated: false }),
    "6 groups",
  );
});

test("resultLabel: groups, capped", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "groups", total: 3, truncated: true }),
    "3 groups · capped",
  );
});

test("resultLabel: named behaves like groups", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "named", total: 12, truncated: false }),
    "12 groups",
  );
});

test("resultLabel: hits with a threshold", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "hits", total: 8, threshold: 0.6 }),
    "8 hits ≥ 0.6",
  );
});

test("resultLabel: hits without a threshold", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "hits", total: 5, threshold: null }),
    "5 hits",
  );
});

test("resultLabel: aggregate", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "aggregate", value: 181 }),
    "= 181",
  );
});

test("resultLabel: syntax error", () => {
  assert.equal(
    F.resultLabel({ ok: false, error: { type: "syntax", message: "bad" } }),
    "syntax error",
  );
});

test("resultLabel: runtime error and rate limited", () => {
  assert.equal(
    F.resultLabel({ ok: false, error: { type: "runtime" } }),
    "runtime error",
  );
  assert.equal(
    F.resultLabel({ ok: false, error: { type: "rate_limit" } }),
    "rate limited",
  );
  assert.equal(
    F.resultLabel({ ok: false, error: { type: "forbidden" } }),
    "forbidden",
  );
});

test("resultLabel: file output adds arrow", () => {
  assert.equal(
    F.resultLabel({
      ok: true,
      result: "groups",
      total: 47,
      truncated: false,
      output: "file",
    }),
    "47 groups → file",
  );
});

// --- gapLabel ---

test("gapLabel: positions and times", () => {
  assert.deepEqual(
    F.gapLabel(
      57592,
      57603,
      "2025-09-03T19:30:48+00:00",
      "2025-09-03T19:32:31+00:00",
    ),
    { plus: "+1 min", label: "10 events between" },
  );
});

test("gapLabel: null time yields empty plus", () => {
  const g = F.gapLabel(57592, 57603, null, "2025-09-03T19:32:31+00:00");
  assert.equal(g.plus, "");
  assert.equal(g.label, "10 events between");
});

test("gapLabel: zero gap reads 0 events between", () => {
  const g = F.gapLabel(10, 11, null, null);
  assert.equal(g.label, "0 events between");
});

// --- rel ---

test("rel boundaries", () => {
  assert.equal(F.rel(9), "just now");
  assert.equal(F.rel(10), "10 s ago");
  assert.equal(F.rel(59), "59 s ago");
  assert.equal(F.rel(60), "1 min ago");
  assert.equal(F.rel(3599), "59 min ago");
  assert.equal(F.rel(3600), "1 h ago");
  assert.equal(F.rel(86400), "1 d ago");
});

// --- dur ---

test("dur formats", () => {
  assert.equal(F.dur(212), "212 ms");
  assert.equal(F.dur(1234), "1.2 s");
  assert.equal(F.dur(30000), "30 s");
});

// --- hms / dayLabel (timezone-independent: derive expectations from Date accessors) ---

test("hms: local time HH:MM:SS", () => {
  const iso = "2026-09-22T19:12:34.107+00:00";
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  const expected = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  assert.equal(F.hms(iso), expected);
});

test("dayLabel: today", () => {
  const iso = "2026-09-22T19:12:34.107+00:00";
  const nowMs = new Date(iso).getTime() + 60000;
  const d = new Date(iso);
  const result = F.dayLabel(iso, nowMs);
  assert.equal(result.label, "Today");
  assert.equal(result.key, `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`);
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  assert.equal(result.sub, `${DOW[d.getDay()]} ${d.getDate()} ${MON[d.getMonth()]}`);
});

test("dayLabel: yesterday", () => {
  const iso = "2026-09-21T19:12:34+00:00";
  const nowMs = new Date("2026-09-22T19:12:34+00:00").getTime();
  assert.equal(F.dayLabel(iso, nowMs).label, "Yesterday");
});

test("dayLabel: older day uses weekday", () => {
  const iso = "2026-09-15T19:12:34+00:00";
  const nowMs = new Date("2026-09-22T19:12:34+00:00").getTime();
  const d = new Date(iso);
  const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  assert.equal(F.dayLabel(iso, nowMs).label, DOW[d.getDay()]);
});

// --- span ---

test("span: last minus first", () => {
  const times = [
    "2025-09-03T19:30:00+00:00",
    "2025-09-03T19:41:00+00:00",
    "2025-09-03T19:47:00+00:00",
  ];
  assert.equal(F.span(times), "17 min");
});

test("span: empty list", () => {
  assert.equal(F.span([]), "—");
  assert.equal(F.span(null), "—");
});

// --- isAgent ---

test("isAgent classification", () => {
  assert.equal(F.isAgent("board"), false);
  assert.equal(F.isAgent("127.0.0.1"), false);
  assert.equal(F.isAgent("codex"), true);
});

// --- highlightParts ---

test("highlightParts: plain text with no terms", () => {
  assert.deepEqual(F.highlightParts("hello world", []), [
    { t: "hello world", m: false },
  ]);
});

test("highlightParts: matches case-insensitively", () => {
  const parts = F.highlightParts("Hello World", ["world"]);
  assert.deepEqual(parts, [
    { t: "Hello ", m: false },
    { t: "World", m: true },
  ]);
});

test("highlightParts: escapes regex metacharacters", () => {
  const parts = F.highlightParts("price is $5.00 today", ["$5.00"]);
  const matched = parts.filter((p) => p.m).map((p) => p.t);
  assert.deepEqual(matched, ["$5.00"]);
});

// --- searchTerms ---

test("searchTerms: quoted phrases, bare words, dropped operators and field prefixes", () => {
  assert.deepEqual(
    F.searchTerms('"verification code" OR password AND text:spike'),
    ["verification code", "password", "spike"],
  );
});

// --- matches / facetCounts ---

const NOW = new Date("2026-09-22T20:00:00+00:00").getTime();

function entry(overrides) {
  return Object.assign(
    {
      kind: "evaluate",
      corpus: "village",
      who: "board",
      ts: "2026-09-22T19:59:00+00:00",
      query: "SELECT field(kind, REQUEST_HUMAN_HELPER)",
      ok: true,
      result: "groups",
      total: 6,
      truncated: false,
    },
    overrides,
  );
}

test("matches: kind filter", () => {
  const e = entry({ kind: "search" });
  assert.equal(F.matches(e, { kinds: { search: true } }, NOW), true);
  assert.equal(F.matches(e, { kinds: { evaluate: true } }, NOW), false);
});

test("matches: source filter", () => {
  const e = entry({ who: "codex" });
  assert.equal(F.matches(e, { srcs: { codex: true } }, NOW), true);
  assert.equal(F.matches(e, { srcs: { board: true } }, NOW), false);
});

test("matches: corpus filter", () => {
  const e = entry({ corpus: "wiki" });
  assert.equal(F.matches(e, { corpora: { wiki: true } }, NOW), true);
  assert.equal(F.matches(e, { corpora: { village: true } }, NOW), false);
});

test("matches: status filter", () => {
  const e = entry({ ok: false, error: { type: "syntax" } });
  assert.equal(F.matches(e, { statuses: { error: true } }, NOW), true);
  assert.equal(F.matches(e, { statuses: { ok: true } }, NOW), false);
});

test("matches: search filter over query/who/corpus/label", () => {
  const e = entry({ query: "SELECT field(kind, REQUEST_HUMAN_HELPER)" });
  assert.equal(F.matches(e, { search: "human_helper" }, NOW), true);
  assert.equal(F.matches(e, { search: "nope-not-there" }, NOW), false);
});

test("matches: range cut-off", () => {
  const e = entry({ ts: "2026-09-22T19:00:00+00:00" }); // 1h before NOW
  assert.equal(F.matches(e, { range: 3600 }, NOW), true);
  assert.equal(F.matches(e, { range: 1800 }, NOW), false);
  assert.equal(F.matches(e, { range: 0 }, NOW), true); // 0 = no cutoff
});

test("facetCounts excludes its own key", () => {
  const entries = [
    entry({ kind: "evaluate" }),
    entry({ kind: "search" }),
    entry({ kind: "search" }),
  ];
  const counts = F.facetCounts(
    entries,
    { kinds: { evaluate: true } },
    NOW,
    "kinds",
    ["evaluate", "search"],
  );
  // the "kinds" filter itself is skipped when counting the "kinds" facet
  assert.deepEqual(counts, { evaluate: 1, search: 2 });
});

// --- lexJson ---

test("lexJson: tokenizes a small object", () => {
  const toks = F.lexJson('{"a":1,"b":"x"}');
  const joined = toks.map((t) => t.t).join("");
  assert.equal(joined, '{"a": 1, "b": "x"}');
  assert.ok(toks.some((t) => t.c === "tk-fn" && t.t === '"a"'));
  assert.ok(toks.some((t) => t.c === "tk-num" && t.t === "1"));
});
