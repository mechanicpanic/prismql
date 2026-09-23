// Pins the corpus card's pure helpers (graph @aleph/prismql, node #86):
// which corpus the card shows, how a field's values read, role ordering.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const CL = require("../../src/prismql/server/board/corpus-logic.js");

const SCHEMA = {
  documents: 381610, sampled: 381610, complete: true,
  id_field: "id", timestamp_field: "time", text_match: "stem",
  board: { kind: "kind", actor: "agent" },
  fields: {
    text: { coverage: 0.78, type: "str", distinct: null, distinct_over: 1000 },
    agent: { coverage: 1, type: "str", distinct: 2, top: [["Grok 4", 5], ["o3", 3]] },
    kind: { coverage: 1, type: "str", distinct: 12, top: [["AGENT_TALK", 9], ["WAIT", 2]] },
    id: { coverage: 1, type: "str", distinct: 381610 },
    time: { coverage: 1, type: "datetime", distinct: null, distinct_over: 1000 },
    room: { coverage: 1, type: "str", distinct: 0 },
  },
  dictionary_terms: { signin: { terms: ["sign in"], match: null }, x: { terms: ["x"], match: "token" } },
  capabilities: { similar: { available: true, model: "MiniLM" }, search: false },
};

test("corpusToShow: the rail's pick, else the request's corpus, else the default", () => {
  const state = { corpusSel: null, corpora: { default: "wiki" } };
  assert.equal(CL.corpusToShow(state, null), "wiki");
  assert.equal(CL.corpusToShow(state, { corpus: "village" }), "village");
  assert.equal(CL.corpusToShow({ ...state, corpusSel: "revisions" }, { corpus: "village" }), "revisions");
  assert.equal(CL.corpusToShow({ corpusSel: null, corpora: null }, null), null);
});

test("valuesOf: counted values with the rest, or why none are listed", () => {
  assert.deepEqual(CL.valuesOf(SCHEMA.fields.kind), {
    values: [{ v: "AGENT_TALK", n: 9 }, { v: "WAIT", n: 2 }], note: "+10 more values",
  });
  assert.deepEqual(CL.valuesOf(SCHEMA.fields.agent).note, "");
  assert.deepEqual(CL.valuesOf(SCHEMA.fields.text), { values: [], note: "over 1,000 values" });
  assert.deepEqual(CL.valuesOf(SCHEMA.fields.id), { values: [], note: "one value per event" });
  assert.deepEqual(CL.valuesOf(SCHEMA.fields.room), { values: [], note: "no values" });
});

test("fieldRows: id, time, kind, actor first, then by name; coverage only when partial", () => {
  const rows = CL.fieldRows(SCHEMA);
  assert.deepEqual(rows.map((r) => r.name), ["id", "time", "kind", "agent", "room", "text"]);
  assert.deepEqual(rows.map((r) => r.role), ["id", "time", "kind", "actor", null, null]);
  assert.equal(rows.find((r) => r.name === "text").coverage, "78% of events");
  assert.equal(rows.find((r) => r.name === "kind").coverage, "");
  assert.equal(rows.find((r) => r.name === "id").note, "unique per event");
});

test("capabilities and dictionaries read what the server reports", () => {
  const caps = CL.capabilities(SCHEMA);
  assert.deepEqual(caps.map((c) => [c.label, c.on]), [["similar", true], ["search", false]]);
  assert.match(caps[0].title, /MiniLM/);
  assert.deepEqual(CL.dictionaryRows(SCHEMA), [
    { name: "signin", match: "stem", terms: ["sign in"] },
    { name: "x", match: "token", terms: ["x"] },
  ]);
});

test("summary names a sample when the values did not come from every event", () => {
  assert.equal(CL.summary(SCHEMA), "381,610 events");
  assert.equal(CL.summary({ ...SCHEMA, complete: false, sampled: 1000 }),
    "381,610 events · values from a sample of 1,000");
});
