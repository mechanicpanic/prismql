// PrismQLBoardStream: backfill plus the live SSE connection into board.js's
// `state` (graph @aleph/prismql, node #76 — the boot-id carry-across-
// restart). Split out of board.js to stay under the 150-line budget;
// exposes only connect(state, render) and reconnect(state, render), the
// latter used by board.js's actions.reconnect (the offline banner's
// "Retry now"). One retry timer, one generation token — an attempt
// superseded by a newer connect()/reconnect() is a no-op, never a second
// stream layered on top of the first (fix round 1, #4; pinned by
// tests/board/board-stream.test.mjs).
(function (root) {
  "use strict";
  var streamHandle = null;
  var retryTimer = null;
  var generation = 0;
  var ENTRY_CAP = 1000;

  // The server's own ring holds at most `activity_max` rows and /activity
  // always returns the NEWEST `limit` of them (rows[-limit:]) — paging by
  // raising `since` only ever re-asks for "newer than the newest page",
  // which is empty, so "loop until short" reads just the last page and
  // silently drops everything older (fix round 1, #1). One generous-limit
  // call is both correct and cheap: the server clamps it to activity_max.
  function backfill(state, since) {
    return window.PrismQLApi.activity(since, 1000).then(function (body) {
      state.boot = body.boot;
      var got = body.entries || [];
      var maxSeq = since;
      got.forEach(function (e) {
        if (typeof e.seq === "number" && e.seq > maxSeq) maxSeq = e.seq;
      });
      state.seq = maxSeq; // the last delivered row's seq, never body.seq (#8)
      return got;
    });
  }

  function onEntry(state, render, entry) {
    state.seq = Math.max(state.seq, entry.seq || 0);
    state.freshSeq = entry.seq;
    if (state.live) state.entries = [entry].concat(state.entries).slice(0, ENTRY_CAP);
    else state.pending = [entry].concat(state.pending);
    setTimeout(function () {
      if (state.freshSeq === entry.seq) { state.freshSeq = null; render(); }
    }, 2500);
    render();
  }

  function onState(state, render, kind, bootId) {
    if (kind === "reset") {
      state.entries = []; state.pending = []; state.seq = 0; state.boot = bootId;
      state.sel = null; state.full = null; state.freshSeq = null;
      connect(state, render);
    } else if (kind === "down") {
      if (!state.down) { state.down = true; render(); }
    } else if (kind === "live") {
      if (state.down) { state.down = false; render(); }
    }
  }

  function connect(state, render) {
    var gen = ++generation;
    if (retryTimer) { clearTimeout(retryTimer); retryTimer = null; }
    backfill(state, 0).then(function (got) {
      if (gen !== generation) return; // superseded by a newer connect()/reconnect()
      state.entries = got.slice().reverse().slice(0, ENTRY_CAP);
      state.pending = [];
      state.down = false;
      render();
      if (streamHandle) { streamHandle.close(); streamHandle = null; }
      streamHandle = window.PrismQLApi.stream(state.seq,
        function (e) { onEntry(state, render, e); },
        function (k, b) { onState(state, render, k, b); },
        state.boot);
    }).catch(function () {
      if (gen !== generation) return;
      // A rejected activity() used to go deaf until reload — retry steadily
      // instead, same 4 s backoff as a dropped SSE connection.
      if (!state.down) { state.down = true; render(); }
      retryTimer = setTimeout(function () { connect(state, render); }, 4000);
    });
  }

  function reconnect(state, render) {
    if (retryTimer) { clearTimeout(retryTimer); retryTimer = null; }
    if (streamHandle) { streamHandle.close(); streamHandle = null; }
    connect(state, render);
  }

  var api = { connect: connect, reconnect: reconnect };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLBoardStream = api;
})(typeof window !== "undefined" ? window : globalThis);
