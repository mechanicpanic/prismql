// PrismQLCorpusSchemas: fetches each corpus's schema once and keeps it in
// state.schemas[name] = {ok, data | error} (graph @aleph/prismql, node #86).
// The server computes it once per load, so a board never refetches it until
// the stream sees a restarted server (reset()). No DOM.
(function (root) {
  "use strict";
  var inflight = {};
  // Bumped by reset(): a settle from before a reset is dropped, not written.
  var generation = 0;

  function bump() { if (window.PrismQLBoard) window.PrismQLBoard.render(); }

  function ensure(state, name) {
    if (!state.schemas) state.schemas = {};
    if (!name || state.schemas[name] || inflight[name]) return;
    inflight[name] = true;
    var gen = generation;
    window.PrismQLApi.schema(name).then(function (data) {
      if (gen !== generation) return;
      delete inflight[name];
      state.schemas[name] = { ok: true, data: data };
      bump();
    }).catch(function (e) {
      if (gen !== generation) return;
      delete inflight[name];
      state.schemas[name] = { ok: false, error: String((e && e.message) || e) };
      bump();
    });
  }

  function retry(state, name) {
    if (state.schemas) delete state.schemas[name];
    ensure(state, name);
  }

  function reset(state) {
    generation++;
    inflight = {};
    state.schemas = {};
  }

  var api = { ensure: ensure, retry: retry, reset: reset };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLCorpusSchemas = api;
})(typeof window !== "undefined" ? window : globalThis);
