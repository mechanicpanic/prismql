// PrismQLInspectorFetch: the paged-result fetch/cache that inspector-
// groups.js and inspector-hits.js share (graph @aleph/prismql, node #63;
// fix round 1). A resolved page is cached forever only when it is really
// a page (PrismQLInspectorPageLogic.isValidPage); a failure (network
// error, 429/5xx, an unrelated JSON body) is kept just long enough to
// show once, then a later fetchPage() call for the same key tries again
// (fix round 1, #2) — never a permanent bad cache entry.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var UI = window.PrismQLInspectorUI;
  var PL = window.PrismQLInspectorPageLogic;

  var FAIL_TTL_MS = 5000;
  var pageCache = {}; // cacheKey -> {status:"loading"} | {status:"done", data}
  var failCache = {}; // cacheKey -> {untilMs, data} — a short-lived stand-in, never the real cache

  function bump() { if (window.PrismQLBoard) window.PrismQLBoard.render(); }

  function markFailed(key, rec, errorInfo) {
    delete pageCache[key];
    failCache[key] = { untilMs: Date.now() + FAIL_TTL_MS, data: { error: errorInfo } };
    rec.status = "done";
    rec.data = failCache[key].data;
    bump();
  }

  function settle(key, rec, data) {
    if (!PL.isValidPage(data)) {
      markFailed(key, rec, { message: PL.errorMessageFor(data) });
      return;
    }
    rec.status = "done";
    rec.data = data;
    bump();
  }

  function fetchPage(rid, offset, limit, fields) {
    var key = PL.cacheKey(rid, offset, limit, fields);
    var hit = pageCache[key];
    if (hit) return hit;
    var failed = failCache[key];
    if (failed && Date.now() < failed.untilMs) return { status: "done", data: failed.data };
    var rec = { status: "loading" };
    pageCache[key] = rec;
    window.PrismQLApi.page(rid, { offset: offset, limit: limit, hydrate: true, fields: fields.join(",") })
      .then(function (data) { settle(key, rec, data); })
      .catch(function (e) { markFailed(key, rec, { message: String((e && e.message) || e) }); });
    return rec;
  }

  function clearCache() {
    pageCache = {};
    failCache = {};
  }

  // Whether groups/hits may fetch yet, and with what board fields: never
  // guess ahead of /corpora loading; once it fails, fetch text-only
  // rather than block forever, and keep retrying corpora in the
  // background (fix round 1, #3).
  function boardFieldsFor(state, corpus) {
    if (state.corpora) return { board: state.corpora.board[corpus] || {}, blocked: false };
    if (state.corporaFailed) return { board: {}, blocked: false };
    return { board: {}, blocked: true };
  }

  function goneBlock(actions, entry) {
    var btn = mk("button", "ghost", "Run again");
    btn.type = "button";
    btn.addEventListener("click", function () { actions.rerun(entry); });
    var wrap = document.createElement("div");
    wrap.appendChild(UI.emptyBlock(
      "This result is no longer kept", "(evicted, reloaded or restarted)",
      { compact: true, action: btn },
    ));
    return wrap;
  }
  function errorBlock(message) {
    var box = mk("div", "errbox");
    box.appendChild(mk("div", "m", message || ""));
    return box;
  }
  function loadingBlock() {
    var wrap = document.createElement("div");
    wrap.appendChild(UI.emptyBlock("Loading…", null, { compact: true }));
    return wrap;
  }

  var api = {
    fetchPage: fetchPage, clearCache: clearCache, boardFieldsFor: boardFieldsFor,
    goneBlock: goneBlock, errorBlock: errorBlock, loadingBlock: loadingBlock,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorFetch = api;
})(typeof window !== "undefined" ? window : globalThis);
