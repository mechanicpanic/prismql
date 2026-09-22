// PrismQLInspectorFetch: the paged-result fetch/cache and the small shared
// blocks ("gone", error, loading) that both chains (inspector-groups.js) and
// hits (inspector-hits.js) need (graph @aleph/prismql, node #63). One cache
// here — keyed by result_id+offset per the task-5 brief, so a re-render
// never refetches — instead of each consumer keeping its own.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;

  var pageCache = {}; // "rid#offset" -> {status:"loading"} | {status:"done", data}
  function fetchPage(rid, offset, limit, fields) {
    var key = rid + "#" + offset;
    var rec = pageCache[key];
    if (rec) return rec;
    rec = { status: "loading" };
    pageCache[key] = rec;
    window.PrismQLApi.page(rid, { offset: offset, limit: limit, hydrate: true, fields: fields.join(",") })
      .then(function (data) { rec.status = "done"; rec.data = data; bump(); })
      .catch(function (e) {
        rec.status = "done";
        rec.data = { error: { message: String((e && e.message) || e) } };
        bump();
      });
    return rec;
  }
  function bump() { if (window.PrismQLBoard) window.PrismQLBoard.render(); }
  function fieldsFor(board) {
    var arr = ["text"];
    if (board.kind) arr.push(board.kind);
    if (board.actor) arr.push(board.actor);
    return arr;
  }

  function goneBlock(actions, entry) {
    var wrap = document.createElement("div");
    var empty = mk("div", "empty"); empty.style.padding = "24px";
    empty.appendChild(mk("strong", null, "This result is no longer kept"));
    empty.appendChild(mk("span", null, "(evicted, reloaded or restarted)"));
    var btn = mk("button", "ghost", "Run again");
    btn.type = "button";
    btn.addEventListener("click", function () { actions.rerun(entry); });
    empty.appendChild(btn);
    wrap.appendChild(empty);
    return wrap;
  }
  function errorBlock(message) {
    var box = mk("div", "errbox");
    box.appendChild(mk("div", "m", message || ""));
    return box;
  }
  function loadingBlock() {
    var wrap = document.createElement("div");
    var empty = mk("div", "empty"); empty.style.padding = "24px";
    empty.appendChild(mk("strong", null, "Loading…"));
    wrap.appendChild(empty);
    return wrap;
  }

  var api = {
    fetchPage: fetchPage, fieldsFor: fieldsFor,
    goneBlock: goneBlock, errorBlock: errorBlock, loadingBlock: loadingBlock,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorFetch = api;
})(typeof window !== "undefined" ? window : globalThis);
