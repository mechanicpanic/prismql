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

  // A real page: {gone:true}, a groups/named page ({results:[...]}), a
  // hits page ({hits:[...]}), or a rows page ({rows:[...]}) — a GROUP BY
  // ... AGGREGATE answer (graph @aleph/prismql, #90). Anything else — a
  // network error, a 429/5xx body, an unrelated FastAPI {"detail":...} —
  // is not a page and must never be cached as one (fix round 1, #2).
  function isValidPage(data) {
    if (!data) return false;
    if (data.gone === true) return true;
    if (Array.isArray(data.results)) return true;
    if (Array.isArray(data.hits)) return true;
    if (Array.isArray(data.rows)) return true;
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

  // A grouped aggregate renders as rows (inspector-rows.js), so a null here
  // is a plain aggregate with nothing to compute; the tile says so in the
  // same words as the kv row (format.js's resultLabel).
  function aggregateValueText(value) {
    return value != null ? String(value) : "no value";
  }

  // Slots come from ids/positions/times (always index-aligned); the
  // server's `events` list drops any id it couldn't hydrate, so by the
  // time that happens its own index no longer lines up with the slots —
  // pair by id instead (fix round 1, #7). A slot with no matching event
  // renders without text.
  // Finding 4: pairs by the corpus's own id field (from /corpora's
  // id_field, default "id") — a corpus configured with a different id
  // field hydrates its events keyed by that field, not "id".
  function pairEventsToSlots(ids, events, idField) {
    idField = idField || "id";
    var byId = {};
    (events || []).forEach(function (e) {
      if (e && e[idField] != null) byId[e[idField]] = e;
    });
    return (ids || []).map(function (id) { return byId[id] || null; });
  }

  // A rows result's value is a number, or a list for `distinct` — joined
  // with ", " for display (graph @aleph/prismql, #90); never JSON. null
  // renders as the board's own empty marker, never the literal "null"
  // (fix round 1, #5) — the filter in fullview-data.js matches this exact
  // text too, so a null row is findable by it.
  function rowValueText(value) {
    if (value == null) return "—";
    return Array.isArray(value) ? value.join(", ") : String(value);
  }

  // Pages a rows result in fixed-size steps from growing offsets, like
  // inspector-groups.js's chain view, instead of a single fetch whose
  // `limit` grows unbounded — the server caps `limit` at `max_results`
  // regardless of what is requested, so a growing-limit fetch stuck at
  // that cap forever (fix round 1, #1). `fetchFn(offset, step)` must
  // return an inspector-fetch.js record ({status:"loading"} or
  // {status:"done", data:{rows:[...]}|{gone:true}|{error:{...}}}).
  // The next offset advances by the count the page actually returned,
  // never by `step` itself, so a page capped below `step` never skips or
  // repeats rows.
  // The one paging loop of the board: the inspector's rows and every full
  // view kind use it (a second copy lived in fullview-load.js). `listKey`
  // names the page's item list ("results", "hits", "rows"); a page's
  // `kept` narrows the bound (scouting kept fewer than it found) and its
  // `labels` (a named result's slot names) are passed through.
  function collectPages(total, target, step, fetchFn, listKey) {
    var out = { items: [], pending: false, bound: total, labels: null };
    var offset = 0;
    while (offset < target && offset < out.bound) {
      var page = fetchFn(offset, step);
      if (page.status === "loading") { out.pending = true; return out; }
      if (page.data.gone) { out.gone = true; return out; }
      if (page.data.error) { out.error = page.data.error; return out; }
      if (page.data.kept != null) out.bound = Math.min(out.bound, page.data.kept);
      if (page.data.labels != null) out.labels = page.data.labels;
      var got = page.data[listKey] || [];
      if (got.length === 0) break; // nothing more to get — never loop forever
      out.items = out.items.concat(got);
      offset += got.length;
    }
    return out;
  }
  function collectRowPages(total, target, step, fetchFn) {
    var r = collectPages(total, target, step, fetchFn, "rows");
    return { rows: r.items, pending: r.pending, gone: r.gone, error: r.error };
  }

  var api = {
    fieldsFor: fieldsFor, cacheKey: cacheKey, isValidPage: isValidPage,
    errorMessageFor: errorMessageFor, groupsMoreLabel: groupsMoreLabel,
    hitsNote: hitsNote, isScored: isScored, aggregateValueText: aggregateValueText,
    pairEventsToSlots: pairEventsToSlots, rowValueText: rowValueText,
    collectRowPages: collectRowPages, collectPages: collectPages,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorPageLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
