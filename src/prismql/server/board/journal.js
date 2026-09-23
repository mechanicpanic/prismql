// PrismQLJournal: the journal head (count, "N errors" pill) and chips
// (graph @aleph/prismql, node #63). The list itself is drawn by the sibling
// module PrismQLJournalList, the rail by PrismQLRail — split to stay under
// the 150-line budget; board.js only ever calls PrismQLJournal.render and
// PrismQLJournal.tick.
(function (root) {
  "use strict";

  // What tick() compares between two 5 s beats: which seqs are visible AND
  // what day label each carries — a range boundary or a midnight rollover
  // changes this signature with the entries themselves untouched (fix
  // round 2, #2). Exported (prefixed _) so tests/board can pin it without
  // a DOM.
  function visibleEntries(state, nowMs) {
    var F = window.PrismQLFormat;
    var ef = window.PrismQLBoardUtil.effFilters(state);
    return state.entries.filter(function (e) { return F.matches(e, ef, nowMs); });
  }
  // Range+search only, no facet filters — the set every facet count and
  // the "X of Y requests" total are really drawn from (facetCounts skips
  // only its OWN facet, never range/search). tick()'s signature is built
  // from THIS, not visibleEntries: an entry a facet filter already hid
  // still ages out of range and must still change the rail's counts (fix
  // round 2, #3).
  function inRangeEntries(state, nowMs) {
    var F = window.PrismQLFormat;
    var ef = window.PrismQLBoardUtil.effFilters(state);
    var rangeOnly = { range: ef.range, search: ef.search, kinds: {}, srcs: {}, corpora: {}, statuses: {} };
    return state.entries.filter(function (e) { return F.matches(e, rangeOnly, nowMs); });
  }
  function signatureOf(entries, nowMs) {
    var F = window.PrismQLFormat;
    return entries.map(function (e) { return e.seq + ":" + F.dayLabel(e.ts, nowMs).label; }).join(",");
  }

  // Finding 5: "X of Y" against inRangeEntries — the same set every facet
  // count and the rail use — never the journal's whole lifetime count.
  function countText(visibleLen, inRangeLen, anyFilter) {
    return (visibleLen === inRangeLen && !anyFilter)
      ? visibleLen + " requests"
      : visibleLen + " of " + inRangeLen + " requests";
  }

  var lastSignature = null;

  function buildChips(state, actions) {
    var chips = [];
    [["kinds", "kind"], ["srcs", "source"], ["corpora", "corpus"], ["statuses", "status"]].forEach(function (g) {
      Object.keys(state.filters[g[0]]).forEach(function (v) {
        chips.push({
          group: g[1], text: v, aria: "Remove " + g[1] + " " + v,
          remove: function () { actions.toggleFacet(g[0], v); },
        });
      });
    });
    var s = (state.filters.search || "").trim(); // whitespace-only: no chip (fix round 1, #6)
    if (s) {
      chips.push({
        group: "text", text: "“" + s + "”", aria: "Clear search",
        remove: function () { actions.setFilter("search", ""); },
      });
    }
    return chips;
  }

  // A rebuilt chip is a new DOM node — refocus by group+text, the same
  // by-key pattern as the rail's facets (fix round 2, #3).
  function renderChips(chips) {
    var mk = window.PrismQLBoardUtil.mk;
    var el = document.getElementById("journal-chips");
    var active = document.activeElement;
    var refocus = (active && el.contains(active)) ? active.dataset.chipKey : null;
    el.innerHTML = "";
    el.hidden = chips.length === 0;
    var again = null;
    chips.forEach(function (c) {
      var key = c.group + ":" + c.text;
      var chip = mk("span", "chip");
      chip.appendChild(mk("b", null, c.group));
      chip.appendChild(document.createTextNode(c.text));
      var btn = mk("button");
      btn.type = "button";
      btn.dataset.chipKey = key;
      btn.setAttribute("aria-label", c.aria);
      btn.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"></path></svg>';
      btn.addEventListener("click", c.remove);
      if (key === refocus) again = btn;
      chip.appendChild(btn);
      el.appendChild(chip);
    });
    if (again) again.focus({ preventScroll: true });
  }

  function renderErrPill(errors, state, actions) {
    var mk = window.PrismQLBoardUtil.mk;
    var el = document.getElementById("journal-errpill");
    el.innerHTML = "";
    if (errors === 0 || state.filters.statuses.error) return;
    var pill = mk("button", "errpill");
    pill.type = "button";
    pill.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M12 8v5M12 16.5v.5"></path><circle cx="12" cy="12" r="9"></circle></svg>';
    pill.appendChild(document.createTextNode(errors + (errors > 1 ? " errors" : " error")));
    pill.addEventListener("click", function () { actions.setFilter("statuses", { error: true }); });
    el.appendChild(pill);
  }

  function render(state, actions, nowMsOverride) {
    var F = window.PrismQLFormat;
    var nowMs = nowMsOverride || Date.now();
    var visible = visibleEntries(state, nowMs);
    var inRange = inRangeEntries(state, nowMs);
    lastSignature = signatureOf(inRange, nowMs);

    if (window.PrismQLRail) window.PrismQLRail.render(state, actions, nowMs);
    if (window.PrismQLRailCorpora) window.PrismQLRailCorpora.render(state, actions);

    var chips = buildChips(state, actions);
    renderChips(chips);
    var anyFilter = chips.length > 0 || state.filters.range !== "24h";

    document.getElementById("journal-count").textContent =
      countText(visible.length, inRange.length, anyFilter);

    var errors = visible.filter(function (e) { return F.status(e) === "error"; }).length;
    renderErrPill(errors, state, actions);

    if (window.PrismQLJournalList) window.PrismQLJournalList.render(state, actions, visible, nowMs, anyFilter);
  }

  // The 5 s beat: re-derive what should be visible. Unchanged (same seqs,
  // same day labels) → just patch ".rel" text, no rebuild, no focus/
  // selection loss (fix round 1, #1). Changed → PrismQLBoard.render(nowMs)
  // so every panel gets fresh counts, not just the journal.
  function tick(state, actions, nowMs) {
    var sig = signatureOf(inRangeEntries(state, nowMs), nowMs);
    if (sig === lastSignature) {
      if (window.PrismQLJournalList) window.PrismQLJournalList.tick(nowMs);
      return;
    }
    if (window.PrismQLBoard) window.PrismQLBoard.render(nowMs);
    else render(state, actions, nowMs);
  }

  var api = {
    render: render, tick: tick, _visibleEntries: visibleEntries,
    _inRangeEntries: inRangeEntries, _signatureOf: signatureOf, _countText: countText,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLJournal = api;
})(typeof window !== "undefined" ? window : globalThis);
