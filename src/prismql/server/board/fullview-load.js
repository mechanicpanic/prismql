// PrismQLFullLoad: paging through the shared fetch cache and the shared
// blocked-view context — used by every full-view kind (groups, hits, rows)
// so a gone/error/loading result renders the same way everywhere. Split
// out of fullview-data.js to keep it under 150 lines (graph @aleph/prismql,
// #90 fix round 1, #6); fullview-rows-context.js (the rows kind) depends on
// it too.
(function (root) {
  "use strict";
  var PF = window.PrismQLInspectorFetch;
  var FL = window.PrismQLFullLogic;
  var Nav = window.PrismQLFullNav;

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
      nav: res.gone ? null : res.nav, total: null, tiles: [], canFilter: false, agents: [],
      note: res.gone ? GONE_NOTE : "",
    };
  }

  // One page of the result, in the view `vs` chose (page, order, reverse):
  // never more than PAGE items, never the pages before it — the DOM stays
  // one page long. The request always asks for PAGE; offsets step by the
  // size the server actually returned (it caps below PAGE at max_results),
  // learned from the first page, which is always fetched first. `nav` is
  // what the pager needs; the count falls back to the journal's total until
  // a page has told the store's own.
  function loadPage(entry, fields, vs, actions, listKey) {
    var offset = vs.page * vs.pageSize;
    var rec = PF.fetchPage(entry.result_id, offset, PAGE, fields, Nav.viewOf(vs));
    var nav = { offset: offset, got: 0, page: vs.page, pageCount: Nav.pageCount(vs.count == null ? entry.total : vs.count, vs.pageSize) };
    if (rec.status === "loading") return { items: [], indices: [], pending: true, blocker: null, gone: false, nav: nav };
    var data = rec.data;
    var blocker = null;
    // "Run again" must leave the full view first (goneBlock only calls
    // actions.rerun — a local stand-in closes #full before it).
    if (data.gone) {
      var rerunActions = { rerun: function (e) { actions.closeFull(); actions.rerun(e); } };
      blocker = PF.goneBlock(rerunActions, entry);
    } else if (data.error) {
      blocker = PF.errorBlock(data.error.message);
    }
    if (blocker) return { items: [], indices: [], pending: false, blocker: blocker, gone: !!data.gone, nav: nav };
    if (offset === 0) vs.pageSize = Nav.effectiveSize(PAGE, data);
    vs.count = Nav.itemCount(data, entry.total || 0);
    var items = data[listKey] || [];
    nav = { offset: offset, got: items.length, page: vs.page, pageCount: Nav.pageCount(vs.count, vs.pageSize), count: vs.count, total: data.total };
    return {
      items: items, indices: Nav.storedIndexes(data, offset, items.length),
      pending: false, blocker: null, gone: false, labels: data.labels || null, nav: nav,
    };
  }

  var api = { loadPage: loadPage, blockedContext: blockedContext, GONE_NOTE: GONE_NOTE };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullLoad = api;
})(typeof window !== "undefined" ? window : globalThis);
