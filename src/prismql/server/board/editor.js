// PrismQLEditor: the "Editor" tab of the inspector aside — a highlighted
// query, corpus/max-groups/hydrate options, Run, and "Your recent
// queries" (graph @aleph/prismql, node #63; task-6 brief). Ports the
// canvas markup ~399-418, run() ~659-675, renderVals' editor fields
// ~920-929. Built once into #inspector-pane (editor-build.js), patched
// here on every render() — never rebuilt — so typing never loses focus,
// caret or selection, including across the 5s beat and journal SSE
// renders (inspector.js leaves #inspector-pane alone while
// state.tab === "editor"; this module owns it entirely there). The
// editor's own state lifecycle and the POST live in editor-actions.js.
(function (root) {
  "use strict";
  var L = window.PrismQLEditorLogic;
  var A = window.PrismQLEditorActions;
  var Build = window.PrismQLEditorBuild;
  var mk = window.PrismQLBoardUtil.mk;

  // A run's own journal entry arriving via the stream: select it and hand
  // off to the Request tab (task-6 brief) — a direct state change, not
  // actions.select()'s own render(), because board.js runs Editor before
  // Inspector: the very same render() pass draws the details pane right
  // after this returns. Checked on every render, not only while on the
  // Editor tab, so it still resolves after the user switches away right
  // after clicking Run.
  function checkPendingRun(state) {
    var found = L.findPendingMatch(state.entries, state.editorPending);
    if (!found) return false;
    state.editorPending = null;
    state.sel = found.seq;
    state.tab = "details";
    return true;
  }

  function patchRecent(state) {
    var recent = document.getElementById("editor-recent");
    recent.innerHTML = "";
    L.recentQueries(state.entries).forEach(function (entry) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.appendChild(mk("span", "t", window.PrismQLFormat.hms(entry.ts)));
      var q = mk("span", "q");
      if (entry.kind === "evaluate") q.innerHTML = window.PrismQLLexer.highlight(L.singleLine(entry.query || ""));
      else q.textContent = L.singleLine(entry.query || "");
      btn.appendChild(q);
      btn.addEventListener("click", function () { A.loadQuery(state, entry); window.PrismQLBoard.render(); });
      recent.appendChild(btn);
    });
  }

  function patchCorpusSelect(ed, corporaState) {
    if (!ed.corpus && corporaState && corporaState.default) ed.corpus = corporaState.default;
    var select = document.getElementById("editor-corpus");
    var names = (corporaState && corporaState.corpora) || [];
    if (select.dataset.count !== String(names.length)) {
      select.innerHTML = "";
      names.forEach(function (name) {
        var o = document.createElement("option");
        o.value = name;
        o.textContent = name;
        select.appendChild(o);
      });
      select.dataset.count = String(names.length);
    }
    select.disabled = names.length === 0;
    if (ed.corpus) select.value = ed.corpus;
  }

  function patchRunState(ed) {
    document.getElementById("editor-box").className = "editor" + (ed.error ? " bad" : "");
    var runBtn = document.getElementById("editor-run");
    runBtn.disabled = ed.running;
    runBtn.firstChild.textContent = ed.running ? "Running…" : "Run";
    document.getElementById("editor-running").hidden = !ed.running;
    if (ed.running) {
      document.getElementById("editor-running-note").textContent =
        "Evaluating on " + (ed.corpus || "the default corpus") + "…";
    }
    var err = document.getElementById("editor-error");
    err.hidden = !ed.error;
    if (ed.error) {
      document.getElementById("editor-error-pos").hidden = !ed.error.pos;
      document.getElementById("editor-error-pos").textContent = ed.error.pos || "";
      document.getElementById("editor-error-msg").textContent = ed.error.message;
    }
  }

  // The textarea's own value is only ever force-set when ed.rev changes
  // (an external load, never a keystroke) — the whole caret-safety
  // contract for typing.
  function patchQuery(ed) {
    var textarea = document.getElementById("editor-textarea");
    var pre = document.getElementById("editor-pre");
    if (pre.dataset.rev === String(ed.rev)) return;
    textarea.value = ed.query;
    pre.innerHTML = window.PrismQLLexer.highlight(ed.query);
    pre.dataset.rev = String(ed.rev);
    document.getElementById("editor-max").value = ed.max;
    document.getElementById("editor-hydrate").checked = !!ed.hydrate;
    if (ed.focus) {
      textarea.focus();
      textarea.setSelectionRange(textarea.value.length, textarea.value.length);
      ed.focus = false;
    }
  }

  function render(state, actions) {
    if (checkPendingRun(state)) return;
    if (state.tab !== "editor") return;
    var pane = document.getElementById("inspector-pane");
    if (!pane) return;
    var ed = A.ensureEditorState(state);
    if (!document.getElementById("editor-textarea")) Build.mount(pane, ed, actions);
    patchCorpusSelect(ed, state.corpora);
    patchRunState(ed);
    patchQuery(ed);
    patchRecent(state);
  }

  var api = { render: render, openInEditor: A.openInEditor, rerun: A.rerun, run: A.run, newQuery: A.newQuery };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditor = api;
})(typeof window !== "undefined" ? window : globalThis);
