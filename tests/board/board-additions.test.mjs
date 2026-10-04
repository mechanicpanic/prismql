// The board's additions of 2026-10-04 (graph @aleph/prismql, #85, #173,
// #174): link numbers in the query, the group's bindings, a finding to copy.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const B = "../../src/prismql/server/board/";
globalThis.window = globalThis;
require(B + "prismql-lexer.js");
const Lexer = globalThis.PrismQLLexer;
const QF = require(B + "query-format.js");
const EF = require(B + "explain-format.js");
const Finding = require(B + "finding.js");
const EL = require(B + "editor-logic.js");

test("numberedLegs puts each link's event number in front of it", () => {
  const q = "SELECT field(kind, b) PRECEDED_BY field(kind, a) INWINDOW 3";
  const pieces = QF.numberedLegs(q, [2, 1], Lexer);
  assert.deepEqual(pieces.map((p) => p.n), [null, 2, 1]);
  assert.equal(pieces.map((p) => p.text).join(""), q);
  assert.equal(pieces[1].text.trim(), "field(kind, b) PRECEDED_BY");
});

test("numberedLegs reads pipe arrows and ignores links inside parentheses", () => {
  const q = "from(a) ~> (from(b) ~> from(c)) |> within(5)";
  assert.equal(QF.numberedLegs(q, [1, 2], Lexer).length, 3);
});

test("numberedLegs gives up when the text and the layout disagree", () => {
  assert.equal(QF.numberedLegs("SELECT from(a) FOLLOWED_BY from(b) INWINDOW 2", [1], Lexer), null);
  assert.equal(QF.numberedLegs("SELECT from(a)", null, Lexer), null);
});

test("bindingsText shows up to three assignments and says when there are more", () => {
  assert.equal(EF.bindingsText([{ y: "o3", a: "GPT-5" }]), "$a = GPT-5, $y = o3");
  const four = [{ a: 1 }, { a: 2 }, { a: 3 }, { a: 4 }];
  assert.equal(EF.bindingsText(four), "$a = 1  ·  $a = 2  ·  $a = 3  ·  +1 more");
    assert.equal(EF.bindingsText([]), "");
});

test("findingMarkdown carries the corpus, the count and a curl that quotes safely", () => {
  const entry = {
    corpus: "village", query: "SELECT contains(it's) INWINDOW 2", total: 7,
    ts: "2026-10-04T15:35:28.595+00:00", label: null,
  };
  const md = Finding.findingMarkdown(entry, "http://localhost:8931");
  assert.match(md, /corpus `village`, 7 groups \(2026-10-04 15:35 UTC\)/);
  assert.match(md, /```prismql\nSELECT contains\(it's\) INWINDOW 2\n```/);
  assert.match(md, /curl -s "\$PRISMQL_SERVER_URL\/evaluate"/);
  assert.match(md, /ours was http:\/\/localhost:8931/);
  assert.match(md, /with the `village` corpus loaded/);
  assert.ok(md.includes("'\\''"), "a single quote in the query is shell-escaped");
});

test("findingMarkdown links the request on the board when it has a seq", () => {
  const md = Finding.findingMarkdown({ corpus: "c", query: "SELECT from(a)", total: 1, seq: 12 }, "http://h");
  assert.match(md, /On our board: http:\/\/h\/board\/#q12/);
});

test("bindingsText says when the engine bound nothing, and when the list was cut", () => {
  assert.equal(EF.bindingsText(null), "variables not bound in this group");
  assert.equal(EF.bindingsText(undefined), "");
  assert.equal(EF.bindingsText([{ a: 1 }, { a: 2 }, { a: 3 }, { a: 4 }], true), "$a = 1  ·  $a = 2  ·  $a = 3  ·  +1 or more");
});

test("numberedLegs shows nothing when a single-quoted string could hide a link", () => {
  const q = "SELECT field(text, 'x ) followed_by y') FOLLOWED_BY from(b) INWINDOW 5";
  assert.equal(QF.numberedLegs(q, [1, 2], Lexer), null);
});

test("numberedLegs puts a pipe link's number after its window, before the link", () => {
  const pieces = QF.numberedLegs("from(a) ~>(5) from(b) |> within(5)", [1, 2], Lexer);
  assert.equal(pieces[2].text.trimStart().startsWith("from(b)"), true);
});

test("a request's own dictionaries replay from the journal; an old entry without terms stays blocked", () => {
  const terms = { frame: ["frame"] };
  assert.equal(EL.hasRequestDictionaries({ dictionaries: ["frame"], dictionary_terms: terms }), false);
  assert.equal(EL.hasRequestDictionaries({ dictionaries: ["frame"] }), true);
  assert.deepEqual(EL.buildEvaluateBody({ query: "q", corpus: "c", dictionaries: terms }), { query: "q", corpus: "c", dictionaries: terms });
  const md = Finding.findingMarkdown({ corpus: "c", query: "SELECT contains(frame)", total: 2, dictionary_terms: terms }, "http://h");
  assert.match(md, /"dictionaries":\{"frame":\["frame"\]\}/);
});

test("keyAction: journal keys, full-view paging, and nothing while typing or with a modifier", () => {
  const Keys = require(B + "board-keys.js");
  const base = { typing: false, modified: false, handled: false, full: false, help: false };
  assert.equal(Keys.keyAction("j", base), "next");
  assert.equal(Keys.keyAction("ArrowUp", base), "prev");
  assert.equal(Keys.keyAction("f", base), "full");
  assert.equal(Keys.keyAction("c", base), "copy");
  assert.equal(Keys.keyAction("j", { ...base, typing: true }), null);
  assert.equal(Keys.keyAction("c", { ...base, modified: true }), null);
  assert.equal(Keys.keyAction("ArrowDown", { ...base, handled: true }), null, "the journal list moved already");
  assert.equal(Keys.keyAction("]", { ...base, full: true }), "pageNext");
  assert.equal(Keys.keyAction("j", { ...base, full: true }), null, "the full view keeps its own keys");
  assert.equal(Keys.keyAction("Escape", { ...base, help: true }), "help");
  assert.equal(Keys.keyAction("j", { ...base, help: true }), null);
});
