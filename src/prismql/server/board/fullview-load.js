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
    var got = window.PrismQLInspectorPageLogic.collectPages(
      entry.total || 0, loadTo, PAGE,
      function (o, n) { return PF.fetchPage(entry.result_id, o, n, fields); },
      listKey,
    );
    var blocker = null;
    // "Run again" must leave the full view first (goneBlock only calls
    // actions.rerun — a local stand-in closes #full before it).
    if (got.gone) {
      var rerunActions = { rerun: function (e) { actions.closeFull(); actions.rerun(e); } };
      blocker = PF.goneBlock(rerunActions, entry);
    } else if (got.error) {
      blocker = PF.errorBlock(got.error.message);
    }
    return {
      items: got.items, pending: got.pending, blocker: blocker, gone: !!got.gone,
      loadBound: got.bound, labels: got.labels,
    };
  }

  var api = { loadPaged: loadPaged, blockedContext: blockedContext, GONE_NOTE: GONE_NOTE };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullLoad = api;
})(typeof window !== "undefined" ? window : globalThis);
