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
  function signatureOf(visible, nowMs) {
    var F = window.PrismQLFormat;
    return visible.map(function (e) { return e.seq + ":" + F.dayLabel(e.ts, nowMs).label; }).join(",");
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
    var U = window.PrismQLBoardUtil;
    var nowMs = nowMsOverride || Date.now();
    var ef = U.effFilters(state);
    var visible = visibleEntries(state, nowMs);
    lastSignature = signatureOf(visible, nowMs);

    if (window.PrismQLRail) window.PrismQLRail.render(state, actions, nowMs);

    var chips = buildChips(state, actions);
    renderChips(chips);
    var anyFilter = chips.length > 0 || state.filters.range !== "24h";

    var inRangeEf = { range: ef.range, search: ef.search, kinds: {}, srcs: {}, corpora: {}, statuses: {} };
    var inRange = state.entries.filter(function (e) { return F.matches(e, inRangeEf, nowMs); });
    document.getElementById("journal-count").textContent =
      (visible.length === inRange.length && !anyFilter)
        ? visible.length + " requests"
        : visible.length + " of " + state.entries.length + " requests";

    var errors = visible.filter(function (e) { return F.status(e) === "error"; }).length;
    renderErrPill(errors, state, actions);

    if (window.PrismQLJournalList) window.PrismQLJournalList.render(state, actions, visible, nowMs, anyFilter);
  }

  // The 5 s beat: re-derive what should be visible right now. Unchanged
  // (same seqs, same day labels) → just patch ".rel" text, no rebuild, no
  // focus or selection loss (fix round 1, #1 — board.js's own interval
  // patches the live note and the inspector's "when" the same cheap way).
  // Changed (a row aged out of the range, or "Today" rolled to
  // "Yesterday") → the top-level PrismQLBoard.render(nowMs), so every
  // panel gets fresh counts, not just the journal.
  function tick(state, actions, nowMs) {
    var visible = visibleEntries(state, nowMs);
    var sig = signatureOf(visible, nowMs);
    if (sig === lastSignature) {
      if (window.PrismQLJournalList) window.PrismQLJournalList.tick(nowMs);
      return;
    }
    if (window.PrismQLBoard) window.PrismQLBoard.render(nowMs);
    else render(state, actions, nowMs);
  }

  var api = { render: render, tick: tick, _visibleEntries: visibleEntries, _signatureOf: signatureOf };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLJournal = api;
})(typeof window !== "undefined" ? window : globalThis);
