// DOM-level pins for the result navigation controls, on a minimal fake DOM:
// the pager footer (Prev/Next disabled at the ends, jump, collapse all), the
// sort/reverse controls, and a verbose group's open/closed rendering in the
// timeline and the table. The browser E2E (scripts/e2e_board_navigation.py)
// covers the same against a real server and Chrome.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const B = "../../src/prismql/server/board/";

function el(tag) {
  const listeners = {};
  const node = {
    tag, children: [], dataset: {}, style: {}, className: "", textContent: "", attrs: {},
    appendChild(c) { node.children.push(c); return c; },
    setAttribute(k, v) { node.attrs[k] = v; },
    getAttribute(k) { return node.attrs[k]; },
    addEventListener(t, fn) { (listeners[t] = listeners[t] || []).push(fn); },
    fire(t, ev) { (listeners[t] || []).forEach((fn) => fn(ev || { preventDefault() {} })); },
    all(pred, out = []) { node.children.forEach((c) => { if (pred(c)) out.push(c); c.all(pred, out); }); return out; },
    byKey(k) { return node.all((c) => c.dataset.fkey === k)[0] || null; },
    byClass(k) { return node.all((c) => (" " + c.className + " ").includes(" " + k + " ")); },
  };
  return node;
}

function load() {
  globalThis.document = { createElement: el, createTextNode: (t) => ({ textContent: t, children: [], dataset: {}, className: "", all() { return []; } }) };
  const Util = require(B + "board-util.js");
  const Nav = require(B + "fullview-nav-logic.js");
  globalThis.window = {
    PrismQLBoardUtil: Util, PrismQLFullNav: Nav,
    PrismQLInspectorUI: { emptyBlock: () => el("div") },
    PrismQLExplainFormat: require(B + "explain-format.js"),
  };
  for (const f of ["fullview-rows.js", "fullview-pager.js", "fullview-timeline.js", "fullview-table.js"]) delete require.cache[require.resolve(B + f)];
  window.PrismQLFullRows = require(B + "fullview-rows.js");
  return {
    Nav, FR: window.PrismQLFullRows, Pager: require(B + "fullview-pager.js"),
    Timeline: require(B + "fullview-timeline.js"), Table: require(B + "fullview-table.js"),
  };
}

function group(idx, n) {
  const ids = Array.from({ length: n }, (_, i) => "e" + i);
  return {
    n: idx + 1, idx, ids, positions: ids.map((_, i) => i), times: ids.map(() => null),
    slots: ids.map((id) => ({ id, agent: "A", kind: "K", text: "t" })),
  };
}
const board = { kind: "kind", actor: "agent" };
const ctxOf = (nav, groups) => ({ kind: "groups", nav, filtered: groups || [], loaded: groups || [] });

test("pager footer: Prev is disabled on the first page, Next on the last, each names its twin for focus", () => {
  const { Nav, Pager } = load();
  const vs = Object.assign(Nav.initial(50), { count: 120, view: "table" });
  let foot = Pager.buildFooter(ctxOf({ page: 0, pageCount: 3 }), vs, () => {});
  assert.equal(foot.byKey("prev").disabled, true);
  assert.equal(foot.byKey("next").disabled, false);
  assert.equal(foot.byKey("next").dataset.falt, "prev");
  assert.equal(foot.byClass("fpage")[0].textContent, "Page 1 of 3");
  foot = Pager.buildFooter(ctxOf({ page: 2, pageCount: 3 }), vs, () => {});
  assert.equal(foot.byKey("next").disabled, true);
  assert.equal(foot.byKey("prev").disabled, false);
});

test("pager footer: Next moves one page and rebuilds; Prev never goes below page 1", () => {
  const { Nav, Pager } = load();
  const vs = Object.assign(Nav.initial(50), { count: 120, group: 3 });
  let rebuilt = 0;
  const foot = Pager.buildFooter(ctxOf({ page: 0, pageCount: 3 }), vs, () => rebuilt++);
  foot.byKey("next").fire("click");
  assert.deepEqual([vs.page, vs.group, rebuilt], [1, 0, 1]);
  foot.byKey("prev").fire("click");
  foot.byKey("prev").fire("click");
  assert.equal(vs.page, 0);
  assert.equal(rebuilt, 2, "a click that changes nothing rebuilds nothing");
});

test("pager footer: the jump form goes to the typed page (1-based) and ignores an empty box; a single page has no jump", () => {
  const { Nav, Pager } = load();
  const vs = Object.assign(Nav.initial(50), { count: 200 });
  let rebuilt = 0;
  const foot = Pager.buildFooter(ctxOf({ page: 0, pageCount: 4 }), vs, () => rebuilt++);
  const input = foot.byKey("jump");
  assert.equal(input.max, "4", "the box is bounded by the page count");
  const form = foot.byClass("fjump")[0];
  input.value = "";
  form.fire("submit", { preventDefault() {} });
  assert.equal(vs.page, 0);
  input.value = "3";
  form.fire("submit", { preventDefault() {} });
  assert.equal(vs.page, 2);
  input.value = "99";
  form.fire("submit", { preventDefault() {} });
  assert.equal(vs.page, 3, "past the end clamps to the last page");
  const single = Pager.buildFooter(ctxOf({ page: 0, pageCount: 1 }), vs, () => {});
  assert.equal(single.byKey("jump"), null);
});

test("pager footer: Collapse/Expand all appear only for groups with verbose ones, and act on this page", () => {
  const { Nav, Pager } = load();
  const vs = Object.assign(Nav.initial(50), { count: 3, view: "timeline" });
  const small = Pager.buildFooter(ctxOf({ page: 0, pageCount: 1 }, [group(0, 4)]), vs, () => {});
  assert.equal(small.byKey("all-open"), null);
  const groups = [group(0, 4), group(1, 60)];
  const foot = Pager.buildFooter(ctxOf({ page: 0, pageCount: 1 }, groups), vs, () => {});
  foot.byKey("all-open").fire("click");
  assert.deepEqual(vs.shown, { 1: 60 });
  foot.byKey("all-close").fire("click");
  assert.deepEqual(vs.shown, { 1: 3 });
  vs.view = "raw";
  assert.equal(Pager.buildFooter(ctxOf({ page: 0, pageCount: 1 }, groups), vs, () => {}).byKey("all-open"), null);
});

test("sort and reverse: the select is for groups only; changing it starts from page 1; reverse is a pressed button", () => {
  const { Nav, Pager } = load();
  const vs = Object.assign(Nav.initial(50), { count: 200, page: 2 });
  let rebuilt = 0;
  const bar = el("div");
  Pager.buildOrder(bar, ctxOf({}), vs, () => rebuilt++);
  const sel = bar.byKey("sort");
  assert.deepEqual(sel.children.map((o) => o.value), ["position", "size"]);
  sel.value = "size";
  sel.fire("change");
  assert.deepEqual([vs.order, vs.page, rebuilt], ["size", 0, 1]);
  const rev = bar.byKey("reverse");
  assert.equal(rev.attrs["aria-pressed"], "false");
  rev.fire("click");
  assert.deepEqual([vs.reverse, vs.page, rebuilt], [true, 0, 2]);
  const hitsBar = el("div");
  Pager.buildOrder(hitsBar, { kind: "hits", nav: {} }, vs, () => {});
  assert.equal(hitsBar.byKey("sort"), null, "hits have no group size to sort by");
  assert.ok(hitsBar.byKey("reverse"));
});

test("timeline detail: a verbose group renders its preview and a toggle, an opened one its events — never the whole group by default", () => {
  const { Timeline } = load();
  const big = group(7, 40);
  const events = (shown) => {
    const d = el("div");
    Timeline.renderDetail(d, big, 130, board, null, shown, () => {});
    return d;
  };
  let d = events({});
  assert.equal(d.byClass("tev").length, 3);
  assert.equal(d.byClass("gcount")[0].textContent, "3 of 40 events shown");
  assert.equal(d.byKey("grp-more-top:7").textContent, "Show all 40 events");
  assert.equal(d.byKey("grp-more-bottom:7"), null, "no bottom button on a bare preview");
  d = events({ 7: 40 });
  assert.equal(d.byClass("tev").length, 40);
  assert.equal(d.byKey("grp-more-top:7"), null);
  assert.equal(d.byKey("grp-close-top:7").dataset.falt, "grp-more-top:7");
  d = events({ 7: 20 });
  assert.equal(d.byClass("tev").length, 20);
  assert.ok(d.byKey("grp-more-bottom:7"), "a partly opened group can be continued from below");
  const small = el("div");
  Timeline.renderDetail(small, group(1, 5), 130, board, null, {}, () => {});
  assert.equal(small.byClass("gtoggle").length, 0, "a small group has no toggle");
  assert.equal(small.byClass("tev").length, 5);
});

test("timeline detail: the toggle reports which group and which action", () => {
  const { Timeline } = load();
  const calls = [];
  const d = el("div");
  Timeline.renderDetail(d, group(7, 40), 130, board, null, {}, (...a) => calls.push(a));
  d.byKey("grp-more-top:7").fire("click");
  assert.deepEqual(calls, [[7, 40, "open"]]);
});

test("table: a toggle row names its group and wires the same actions; opened rows follow vs.shown", () => {
  const { FR, Table } = load();
  const rows = FR.groupTableRows([group(7, 40)], board, {});
  const wrap = el("div");
  const calls = [];
  Table.renderTable(wrap, "groups", "1fr", ["x"], rows, board, (...a) => calls.push(a));
  const toggle = wrap.byClass("tmore")[0];
  assert.match(toggle.all((c) => c.className === "gcount")[0].textContent, /group 8: 3 of 40 events shown/);
  wrap.byKey("grp-more:7").fire("click");
  assert.deepEqual(calls, [[7, 40, "open"]]);
  assert.equal(wrap.byClass("tr").length - 1, 3 + 1, "header excluded: 3 event rows + the toggle row");
});

test("raw lines carry each group's stored number, not its place on the page", () => {
  load();
  window.PrismQLLexJson = require(B + "lexjson.js");
  delete require.cache[require.resolve(B + "fullview-table.js")];
  const Table = require(B + "fullview-table.js");
  const out = el("div");
  Table.renderRaw(out, [{ ids: ["a"] }, { ids: ["b"] }], 0, [78, 21]);
  const nos = out.byClass("no").map((n) => n.textContent);
  assert.deepEqual(nos, ["78", "21"]);
});
