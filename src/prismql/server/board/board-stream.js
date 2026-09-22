// PrismQLBoardStream: backfill plus the live SSE connection into board.js's
// `state` (graph @aleph/prismql, node #76 — the boot-id carry-across-
// restart). Split out of board.js to stay under the 150-line budget;
// exposes only connect(state, render) and reconnect(state, render), the
// latter used by board.js's actions.reconnect (the offline banner's
// "Retry now").
(function (root) {
  "use strict";
  var streamHandle = null;

  // Pages through activity(0) — api.js's fixed limit of 200 — until a page
  // comes back short, i.e. the journal's whole history (task-4 brief, step 1).
  async function backfill(state) {
    var since = 0, all = [];
    for (;;) {
      var body = await window.PrismQLApi.activity(since);
      state.boot = body.boot;
      var got = body.entries || [];
      all = all.concat(got);
      if (got.length < 200) { state.seq = body.seq; break; }
      since = got[got.length - 1].seq;
    }
    return all;
  }

  function onEntry(state, render, entry) {
    state.seq = Math.max(state.seq, entry.seq || 0);
    state.freshSeq = entry.seq;
    if (state.live) state.entries = [entry].concat(state.entries);
    else state.pending = [entry].concat(state.pending);
    setTimeout(function () {
      if (state.freshSeq === entry.seq) { state.freshSeq = null; render(); }
    }, 2500);
    render();
  }

  function onState(state, render, kind, bootId) {
    if (kind === "reset") {
      if (streamHandle) streamHandle.close();
      state.entries = []; state.pending = []; state.seq = 0; state.boot = bootId;
      connect(state, render);
    } else if (kind === "down") {
      if (!state.down) { state.down = true; render(); }
    } else if (kind === "live") {
      if (state.down) { state.down = false; render(); }
    }
  }

  function connect(state, render) {
    backfill(state).then(function (all) {
      state.entries = all.slice().reverse();
      state.down = false;
      render();
      streamHandle = window.PrismQLApi.stream(state.seq,
        function (e) { onEntry(state, render, e); },
        function (k, b) { onState(state, render, k, b); },
        state.boot);
    }).catch(function () {
      // A rejected activity() used to go deaf until reload — retry steadily
      // instead, same 4 s backoff as a dropped SSE connection.
      if (!state.down) { state.down = true; render(); }
      setTimeout(function () { connect(state, render); }, 4000);
    });
  }

  function reconnect(state, render) {
    if (streamHandle) streamHandle.close();
    connect(state, render);
  }

  var api = { connect: connect, reconnect: reconnect };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLBoardStream = api;
})(typeof window !== "undefined" ? window : globalThis);
