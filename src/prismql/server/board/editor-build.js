// PrismQLEditorBuild: builds the editor's DOM into #inspector-pane once
// (graph @aleph/prismql, node #63; task-6 brief) — split out of editor.js
// to stay under the 150-line budget. Only mount() is called from outside;
// patching an already-built editor is editor.js's job (state changes far
// more often than the DOM shape does).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;

  // Just corpus + Run: "max groups" and "with event text" have no visible
  // effect on the board and were dropped (fix round 1, #5).
  function buildOpts(pane, ed) {
    var opts = mk("div", "opts");
    var corpusLabel = mk("label", null, "corpus ");
    var select = document.createElement("select");
    select.className = "field";
    select.id = "editor-corpus";
    corpusLabel.appendChild(select);
    opts.appendChild(corpusLabel);

    var fmtBtn = mk("button", "ghost", "Format");
    fmtBtn.type = "button";
    fmtBtn.id = "editor-format";
    fmtBtn.title = "Put each link, window and clause on its own line";
    fmtBtn.style.marginLeft = "auto";
    fmtBtn.addEventListener("click", function () {
      var ta = document.getElementById("editor-textarea");
      if (!ta) return;
      ta.value = window.PrismQLQueryFormat.formatQuery(ta.value);
      ta.dispatchEvent(new Event("input", { bubbles: true }));
      ta.focus();
    });
    opts.appendChild(fmtBtn);

    var runBtn = mk("button", "primary");
    runBtn.type = "button";
    runBtn.id = "editor-run";
    runBtn.appendChild(mk("span", null, "Run"));
    runBtn.appendChild(mk("span", "kbd", "⌘⏎"));
    opts.appendChild(runBtn);
    pane.appendChild(opts);

    select.addEventListener("change", function () { ed.corpus = select.value; });
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

    var dictNote = mk("div", "inline-note");
    dictNote.id = "editor-dict-note";
    dictNote.hidden = true;
    pane.appendChild(dictNote);

    buildOpts(pane, ed);
    buildSkel(pane);

    var sect = mk("div", "sect", "Your recent queries");
    sect.appendChild(mk("span", "push", "click to load"));
    pane.appendChild(sect);
    var recent = mk("div", "recent");
    recent.id = "editor-recent";
    pane.appendChild(recent);

    // Typing clears a stale error immediately, in place — no full redraw
    // needed to drop the red border once the query it complained about
    // has actually changed (fix round 1, #4).
    textarea.addEventListener("input", function () {
      ed.query = textarea.value;
      pre.innerHTML = window.PrismQLLexer.highlight(textarea.value);
      if (ed.error) {
        ed.error = null;
        box.className = "editor";
        err.hidden = true;
      }
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
