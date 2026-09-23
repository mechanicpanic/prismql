// PrismQLInspectorCorpus: the inspector's Corpus tab — what a corpus holds and
// can answer: event count, capabilities, role fields, every field with its
// most frequent values and counts, and the dictionaries' words (graph
// @aleph/prismql, node #86). Reads state.schemas via corpus-schemas.js;
// wording and ordering come from corpus-logic.js.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var CL = window.PrismQLCorpusLogic;
  var PF = window.PrismQLInspectorFetch;

  function header(pane, name, schema) {
    var head = mk("div", "dhead");
    head.appendChild(mk("span", "cname", name));
    var caps = mk("span", "caps");
    CL.capabilities(schema).forEach(function (c) {
      var chip = mk("span", "cap" + (c.on ? " on" : ""), c.label);
      chip.title = c.title;
      caps.appendChild(chip);
    });
    head.appendChild(caps);
    pane.appendChild(head);
    pane.appendChild(mk("p", "when", CL.summary(schema)));
  }

  function kv(pane, schema) {
    var dl = mk("dl", "kv");
    var board = schema.board || {};
    var pairs = [
      ["Backend", schema.backend + " · text " + schema.text_search],
      ["Text match", schema.text_match + " · " + schema.text_language],
      ["Id", schema.id_field],
      ["Time", schema.timestamp_field],
    ];
    if (board.kind || board.actor) {
      pairs.push(["Kind · actor", (board.kind || "—") + " · " + (board.actor || "—")]);
    }
    pairs.forEach(function (p) {
      dl.appendChild(mk("dt", null, p[0]));
      dl.appendChild(mk("dd", "mono", p[1]));
    });
    pane.appendChild(dl);
  }

  function field(row) {
    var div = mk("div", "fld");
    var fh = mk("div", "fh");
    fh.appendChild(mk("span", "fn", row.name));
    fh.appendChild(mk("span", "ft", row.type));
    if (row.role) fh.appendChild(mk("span", "role", row.role));
    if (row.coverage) fh.appendChild(mk("span", "cov", row.coverage));
    div.appendChild(fh);
    if (row.values.length) {
      var vals = mk("div", "vals");
      row.values.forEach(function (p) {
        var v = mk("span", "val", String(p.v));
        v.title = p.v + " — " + CL.fmt(p.n) + " events";
        v.appendChild(mk("b", null, CL.fmt(p.n)));
        vals.appendChild(v);
      });
      div.appendChild(vals);
    }
    if (row.note) div.appendChild(mk("span", "vnote", row.note));
    return div;
  }

  function section(pane, title, note) {
    var s = mk("div", "sect", title);
    if (note) s.appendChild(mk("span", "push", note));
    pane.appendChild(s);
  }

  function dictionaries(pane, schema) {
    var rows = CL.dictionaryRows(schema);
    section(pane, "Dictionaries", rows.length ? String(rows.length) : "none");
    rows.forEach(function (d) {
      var div = mk("div", "fld");
      var fh = mk("div", "fh");
      fh.appendChild(mk("span", "fn", d.name));
      fh.appendChild(mk("span", "ft", d.match));
      div.appendChild(fh);
      var vals = mk("div", "vals");
      d.terms.forEach(function (t) { vals.appendChild(mk("span", "val", t)); });
      div.appendChild(vals);
      pane.appendChild(div);
    });
  }

  function render(pane, state) {
    var entry = window.PrismQLBoardUtil.findEntry(state, state.sel);
    var name = CL.corpusToShow(state, entry);
    if (!name) {
      pane.appendChild(state.corporaFailed
        ? PF.errorBlock("The server's corpus list did not load; retrying.")
        : PF.loadingBlock());
      return;
    }
    window.PrismQLCorpusSchemas.ensure(state, name);
    var rec = state.schemas && state.schemas[name];
    if (!rec) { pane.appendChild(PF.loadingBlock()); return; }
    if (!rec.ok) {
      pane.appendChild(PF.errorBlock(rec.error));
      var again = mk("button", "ghost", "Try again");
      again.type = "button";
      again.addEventListener("click", function () { window.PrismQLCorpusSchemas.retry(state, name); });
      pane.appendChild(again);
      return;
    }
    var schema = rec.data;
    header(pane, name, schema);
    kv(pane, schema);
    var rows = CL.fieldRows(schema);
    section(pane, "Fields", String(rows.length));
    var list = mk("div", "flds");
    rows.forEach(function (r) { list.appendChild(field(r)); });
    pane.appendChild(list);
    dictionaries(pane, schema);
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorCorpus = api;
})(typeof window !== "undefined" ? window : globalThis);
