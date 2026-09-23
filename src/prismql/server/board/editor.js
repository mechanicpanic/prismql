// PrismQLEditor: the "Editor" tab of the inspector aside — a highlighted
// query, a corpus picker, Run, and "Your recent queries" (graph
// @aleph/prismql, node #63; task-6 brief, fix round 1). Ports the canvas
// markup ~399-418, run() ~659-675, renderVals' editor fields ~920-929.
// Built once into #inspector-pane (editor-build.js), patched here on
// every render() — never rebuilt — so typing never loses focus, caret or
// selection, including across the 5s beat and journal SSE renders
// (inspector.js leaves #inspector-pane alone while state.tab === "editor";
// this module owns it entirely there). The editor's own state lifecycle
// and the POST live in editor-actions.js.
(function (root) {
  "use strict";
  var L = window.PrismQLEditorLogic;
  var A = window.PrismQLEditorActions;
  var Build = window.PrismQLEditorBuild;
  var mk = window.PrismQLBoardUtil.mk;

  // A run's own journal entry, live or still held in state.pending while
  // paused: found, it's selected and the board switches to the Request
  // tab — unless the user has edited the query since the run started, in
  // which case only the pending marker clears, no tab flip, no focus
  // steal (fix round 1, #2 and #3). Checked on every render, not only
  // while on the Editor tab; board.js runs Editor before Inspector so a
  // flip here draws in the very same pass.
  function checkPendingRun(state) {
    var ed = state.editor;
    var resolved = L.resolvePendingRun(state.entries, state.pending, state.editorPending, ed ? ed.query : "");
    if (!resolved) return false;
    state.editorPending = null;
    if (!resolved.select) return false;
    state.sel = resolved.entry.seq;
    state.tab = "details";
    return true;
  }

  // Redrawn only when the actual set of recent seqs changes, not on every
  // beat/stream render (fix round 1, #6).
  function patchRecent(state) {
    var recent = document.getElementById("editor-recent");
    var list = L.recentQueries(state.entries);
    var sig = list.map(function (e) { return e.seq; }).join(",");
    if (recent.dataset.sig === sig) return;
    recent.dataset.sig = sig;
    recent.innerHTML = "";
    list.forEach(function (entry) {
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

  // Rebuilds the option list when the known names actually differ, not
  // only their count (fix round 1, #7); a corpus the editor still holds
  // but that isn't among them stays selectable, clearly marked, rather
  // than silently swapped for something else.
  function patchCorpusSelect(ed, corporaState) {
    if (!ed.corpus && corporaState && corporaState.default) ed.corpus = corporaState.default;
    var select = document.getElementById("editor-corpus");
    var names = (corporaState && corporaState.corpora) || [];
    var unknown = L.unknownCorpus(ed, corporaState) ? ed.corpus : null;
    var sig = names.join(",") + "|" + (unknown || "");
    if (select.dataset.sig !== sig) {
      select.innerHTML = "";
      names.forEach(function (name) { select.appendChild(new Option(name, name)); });
      if (unknown) select.appendChild(new Option(unknown + " (not on this server)", unknown));
      select.dataset.sig = sig;
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
