// PrismQLJournal: the journal head (count, "N errors" pill) and chips
// (graph @aleph/prismql, node #63). The list itself is drawn by the sibling
// module PrismQLJournalList, the rail by PrismQLRail — split to stay under
// the 150-line budget; board.js only ever calls PrismQLJournal.render.
(function (root) {
  "use strict";

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

  function renderChips(chips) {
    var mk = window.PrismQLBoardUtil.mk;
    var el = document.getElementById("journal-chips");
    el.innerHTML = "";
    el.hidden = chips.length === 0;
    chips.forEach(function (c) {
      var chip = mk("span", "chip");
      chip.appendChild(mk("b", null, c.group));
      chip.appendChild(document.createTextNode(c.text));
      var btn = mk("button");
      btn.type = "button";
      btn.setAttribute("aria-label", c.aria);
      btn.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"></path></svg>';
      btn.addEventListener("click", c.remove);
      chip.appendChild(btn);
      el.appendChild(chip);
    });
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

  function render(state, actions) {
    var F = window.PrismQLFormat;
    var U = window.PrismQLBoardUtil;
    var nowMs = Date.now();
    var ef = U.effFilters(state);
    var visible = state.entries.filter(function (e) { return F.matches(e, ef, nowMs); });

    if (window.PrismQLRail) window.PrismQLRail.render(state, actions);

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

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLJournal = api;
})(typeof window !== "undefined" ? window : globalThis);
