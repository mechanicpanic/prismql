// PrismQLInspectorHits: the hits view for search/similar results — a fixed
// first page of 3, scores/bars for similar, highlight marks for search
// (graph @aleph/prismql, node #63; task-5 brief). Fetching and the shared
// blocker blocks (gone/error/loading) live in inspector-fetch.js.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;
  var PF = window.PrismQLInspectorFetch;

  function hitDiv(h, board, terms, scored) {
    var div = mk("div", "hit" + (scored ? "" : " noscore"));
    if (scored) {
      var sc = document.createElement("div");
      sc.appendChild(mk("div", "sc", Number(h.score).toFixed(3)));
      var bar = mk("div", "bar");
      var i = document.createElement("i");
      i.style.width = Math.max(0, Math.min(1, h.score)) * 100 + "%";
      bar.appendChild(i);
      sc.appendChild(bar);
      div.appendChild(sc);
    }
    var right = document.createElement("div"); right.style.minWidth = "0";
    var evWrap = mk("div", "ev");
    var l = mk("div", "l"); l.style.gridColumn = "1 / -1";
    var event = h.event || {};
    if (board.kind && event[board.kind] != null) l.appendChild(mk("span", "k", String(event[board.kind])));
    if (board.actor && event[board.actor] != null) l.appendChild(mk("span", "a", String(event[board.actor])));
    l.appendChild(mk("span", "t", h.time ? IF.localDateTime(h.time) : ""));
    evWrap.appendChild(l);
    right.appendChild(evWrap);
    var x = mk("div", "x");
    F.highlightParts(event.text || "", terms).forEach(function (p) {
      if (p.m) x.appendChild(mk("mark", null, p.t));
      else x.appendChild(document.createTextNode(p.t));
    });
    right.appendChild(x);
    div.appendChild(right);
    return div;
  }

  function render(entry, state, actions) {
    var board = (state.corpora.board || {})[entry.corpus] || {};
    var rec = PF.fetchPage(entry.result_id, 0, 3, PF.fieldsFor(board));
    if (rec.status === "loading") return { note: "", body: PF.loadingBlock() };
    if (rec.data.gone) return { note: "", body: PF.goneBlock(actions, entry) };
    if (rec.data.error) return { note: "", body: PF.errorBlock(rec.data.error.message) };
    var scored = entry.kind === "similar";
    var terms = entry.kind === "search" ? F.searchTerms(entry.query || "") : [];
    var body = document.createElement("div");
    (rec.data.hits || []).forEach(function (h) { body.appendChild(hitDiv(h, board, terms, scored)); });
    return { note: rec.data.count + " of " + entry.total, body: body };
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorHits = api;
})(typeof window !== "undefined" ? window : globalThis);
