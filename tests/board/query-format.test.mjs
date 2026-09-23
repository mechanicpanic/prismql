// Pins the query line breaks (graph @aleph/prismql, node #84): links,
// windows, clauses and pipe stages start lines at the top level only, and a
// query already broken by its author is left alone.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
require("../../src/prismql/server/board/prismql-lexer.js"); // sets globalThis.PrismQLLexer
const QF = require("../../src/prismql/server/board/query-format.js");

test("a classic chain: links on their own lines, the window indented", () => {
  assert.equal(
    QF.breakLines('SELECT contains(outreach) AND field(agent, $a) FOLLOWED_BY field(kind, "AGENT_TALK") AND field(agent, !$a) DURING 1 hour'),
    'SELECT contains(outreach) AND field(agent, $a)\nFOLLOWED_BY field(kind, "AGENT_TALK") AND field(agent, !$a)\n  DURING 1 hour',
  );
});

test("clauses: GROUP BY and AGGREGATE start lines; a bare BY does not", () => {
  assert.equal(
    QF.breakLines("SELECT from(a) GROUP BY user AGGREGATE count()"),
    "SELECT from(a)\nGROUP BY user\nAGGREGATE count()",
  );
});

test("inside parentheses and strings nothing moves", () => {
  const q = 'SELECT (SELECT from(a) FOLLOWED_BY from(b) INWINDOW 2) ; (SELECT contains_phrase("x followed_by y")) INWINDOW 5';
  assert.equal(
    QF.breakLines(q),
    'SELECT (SELECT from(a) FOLLOWED_BY from(b) INWINDOW 2) ; (SELECT contains_phrase("x followed_by y"))\n  INWINDOW 5',
  );
});

test("pipe dialect: links and |> stages start lines, + stays", () => {
  assert.equal(
    QF.breakLines("from(alice) + from(bob) ~> contains(thanks) |> within(5) |> count()"),
    "from(alice) + from(bob)\n~> contains(thanks)\n|> within(5)\n|> count()",
  );
});

test("an author's own line breaks, empty and one-line queries are kept", () => {
  assert.equal(QF.breakLines("SELECT a\n  FOLLOWED_BY b INWINDOW 3"), "SELECT a\n  FOLLOWED_BY b INWINDOW 3");
  assert.equal(QF.breakLines("SELECT from(a)"), "SELECT from(a)");
  assert.equal(QF.breakLines(""), "");
});

test("Format in the editor: the author's breaks give way, strings stay", () => {
  assert.equal(
    QF.formatQuery('SELECT a\n   FOLLOWED_BY contains_phrase("two  spaces")   INWINDOW 3\n'),
    'SELECT a\nFOLLOWED_BY contains_phrase("two  spaces")\n  INWINDOW 3',
  );
});
