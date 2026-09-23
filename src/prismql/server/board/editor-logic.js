// PrismQLEditorLogic: pure helpers for the editor (graph @aleph/prismql,
// node #63; task-6 brief) — clamping, the 422 body → inline-error shape,
// which journal entry a run resolves to, and the recent-queries list. No
// DOM, no window, so these are unit-testable directly under node.
(function (root) {
  "use strict";

  // "max groups" → max_results, clamped >= 1; blank/garbage sends nothing
  // so the server's own default applies.
  function clampMax(raw) {
    if (raw === "" || raw == null) return null;
    var n = Math.floor(Number(raw));
    if (!isFinite(n) || isNaN(n)) return null;
    return n < 1 ? 1 : n;
  }

  // POST /evaluate body from the editor's own state — never sends a corpus
  // or max_results the user hasn't actually set (global-constraints.md:
  // "never guess a column" applies just as much to never guessing a field).
  function buildEvaluateBody(ed) {
    var body = { query: ed.query, hydrate: !!ed.hydrate };
    if (ed.corpus) body.corpus = ed.corpus;
    var max = clampMax(ed.max);
    if (max != null) body.max_results = max;
    return body;
  }

  // A 422's error body carries line/column only for a syntax error
  // (app.py); a runtime error has a message only. Any other failure
  // (network, 403, 429, 5xx) is described by its status + message.
  function describeError(status, body) {
    var err = body && body.error;
    if (status === 422 && err) {
      var hasPos = err.line != null && err.column != null;
      return { pos: hasPos ? err.line + ":" + err.column : null, message: err.message || "invalid query" };
    }
    if (err && err.message) return { pos: null, message: "HTTP " + status + " · " + err.message };
    return { pos: null, message: "HTTP " + (status || "—") + " · request failed" };
  }

  // Which arrived journal entry answers a just-finished run: the newest
  // board entry carrying the run's own result_id, or — for an aggregate,
  // which never gets one — the newest board entry with the same query that
  // arrived no earlier than the run started (task-6 brief).
  function findPendingMatch(entries, pending) {
    if (!pending) return null;
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (e.who !== "board") continue;
      if (pending.resultId != null) {
        if (e.result_id === pending.resultId) return e;
        continue;
      }
      if (e.query !== pending.query) continue;
      var t = new Date(e.ts).getTime();
      if (!isNaN(t) && t + 1000 >= pending.sinceMs) return e;
    }
    return null;
  }

  // The last 5 journal entries this editor itself sent (who === "board"),
  // newest first — `state.entries` is already newest-first.
  function recentQueries(entries) {
    var out = [];
    for (var i = 0; i < entries.length && out.length < 5; i++) {
      if (entries[i].who === "board") out.push(entries[i]);
    }
    return out;
  }

  // The recent list shows one line per query; a real multi-line query
  // collapses to spaces there (the full text still loads into the editor).
  function singleLine(q) {
    return (q || "").replace(/\s*\n\s*/g, " ");
  }

  var api = {
    clampMax: clampMax, buildEvaluateBody: buildEvaluateBody,
    describeError: describeError, findPendingMatch: findPendingMatch,
    recentQueries: recentQueries, singleLine: singleLine,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
