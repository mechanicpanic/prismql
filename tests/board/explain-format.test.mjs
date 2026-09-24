// How the board shows why an event is in a result (graph @aleph/prismql, #119).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const E = require("../../src/prismql/server/board/explain-format.js");

const why = [
  { predicate: "field(kind, THOUGHT)" },
  { predicate: "contains(evalaware)", matches: [
    { term: "honeypot", field: "text", start: 12, end: 20 },
    { term: "being tested", field: "text", start: 22, end: 34 },
    { term: "tested", field: "text", start: 28, end: 34 },
    { term: "sign in", field: "content", start: 0, end: 7 },
  ] },
  { predicate: 'similar_to("x", 0.5)', score: 0.61234 },
];

test("matched spans are marked, overlaps merged", () => {
  const text = "I suspect a honeypot; being tested again";
  assert.deepEqual(E.textParts(text, why), [
    { t: "I suspect a ", m: false },
    { t: "honeypot", m: true },
    { t: "; ", m: false },
    { t: "being tested", m: true },
    { t: " again", m: false },
  ]);
});

test("no explanation, or spans past the text, leave it whole", () => {
  assert.deepEqual(E.textParts("plain", []), [{ t: "plain", m: false }]);
  assert.deepEqual(E.textParts("short", [{ matches: [{ field: "text", start: 3, end: 99 }] }]),
    [{ t: "short", m: false }]);
  assert.deepEqual(E.textParts(null, why), [{ t: "", m: false }]);
});

test("scores and matches outside the text are listed", () => {
  assert.deepEqual(E.scores(why), ["0.612"]);
  assert.deepEqual(E.elsewhere(why), ["content: sign in"]);
});

test("offsets are characters: an emoji before a match does not shift it", () => {
  const text = "🔥🔥 being tested";
  const w = [{ matches: [{ field: "text", start: 9, end: 15 }] }];
  assert.deepEqual(E.textParts(text, w), [
    { t: "🔥🔥 being ", m: false },
    { t: "tested", m: true },
  ]);
});
