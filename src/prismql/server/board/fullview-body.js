// PrismQLFullBody: the full view's `.fbody` dispatch — timeline/table/raw/
// summary per the active view, the shared "Load more" button and
// scroll-to-end auto-load (task-7 brief; graph @aleph/prismql, node #76).
// Never paginates past `ctx.loadBound` (fullview-load.js, through
// collectPages, already clamps it to what the store actually kept).
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
  var FL = window.PrismQLFullLogic;

  var PAGE = FL.PAGE; // fix round 1, #8: one shared constant, not a literal per file

  // Fix round 1, #5: the count is dropped here — the fnote above already
  // says "<loaded> of <total> loaded" (plus "kept K" for hits), so this
  // row only ever needs to say whether more can be asked for.
  function appendLoadMore(container, ctx, vs, onMore) {
    if (ctx.kind !== "groups" && ctx.kind !== "hits" && ctx.kind !== "rows") return;
    if (ctx.loaded.length >= ctx.loadBound) return;
    var wrap = mk("div", "more");
    if (ctx.pending) {
      wrap.appendChild(mk("span", null, "loading…"));
    } else {
      var btn = mk("button", "ghost", "Load more");
      btn.type = "button";
      btn.addEventListener("click", function () { vs.loadTo += PAGE; onMore(); });
      wrap.appendChild(btn);
    }
    container.appendChild(wrap);
  }
  function attachInfiniteScroll(container, ctx, vs, onMore) {
    if (ctx.kind !== "groups" && ctx.kind !== "hits" && ctx.kind !== "rows") return;
    if (ctx.pending || ctx.loaded.length >= ctx.loadBound) return;
    container.addEventListener("scroll", function onScroll() {
      if (container.scrollTop + container.clientHeight >= container.scrollHeight - 40) {
        container.removeEventListener("scroll", onScroll);
        vs.loadTo += PAGE;
        onMore();
      }
    });
  }
  function loadable(el, ctx, vs, onMore) {
    appendLoadMore(el, ctx, vs, onMore);
    attachInfiniteScroll(el, ctx, vs, onMore);
  }

  function buildTimeline(body, ctx, board, vs, onMore, onPick) {
    var tl = mk("div", "tl");
    var nav = mk("div", "gnav");
    nav.setAttribute("aria-label", "Groups");
    var gi = Math.min(vs.group, Math.max(0, ctx.filtered.length - 1));
    Timeline.renderNav(nav, ctx.filtered, board, gi, onPick);
    loadable(nav, ctx, vs, onMore);
    tl.appendChild(nav);
    var detail = mk("div", "gdetail");
    Timeline.renderDetail(detail, ctx.filtered[gi], ctx.total, board, ctx.labels);
    tl.appendChild(detail);
    body.appendChild(tl);
    return ctx.filtered;
  }
  function buildTable(body, ctx, outputKind, board, vs, onMore) {
    var wrap = mk("div", "tbl");
    wrap.setAttribute("role", "table");
    wrap.setAttribute("aria-label", "Output as a table");
    var heads = FR.tableHeadsFor(outputKind, ctx.scored, board);
    var rows = outputKind === "groups" ? FR.groupTableRows(ctx.filtered, board)
      : outputKind === "rows" ? FR.rowTableRows(ctx.filtered)
      : FR.hitTableRows(ctx.filtered, board, ctx.terms, ctx.scored);
    Table.renderTable(wrap, outputKind, heads.cols, heads.heads, rows, board);
    loadable(wrap, ctx, vs, onMore);
    body.appendChild(wrap);
  }
  function buildRaw(body, entry, ctx, vs, onMore) {
    var raw = mk("div", "raw");
    raw.setAttribute("aria-label", "Raw output, one JSON object per line");
    Table.renderRaw(raw, Data.rawItemsFor(ctx, entry));
    loadable(raw, ctx, vs, onMore);
    body.appendChild(raw);
  }

  // Returns the filtered groups behind the Timeline view (or [] otherwise)
  // — the caller caches it for ↑/↓ nav, since the DOM alone can't tell a
  // filtered-out group from one never loaded.
  function build(el, entry, ctx, outputKind, board, vs, actions, onMore, onPick) {
    var body = mk("div", "fbody");
    var filteredGroups = [];
    if (ctx.blocker) {
      body.appendChild(ctx.blocker);
    } else if (ctx.pending && ctx.loaded.length === 0) {
      body.appendChild(PF.loadingBlock());
    } else if (vs.view === "timeline") {
      filteredGroups = buildTimeline(body, ctx, board, vs, onMore, onPick);
    } else if (vs.view === "table") {
      buildTable(body, ctx, outputKind, board, vs, onMore);
    } else if (vs.view === "raw") {
      buildRaw(body, entry, ctx, vs, onMore);
    } else {
      body.appendChild(Fcenter.build(entry, outputKind, actions));
    }
    el.appendChild(body);
    return filteredGroups;
  }

  var api = { build: build };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullBody = api;
})(typeof window !== "undefined" ? window : globalThis);
