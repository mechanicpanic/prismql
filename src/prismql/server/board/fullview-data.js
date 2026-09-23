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

  var PAGE = 50;

  // Pages of PAGE through the offset the "Load more"/scroll-to-end action
  // asked for (vs.loadTo), never past what the store actually kept — a
  // hits page's own `kept` (page_payload: len(stored), graph #65) can be
  // smaller than `total` (the found count) when scouting capped the depth.
  function loadPaged(entry, fields, loadTo, actions, listKey) {
    var items = [], pending = false, blocker = null, loadBound = entry.total || 0;
    for (var o = 0; o < loadTo && o < loadBound && !blocker; o += PAGE) {
      var rec = PF.fetchPage(entry.result_id, o, PAGE, fields);
      if (rec.status === "loading") { pending = true; break; }
      if (rec.data.gone) { blocker = PF.goneBlock(actions, entry); break; }
      if (rec.data.error) { blocker = PF.errorBlock(rec.data.error.message); break; }
      if (rec.data.kept != null) loadBound = Math.min(loadBound, rec.data.kept);
      (rec.data[listKey] || []).forEach(function (x) { items.push(x); });
    }
    return { items: items, pending: pending, blocker: blocker, loadBound: loadBound };
  }

  function groupsContext(entry, board, vs, actions) {
    var fields = PL.fieldsFor(board);
    var res = loadPaged(entry, fields, vs.loadTo, actions, "results");
    var groups = res.items.map(function (g, i) {
      return {
        n: i + 1, ids: g.ids, positions: g.positions, times: g.times,
        slots: PL.pairEventsToSlots(g.ids, g.events), raw: g,
      };
    });
    var q = vs.q.trim().toLowerCase();
    var filtered = groups.filter(function (g) { return FL.groupPassesFilter(g.slots, board, q, vs.agents); });
    var hasActor = !!board.actor;
    var allEvents = [];
    groups.forEach(function (g) { (g.slots || []).forEach(function (e) { allEvents.push(e); }); });
    var leadActors = groups.map(function (g) { return FL.actorOf(g.slots[0], board); });
    return {
      kind: "groups", loaded: groups, filtered: filtered,
      pending: res.pending, blocker: res.blocker, loadBound: res.loadBound, total: entry.total,
      canFilter: true, agents: FL.agentChipList(leadActors, vs.agents),
      tiles: FL.groupsTiles(
        groups.length, entry.total, FL.countEvents(groups),
        FL.distinctActorCount(allEvents, board), hasActor,
        FL.timeRangeLabel(FL.allTimes(groups)),
      ),
      note: FL.loadNote(groups.length, entry.total, filtered.length < groups.length ? filtered.length : null),
    };
  }

  function hitsContext(entry, board, vs, actions) {
    var fields = PL.fieldsFor(board);
    var res = loadPaged(entry, fields, vs.loadTo, actions, "hits");
    var hits = res.items;
    var q = vs.q.trim().toLowerCase();
    var filtered = hits.filter(function (h) { return FL.hitPassesFilter(h, board, q, vs.agents); });
    var scored = PL.isScored(entry.kind);
    var hasActor = !!board.actor;
    var kept = res.loadBound < entry.total ? res.loadBound : null;
    var terms = entry.kind === "search" ? F.searchTerms(entry.query || "") : [];
    var actorVals = hits.map(function (h) { return FL.actorOf(h.event, board); });
    return {
      kind: "hits", loaded: hits, filtered: filtered,
      pending: res.pending, blocker: res.blocker, loadBound: res.loadBound, total: entry.total,
      canFilter: true, agents: FL.agentChipList(actorVals, vs.agents), scored: scored, terms: terms,
      tiles: FL.hitsTiles(
        hits.length, entry.total, kept, scored, FL.topScore(hits),
        FL.distinctActorCount(hits.map(function (h) { return h.event; }), board), hasActor,
        FL.timeRangeLabel(hits.map(function (h) { return h.time; })),
      ),
      note: FL.loadNote(hits.length, entry.total, filtered.length < hits.length ? filtered.length : null),
    };
  }

  function summaryContext() {
    return { kind: "summary", loaded: [], filtered: [], pending: false, blocker: null, tiles: [], canFilter: false, agents: [], note: "" };
  }

  function buildContext(entry, board, outputKind, vs, actions) {
    if (outputKind === "groups") return groupsContext(entry, board, vs, actions);
    if (outputKind === "hits") return hitsContext(entry, board, vs, actions);
    return summaryContext();
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
