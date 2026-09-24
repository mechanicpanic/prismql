// PrismQLFullTable: the Table and Raw JSON views' DOM — grid rows for
// groups/hits, and one line per loaded item tokenized by lexJson (task-7
// brief; graph @aleph/prismql, node #76). lexJson output is untrusted
// corpus text, never HTML-escaped by the tokenizer itself — every token
// lands via `mk()`'s textContent, never innerHTML (global-constraints.md).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var LexJson = window.PrismQLLexJson;

  function headerRow(cols, heads) {
    var tr = mk("div", "tr th");
    tr.setAttribute("role", "row");
    tr.style.gridTemplateColumns = cols;
    heads.forEach(function (h) {
      var span = mk("span", null, h);
      span.setAttribute("role", "columnheader");
      tr.appendChild(span);
    });
    return tr;
  }
  // Fix round 1, #6: a kind/actor cell exists only when the column does
  // (tableHeadsFor already dropped it) — never an empty cell standing in
  // for a field the corpus doesn't set.
  function groupRow(cols, r, board) {
    var tr = mk("div", "tr" + (r.cls ? " " + r.cls : ""));
    tr.setAttribute("role", "row");
    tr.style.gridTemplateColumns = cols;
    tr.appendChild(mk("span", "g", r.group !== "" ? String(r.group) : ""));
    tr.appendChild(mk("span", "m", String(r.n)));
    tr.appendChild(mk("span", "m", r.ts != null ? r.ts : ""));
    if (board.kind) tr.appendChild(mk("span", "k", r.kind != null ? String(r.kind) : ""));
    if (board.actor) tr.appendChild(mk("span", "a", r.actor != null ? String(r.actor) : ""));
    var x = mk("span", "x", r.parts ? null : r.text != null ? String(r.text) : "—");
    // matched spans marked (#119)
    (r.parts || []).forEach(function (p) {
      x.appendChild(p.m ? mk("mark", null, p.t) : document.createTextNode(p.t));
    });
    tr.appendChild(x);
    return tr;
  }
  // A rows result's table row: just key/value, no board-dependent columns
  // (graph @aleph/prismql, #90) — there is no event to draw kind/actor from.
  function rowRow(cols, r) {
    var tr = mk("div", "tr");
    tr.setAttribute("role", "row");
    tr.style.gridTemplateColumns = cols;
    tr.appendChild(mk("span", "k", r.key));
    tr.appendChild(mk("span", "v", r.value));
    return tr;
  }
  function hitRow(cols, r, board) {
    var tr = mk("div", "tr");
    tr.setAttribute("role", "row");
    tr.style.gridTemplateColumns = cols;
    var scoreCell = mk("span", "m", r.score);
    if (r.pct != null) {
      var bar = mk("span", "sbar");
      var i = document.createElement("i");
      i.style.width = r.pct;
      bar.appendChild(i);
      scoreCell.appendChild(bar);
    }
    tr.appendChild(scoreCell);
    tr.appendChild(mk("span", "m", r.ts != null ? r.ts : ""));
    if (board.kind) tr.appendChild(mk("span", "k", r.kind != null ? String(r.kind) : ""));
    if (board.actor) tr.appendChild(mk("span", "a", r.actor != null ? String(r.actor) : ""));
    var x = mk("span", "x");
    r.parts.forEach(function (p) {
      if (p.m) x.appendChild(mk("mark", null, p.t));
      else x.appendChild(document.createTextNode(p.t));
    });
    tr.appendChild(x);
    return tr;
  }

  function renderTable(el, kind, cols, heads, rows, board) {
    board = board || {};
    el.appendChild(headerRow(cols, heads));
    if (!rows.length) {
      var empty = mk("div", "empty");
      empty.appendChild(mk("strong", null, "Nothing matches the filter"));
      el.appendChild(empty);
      return;
    }
    rows.forEach(function (r) {
      var row = kind === "groups" ? groupRow(cols, r, board)
        : kind === "rows" ? rowRow(cols, r)
        : hitRow(cols, r, board);
      el.appendChild(row);
    });
  }

  function rawLine(no, obj) {
    var div = mk("div", "ln");
    div.appendChild(mk("span", "no", String(no)));
    var cd = mk("span", "cd");
    LexJson.lexJson(JSON.stringify(obj)).forEach(function (tok) {
      cd.appendChild(mk("span", tok.c || null, tok.t));
    });
    div.appendChild(cd);
    return div;
  }
  function renderRaw(el, items) {
    if (!items.length) {
      var empty = mk("div", "empty");
      empty.appendChild(mk("strong", null, "Nothing loaded yet"));
      el.appendChild(empty);
      return;
    }
    items.forEach(function (obj, i) { el.appendChild(rawLine(i + 1, obj)); });
  }

  var api = { renderTable: renderTable, renderRaw: renderRaw };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullTable = api;
})(typeof window !== "undefined" ? window : globalThis);
