// PrismQLEditorActions: state.editor's lifecycle — its lazy default, the
// four board actions the brief asks for (openInEditor/rerun/run/newQuery),
// and the POST itself (graph @aleph/prismql, node #63; task-6 brief).
// Split out of editor.js to stay under the 150-line budget; editor.js
// calls run()/rerun() through actions.run() (wired in board.js), never
// directly, so every run reaches the same render().
(function (root) {
  "use strict";
  var L = typeof module === "object" && module.exports
    ? require("./editor-logic.js")
    : root.PrismQLEditorLogic;

  function ensureEditorState(state) {
    if (!state.editor) {
      state.editor = {
        query: "SELECT ", corpus: null, max: "", hydrate: false,
        running: false, error: null, rev: 0, focus: false,
      };
    }
    return state.editor;
  }

  function loadQuery(state, entry) {
    var ed = ensureEditorState(state);
    ed.query = entry.query || "";
    ed.corpus = entry.corpus || ed.corpus;
    ed.error = null;
    ed.rev++;
  }

  function openInEditor(state, render, entry) {
    loadQuery(state, entry);
    state.tab = "editor";
    render();
  }

  function rerun(state, render, entry) {
    loadQuery(state, entry);
    state.tab = "editor";
    render();
    run(state, render);
  }

  function newQuery(state, render) {
    var ed = ensureEditorState(state);
    ed.query = "SELECT ";
    ed.error = null;
    ed.rev++;
    ed.focus = true;
    state.tab = "editor";
    render();
  }

  function run(state, render) {
    var ed = ensureEditorState(state);
    if (ed.running) return;
    ed.running = true;
    ed.error = null;
    render();
    var sentQuery = ed.query;
    var startedAt = Date.now();
    window.PrismQLApi.evaluate(L.buildEvaluateBody(ed)).then(function (res) {
      ed.running = false;
      if (res.status === 200 && res.body && res.body.ok) {
        state.editorPending = {
          resultId: res.body.result_id != null ? res.body.result_id : null,
          query: sentQuery, sinceMs: startedAt,
        };
      } else {
        ed.error = L.describeError(res.status, res.body);
      }
      render();
    }).catch(function (e) {
      ed.running = false;
      ed.error = { pos: null, message: (e && e.message) || "request failed" };
      render();
    });
  }

  var api = {
    ensureEditorState: ensureEditorState, loadQuery: loadQuery,
    openInEditor: openInEditor, rerun: rerun, run: run, newQuery: newQuery,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorActions = api;
})(typeof window !== "undefined" ? window : globalThis);
