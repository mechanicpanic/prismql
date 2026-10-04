// PrismQLFullBody: the full view's `.fbody` dispatch — timeline/table/raw/
// summary per the active view and the pager footer under it (task-7 brief;
// graph @aleph/prismql, node #76). One page at a time: nothing here ever
// accumulates earlier pages (fullview-load.js loads exactly vs.page).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var PF = window.PrismQLInspectorFetch;
  var FR = window.PrismQLFullRows;
  var Data = window.PrismQLFullData;
  var Header = window.PrismQLFullHeader;
  var Fcenter = window.PrismQLFullFcenter;
  var Timeline = window.PrismQLFullTimeline;
  var Table = window.PrismQLFullTable;
  var Pager = window.PrismQLFullPager;
  var Nav = window.PrismQLFullNav;

  // A verbose group opens or folds: state in vs.shown, then a rebuild.
  function toggler(vs, onChange) {
    return function (idx, total, action) { Nav.applyShown(vs, idx, total, action); onChange(); };
  }

  function buildTimeline(body, ctx, board, vs, onChange, onPick) {
    var tl = mk("div", "tl");
    var nav = mk("div", "gnav");
    nav.setAttribute("aria-label", "Groups");
    var gi = Math.min(vs.group, Math.max(0, ctx.filtered.length - 1));
    Timeline.renderNav(nav, ctx.filtered, board, gi, onPick);
    tl.appendChild(nav);
    var detail = mk("div", "gdetail");
    Timeline.renderDetail(detail, ctx.filtered[gi], ctx.total, board, ctx.labels, vs.shown, toggler(vs, onChange));
    tl.appendChild(detail);
    body.appendChild(tl);
    return ctx.filtered;
  }
  function buildTable(body, ctx, outputKind, board, vs, onChange) {
    var wrap = mk("div", "tbl");
    wrap.setAttribute("role", "table");
    wrap.setAttribute("aria-label", "Output as a table");
    var heads = FR.tableHeadsFor(outputKind, ctx.scored, board);
    var rows = outputKind === "groups" ? FR.groupTableRows(ctx.filtered, board, vs.shown)
      : outputKind === "rows" ? FR.rowTableRows(ctx.filtered)
      : FR.hitTableRows(ctx.filtered, board, ctx.terms, ctx.scored);
    Table.renderTable(wrap, outputKind, heads.cols, heads.heads, rows, board, toggler(vs, onChange));
    body.appendChild(wrap);
  }
  function buildRaw(body, entry, ctx, vs) {
    var raw = mk("div", "raw");
    raw.setAttribute("aria-label", "Raw output, one JSON object per line");
    Table.renderRaw(raw, Data.rawItemsFor(ctx, entry), ctx.nav ? ctx.nav.offset : 0);
    body.appendChild(raw);
  }

  // Returns the filtered groups behind the Timeline view (or [] otherwise)
  // — the caller caches it for ↑/↓ nav, since the DOM alone can't tell a
  // filtered-out group from one never loaded.
  function build(el, entry, ctx, outputKind, board, vs, actions, onChange, onPick) {
    var body = mk("div", "fbody");
    var filteredGroups = [];
    if (ctx.blocker) {
      body.appendChild(ctx.blocker);
    } else if (ctx.pending && ctx.loaded.length === 0) {
      body.appendChild(PF.loadingBlock());
    } else if (vs.view === "timeline") {
      filteredGroups = buildTimeline(body, ctx, board, vs, onChange, onPick);
    } else if (vs.view === "table") {
      buildTable(body, ctx, outputKind, board, vs, onChange);
    } else if (vs.view === "raw") {
      buildRaw(body, entry, ctx, vs);
    } else {
      body.appendChild(Fcenter.build(entry, outputKind, actions));
    }
    // Paged kinds keep their footer through loading and a failed page (the
    // way back); a gone result has no nav at all.
    if (ctx.nav && (vs.view !== "summary" || ctx.blocker)) body.appendChild(Pager.buildFooter(ctx, vs, onChange));
    el.appendChild(body);
    return filteredGroups;
  }

  var api = { build: build };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullBody = api;
})(typeof window !== "undefined" ? window : globalThis);
