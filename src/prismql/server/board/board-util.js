// PrismQLBoardUtil: small helpers shared by the board's view modules — a
// range-label→seconds lookup, the format.js filter object built from
// `state`, a terse DOM-element constructor, and the entries/pending cap
// (graph @aleph/prismql, node #63). One home so rail.js/journal.js/
// journal-list.js/board-stream.js don't each carry their own copy (fix
// round 1, #11; the cap helper added in fix round 2, #1 — every site that
// prepends to entries or pending must go through it, or the cap is a lie).
(function (root) {
  "use strict";

  var RANGES = [["15m", 900], ["1h", 3600], ["24h", 86400], ["7d", 604800], ["all", 0]];
  var CAP = 1000;

  function rangeSeconds(label) {
    for (var i = 0; i < RANGES.length; i++) if (RANGES[i][0] === label) return RANGES[i][1];
    return 86400;
  }

  function effFilters(state) {
    var f = state.filters;
    return { range: rangeSeconds(f.range), search: f.search, kinds: f.kinds, srcs: f.srcs, corpora: f.corpora, statuses: f.statuses };
  }

  function mk(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function cap(arr) {
    return arr.length > CAP ? arr.slice(0, CAP) : arr;
  }

  var api = { RANGES: RANGES, CAP: CAP, rangeSeconds: rangeSeconds, effFilters: effFilters, mk: mk, cap: cap };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLBoardUtil = api;
})(typeof window !== "undefined" ? window : globalThis);
