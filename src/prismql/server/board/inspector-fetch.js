// PrismQLInspectorFetch: the paged-result fetch/cache that inspector-
// groups.js and inspector-hits.js share (graph @aleph/prismql, node #63;
// fix rounds 1-2). A resolved page is cached forever only when it is
// really a page (PrismQLInspectorPageLogic.isValidPage); a failure
// (network error, 429/5xx, an unrelated JSON body) is kept just long
// enough to show once, then either a later fetchPage() call for the same
// key or the failure's own expiry timer tries again — never a permanent
// bad cache entry, never a stuck one for an idle viewer.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var UI = window.PrismQLInspectorUI;
  var PL = window.PrismQLInspectorPageLogic;
  var L = window.PrismQLEditorLogic;

  var FAIL_TTL_MS = 5000;
  var pageCache = {}; // cacheKey -> {status:"loading"} | {status:"done", data}
  var failCache = {}; // cacheKey -> {untilMs, data} — a short-lived stand-in, never the real cache
  var failTimers = {}; // cacheKey -> the one pending "try again" timer for it
  // Bumped by clearCache() (a stream reset): a fetch started before the
  // bump must not write its outcome into the fresh caches (fix round 2,
  // #4) — its own closure carries the generation it was asked under.
  var generation = 0;

  function bump() { if (window.PrismQLBoard) window.PrismQLBoard.render(); }

  // A failure heals itself for an idle viewer too: once the TTL passes,
  // fire one render so the next read of this key retries (fix round 2,
  // #2) — de-duplicated, so repeated failures don't stack timers.
  function scheduleRetryRender(key) {
    if (failTimers[key]) return;
    failTimers[key] = setTimeout(function () {
      delete failTimers[key];
      bump();
    }, FAIL_TTL_MS + 1);
  }

  function markFailed(key, rec, gen, errorInfo) {
    if (gen !== generation) return; // a reset happened while this was in flight
    delete pageCache[key];
    failCache[key] = { untilMs: Date.now() + FAIL_TTL_MS, data: { error: errorInfo } };
    rec.status = "done";
    rec.data = failCache[key].data;
    scheduleRetryRender(key);
    bump();
  }

  function settle(key, rec, gen, data) {
    if (gen !== generation) return;
    if (!PL.isValidPage(data)) {
      markFailed(key, rec, gen, { message: PL.errorMessageFor(data) });
      return;
    }
    rec.status = "done";
    rec.data = data;
    bump();
  }

  // `view` ({order, reverse}) is the optional order of the result's pages;
  // absent, the stored order.
  function fetchPage(rid, offset, limit, fields, view) {
    var key = PL.cacheKey(rid, offset, limit, fields, view);
    var hit = pageCache[key];
    if (hit) return hit;
    var failed = failCache[key];
    if (failed && Date.now() < failed.untilMs) return { status: "done", data: failed.data };
    var rec = { status: "loading" };
    var gen = generation;
    pageCache[key] = rec;
    var opts = { offset: offset, limit: limit, hydrate: true, fields: fields.join(","), explain: true };
    if (view) { opts.order = view.order; opts.reverse = view.reverse; }
    window.PrismQLApi.page(rid, opts)
      .then(function (data) { settle(key, rec, gen, data); })
      .catch(function (e) { markFailed(key, rec, gen, { message: String((e && e.message) || e) }); });
    return rec;
  }

  function clearCache() {
    generation++;
    pageCache = {};
    failCache = {};
    Object.keys(failTimers).forEach(function (k) { clearTimeout(failTimers[k]); });
    failTimers = {};
  }

  // Whether groups/hits may fetch yet, and with what board fields: never
  // guess ahead of /corpora loading; once it fails, fetch text-only
  // rather than block forever. A `board` missing its own map (a
  // malformed /corpora response) never throws (fix round 2, #1).
  function boardFieldsFor(state, corpus) {
    if (state.corpora) return {
      board: (state.corpora.board || {})[corpus] || {},
      idField: (state.corpora.id_field || {})[corpus] || "id",
      blocked: false,
    };
    if (state.corporaFailed) return { board: {}, idField: "id", blocked: false };
    return { board: {}, idField: "id", blocked: true };
  }

  // Round 2, #5: same dictionaries gate as the inspector's own Run again
  // (inspector-detail.js) — a gone result whose request used request-scoped
  // dictionaries can't be replayed either; disable, don't wire the click.
  function goneBlock(actions, entry) {
    var blocked = L.hasRequestDictionaries(entry);
    var btn = mk("button", "ghost", "Run again");
    btn.type = "button";
    if (blocked) { btn.disabled = true; btn.title = L.DICT_NOTE; }
    else btn.addEventListener("click", function () { actions.rerun(entry); });
    var wrap = document.createElement("div");
    wrap.appendChild(UI.emptyBlock(
      "This result is no longer kept", "(evicted, reloaded or restarted)",
      { compact: true, action: btn },
    ));
    if (blocked) wrap.appendChild(mk("div", "dict-note", L.DICT_NOTE));
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
