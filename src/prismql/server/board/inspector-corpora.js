// PrismQLInspectorCorpora: fetches /corpora once and keeps state.corpora/
// state.corporaFailed current, retried with backoff on failure (graph
// @aleph/prismql, node #63; fix round 2, #1 and #5). No DOM here —
// state and a render() call are its whole surface, so it's testable with
// a fake window and mock timers, same as board-stream.js.
(function (root) {
  "use strict";
  var RETRY_MS = 5000;
  var fetching = false;
  var retryTimer = null;

  function bump() { if (window.PrismQLBoard) window.PrismQLBoard.render(); }

  // At most one request in flight; a failure's own render() must never
  // re-trigger a new one right away — the retry is a real timer, not
  // "whatever render happens next" (an unthrottled retry-on-render
  // measured ~2000 req/s against a failing /corpora).
  function ensure(state) {
    if (state.corpora || fetching || retryTimer) return;
    fetching = true;
    window.PrismQLApi.corpora().then(function (data) {
      fetching = false;
      state.corpora = data;
      bump();
    }).catch(function () {
      fetching = false;
      state.corporaFailed = true;
      retryTimer = setTimeout(function () {
        retryTimer = null;
        ensure(state);
      }, RETRY_MS);
      bump();
    });
  }

  // A stream reset: the restarted server's board config may differ from
  // what we cached — drop it and let the next render's ensure() ask again.
  function reset(state) {
    if (retryTimer) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
    fetching = false;
    state.corpora = null;
    state.corporaFailed = false;
  }

  var api = { ensure: ensure, reset: reset };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorCorpora = api;
})(typeof window !== "undefined" ? window : globalThis);
