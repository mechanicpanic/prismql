// PrismQLBoardCols: widths of the board's resizable columns — the filter
// rail and the inspector; the journal takes the rest (graph @aleph/prismql,
// #118). Pure, unit-tested under node; board-resize.js does the DOM.
(function (root) {
  "use strict";

  var DEFAULTS = { rail: 232, insp: 520 };
  var RAIL_MIN = 160, RAIL_MAX = 420;
  var INSP_MIN = 320, INSP_MAX = 1100;
  var JOURNAL_MIN = 360;

  function within(v, lo, hi) { return Math.max(lo, Math.min(hi, Math.round(v))); }

  // Each column within its bounds; then, if the journal would fall below
  // its minimum, the inspector gives way first and the rail second. On a
  // narrow screen the rail is hidden and does not count (noRail).
  function clamp(cols, viewport, noRail) {
    var rail = within(cols.rail, RAIL_MIN, RAIL_MAX);
    var insp = within(cols.insp, INSP_MIN, INSP_MAX);
    var railTaken = noRail ? 0 : rail;
    var over = railTaken + insp + JOURNAL_MIN - viewport;
    if (over > 0) {
      var fromInsp = Math.min(over, insp - INSP_MIN);
      insp -= fromInsp;
      over -= fromInsp;
      if (over > 0 && !noRail) rail -= Math.min(over, rail - RAIL_MIN);
    }
    return { rail: rail, insp: insp };
  }

  // A stored value counts only when both widths are numbers.
  function parse(text) {
    try {
      var v = JSON.parse(text);
      if (v && typeof v.rail === "number" && typeof v.insp === "number") return { rail: v.rail, insp: v.insp };
    } catch (e) { /* not ours, or corrupt: defaults */ }
    return { rail: DEFAULTS.rail, insp: DEFAULTS.insp };
  }

  var api = {
    DEFAULTS: DEFAULTS, RAIL_MIN: RAIL_MIN, RAIL_MAX: RAIL_MAX, INSP_MIN: INSP_MIN,
    INSP_MAX: INSP_MAX, JOURNAL_MIN: JOURNAL_MIN, clamp: clamp, parse: parse,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLBoardCols = api;
})(typeof window !== "undefined" ? window : globalThis);
