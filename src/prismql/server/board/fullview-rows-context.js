// PrismQLFullRowsContext: the full view's context for a "rows" result
// (GROUP BY ... AGGREGATE answer, graph @aleph/prismql, #90) — flat
// key/value pairs, no board fields; fullview-load.js's loadPaged already
// covers paging. Split out of fullview-data.js to keep it under 150 lines
// (fix round 1, #6).
(function (root) {
  "use strict";
  var PL = window.PrismQLInspectorPageLogic;
  var Nav = typeof module === "object" && module.exports
    ? require("./fullview-nav-logic.js") : window.PrismQLFullNav;
  var PFLoad = typeof module === "object" && module.exports
    ? require("./fullview-load.js") : window.PrismQLFullLoad;

  function rowsContext(entry, vs, actions) {
    var res = PFLoad.loadPage(entry, [], vs, actions, "rows");
    if (res.blocker) return PFLoad.blockedContext("rows", res);
    var rows = res.items;
    var q = vs.q.trim().toLowerCase();
    // Filter on exactly the text the cell shows (fix round 1, #5) — a
    // list renders joined with ", " and null renders "—", never
    // String(r.value)'s "x,y" or the literal "null".
    var filtered = !q ? rows : rows.filter(function (r) {
      return String(r.key).toLowerCase().indexOf(q) >= 0
        || PL.rowValueText(r.value).toLowerCase().indexOf(q) >= 0;
    });
    var tiles = rows.length === 0 ? [] : [{ v: rows.length + " / " + entry.total, l: "rows on this page" }];
    return {
      kind: "rows", loaded: rows, filtered: filtered,
      pending: res.pending, blocker: res.blocker, nav: res.nav, total: entry.total,
      canFilter: true, agents: [], tiles: tiles,
      note: res.nav.count == null ? "" : Nav.pageNote(res.nav.offset, res.nav.got, res.nav.count, filtered.length, res.nav.total),
    };
  }

  var api = { rowsContext: rowsContext };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullRowsContext = api;
})(typeof window !== "undefined" ? window : globalThis);
