import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const F = require("../../src/prismql/server/board/format.js");
const Lex = require("../../src/prismql/server/board/lexjson.js");

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

test("resultLabel: aggregate with a null value (GROUP BY) reads 'per group'", () => {
  assert.equal(
    F.resultLabel({ ok: true, result: "aggregate", value: null }),
    "= per group",
  );
});

// "grouped" is the small non-list GROUP BY journal shape.
test("resultLabel: grouped with a numeric count", () => {
  assert.equal(F.resultLabel({ ok: true, result: "grouped", count: 5 }), "5 groups");
});

test("resultLabel: grouped without a numeric count falls back to 'grouped'", () => {
  assert.equal(F.resultLabel({ ok: true, result: "grouped", count: null }), "grouped");
  assert.equal(F.resultLabel({ ok: true, result: "grouped" }), "grouped");
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

// resultLabel always returns a string, even with no error.type.
test("resultLabel: failure with no error.type reads 'error'", () => {
  assert.equal(F.resultLabel({ ok: false }), "error");
  assert.equal(F.resultLabel({ ok: false, error: {} }), "error");
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

// --- gapLabel: unordered INWINDOW groups are not clamped ---

test("gapLabel: forward gap, positions and times", () => {
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

test("gapLabel: backward gap is signed, never clamped", () => {
  const t1 = "2025-09-03T19:30:00+00:00";
  const t2 = "2025-09-03T19:31:00+00:00"; // t2 is later than t1
  assert.deepEqual(F.gapLabel(100, 90, t2, t1), {
    plus: "−1 min",
    label: "9 events between",
  });
});

test("gapLabel: null time yields empty plus", () => {
  const g = F.gapLabel(57592, 57603, null, "2025-09-03T19:32:31+00:00");
  assert.equal(g.plus, "");
  assert.equal(g.label, "10 events between");
});

test("gapLabel: adjacent positions read 0 events between", () => {
  const g = F.gapLabel(10, 11, null, null);
  assert.equal(g.label, "0 events between");
});

// Fix round 1, #4: singular only at exactly one event between; 0 stays plural.
test("gapLabel: exactly one event between is singular", () => {
  const g = F.gapLabel(1, 3, null, null);
  assert.equal(g.label, "1 event between");
});

test("gapLabel: the same position reads 'same event'", () => {
  const g = F.gapLabel(42, 42, null, null);
  assert.equal(g.label, "same event");
});

test("gapLabel: undefined/null positions yield an empty label, never NaN", () => {
  assert.equal(F.gapLabel(null, 90, null, null).label, "");
  assert.equal(F.gapLabel(100, undefined, null, null).label, "");
  assert.notEqual(F.gapLabel(null, 90, null, null).label, "NaN events between");
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

// --- dur: rounding, sub-ms, and the 9999ms boundary ---

test("dur: sub-millisecond", () => {
  assert.equal(F.dur(0.43), "<1 ms");
  assert.equal(F.dur(0), "<1 ms");
});

test("dur: rounds whole milliseconds", () => {
  assert.equal(F.dur(212.47), "212 ms");
  assert.equal(F.dur(212), "212 ms");
});

test("dur: one decimal second", () => {
  assert.equal(F.dur(1234), "1.2 s");
});

test("dur: 9999ms reads 10 s, not 10.0 s", () => {
  assert.equal(F.dur(9999), "10 s");
});

test("dur: whole seconds at and above 10000ms", () => {
  assert.equal(F.dur(30000), "30 s");
});

// the ms/s split tests the ROUNDED value, not the raw one.
test("dur: rounding across the 1000ms boundary reads seconds, not 1000 ms", () => {
  assert.equal(F.dur(999.6), "1.0 s");
});

// a missing elapsed_ms must not read "NaN s" or "<1 ms".
test("dur: a missing duration reads an em dash", () => {
  assert.equal(F.dur(undefined), "—");
  assert.equal(F.dur(null), "—");
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

// --- span: drop nulls, max-min, not last-first ---

test("span: last minus first when ascending", () => {
  const times = [
    "2025-09-03T19:30:00+00:00",
    "2025-09-03T19:41:00+00:00",
    "2025-09-03T19:47:00+00:00",
  ];
  assert.equal(F.span(times), "17 min");
});

test("span: all null yields —", () => {
  assert.equal(F.span([null, null]), "—");
  assert.equal(F.span([]), "—");
  assert.equal(F.span(null), "—");
});

test("span: a single non-null time yields 0 s", () => {
  assert.equal(F.span(["2025-09-03T19:30:00+00:00", null]), "0 s");
});

test("span: unordered times yield the positive span, not a negative one", () => {
  const later = "2025-09-03T19:47:00+00:00";
  const earlier = "2025-09-03T19:30:00+00:00";
  assert.equal(F.span([later, earlier]), "17 min");
});

// --- isAgent ---

test("isAgent classification", () => {
  assert.equal(F.isAgent("board"), false);
  assert.equal(F.isAgent("127.0.0.1"), false);
  assert.equal(F.isAgent("codex"), true);
});

test("isAgent: non-string input is false", () => {
  assert.equal(F.isAgent(null), false);
  assert.equal(F.isAgent(undefined), false);
  assert.equal(F.isAgent(42), false);
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

// empty terms are ignored, not turned into a broken regex.
test("highlightParts: ignores empty terms", () => {
  const parts = F.highlightParts("hello world", ["", "world", ""]);
  const matched = parts.filter((p) => p.m).map((p) => p.t);
  assert.deepEqual(matched, ["world"]);
});

test("highlightParts: all-empty terms pass through like no terms", () => {
  assert.deepEqual(F.highlightParts("hello world", ["", ""]), [
    { t: "hello world", m: false },
  ]);
});

// empty text passes through like the no-terms path.
test("highlightParts: empty text", () => {
  assert.deepEqual(F.highlightParts("", ["term"]), [{ t: "", m: false }]);
  assert.deepEqual(F.highlightParts("", []), [{ t: "", m: false }]);
});

// a trailing "*" is a prefix match, not a literal asterisk.
test("highlightParts: a trailing * matches as a word-continuation prefix", () => {
  const parts = F.highlightParts("passing the password test", ["pass*"]);
  const matched = parts.filter((p) => p.m).map((p) => p.t);
  assert.deepEqual(matched, ["passing", "password"]);
});

// a bare "*" would match everything; drop it rather than highlight all text.
test("highlightParts: a bare * term is dropped, not treated as match-all", () => {
  assert.deepEqual(F.highlightParts("hello world", ["*"]), [
    { t: "hello world", m: false },
  ]);
});

// --- searchTerms ---

test("searchTerms: quoted phrases, bare words, dropped operators and field prefixes", () => {
  assert.deepEqual(
    F.searchTerms('"verification code" OR password AND text:spike'),
    ["verification code", "password", "spike"],
  );
});

test("searchTerms: strips wrapping parens and +/-", () => {
  assert.deepEqual(F.searchTerms("(hello) -world +required"), [
    "hello",
    "world",
    "required",
  ]);
});

test("searchTerms: keeps a trailing * as a prefix term", () => {
  assert.deepEqual(F.searchTerms("pass* filter"), ["pass*", "filter"]);
});

test("searchTerms: skips the token right after NOT", () => {
  assert.deepEqual(F.searchTerms("red NOT blue OR green"), ["red", "green"]);
});

// field:"phrase" resolves to the phrase, not a leftover token.
test('searchTerms: field:"phrase" resolves to the phrase', () => {
  assert.deepEqual(F.searchTerms('field:"phrase" bare'), ["phrase", "bare"]);
});

test("searchTerms: drops terms that strip down to empty", () => {
  assert.deepEqual(F.searchTerms("() -- +"), []);
});

// a bare "*" would match every term (highlightParts treats it as match-all);
// drop it, same as any term that is empty once its trailing * is removed.
test("searchTerms: drops a bare * (match-everything)", () => {
  assert.deepEqual(F.searchTerms("*"), []);
  assert.deepEqual(F.searchTerms("* filter"), ["filter"]);
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

// --- lexJson: now the sibling lexjson.js's PrismQLLexJson ---

test("lexJson: tokenizes a small object", () => {
  const toks = Lex.lexJson('{"a":1,"b":"x"}');
  const joined = toks.map((t) => t.t).join("");
  assert.equal(joined, '{"a": 1, "b": "x"}');
  assert.ok(toks.some((t) => t.c === "tk-fn" && t.t === '"a"'));
  assert.ok(toks.some((t) => t.c === "tk-num" && t.t === "1"));
});
