// PrismQLInspectorRows: the table view for a GROUP BY ... AGGREGATE answer
// kept as a "rows" result (graph @aleph/prismql, #90, extends #63) — a flat
// key/value table, paged in fixed steps from growing offsets like
// inspector-groups.js's chain view ("Show N more"): PrismQLInspectorPageLogic
// .collectRowPages advances by the count each page actually returned, never
// past the server's own max_results cap (fix round 1, #1). No hydrate, no
// board fields: a rows page carries no ids to fetch.
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
    var res = PL.collectRowPages(total, target, PAGE, function (offset, limit) {
      return PF.fetchPage(rid, offset, limit, []);
    });
    if (res.pending && res.rows.length === 0) return { note: "", body: PF.loadingBlock() };
    if (res.gone) return { note: "", body: PF.goneBlock(actions, entry) };
    if (res.error) return { note: "", body: PF.errorBlock(res.error.message) };
    var rows = res.rows;
    var body = document.createElement("div");
    body.appendChild(tableFor(rows));
    var more = mk("div", "more");
    more.appendChild(mk("span", null, res.pending ? "loading…" : PL.groupsMoreLabel(rows.length, total)));
    if (!res.pending && rows.length < total) {
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
