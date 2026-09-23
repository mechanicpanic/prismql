// PrismQLEditorActions: state.editor's lifecycle — its lazy default, the
// four board actions the brief asks for (openInEditor/rerun/run/newQuery),
// and the POST itself (graph @aleph/prismql, node #63; task-6 brief).
// Split out of editor.js to stay under the 150-line budget; editor.js
// calls run()/rerun() through actions.run() (wired in board.js), never
// directly, so every run reaches the same render().
(function (root) {
  "use strict";
  var node = typeof module === "object" && module.exports;
  var L = node ? require("./editor-logic.js") : root.PrismQLEditorLogic;
  var K = node ? require("./editor-kinds.js") : root.PrismQLEditorKinds;

  function ensureEditorState(state) {
    if (!state.editor) {
      state.editor = { kind: "evaluate", query: "SELECT ", corpus: null, top: "", threshold: "",
        running: false, error: null, rev: 0, focus: false, dictNote: null };
    }
    return state.editor;
  }

  function loadQuery(state, entry) {
    var ed = ensureEditorState(state);
    ed.kind = L.KINDS.indexOf(entry.kind) >= 0 ? entry.kind : "evaluate";
    ed.query = entry.query || "";
    ed.corpus = entry.corpus || ed.corpus;
    if (ed.kind === "similar") ed.threshold = entry.threshold != null ? String(entry.threshold) : "";
    ed.error = null;
    // Finding 3: "Open in editor" stays offered for an entry that used
    // request-scoped dictionaries, but the same note the inspector shows
    // follows the query text in here too — the board never held the terms.
    ed.dictNote = L.hasRequestDictionaries(entry) ? L.DICT_NOTE : null;
    ed.rev++;
  }

  function openInEditor(state, render, entry) {
    loadQuery(state, entry);
    state.tab = "editor";
    render();
  }

  // Finding 3: only evaluate replays through the editor/(re)run — search
  // and similar post straight back to their own endpoint. Neither path
  // runs at all when the entry used request-scoped dictionaries; the
  // board never held their terms to resend (inspector-detail.js disables
  // the button and shows L.DICT_NOTE before this is ever reached).
  // Round 2, #4: never fire-and-forget — a failure (422/429/403/network)
  // lands in state.rerunError, keyed by the entry's own seq, and the
  // promise is always caught, never left to reject unhandled.
  function rerun(state, render, entry) {
    if (L.hasRequestDictionaries(entry)) return;
    if (entry.kind !== "evaluate") {
      var apiFn = entry.kind === "search" ? window.PrismQLApi.search : window.PrismQLApi.similar;
      state.rerunError = null;
      apiFn(L.rerunBody(entry)).then(function (res) {
        var outcome = L.rerunOutcome(res);
        if (!outcome.ok) state.rerunError = { seq: entry.seq, message: outcome.error.message };
        render();
      }).catch(function (e) {
        state.rerunError = { seq: entry.seq, message: (e && e.message) || "request failed" };
        render();
      });
      return;
    }
    loadQuery(state, entry);
    state.tab = "editor";
    render();
    run(state, render);
  }

  // Switching kind keeps typed text; only an untouched starting text
  // ("SELECT " or empty) is swapped for the new kind's own start.
  function setKind(state, render, kind) {
    var ed = ensureEditorState(state);
    if (ed.kind === kind) return;
    if (ed.query.trim() === K.kindInfo(ed.kind).start.trim()) ed.query = K.kindInfo(kind).start;
    ed.kind = kind;
    ed.error = null;
    ed.rev++;
    ed.focus = true;
    render();
  }

  function newQuery(state, render) {
    var ed = ensureEditorState(state);
    ed.kind = "evaluate";
    ed.query = "SELECT ";
    ed.error = null;
    ed.dictNote = null;
    ed.rev++;
    ed.focus = true;
    state.tab = "editor";
    render();
  }

  function run(state, render) {
    var ed = ensureEditorState(state);
    if (ed.running) return;
    if (L.unknownCorpus(ed, state.corpora)) {
      ed.error = { pos: null, message: "corpus ‘" + ed.corpus + "’ is not on this server" };
      render();
      return;
    }
    var request = K.buildRunBody(ed);
    if (request.error) {
      ed.error = { pos: null, message: request.error };
      render();
      return;
    }
    ed.running = true;
    ed.error = null;
    render();
    var sentQuery = ed.query;
    // The server always journals a real corpus (req.corpus or its own
    // default_corpus) — resolve a null one to the known default here too,
    // or findPendingMatch's corpus check has nothing real to compare
    // against (fix round 3).
    var sentCorpus = ed.corpus || (state.corpora && state.corpora.default) || null;
    var baselineSeq = state.seq; // no clocks in run<->entry matching (fix round 1, #2)
    var baselineBoot = state.boot; // a restart voids the baseline (fix round 2, #2)
    window.PrismQLApi[request.endpoint](request.body).then(function (res) {
      ed.running = false;
      if (res.status === 200 && res.body && res.body.ok) {
        state.editorPending = {
          resultId: res.body.result_id != null ? res.body.result_id : null,
          query: sentQuery, corpus: sentCorpus, baselineSeq: baselineSeq, boot: baselineBoot,
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
    openInEditor: openInEditor, rerun: rerun, run: run, newQuery: newQuery, setKind: setKind,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorActions = api;
})(typeof window !== "undefined" ? window : globalThis);
