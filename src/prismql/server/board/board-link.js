// PrismQLBoardLink: a request's own address on the board, `/board/#q<seq>`
// (graph @aleph/prismql, #174) — opening it selects that request in the
// journal, whatever its age. Copy finding puts the address in the Markdown.
(function (root) {
  "use strict";
  var listening = false;

  function seqFromHash(hash) {
    var m = /^#q(\d+)$/.exec(hash || "");
    return m ? Number(m[1]) : null;
  }

  function apply(state) {
    var seq = seqFromHash(root.location ? root.location.hash : "");
    if (seq == null || !state.entries.some(function (e) { return e.seq === seq; })) return false;
    state.sel = seq;
    state.tab = "details";
    state.filters.range = "all"; // an older request is still in the journal
    return true;
  }

  // Called once the journal has loaded: select the linked request, and do
  // the same whenever the address changes.
  function attach(state, render) {
    apply(state);
    if (listening || !root.addEventListener) return;
    listening = true;
    root.addEventListener("hashchange", function () { if (apply(state)) render(); });
  }

  var api = { seqFromHash: seqFromHash, attach: attach };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLBoardLink = api;
})(typeof window !== "undefined" ? window : globalThis);
