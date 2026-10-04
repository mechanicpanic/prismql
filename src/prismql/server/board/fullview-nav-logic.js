// PrismQLFullNav: pure view state of the full view's result navigation —
// which page, which order (stored or by group size), reversed or not, which
// verbose groups are open — and what each means for a fetch and for the
// words on screen. The view only chooses WHICH stored items a page shows
// (GET /results/{rid}?order=&reverse=); it never changes a result. Window-
// free like fullview-logic.js so it is node-testable without a fake DOM.
(function (root) {
  "use strict";

  // A group with more events than COLLAPSE_AT is "verbose": it starts as its
  // first PREVIEW events, and opens STEP events at a time, so no click ever
  // puts hundreds of event cards in the DOM at once.
  var COLLAPSE_AT = 10;
  var PREVIEW = 3;
  var STEP = 100;
  var ORDERS = [
    { value: "position", label: "Original order" },
    { value: "size", label: "Largest groups first" },
  ];

  function initial(pageSize) {
    return { page: 0, pageSize: pageSize, count: null, order: "position", reverse: false, shown: {}, resetScroll: false };
  }

  function pageCount(count, pageSize) {
    return count == null ? 1 : Math.max(1, Math.ceil(count / pageSize));
  }
  function clampPage(page, count, pageSize) {
    return Math.max(0, Math.min(page, pageCount(count, pageSize) - 1));
  }
  function goPage(vs, page) {
    var next = clampPage(Math.floor(Number(page)) || 0, vs.count, vs.pageSize);
    if (next === vs.page) return false;
    vs.page = next;
    vs.group = 0;
    vs.resetScroll = true;
    return true;
  }
  // A new order starts from the first page: a position in the old order
  // means nothing in the new one.
  function setOrder(vs, order) {
    if (order === vs.order) return;
    vs.order = order; vs.page = 0; vs.group = 0; vs.resetScroll = true;
  }
  function toggleReverse(vs) {
    vs.reverse = !vs.reverse; vs.page = 0; vs.group = 0; vs.resetScroll = true;
  }

  // The fetch's view: only a non-default one is sent (and keyed in the
  // cache, inspector-page-logic.js), so the stored-order page stays exactly
  // the page it always was.
  function viewOf(vs) {
    return vs.order === "position" && !vs.reverse ? null : { order: vs.order, reverse: vs.reverse };
  }

  // The server caps a page at its max_results, however large a `limit` asks
  // for: a window that came back SHORT while more remain is the cap showing.
  // Offsets are then stepped by it, never by the size asked for, so no item
  // is skipped between pages.
  function effectiveSize(requested, data) {
    return data && data.truncated && data.count > 0 && data.count < requested ? data.count : requested;
  }
  // How many items the store holds: hits keep fewer than they found.
  function itemCount(data, fallback) {
    if (data.kept != null) return data.kept;
    return data.total != null ? data.total : fallback;
  }
  // 0-based position of each page item in the STORED result — the number a
  // group keeps whatever the order. A default page names none; they follow.
  function storedIndexes(data, offset, got) {
    if (data.indices && data.indices.length === got) return data.indices;
    var out = [];
    for (var i = 0; i < got; i++) out.push(offset + i);
    return out;
  }

  function isVerbose(total) { return total > COLLAPSE_AT; }
  function visibleCount(total, shown) {
    if (!isVerbose(total)) return total;
    return Math.min(total, Math.max(PREVIEW, shown == null ? PREVIEW : shown));
  }
  // "open"/"more" show STEP further events; "close" goes back to the preview.
  function nextShown(total, shown, action) {
    if (action === "close") return PREVIEW;
    return Math.min(total, visibleCount(total, shown) + STEP);
  }
  function applyShown(vs, idx, total, action) {
    vs.shown[idx] = nextShown(total, vs.shown[idx], action);
  }
  // Every verbose group in `groups` ({idx, ids}) at once, for the page.
  function setAll(vs, groups, action) {
    groups.forEach(function (g) {
      var total = (g.ids || []).length;
      if (isVerbose(total)) applyShown(vs, g.idx, total, action === "close" ? "close" : "open");
    });
  }
  function toggleText(total, shown) {
    var seen = visibleCount(total, shown);
    var left = total - seen;
    return {
      seen: seen, left: left,
      more: left <= 0 ? null : left <= STEP ? "Show all " + total + " events" : "Show " + STEP + " more (" + left + " left)",
      close: seen > PREVIEW ? "Collapse to first " + PREVIEW : null,
    };
  }

  // The fnote of a page: the filter's reach is THIS page only, and what is
  // kept can fall short of what was found.
  function pageNote(offset, got, count, matched, total) {
    var parts = [];
    if (matched != null && matched < got) parts.push(matched + " of " + got + " on this page match");
    parts.push(got ? (offset + 1) + "–" + (offset + got) + " of " + count : "0 of " + count);
    if (total != null && total > count) parts.push(total + " found");
    return parts.join(" · ");
  }

  var api = {
    COLLAPSE_AT: COLLAPSE_AT, PREVIEW: PREVIEW, STEP: STEP, ORDERS: ORDERS,
    initial: initial, pageCount: pageCount, clampPage: clampPage, goPage: goPage,
    setOrder: setOrder, toggleReverse: toggleReverse, viewOf: viewOf,
    effectiveSize: effectiveSize, itemCount: itemCount, storedIndexes: storedIndexes,
    isVerbose: isVerbose, visibleCount: visibleCount, nextShown: nextShown,
    applyShown: applyShown, setAll: setAll, toggleText: toggleText, pageNote: pageNote,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullNav = api;
})(typeof window !== "undefined" ? window : globalThis);
