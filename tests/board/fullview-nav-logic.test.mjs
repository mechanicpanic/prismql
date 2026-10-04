// Pins the full view's result-navigation state (pure): which page, which
// order, reversed or not, which verbose groups are open — and what each
// means for the fetch and the words on screen. The view only chooses WHICH
// stored items a page shows; it never touches the result.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const Nav = require("../../src/prismql/server/board/fullview-nav-logic.js");
const PL = require("../../src/prismql/server/board/inspector-page-logic.js");

const fresh = (count) => Object.assign(Nav.initial(50), { group: 0, count });

// --- paging ---

test("pageCount: at least one page, ceil of count over size, unknown count is one page", () => {
  assert.equal(Nav.pageCount(0, 50), 1);
  assert.equal(Nav.pageCount(50, 50), 1);
  assert.equal(Nav.pageCount(51, 50), 2);
  assert.equal(Nav.pageCount(200, 50), 4);
  assert.equal(Nav.pageCount(null, 50), 1);
});
test("goPage: clamps into range, resets the selected group, asks for a scroll reset; same page is a no-op", () => {
  const vs = fresh(200);
  vs.group = 7;
  assert.equal(Nav.goPage(vs, 2), true);
  assert.deepEqual([vs.page, vs.group, vs.resetScroll], [2, 0, true]);
  assert.equal(Nav.goPage(vs, 99), true);
  assert.equal(vs.page, 3, "past the end lands on the last page");
  assert.equal(Nav.goPage(vs, 3), false);
  assert.equal(Nav.goPage(vs, -5), true);
  assert.equal(vs.page, 0);
  assert.equal(Nav.goPage(vs, "abc"), false, "a non-number goes nowhere (page 0 stays)");
});
test("a changed order or a reverse starts again from the first page", () => {
  const vs = fresh(200);
  Nav.goPage(vs, 3);
  Nav.setOrder(vs, "size");
  assert.deepEqual([vs.order, vs.page], ["size", 0]);
  Nav.goPage(vs, 2);
  Nav.setOrder(vs, "size");
  assert.equal(vs.page, 2, "choosing the order already shown changes nothing");
  Nav.toggleReverse(vs);
  assert.deepEqual([vs.reverse, vs.page], [true, 0]);
  Nav.toggleReverse(vs);
  assert.equal(vs.reverse, false);
});

// --- the fetch's view ---

test("viewOf: the default view sends nothing; any other names order and reverse", () => {
  assert.equal(Nav.viewOf(fresh(1)), null);
  assert.deepEqual(Nav.viewOf(Object.assign(fresh(1), { order: "size" })), { order: "size", reverse: false });
  assert.deepEqual(Nav.viewOf(Object.assign(fresh(1), { reverse: true })), { order: "position", reverse: true });
});
test("cacheKey: the default key is unchanged; another order or reverse never shares a page with it", () => {
  const f = ["text"];
  const base = PL.cacheKey("r1", 0, 50, f);
  assert.equal(base, "r1|0|50|text");
  assert.equal(PL.cacheKey("r1", 0, 50, f, null), base);
  const keys = [
    PL.cacheKey("r1", 0, 50, f, { order: "size", reverse: false }),
    PL.cacheKey("r1", 0, 50, f, { order: "size", reverse: true }),
    PL.cacheKey("r1", 0, 50, f, { order: "position", reverse: true }),
  ];
  assert.equal(new Set([base, ...keys]).size, 4);
});

// --- what the server answered ---

test("effectiveSize: a short window with more to come is the server's cap; anything else is the size asked", () => {
  assert.equal(Nav.effectiveSize(50, { count: 25, truncated: true }), 25);
  assert.equal(Nav.effectiveSize(50, { count: 50, truncated: true }), 50);
  assert.equal(Nav.effectiveSize(50, { count: 7, truncated: false }), 50, "the last page is short by nature");
  assert.equal(Nav.effectiveSize(50, { count: 0, truncated: true }), 50);
});
test("itemCount: what the store kept (hits), else what was found, else the journal's total", () => {
  assert.equal(Nav.itemCount({ kept: 10, total: 90 }, 5), 10);
  assert.equal(Nav.itemCount({ total: 90 }, 5), 90);
  assert.equal(Nav.itemCount({}, 5), 5);
});
test("storedIndexes: the server's list when it named one, else the page's own offsets", () => {
  assert.deepEqual(Nav.storedIndexes({ indices: [9, 3] }, 0, 2), [9, 3]);
  assert.deepEqual(Nav.storedIndexes({}, 50, 3), [50, 51, 52]);
  assert.deepEqual(Nav.storedIndexes({ indices: [1] }, 0, 2), [0, 1], "a list that does not fit the page is not trusted");
});

// --- verbose groups ---

test("visibleCount: a small group shows everything; a verbose one starts at its preview", () => {
  assert.equal(Nav.visibleCount(10, undefined), 10);
  assert.equal(Nav.visibleCount(11, undefined), 3);
  assert.equal(Nav.visibleCount(500, undefined), 3);
  assert.equal(Nav.visibleCount(500, 103), 103);
  assert.equal(Nav.visibleCount(40, 103), 40, "never more than the group has");
  assert.equal(Nav.visibleCount(500, 0), 3, "never below the preview");
});
test("nextShown: opens STEP at a time, closes back to the preview", () => {
  assert.equal(Nav.nextShown(500, undefined, "open"), 103);
  assert.equal(Nav.nextShown(500, 103, "open"), 203);
  assert.equal(Nav.nextShown(50, undefined, "open"), 50);
  assert.equal(Nav.nextShown(500, 203, "close"), 3);
});
test("toggleText: names what the button does, nothing for a group that cannot do it", () => {
  assert.deepEqual(Nav.toggleText(42, undefined), { seen: 3, left: 39, more: "Show all 42 events", close: null });
  assert.equal(Nav.toggleText(500, undefined).more, "Show 100 more (497 left)");
  const open = Nav.toggleText(42, 42);
  assert.deepEqual([open.more, open.close], [null, "Collapse to first 3"]);
});
test("setAll: opens or folds every verbose group of the page and leaves small ones alone", () => {
  const vs = fresh(3);
  const groups = [{ idx: 0, ids: new Array(5) }, { idx: 7, ids: new Array(60) }, { idx: 9, ids: new Array(300) }];
  Nav.setAll(vs, groups, "open");
  assert.deepEqual(vs.shown, { 7: 60, 9: 103 });
  Nav.setAll(vs, groups, "close");
  assert.deepEqual(vs.shown, { 7: 3, 9: 3 });
});

// --- the note ---

test("pageNote: the page's place in the result; a filter says it reaches this page only", () => {
  assert.equal(Nav.pageNote(50, 50, 371, null, 371), "51–100 of 371");
  assert.equal(Nav.pageNote(0, 50, 371, 12, 371), "12 of 50 on this page match · 1–50 of 371");
  assert.equal(Nav.pageNote(0, 50, 371, 50, 371), "1–50 of 371", "a filter matching the whole page reads as no filter");
  assert.equal(Nav.pageNote(0, 2, 2, null, 3), "1–2 of 2 · 3 found", "hits kept fewer than found");
  assert.equal(Nav.pageNote(0, 0, 0, null, 0), "0 of 0");
});

// --- keys a control keeps ---

test("keepsArrow: a Sort select keeps all four arrows, pager/order buttons keep ←/→ only", () => {
  const select = { tagName: "SELECT" };
  for (const k of ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]) assert.equal(Nav.keepsArrow(select, k), true, k);
  const inPager = { tagName: "BUTTON", closest: (sel) => (sel.includes(".fpager") ? {} : null) };
  assert.equal(Nav.keepsArrow(inPager, "ArrowRight"), true);
  assert.equal(Nav.keepsArrow(inPager, "ArrowLeft"), true);
  assert.equal(Nav.keepsArrow(inPager, "ArrowDown"), false, "↑/↓ still walk the groups");
  assert.equal(Nav.keepsArrow({ tagName: "BUTTON", closest: () => null }, "ArrowRight"), false, "other buttons keep the entry shortcuts");
  assert.equal(Nav.keepsArrow(select, "Escape"), false, "Esc is never kept: it closes the view");
  assert.equal(Nav.keepsArrow(null, "ArrowDown"), false);
});
