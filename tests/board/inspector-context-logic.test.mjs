// The inspector's "context" (graph @aleph/prismql, #120).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const C = require("../../src/prismql/server/board/inspector-context-logic.js");

test("params ask for the same actor when the corpus names one", () => {
  assert.deepEqual(C.params("village", 42, "agent", true),
    { corpus: "village", id: "42", minutes: "10", same: "agent" });
  assert.deepEqual(C.params("village", "e1", "agent", false),
    { corpus: "village", id: "e1", minutes: "10" });
  assert.deepEqual(C.params("wiki", "e1", undefined, true),
    { corpus: "wiki", id: "e1", minutes: "10" });
});

test("a key tells same-actor from all-events answers apart", () => {
  assert.notEqual(C.key(C.params("v", "e1", "agent", true)), C.key(C.params("v", "e1", "agent", false)));
});

test("offsets read as a signed place", () => {
  assert.deepEqual([-2, 0, 3].map(C.offsetLabel), ["-2", "0", "+3"]);
});

test("the heading names the window, who, and how many neighbours", () => {
  const body = { same_value: "ada", events: [{}, {}, {}] };
  assert.equal(C.heading(body, "agent", true), "±10 min · agent ada · 2 neighbours");
  assert.equal(C.heading({ events: [{}, {}] }, "agent", false), "±10 min · all events · 1 neighbour");
});
