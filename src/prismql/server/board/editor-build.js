// PrismQLEditorBuild: builds the editor's DOM into #inspector-pane once
// (graph @aleph/prismql, node #63; task-6 brief) — split out of editor.js
// to stay under the 150-line budget. Only mount() is called from outside;
// patching an already-built editor is editor.js's job (state changes far
// more often than the DOM shape does).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;

  function buildOpts(pane, ed) {
    var opts = mk("div", "opts");
    var corpusLabel = mk("label", null, "corpus ");
    var select = document.createElement("select");
    select.className = "field";
    select.id = "editor-corpus";
    corpusLabel.appendChild(select);
    opts.appendChild(corpusLabel);

    var maxLabel = mk("label", null, "max groups ");
    var max = document.createElement("input");
    max.className = "field";
    max.type = "number";
    max.min = "1";
    max.id = "editor-max";
    max.style.width = "64px";
    maxLabel.appendChild(max);
    opts.appendChild(maxLabel);

    var hydrateLabel = document.createElement("label");
    var hydrate = document.createElement("input");
    hydrate.type = "checkbox";
    hydrate.id = "editor-hydrate";
    hydrateLabel.appendChild(hydrate);
    hydrateLabel.appendChild(document.createTextNode(" with event text"));
    opts.appendChild(hydrateLabel);

    var runBtn = mk("button", "primary");
    runBtn.type = "button";
    runBtn.id = "editor-run";
    runBtn.style.marginLeft = "auto";
    runBtn.appendChild(mk("span", null, "Run"));
    runBtn.appendChild(mk("span", "kbd", "⌘⏎"));
    opts.appendChild(runBtn);
    pane.appendChild(opts);

    select.addEventListener("change", function () { ed.corpus = select.value; });
    max.addEventListener("input", function () { ed.max = max.value; });
    hydrate.addEventListener("change", function () { ed.hydrate = hydrate.checked; });
  }

  function buildSkel(pane) {
    var skel = mk("div");
    skel.id = "editor-running";
    skel.style.cssText = "display:flex;flex-direction:column;gap:8px";
    var note = mk("div");
    note.id = "editor-running-note";
    note.style.cssText = "font-size:12px;color:var(--muted)";
    skel.appendChild(note);
    skel.appendChild(mk("div", "skel"));
    var b = mk("div", "skel");
    b.style.height = "88px";
    skel.appendChild(b);
    pane.appendChild(skel);
  }

  // ed is state.editor (already ensured by the caller); actions is the
  // board's action dispatcher — Run only ever goes through actions.run()
  // so it always reaches the same render() the rest of the board uses.
  function mount(pane, ed, actions) {
    pane.innerHTML = "";
    var box = mk("div");
    box.id = "editor-box";
    var pre = document.createElement("pre");
    pre.id = "editor-pre";
    pre.setAttribute("aria-hidden", "true");
    var textarea = document.createElement("textarea");
    textarea.id = "editor-textarea";
    textarea.setAttribute("aria-label", "Query");
    textarea.spellcheck = false;
    box.appendChild(pre);
    box.appendChild(textarea);
    pane.appendChild(box);

    var err = mk("div", "inline-err");
    err.id = "editor-error";
    err.setAttribute("role", "alert");
    err.hidden = true;
    var pos = mk("b", null, "");
    pos.id = "editor-error-pos";
    err.appendChild(pos);
    var msg = mk("span", null, "");
    msg.id = "editor-error-msg";
    err.appendChild(msg);
    pane.appendChild(err);

    buildOpts(pane, ed);
    buildSkel(pane);

    var sect = mk("div", "sect", "Your recent queries");
    sect.appendChild(mk("span", "push", "click to load"));
    pane.appendChild(sect);
    var recent = mk("div", "recent");
    recent.id = "editor-recent";
    pane.appendChild(recent);

    textarea.addEventListener("input", function () {
      ed.query = textarea.value;
      pre.innerHTML = window.PrismQLLexer.highlight(textarea.value);
      ed.error = null;
    });
    textarea.addEventListener("scroll", function () {
      pre.scrollTop = textarea.scrollTop;
      pre.scrollLeft = textarea.scrollLeft;
    });
    textarea.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); actions.run(); }
    });
    document.getElementById("editor-run").addEventListener("click", function () { actions.run(); });
  }

  var api = { mount: mount };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorBuild = api;
})(typeof window !== "undefined" ? window : globalThis);
