// PrismQLEditorKindbar: the editor's kind switch (Query · Search ·
// Similar) and the two number fields a scout takes, top and threshold
// (graph @aleph/prismql, #111). Built once with the editor, patched on
// every render by editor.js; what differs per kind is data in
// editor-kinds.js.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var K = window.PrismQLEditorKinds;
  var KINDS = window.PrismQLEditorLogic.KINDS;

  function numberField(id, label, placeholder, onInput) {
    var wrap = mk("label", null, label + " ");
    wrap.id = id + "-label";
    var input = document.createElement("input");
    input.className = "field num";
    input.id = id;
    input.inputMode = "decimal";
    input.placeholder = placeholder;
    input.addEventListener("input", function () { onInput(input.value); });
    wrap.appendChild(input);
    return wrap;
  }

  // The switch goes above the text box; the fields go into the options
  // row, before Format (which only a query has).
  function build(pane, opts, ed) {
    var seg = mk("div", "seg kinds");
    seg.id = "editor-kinds";
    seg.setAttribute("role", "tablist");
    KINDS.forEach(function (kind) {
      var btn = mk("button", null, K.kindInfo(kind).label);
      btn.type = "button";
      btn.dataset.kind = kind;
      btn.setAttribute("role", "tab");
      btn.addEventListener("click", function () {
        var board = window.PrismQLBoard;
        window.PrismQLEditorActions.setKind(board.state, board.render, kind);
      });
      seg.appendChild(btn);
    });
    pane.insertBefore(seg, pane.firstChild);

    var fmt = document.getElementById("editor-format");
    opts.insertBefore(numberField("editor-top", "top", String(K.DEFAULT_TOP),
      function (v) { ed.top = v; }), fmt);
    opts.insertBefore(numberField("editor-threshold", "threshold", "none",
      function (v) { ed.threshold = v; }), fmt);
  }

  function escape(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // A query is highlighted by the language's lexer; search and similar
  // text is not the language, so it is shown as typed.
  function paint(ed, text) {
    return K.kindInfo(ed.kind).highlight ? window.PrismQLLexer.highlight(text) : escape(text);
  }

  function patch(ed) {
    var kind = ed.kind || "evaluate";
    var buttons = document.querySelectorAll("#editor-kinds button");
    for (var i = 0; i < buttons.length; i++) {
      var on = buttons[i].dataset.kind === kind;
      buttons[i].className = on ? "on" : "";
      buttons[i].setAttribute("aria-selected", on ? "true" : "false");
    }
    var info = K.kindInfo(kind);
    var textarea = document.getElementById("editor-textarea");
    textarea.placeholder = info.placeholder;
    textarea.setAttribute("aria-label", info.label);
    document.getElementById("editor-top-label").hidden = kind === "evaluate";
    document.getElementById("editor-threshold-label").hidden = kind !== "similar";
    document.getElementById("editor-format").hidden = kind !== "evaluate";
    // Format carries the push to the right; without it, Run does
    document.getElementById("editor-run").style.marginLeft = kind === "evaluate" ? "" : "auto";
    var top = document.getElementById("editor-top");
    if (document.activeElement !== top) top.value = ed.top || "";
    var th = document.getElementById("editor-threshold");
    if (document.activeElement !== th) th.value = ed.threshold || "";
  }

  var api = { build: build, patch: patch, paint: paint };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorKindbar = api;
})(typeof window !== "undefined" ? window : globalThis);
