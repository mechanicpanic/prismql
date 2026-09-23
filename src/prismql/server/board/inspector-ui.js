// PrismQLInspectorUI: small DOM helpers shared across the inspector's
// files — the empty-state block, the kind/actor spans on an event line,
// and the full-view icon — so groups/hits/fetch/detail/output don't each
// carry their own copy (fix round 1, #9; graph @aleph/prismql, node #63).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;

  var ICON_FULL = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"></path></svg>';

  // Finding 6: one icon per empty state, same slot, so every column's
  // icon/title/body lines fall on the same horizontal lines. The journal's
  // own filter icon and the inspector's cursor icon are the two the board
  // currently uses; a caller passes one via opts.icon.
  var ICON_EMPTY_FILTER = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"></path></svg>';
  var ICON_EMPTY_CURSOR = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3l14 8-6 1.5-2 6.5-6-16z"></path></svg>';

  // title/detail plus an optional icon and a trailing element (a button).
  // Pass opts.compact for the smaller in-body padding the output sections
  // use; the top-level "nothing selected"/"no requests" panes keep
  // board.css's larger default .empty padding. opts.icon, when given, is
  // the same slot every empty state uses — the icon always sits above the
  // title, never conditionally, so titles line up across columns.
  function emptyBlock(title, detail, opts) {
    opts = opts || {};
    var empty = mk("div", "empty");
    if (opts.compact) empty.style.padding = "24px";
    if (opts.icon) {
      var icon = document.createElement("div");
      icon.className = "eicon";
      icon.setAttribute("aria-hidden", "true");
      icon.innerHTML = opts.icon;
      empty.appendChild(icon);
    }
    empty.appendChild(mk("strong", null, title));
    if (detail) empty.appendChild(mk("span", null, detail));
    if (opts.action) empty.appendChild(opts.action);
    return empty;
  }

  // The kind/actor spans on an `.l` event line — a group's slot event and
  // a hit's event share this exact shape (fix round 1, #9).
  function kindActorSpans(l, event, board) {
    if (board.kind && event && event[board.kind] != null) {
      l.appendChild(mk("span", "k", String(event[board.kind])));
    }
    if (board.actor && event && event[board.actor] != null) {
      l.appendChild(mk("span", "a", String(event[board.actor])));
    }
  }

  var api = {
    ICON_FULL: ICON_FULL, ICON_EMPTY_FILTER: ICON_EMPTY_FILTER, ICON_EMPTY_CURSOR: ICON_EMPTY_CURSOR,
    emptyBlock: emptyBlock, kindActorSpans: kindActorSpans,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorUI = api;
})(typeof window !== "undefined" ? window : globalThis);
