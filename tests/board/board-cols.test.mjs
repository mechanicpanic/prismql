// Column widths for the board's resizable columns (graph @aleph/prismql,
// #118): bounds, the journal's minimum, what a stored value may be.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const C = require("../../src/prismql/server/board/board-cols.js");

test("defaults are the old fixed layout", () => {
  assert.deepEqual(C.DEFAULTS, { rail: 232, insp: 520 });
});

test("each column stays within its bounds", () => {
  assert.deepEqual(C.clamp({ rail: 20, insp: 5000 }, 3000), { rail: C.RAIL_MIN, insp: C.INSP_MAX });
  assert.deepEqual(C.clamp({ rail: 9999, insp: 10 }, 3000), { rail: C.RAIL_MAX, insp: C.INSP_MIN });
});

test("the journal keeps its minimum: the inspector gives way first, then the rail", () => {
  const vw = 1200;
  const got = C.clamp({ rail: 400, insp: 800 }, vw);
  assert.equal(got.rail + got.insp + C.JOURNAL_MIN, vw);
  assert.equal(got.rail, 400);
  const tight = C.clamp({ rail: 400, insp: 800 }, C.RAIL_MIN + C.INSP_MIN + C.JOURNAL_MIN);
  assert.deepEqual(tight, { rail: C.RAIL_MIN, insp: C.INSP_MIN });
});

test("without the rail (narrow screens) only the inspector counts", () => {
  const got = C.clamp({ rail: 400, insp: 900 }, 1000, true);
  assert.equal(got.insp, 1000 - C.JOURNAL_MIN);
  assert.equal(got.rail, 400);
});

test("a stored value is read only when it is two numbers", () => {
  assert.deepEqual(C.parse('{"rail":300,"insp":600}'), { rail: 300, insp: 600 });
  assert.deepEqual(C.parse("nonsense"), C.DEFAULTS);
  assert.deepEqual(C.parse('{"rail":"wide"}'), C.DEFAULTS);
  assert.deepEqual(C.parse(null), C.DEFAULTS);
});
