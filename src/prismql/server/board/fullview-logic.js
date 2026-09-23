// PrismQLFullLogic: pure logic for the full-screen output view (task-7
// brief; graph @aleph/prismql, node #76) — the calendar time-range label,
// the "<loaded> of <total> loaded"/"<m> of <loaded> match" note, which
// views a result kind gets, text/actor-chip filtering over what is
// actually loaded, and the summary tiles. No fake data: every value here
// is derived from loaded items or the journal entry, never invented
// (global-constraints.md). Window-free like format.js so it is
// node-testable without a fake DOM.
(function (root) {
  "use strict";

  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var VIEWS = { groups: ["timeline", "table", "raw"], hits: ["table", "raw"] };
  // The one page size every loader/Load-more/scroll-to-end site reads (fix
  // round 1, #8) — fullview-data.js, fullview-body.js and fullview.js all
  // read this instead of each carrying its own literal 50.
  var PAGE = 50;

  function timeRangeLabel(times) {
    var ds = (times || []).filter(function (t) { return t != null; })
      .map(function (t) { return new Date(t); })
      .filter(function (d) { return !isNaN(d.getTime()); })
      .sort(function (a, b) { return a - b; });
    if (!ds.length) return "—";
    var a = ds[0], b = ds[ds.length - 1];
    var sameYear = a.getFullYear() === b.getFullYear();
    var sameMonth = sameYear && a.getMonth() === b.getMonth();
    var sameDay = sameMonth && a.getDate() === b.getDate();
    var da = MON[a.getMonth()] + " " + a.getDate() + (sameYear ? "" : " " + a.getFullYear());
    if (sameDay) return da;
    if (sameMonth) return da + "–" + b.getDate();
    return da + "–" + MON[b.getMonth()] + " " + b.getDate() + (sameYear ? "" : " " + b.getFullYear());
  }

  function loadNote(loadedCount, total, matchedCount) {
    var base = loadedCount + " of " + total + " loaded";
    if (matchedCount != null && matchedCount < loadedCount) {
      return matchedCount + " of " + loadedCount + " match · " + base;
    }
    return base;
  }

  function viewsFor(kind) { return VIEWS[kind] || ["summary", "raw"]; }

  function fieldText(event, board) {
    if (!event) return "";
    var parts = [];
    if (board.kind && event[board.kind] != null) parts.push(String(event[board.kind]));
    if (board.actor && event[board.actor] != null) parts.push(String(event[board.actor]));
    if (event.text) parts.push(String(event.text));
    return parts.join(" ").toLowerCase();
  }
  function actorOf(event, board) {
    return board && board.actor && event && event[board.actor] != null ? String(event[board.actor]) : null;
  }

  // The agent chip filters by the group's LEAD (first slot) actor, same as
  // the design canvas's `agentList` keyed off `g.events[0].agent`.
  function groupPassesFilter(slots, board, q, agentSel) {
    var hasAgentFilter = agentSel && Object.keys(agentSel).length > 0;
    if (hasAgentFilter) {
      var lead = actorOf(slots[0], board);
      if (!lead || !agentSel[lead]) return false;
    }
    if (!q) return true;
    return slots.some(function (e) { return fieldText(e, board).indexOf(q) >= 0; });
  }
  function hitPassesFilter(hit, board, q, agentSel) {
    var event = hit.event || null;
    var hasAgentFilter = agentSel && Object.keys(agentSel).length > 0;
    if (hasAgentFilter) {
      var actor = actorOf(event, board);
      if (!actor || !agentSel[actor]) return false;
    }
    if (!q) return true;
    return fieldText(event, board).indexOf(q) >= 0;
  }

  function agentChipList(values, selected) {
    var seen = {}, out = [];
    (values || []).forEach(function (v) {
      if (v == null || seen[v]) return;
      seen[v] = true;
      out.push({ label: v, on: !!(selected && selected[v]) });
    });
    return out;
  }

  function countEvents(groups) {
    return (groups || []).reduce(function (n, g) { return n + ((g.ids || []).length); }, 0);
  }
  function allTimes(groups) {
    var out = [];
    (groups || []).forEach(function (g) { (g.times || []).forEach(function (t) { out.push(t); }); });
    return out;
  }
  function topScore(hits) {
    var best = null;
    (hits || []).forEach(function (h) {
      if (h.score != null && (best == null || h.score > best)) best = h.score;
    });
    return best;
  }

  function groupsTiles(loadedCount, total, eventCount, actorCount, hasActor, timeRange) {
    var tiles = [
      { v: loadedCount + " / " + total, l: "groups loaded" },
      { v: String(eventCount), l: "events" },
    ];
    if (hasActor) tiles.push({ v: String(actorCount), l: "actors" });
    tiles.push({ v: timeRange, l: "time range" });
    return tiles;
  }
  // At most 4 tiles — the canvas's fixed 4-column grid (fix round 1,
  // #12/13). `kept` (page_payload's own field for a hits page: results.py,
  // "found; exceeds len() when scouting kept only a depth") never gets a
  // 5th tile here — it lives in hitsNote's fnote text instead. A null
  // `topScoreVal` (nothing scored yet — topScore([]) === null) reads "—",
  // never "0.000" (fix round 1, #2: no invented numbers).
  function hitsTiles(loadedCount, total, scored, topScoreVal, sourceCount, hasActor, timeRange) {
    var tiles = [{ v: loadedCount + " / " + total, l: "hits loaded" }];
    tiles.push(scored
      ? { v: topScoreVal != null ? Number(topScoreVal).toFixed(3) : "—", l: "top score" }
      : { v: "exact", l: "match type" });
    if (hasActor) tiles.push({ v: String(sourceCount), l: "sources" });
    tiles.push({ v: timeRange, l: "time range" });
    return tiles;
  }

  // The hits fnote: the load/match note plus "kept K" when the store could
  // not retrieve every found hit (fix round 1, #5 — dropped from the
  // Load-more row so it is said exactly once).
  function hitsNote(loadedCount, total, matchedCount, kept) {
    var note = loadNote(loadedCount, total, matchedCount);
    if (kept != null && kept < total) note += " · kept " + kept;
    return note;
  }

  var api = {
    PAGE: PAGE,
    timeRangeLabel: timeRangeLabel, loadNote: loadNote, hitsNote: hitsNote, viewsFor: viewsFor,
    fieldText: fieldText, actorOf: actorOf,
    groupPassesFilter: groupPassesFilter, hitPassesFilter: hitPassesFilter,
    agentChipList: agentChipList, countEvents: countEvents,
    allTimes: allTimes, topScore: topScore,
    groupsTiles: groupsTiles, hitsTiles: hitsTiles,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
