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
  assert.equal(EF.bindingsText(null), "");
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
  assert.match(md, /curl -s http:\/\/localhost:8931\/evaluate/);
  assert.ok(md.includes("'\\''"), "a single quote in the query is shell-escaped");
});
