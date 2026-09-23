// PrismQLFullRows: pure row/item shaping for the full view's table,
// timeline nav and vertical timeline (task-7 brief; graph @aleph/prismql,
// node #76) — window-free like inspector-page-logic.js. Callers already
// paired a group's `events` to its `ids` by id, not index (fix round 1,
// #7 — inspector-page-logic.js's pairEventsToSlots), and pass the result
// in as `slots`; a slot with no matching event renders without kind/actor/
// text, never a guess.
(function (root) {
  "use strict";
  var F = typeof module === "object" && module.exports
    ? require("./format.js")
    : root.PrismQLFormat;
  var IF = typeof module === "object" && module.exports
    ? require("./inspector-format.js")
    : root.PrismQLInspectorFormat;

  // Fix round 1, #6: the kind/actor columns appear only when the corpus
  // board config sets that field — same rule the timeline cards already
  // follow (never a guessed or empty-but-present column).
  function tableHeadsFor(kind, scored, board) {
    board = board || {};
    var heads = [], cols = [];
    if (kind === "groups") {
      heads.push("group", "#", "time"); cols.push("56px", "44px", "168px");
      if (board.kind) { heads.push("kind"); cols.push("minmax(0,230px)"); }
      if (board.actor) { heads.push("agent"); cols.push("150px"); }
    } else {
      heads.push(scored ? "score" : "match", "time"); cols.push("96px", "168px");
      if (board.kind) { heads.push("kind"); cols.push("minmax(0,170px)"); }
      if (board.actor) { heads.push("source"); cols.push("150px"); }
    }
    heads.push("text"); cols.push("minmax(0,1fr)");
    return { cols: cols.join(" "), heads: heads };
  }

  function fieldOf(event, key) {
    return event && key && event[key] != null ? event[key] : null;
  }
  // The table's TIME column is a fixed grid cell, not a wrapping one — the
  // server's full ISO instant (microseconds, offset) overruns it into the
  // next column, so every table row shows the same compact local form the
  // rest of the board uses (inspector-format.js's localDateTime).
  function shortTime(t) { return t != null ? IF.localDateTime(t) : null; }

  function groupTableRows(groups, board) {
    var rows = [];
    (groups || []).forEach(function (g) {
      var ids = g.ids || [], slots = g.slots || [];
      ids.forEach(function (id, j) {
        var ev = slots[j];
        rows.push({
          cls: j === 0 ? "first" : "", group: j === 0 ? g.n : "", n: j + 1,
          ts: shortTime((g.times || [])[j]),
          kind: fieldOf(ev, board.kind), actor: fieldOf(ev, board.actor),
          text: ev && ev.text != null ? ev.text : null,
        });
      });
    });
    return rows;
  }

  // BM25 never surfaces as a "score" for search — an unscored cell reads
  // "exact" with a full bar, the canvas's own wording (fix round 1, #7);
  // "match" is only the column HEADER's label (tableHeadsFor), never the
  // cell's own value (global-constraints.md: never show BM25 as a score).
  function hitTableRows(hits, board, terms, scored) {
    return (hits || []).map(function (h) {
      var event = h.event || null;
      return {
        score: scored ? Number(h.score).toFixed(3) : "exact",
        pct: scored ? Math.max(0, Math.min(1, h.score)) * 100 + "%" : "100%",
        ts: shortTime(h.time),
        kind: fieldOf(event, board.kind), actor: fieldOf(event, board.actor),
        parts: F.highlightParts((event && event.text) || "", terms || []),
      };
    });
  }

  function timelineItems(group, board) {
    var ids = group.ids || [], positions = group.positions || [];
    var times = group.times || [], slots = group.slots || [];
    var items = [];
    for (var j = 0; j < ids.length; j++) {
      if (j > 0) {
        var gap = F.gapLabel(positions[j - 1], positions[j], times[j - 1], times[j]);
        items.push({ isGap: true, plus: gap.plus, label: gap.label });
      }
      var ev = slots[j], t = times[j];
      items.push({
        isGap: false, n: j + 1,
        hms: t != null ? F.hms(t) : "", date: t != null ? IF.localDateTime(t).split(" ")[0] : "",
        kind: fieldOf(ev, board.kind), actor: fieldOf(ev, board.actor),
        text: ev && ev.text != null ? ev.text : null,
      });
    }
    return items;
  }

  function navItemFor(group, board) {
    var slots = group.slots || [];
    var lead = slots[0] || null;
    var withText = slots.filter(function (e) { return e && e.text; })[0];
    var snip = withText ? withText.text : (fieldOf(lead, board.kind) || "");
    var t0 = (group.times || [])[0];
    return {
      n: group.n, actor: fieldOf(lead, board.actor) || "",
      span: F.span(group.times || []), snip: snip || "",
      date: t0 != null ? IF.localDateTime(t0) : "",
    };
  }

  function groupHeaderInfo(group, total, board) {
    var times = (group.times || []).filter(function (t) { return t != null; });
    var lead = (group.slots || [])[0] || null;
    return {
      n: group.n, total: total, actor: fieldOf(lead, board.actor) || "",
      span: F.span(group.times || []),
      range: times.length ? IF.localDateTime(times[0]) + " → " + F.hms(times[times.length - 1]) : "",
    };
  }

  var api = {
    tableHeadsFor: tableHeadsFor, groupTableRows: groupTableRows, hitTableRows: hitTableRows,
    timelineItems: timelineItems, navItemFor: navItemFor, groupHeaderInfo: groupHeaderInfo,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullRows = api;
})(typeof window !== "undefined" ? window : globalThis);
