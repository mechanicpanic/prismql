// PrismQLRailCorpora: the rail's "Corpora" block — every corpus the server
// holds, its event count and what it can answer; a click opens its card in
// the inspector's Corpus tab (graph @aleph/prismql, node #86).
(function (root) {
  "use strict";

  function row(name, state, actions) {
    var U = window.PrismQLBoardUtil;
    var CL = window.PrismQLCorpusLogic;
    var shown = state.tab === "corpus" && CL.corpusToShow(state, U.findEntry(state, state.sel)) === name;
    var btn = U.mk("button", "crow" + (shown ? " on" : ""));
    btn.type = "button";
    btn.dataset.corpus = name;
    btn.appendChild(U.mk("span", "cn", name));
    var rec = state.schemas && state.schemas[name];
    if (rec && rec.ok) {
      CL.capabilities(rec.data).forEach(function (c) {
        if (c.on) {
          var mark = U.mk("span", "cmark", c.label);
          mark.title = c.title;
          btn.appendChild(mark);
        }
      });
      btn.appendChild(U.mk("span", "n", CL.fmt(rec.data.documents)));
    } else {
      btn.appendChild(U.mk("span", "n", rec ? "—" : "…"));
    }
    btn.setAttribute("aria-label", name + " corpus: open its fields and values");
    btn.addEventListener("click", function () { actions.openCorpus(name); });
    return btn;
  }

  function render(state, actions) {
    var el = document.getElementById("rail-corpora");
    if (!el) return;
    var names = state.corpora ? state.corpora.corpora : [];
    names.forEach(function (n) { window.PrismQLCorpusSchemas.ensure(state, n); });
    var active = document.activeElement;
    var refocus = active && el.contains(active) ? active.dataset.corpus : null;
    el.innerHTML = "";
    names.forEach(function (n) {
      var b = row(n, state, actions);
      el.appendChild(b);
      if (n === refocus) b.focus({ preventScroll: true });
    });
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLRailCorpora = api;
})(typeof window !== "undefined" ? window : globalThis);
