// PrismQLRail: the filter rail — time range, kind/source/corpus/status
// facets and "reset all filters" (graph @aleph/prismql, node #63). Called
// from PrismQLJournal.render(); split out to keep both files under the
// 150-line budget (authorized by the task-4 brief). No public entry point
// of its own beyond render(state, actions).
(function (root) {
  "use strict";

  var KIND_COLOR = { evaluate: "var(--k-evaluate)", search: "var(--k-search)", similar: "var(--k-similar)" };
  var STATUS_COLOR = { ok: "var(--ok)", capped: "var(--warn)", error: "var(--err)", empty: "var(--faint)" };
  var KIND_VALUES = ["evaluate", "search", "similar"];
  var STATUS_VALUES = ["ok", "capped", "empty", "error"];

  // Distinct values actually seen (never a hardcoded list — "who" and
  // "corpus" are open-ended, unlike kind/status which are the server's own
  // fixed vocabulary).
  function distinct(entries, field) {
    var seen = {}, out = [];
    entries.forEach(function (e) {
      var v = e[field];
      if (v != null && !seen[v]) { seen[v] = true; out.push(v); }
    });
    return out.sort();
  }

  function renderRanges(state, actions) {
    var U = window.PrismQLBoardUtil;
    var el = document.getElementById("rail-range");
    var active = document.activeElement;
    var refocus = (active && el.contains(active)) ? active.dataset.range : null;
    el.innerHTML = "";
    var again = null;
    U.RANGES.forEach(function (r) {
      var on = state.filters.range === r[0];
      var btn = U.mk("button", on ? "on" : "", r[0]);
      btn.type = "button";
      btn.dataset.range = r[0];
      btn.setAttribute("aria-pressed", String(on));
      btn.addEventListener("click", function () { actions.setFilter("range", r[0]); });
      if (r[0] === refocus) again = btn;
      el.appendChild(btn);
    });
    if (again) again.focus({ preventScroll: true });
  }

  // A rebuilt checkbox is a new DOM node — the browser drops focus to
  // <body> unless we restore it by the value the input carried, not by
  // node identity (fix round 1, #2).
  function renderFacetGroup(elId, key, values, nowMs, state, actions, opts) {
    var U = window.PrismQLBoardUtil;
    var el = document.getElementById(elId);
    var active = document.activeElement;
    var refocus = (active && active.tagName === "INPUT" && el.contains(active)) ? active.dataset.value : null;
    el.innerHTML = "";
    var counts = window.PrismQLFormat.facetCounts(state.entries, U.effFilters(state), nowMs, key, values);
    var again = null;
    values.forEach(function (v) {
      var n = counts[v] || 0;
      var on = !!state.filters[key][v];
      var label = U.mk("label", "facet" + (n === 0 && !on ? " zero" : ""));
      var input = document.createElement("input");
      input.type = "checkbox";
      input.checked = on;
      input.dataset.value = String(v);
      input.addEventListener("change", function () { actions.toggleFacet(key, v); });
      label.appendChild(input);
      if (String(v) === refocus) again = input;
      if (opts.color) {
        var dot = U.mk("span", "dot");
        dot.style.background = opts.color[v] || "";
        if (opts.round) dot.style.borderRadius = "50%";
        label.appendChild(dot);
      }
      label.appendChild(document.createTextNode(v));
      if (opts.agent && window.PrismQLFormat.isAgent(v)) label.appendChild(U.mk("span", "who", "agent"));
      label.appendChild(U.mk("span", "n", String(n)));
      el.appendChild(label);
    });
    if (again) again.focus({ preventScroll: true });
  }

  function anyFilter(state) {
    var f = state.filters;
    return f.range !== "24h" || f.search.trim() !== "" ||
      Object.keys(f.kinds).length > 0 || Object.keys(f.srcs).length > 0 ||
      Object.keys(f.corpora).length > 0 || Object.keys(f.statuses).length > 0;
  }

  function render(state, actions) {
    var nowMs = Date.now();
    renderRanges(state, actions);
    renderFacetGroup("rail-kind", "kinds", KIND_VALUES, nowMs, state, actions, { color: KIND_COLOR });
    renderFacetGroup("rail-source", "srcs", distinct(state.entries, "who"), nowMs, state, actions, { agent: true });
    renderFacetGroup("rail-corpus", "corpora", distinct(state.entries, "corpus"), nowMs, state, actions, {});
    renderFacetGroup("rail-status", "statuses", STATUS_VALUES, nowMs, state, actions, { color: STATUS_COLOR, round: true });

    var resetEl = document.getElementById("rail-reset");
    var resetHadFocus = resetEl.contains(document.activeElement);
    resetEl.innerHTML = "";
    if (anyFilter(state)) {
      var btn = window.PrismQLBoardUtil.mk("button", "reset", "Reset all filters");
      btn.type = "button";
      btn.addEventListener("click", function () { actions.resetFilters(); });
      resetEl.appendChild(btn);
      if (resetHadFocus) btn.focus({ preventScroll: true });
    }
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLRail = api;
})(typeof window !== "undefined" ? window : globalThis);
