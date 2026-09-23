// PrismQLEditorLogic: pure helpers for the editor (graph @aleph/prismql,
// node #63; task-6 brief, fix round 1). No DOM, no window, so these are
// unit-testable directly under node.
(function (root) {
  "use strict";

  // POST /evaluate body: just {query, corpus} — max groups and hydrate
  // have no visible effect on the board (the inspector pages the kept
  // result itself and always hydrates), so those controls were dropped
  // (fix round 1, #5 — a deviation from the canvas, noted in the report).
  function buildEvaluateBody(ed) {
    var body = { query: ed.query };
    if (ed.corpus) body.corpus = ed.corpus;
    return body;
  }

  // A 422's error body carries line/column only for a syntax error
  // (app.py); a runtime error has a message only. FastAPI's own request
  // validation 422 ({"detail": [...]}) never reaches that shape at all —
  // its messages are joined instead (fix round 1, #8). Any other failure
  // (network, 403, 429, 5xx) is described by its status + message.
  function describeError(status, body) {
    var err = body && body.error;
    if (status === 422 && err) {
      var hasPos = err.line != null && err.column != null;
      return { pos: hasPos ? err.line + ":" + err.column : null, message: err.message || "invalid query" };
    }
    if (body && Array.isArray(body.detail)) {
      var msgs = body.detail.map(function (d) { return (d && d.msg) || String(d); }).join("; ");
      return { pos: null, message: msgs || "invalid request" };
    }
    if (err && err.message) return { pos: null, message: "HTTP " + status + " · " + err.message };
    return { pos: null, message: "HTTP " + (status || "—") + " · request failed" };
  }

  // Which arrived journal entry answers a just-finished run — no clocks:
  // the run remembers state.seq as it stood before the POST
  // (pending.baselineSeq) and state.boot (pending.boot); the answer is the
  // lowest-seq board entry above that baseline carrying the run's own
  // result_id, or — for an aggregate, which never gets one — the same
  // query AND the same corpus (fix round 1, #2; fix round 2, #3). A
  // server restart between the run and its answer changes state.boot and
  // restarts its seq counter from a small number again — a baseline born
  // under the old boot no longer means anything, so it's treated as 0
  // instead (fix round 2, #2); the matching rules themselves (who, query,
  // corpus, result_id) are unchanged — a restart never widens who a
  // pending run is allowed to match, only resets where it starts looking.
  // pending.corpus is only ever null when the editor ran before /corpora
  // had loaded (or once it failed) — the server always journals a real
  // corpus name (req.corpus or its own default_corpus), never a null one,
  // so that case skips the corpus comparison instead of requiring the
  // impossible entry.corpus === null (fix round 3).
  function findPendingMatch(entries, pending, currentBoot) {
    if (!pending) return null;
    var baseline = pending.boot === currentBoot ? pending.baselineSeq : 0;
    var best = null;
    for (var i = 0; i < entries.length; i++) {
      var e = entries[i];
      if (e.who !== "board" || e.seq == null || e.seq <= baseline) continue;
      var matches = pending.resultId != null
        ? e.result_id === pending.resultId
        : e.query === pending.query && (pending.corpus == null || e.corpus === pending.corpus);
      if (matches && (best == null || e.seq < best.seq)) best = e;
    }
    return best;
  }

  // Resolves a pending run against both the live and the paused journal —
  // a paused board never merges into `entries` (fix round 1, #3). Returns
  // null while unresolved, else {entry, select}: select is false once the
  // user has edited the query since the run started — the marker still
  // clears, but nothing steals focus or flips the tab.
  function resolvePendingRun(entries, pendingQueue, pending, currentQuery, currentBoot) {
    if (!pending) return null;
    var found = findPendingMatch(entries, pending, currentBoot) || findPendingMatch(pendingQueue, pending, currentBoot);
    if (!found) return null;
    return { entry: found, select: pending.query === currentQuery };
  }

  // True only once /corpora has actually loaded and ed.corpus isn't in
  // it — never true before the list has loaded, when absence proves
  // nothing (fix round 1, #7).
  function unknownCorpus(ed, corporaState) {
    if (!ed.corpus || !corporaState) return false;
    return (corporaState.corpora || []).indexOf(ed.corpus) === -1;
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

  // Finding 3: "Run again" replays a request by its own kind — evaluate
  // through the editor (no body here, null), search/similar directly
  // against their own endpoints. A request that used request-scoped
  // dictionaries can't be replayed: the board never held their terms.
  var DICT_NOTE = "used request dictionaries — the board can't replay them";
  var DEFAULT_LIMIT = 20;

  function hasRequestDictionaries(entry) {
    return !!(entry.dictionaries && entry.dictionaries.length);
  }

  function rerunBody(entry) {
    if (entry.kind !== "search" && entry.kind !== "similar") return null;
    var limit = entry.total > 0 ? entry.total : DEFAULT_LIMIT;
    var body = entry.kind === "search" ? { query: entry.query } : { text: entry.query };
    if (entry.corpus) body.corpus = entry.corpus;
    if (entry.kind === "similar" && entry.threshold != null) body.threshold = entry.threshold;
    body.limit = limit;
    return body;
  }

  var api = {
    buildEvaluateBody: buildEvaluateBody, describeError: describeError,
    findPendingMatch: findPendingMatch, resolvePendingRun: resolvePendingRun,
    unknownCorpus: unknownCorpus, recentQueries: recentQueries, singleLine: singleLine,
    hasRequestDictionaries: hasRequestDictionaries, rerunBody: rerunBody, DICT_NOTE: DICT_NOTE,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
