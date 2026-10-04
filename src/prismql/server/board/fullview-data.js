// PrismQLFullData: the full view's data assembly — paged loading through
// the shared fetch cache (inspector-fetch.js), the filtered/loaded sets and
// the summary tiles for groups and hits (task-7 brief; graph @aleph/prismql,
// node #76). Not pure (it calls PF.fetchPage), so kept apart from
// fullview-logic.js/fullview-rows.js, which stay node-testable. Paging and
// the shared blocked-view context live in fullview-load.js; the "rows" kind
// (GROUP BY ... AGGREGATE, #90) lives in fullview-rows-context.js — both
// split out to keep this file under 150 lines (fix round 1, #6).
(function (root) {
  "use strict";
  var PL = window.PrismQLInspectorPageLogic;
  var FL = window.PrismQLFullLogic;
  var F = window.PrismQLFormat;
  var Nav = typeof module === "object" && module.exports
    ? require("./fullview-nav-logic.js") : window.PrismQLFullNav;
  var PFLoad = typeof module === "object" && module.exports
    ? require("./fullview-load.js") : window.PrismQLFullLoad;
  var RowsContext = typeof module === "object" && module.exports
    ? require("./fullview-rows-context.js") : window.PrismQLFullRowsContext;

  var loadPage = PFLoad.loadPage;
  var blockedContext = PFLoad.blockedContext;

  // The fnote: where this page sits in the result, and that a filter
  // reaches this page only.
  function pageNote(res, matched) {
    var n = res.nav;
    return n.count == null ? "" : Nav.pageNote(n.offset, n.got, n.count, matched, n.total);
  }

  // The chips can carry a selected agent this page has none of (so the
  // filter stays undoable); the tile counts only the page's own.
  function onPage(actorValues) { return FL.agentChipList(actorValues, null).length; }

  function groupsContext(entry, board, vs, actions, idField) {
    var fields = PL.fieldsFor(board);
    var res = loadPage(entry, fields, vs, actions, "results");
    if (res.blocker) return blockedContext("groups", res);
    // n is the group's number in the STORED result, whatever the order or
    // page shows it in; idx (0-based) keys its open/closed state.
    var groups = res.items.map(function (g, i) {
      return {
        n: res.indices[i] + 1, idx: res.indices[i], ids: g.ids, positions: g.positions, times: g.times,
        slots: PL.pairEventsToSlots(g.ids, g.events, idField), explain: g.explain, raw: g,
        bindings: g.bindings, bindingsCut: g.bindings_truncated,
      };
    });
    var q = vs.q.trim().toLowerCase();
    var filtered = groups.filter(function (g) { return FL.groupPassesFilter(g.slots, board, q, vs.agents); });
    var hasActor = !!board.actor;
    // Fix round 1, #1: the "actors" tile counts the SAME list the chips
    // show — distinct first-slot actors of loaded groups — never a wider
    // count over every event.
    var leadActors = groups.map(function (g) { return FL.actorOf(g.slots[0], board); });
    var agents = FL.agentChipList(leadActors, vs.agents);
    // Fix round 1, #2: nothing loaded yet (still pending) has no real
    // numbers to show — an empty tiles array, not invented zeros.
    var tiles = groups.length === 0 ? [] : FL.groupsTiles(
      groups.length, entry.total, FL.countEvents(groups), onPage(leadActors), hasActor,
      FL.timeRangeLabel(FL.allTimes(groups)),
    );
    return {
      kind: "groups", loaded: groups, filtered: filtered,
      pending: res.pending, blocker: res.blocker, nav: res.nav, total: entry.total,
      canFilter: true, agents: agents, tiles: tiles, labels: res.labels,
      note: pageNote(res, filtered.length),
    };
  }

  function hitsContext(entry, board, vs, actions) {
    var fields = PL.fieldsFor(board);
    var res = loadPage(entry, fields, vs, actions, "hits");
    if (res.blocker) return blockedContext("hits", res);
    var hits = res.items;
    var q = vs.q.trim().toLowerCase();
    var filtered = hits.filter(function (h) { return FL.hitPassesFilter(h, board, q, vs.agents); });
    var scored = PL.isScored(entry.kind);
    var hasActor = !!board.actor;
    var terms = entry.kind === "search" ? F.searchTerms(entry.query || "") : [];
    var actorVals = hits.map(function (h) { return FL.actorOf(h.event, board); });
    var agents = FL.agentChipList(actorVals, vs.agents);
    var tiles = hits.length === 0 ? [] : FL.hitsTiles(
      hits.length, entry.total, scored, FL.topScore(hits), onPage(actorVals), hasActor,
      FL.timeRangeLabel(hits.map(function (h) { return h.time; })),
    );
    return {
      kind: "hits", loaded: hits, filtered: filtered,
      pending: res.pending, blocker: res.blocker, nav: res.nav, total: entry.total,
      canFilter: true, agents: agents, scored: scored, terms: terms, tiles: tiles,
      note: pageNote(res, filtered.length),
    };
  }

  // Fix round 1, #7: the canvas's own summary-note wording, verbatim.
  var SUMMARY_NOTES = {
    aggregate: "single value", error: "the request failed before producing output",
    file: "output went to a file", empty: "empty result",
  };
  function summaryContext(outputKind) {
    return {
      kind: "summary", loaded: [], filtered: [], pending: false, blocker: null,
      tiles: [], canFilter: false, agents: [], note: SUMMARY_NOTES[outputKind] || "",
    };
  }

  function buildContext(entry, board, outputKind, vs, actions, idField) {
    if (outputKind === "groups") return groupsContext(entry, board, vs, actions, idField);
    if (outputKind === "hits") return hitsContext(entry, board, vs, actions);
    if (outputKind === "rows") return RowsContext.rowsContext(entry, vs, actions);
    return summaryContext(outputKind);
  }

  // The loaded items exactly as the server sent them — a group's `raw`
  // (ids/positions/times/events) or a hit object outright — filtered the
  // same way the table is (design canvas: raw JSON is built from the
  // filtered set, `fgs`/`fh`, not the full loaded one). Anything else
  // (aggregate/grouped/file/error/empty) has no paged items at all, so raw
  // shows the journal entry itself — its real fields, nothing invented.
  function rawItemsFor(ctx, entry) {
    if (ctx.kind === "groups") return ctx.filtered.map(function (g) { return g.raw; });
    if (ctx.kind === "hits" || ctx.kind === "rows") return ctx.filtered;
    return [entry];
  }

  var api = { buildContext: buildContext, rawItemsFor: rawItemsFor };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullData = api;
})(typeof window !== "undefined" ? window : globalThis);
