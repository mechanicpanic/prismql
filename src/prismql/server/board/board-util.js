// PrismQLBoardUtil: small helpers shared by the board's view modules — a
// range-label→seconds lookup, the format.js filter object built from
// `state`, and a terse DOM-element constructor (graph @aleph/prismql, node
// #63). One home so rail.js/journal.js/journal-list.js don't each carry
// their own copy (fix round 1, #11).
(function (root) {
  "use strict";

  var RANGES = [["15m", 900], ["1h", 3600], ["24h", 86400], ["7d", 604800], ["all", 0]];

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

  var api = { RANGES: RANGES, rangeSeconds: rangeSeconds, effFilters: effFilters, mk: mk };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLBoardUtil = api;
})(typeof window !== "undefined" ? window : globalThis);
