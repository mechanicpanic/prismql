// PrismQLFullData: the full view's data assembly — paged loading through
// the shared fetch cache (inspector-fetch.js), the filtered/loaded sets and
// the summary tiles for groups and hits (task-7 brief; graph @aleph/prismql,
// node #76). Not pure (it calls PF.fetchPage), so kept apart from
// fullview-logic.js/fullview-rows.js, which stay node-testable.
(function (root) {
  "use strict";
  var PL = window.PrismQLInspectorPageLogic;
  var PF = window.PrismQLInspectorFetch;
  var FL = window.PrismQLFullLogic;
  var F = window.PrismQLFormat;

  var PAGE = FL.PAGE; // fix round 1, #8: one shared constant, not a literal per file

  // Fix round 1, #2: a fetch that turned up nothing has nothing real to
  // show — "the corpus's whole story" would be an invented one. Fix round
  // 2, #4: a blocked view has nothing to filter either — canFilter false
  // hides the filter box and chips (the view switch itself is trimmed to
  // Summary/Raw by the caller, fullview.js).
  var GONE_NOTE = "result no longer kept";
  function blockedContext(kind, res) {
    return {
      kind: kind, loaded: [], filtered: [], pending: false, blocker: res.blocker, gone: res.gone,
      loadBound: res.loadBound, total: null, tiles: [], canFilter: false, agents: [],
      note: res.gone ? GONE_NOTE : "",
    };
  }

  // Pages through vs.loadTo, never past what the store kept (`kept` can be
  // less than `total` when scouting capped the depth). Finding 1: a page
  // can hold fewer than PAGE items (max_results < PAGE caps every page),
  // so the offset advances by the page's own returned count, stopping on
  // an empty page or loadBound.
  function loadPaged(entry, fields, loadTo, actions, listKey) {
    var items = [], pending = false, blocker = null, gone = false, loadBound = entry.total || 0;
    var labels = null; // finding 5: a named result's slot labels
    for (var o = 0; o < loadTo && o < loadBound && !blocker; ) {
      var rec = PF.fetchPage(entry.result_id, o, PAGE, fields);
      if (rec.status === "loading") { pending = true; break; }
      // "Run again" must leave the full view first (goneBlock only calls
      // actions.rerun — a local stand-in closes #full before it).
      if (rec.data.gone) {
        var rerunActions = { rerun: function (e) { actions.closeFull(); actions.rerun(e); } };
        blocker = PF.goneBlock(rerunActions, entry);
        gone = true;
        break;
      }
      if (rec.data.error) { blocker = PF.errorBlock(rec.data.error.message); break; }
      if (rec.data.kept != null) loadBound = Math.min(loadBound, rec.data.kept);
      if (rec.data.labels != null) labels = rec.data.labels;
      var page = rec.data[listKey] || [];
      page.forEach(function (x) { items.push(x); });
      if (page.length === 0) break;
      o += page.length;
    }
    return { items: items, pending: pending, blocker: blocker, gone: gone, loadBound: loadBound, labels: labels };
  }

  function groupsContext(entry, board, vs, actions, idField) {
    var fields = PL.fieldsFor(board);
    var res = loadPaged(entry, fields, vs.loadTo, actions, "results");
    if (res.blocker) return blockedContext("groups", res);
    var groups = res.items.map(function (g, i) {
      return {
        n: i + 1, ids: g.ids, positions: g.positions, times: g.times,
        slots: PL.pairEventsToSlots(g.ids, g.events, idField), raw: g,
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
      groups.length, entry.total, FL.countEvents(groups), agents.length, hasActor,
      FL.timeRangeLabel(FL.allTimes(groups)),
    );
    return {
      kind: "groups", loaded: groups, filtered: filtered,
      pending: res.pending, blocker: res.blocker, loadBound: res.loadBound, total: entry.total,
      canFilter: true, agents: agents, tiles: tiles, labels: res.labels,
      note: FL.loadNote(groups.length, entry.total, filtered.length < groups.length ? filtered.length : null),
    };
  }

  function hitsContext(entry, board, vs, actions) {
    var fields = PL.fieldsFor(board);
    var res = loadPaged(entry, fields, vs.loadTo, actions, "hits");
    if (res.blocker) return blockedContext("hits", res);
    var hits = res.items;
    var q = vs.q.trim().toLowerCase();
    var filtered = hits.filter(function (h) { return FL.hitPassesFilter(h, board, q, vs.agents); });
    var scored = PL.isScored(entry.kind);
    var hasActor = !!board.actor;
    var kept = res.loadBound < entry.total ? res.loadBound : null;
    var terms = entry.kind === "search" ? F.searchTerms(entry.query || "") : [];
    var actorVals = hits.map(function (h) { return FL.actorOf(h.event, board); });
    var agents = FL.agentChipList(actorVals, vs.agents);
    var tiles = hits.length === 0 ? [] : FL.hitsTiles(
      hits.length, entry.total, scored, FL.topScore(hits), agents.length, hasActor,
      FL.timeRangeLabel(hits.map(function (h) { return h.time; })),
    );
    return {
      kind: "hits", loaded: hits, filtered: filtered,
      pending: res.pending, blocker: res.blocker, loadBound: res.loadBound, total: entry.total,
      canFilter: true, agents: agents, scored: scored, terms: terms, tiles: tiles,
      note: FL.hitsNote(hits.length, entry.total, filtered.length < hits.length ? filtered.length : null, kept),
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
    if (ctx.kind === "hits") return ctx.filtered;
    return [entry];
  }

  var api = { buildContext: buildContext, rawItemsFor: rawItemsFor };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullData = api;
})(typeof window !== "undefined" ? window : globalThis);
