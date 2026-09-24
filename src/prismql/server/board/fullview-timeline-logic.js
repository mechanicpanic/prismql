// PrismQLFullTimelineLogic: pure shaping for the full view's timeline — the
// event and gap items of one group, its nav entry and its header (graph
// @aleph/prismql, node #76). Split out of fullview-rows.js (the table
// shaping) to keep each under 150 lines; fullview-rows.js re-exports these.
(function (root) {
  "use strict";
  var F = typeof module === "object" && module.exports
    ? require("./format.js")
    : root.PrismQLFormat;
  var IF = typeof module === "object" && module.exports
    ? require("./inspector-format.js")
    : root.PrismQLInspectorFormat;

  function fieldOf(event, key) {
    return event && key && event[key] != null ? event[key] : null;
  }

  // Finding 5: a named result (labels — pattern_names, shared by every
  // group) shows its own slot label on each event item instead of the
  // generic "event n"; an unnamed slot (labels[j] absent/null) still
  // falls back to "event n" at render time (fullview-timeline.js).
  function timelineItems(group, board, labels) {
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
        isGap: false, n: j + 1, label: (labels && labels[j]) || null,
        hms: t != null ? F.hms(t) : "", date: t != null ? IF.localDateTime(t).split(" ")[0] : "",
        kind: fieldOf(ev, board.kind), actor: fieldOf(ev, board.actor),
        text: ev && ev.text != null ? ev.text : null,
        why: (group.explain || [])[j] || null,
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
    // Finding 5: INWINDOW groups are unordered — `times` is not
    // guaranteed chronological, so the range is the min/max of the
    // non-null times, never the filtered array's first/last element.
    var times = (group.times || []).filter(function (t) { return t != null; });
    var ms = times.map(function (t) { return new Date(t).getTime(); });
    var earliest = times[ms.indexOf(Math.min.apply(null, ms))];
    var latest = times[ms.indexOf(Math.max.apply(null, ms))];
    var lead = (group.slots || [])[0] || null;
    return {
      n: group.n, total: total, actor: fieldOf(lead, board.actor) || "",
      span: F.span(group.times || []),
      range: times.length ? IF.localDateTime(earliest) + " → " + F.hms(latest) : "",
    };
  }

  var api = { timelineItems: timelineItems, navItemFor: navItemFor, groupHeaderInfo: groupHeaderInfo };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullTimelineLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
