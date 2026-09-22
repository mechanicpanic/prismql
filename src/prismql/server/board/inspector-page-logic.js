// PrismQLInspectorPageLogic: pure logic for page fetches and their display
// — cache keys, which JSON shapes count as a real page, the field list a
// fetch asks for, "showing k of total" style labels, the score-vs-noscore
// decision and pairing a group's events to its slots by id (graph
// @aleph/prismql, node #63; fix round 1). Kept window-free like format.js
// so it is node-testable without a fake DOM.
(function (root) {
  "use strict";

  function fieldsFor(board) {
    var arr = ["text"];
    if (board && board.kind) arr.push(board.kind);
    if (board && board.actor) arr.push(board.actor);
    return arr;
  }

  // rid|offset|limit|fields(sorted) — a page fetched with a different
  // field list (text-only, before /corpora has loaded) never collides
  // with the fully-fielded page for the same offset (fix round 1, #3).
  function cacheKey(rid, offset, limit, fields) {
    var sorted = (fields || []).slice().sort().join(",");
    return rid + "|" + offset + "|" + limit + "|" + sorted;
  }

  // A real page: {gone:true}, a groups/named page ({results:[...]}), or a
  // hits page ({hits:[...]}). Anything else — a network error, a 429/5xx
  // body, an unrelated FastAPI {"detail":...} — is not a page and must
  // never be cached as one (fix round 1, #2).
  function isValidPage(data) {
    if (!data) return false;
    if (data.gone === true) return true;
    if (Array.isArray(data.results)) return true;
    if (Array.isArray(data.hits)) return true;
    return false;
  }

  // The server's own {error:{message}} shape (a 429, a runtime error) is
  // shown as-is; anything else that isn't a page (an unrecognized JSON
  // body) gets one honest, generic message — never "showing 0 of N" or
  // "undefined of N" built from fields that were never there.
  function errorMessageFor(data) {
    if (data && data.error && data.error.message) return data.error.message;
    return "the server answered without a page";
  }

  function groupsMoreLabel(loadedCount, total) {
    return "showing " + loadedCount + " of " + total;
  }
  function hitsNote(loadedCount, total) {
    return loadedCount + " of " + total;
  }
  function isScored(kind) {
    return kind === "similar";
  }

  // A per-group aggregate (AGGREGATE ... GROUP BY ...) never stores its
  // breakdown in the journal — entry.value is null exactly then, and the
  // kv row already reads "= per group" (format.js's resultLabel); the big
  // tile must say the same thing, not "—" (fix round 1, #6).
  function aggregateValueText(value) {
    return value != null ? String(value) : "per group";
  }

  // Slots come from ids/positions/times (always index-aligned); the
  // server's `events` list drops any id it couldn't hydrate, so by the
  // time that happens its own index no longer lines up with the slots —
  // pair by id instead (fix round 1, #7). A slot with no matching event
  // renders without text.
  function pairEventsToSlots(ids, events) {
    var byId = {};
    (events || []).forEach(function (e) {
      if (e && e.id != null) byId[e.id] = e;
    });
    return (ids || []).map(function (id) { return byId[id] || null; });
  }

  var api = {
    fieldsFor: fieldsFor, cacheKey: cacheKey, isValidPage: isValidPage,
    errorMessageFor: errorMessageFor, groupsMoreLabel: groupsMoreLabel,
    hitsNote: hitsNote, isScored: isScored, aggregateValueText: aggregateValueText,
    pairEventsToSlots: pairEventsToSlots,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorPageLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
