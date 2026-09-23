// PrismQLInspectorRows: the table view for a GROUP BY ... AGGREGATE answer
// kept as a "rows" result (graph @aleph/prismql, #90, extends #63) — a flat
// key/value table, paged like inspector-groups.js's chain view ("Show N
// more"). No hydrate, no board fields: a rows page carries no ids to fetch.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var PL = window.PrismQLInspectorPageLogic;
  var PF = window.PrismQLInspectorFetch;

  var PAGE = 20;
  // Same per-seq "how many shown" tracker as inspector-groups.js, kept
  // separate: the two views page independently and never share state.
  var shown = { seq: null, n: PAGE };
  function shownFor(seq) {
    if (shown.seq !== seq) {
      shown.seq = seq;
      shown.n = PAGE;
    }
    return shown.n;
  }
  function bumpShown(seq) {
    if (shown.seq !== seq) return;
    shown.n += PAGE;
    if (window.PrismQLBoard) window.PrismQLBoard.render();
  }

  function rowTr(r) {
    var tr = mk("tr");
    tr.appendChild(mk("td", "k", String(r.key)));
    tr.appendChild(mk("td", "v", PL.rowValueText(r.value)));
    return tr;
  }
  function tableFor(rows) {
    var table = mk("table", "rows-table");
    var body = mk("tbody");
    rows.forEach(function (r) { body.appendChild(rowTr(r)); });
    table.appendChild(body);
    return table;
  }

  function render(entry, state, actions) {
    var rid = entry.result_id, total = entry.total;
    var target = shownFor(entry.seq);
    var rec = PF.fetchPage(rid, 0, target, []);
    if (rec.status === "loading") return { note: "", body: PF.loadingBlock() };
    if (rec.data.gone) return { note: "", body: PF.goneBlock(actions, entry) };
    if (rec.data.error) return { note: "", body: PF.errorBlock(rec.data.error.message) };
    var rows = rec.data.rows || [];
    var body = document.createElement("div");
    body.appendChild(tableFor(rows));
    var more = mk("div", "more");
    more.appendChild(mk("span", null, PL.groupsMoreLabel(rows.length, total)));
    if (rows.length < total) {
      var btn = mk("button", "ghost", "Show " + PAGE + " more");
      btn.type = "button";
      btn.addEventListener("click", function () { bumpShown(entry.seq); });
      more.appendChild(btn);
    }
    body.appendChild(more);
    var note = (typeof total === "number" ? total : rows.length) + " groups";
    return { note: note, body: body };
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorRows = api;
})(typeof window !== "undefined" ? window : globalThis);
