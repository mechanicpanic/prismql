// PrismQLRail: the filter rail — time range, kind/source/corpus/status
// facets and "reset all filters" (graph @aleph/prismql, node #63). Called
// from PrismQLJournal.render(); split out to keep both files under the
// 150-line budget (authorized by the task-4 brief). No public entry point
// of its own beyond render(state, actions).
(function (root) {
  "use strict";

  var RANGES = [["15m", 900], ["1h", 3600], ["24h", 86400], ["7d", 604800], ["all", 0]];
  var KIND_COLOR = { evaluate: "var(--k-evaluate)", search: "var(--k-search)", similar: "var(--k-similar)" };
  var STATUS_COLOR = { ok: "var(--ok)", capped: "var(--warn)", error: "var(--err)", empty: "var(--faint)" };
  var KIND_VALUES = ["evaluate", "search", "similar"];
  var STATUS_VALUES = ["ok", "capped", "empty", "error"];

  function rangeSeconds(label) {
    for (var i = 0; i < RANGES.length; i++) if (RANGES[i][0] === label) return RANGES[i][1];
    return 86400;
  }

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

  function effFilters(state) {
    var f = state.filters;
    return { range: rangeSeconds(f.range), search: f.search, kinds: f.kinds, srcs: f.srcs, corpora: f.corpora, statuses: f.statuses };
  }

  function renderRanges(state, actions) {
    var el = document.getElementById("rail-range");
    el.innerHTML = "";
    RANGES.forEach(function (r) {
      var on = state.filters.range === r[0];
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = on ? "on" : "";
      btn.setAttribute("aria-pressed", String(on));
      btn.textContent = r[0];
      btn.addEventListener("click", function () { actions.setFilter("range", r[0]); });
      el.appendChild(btn);
    });
  }

  function renderFacetGroup(elId, key, values, nowMs, state, actions, opts) {
    var el = document.getElementById(elId);
    el.innerHTML = "";
    var counts = window.PrismQLFormat.facetCounts(state.entries, effFilters(state), nowMs, key, values);
    values.forEach(function (v) {
      var n = counts[v] || 0;
      var on = !!state.filters[key][v];
      var label = document.createElement("label");
      label.className = "facet" + (n === 0 && !on ? " zero" : "");
      var input = document.createElement("input");
      input.type = "checkbox";
      input.checked = on;
      input.addEventListener("change", function () { actions.toggleFacet(key, v); });
      label.appendChild(input);
      if (opts.color) {
        var dot = document.createElement("span");
        dot.className = "dot";
        dot.style.background = opts.color[v] || "";
        if (opts.round) dot.style.borderRadius = "50%";
        label.appendChild(dot);
      }
      label.appendChild(document.createTextNode(v));
      if (opts.agent && window.PrismQLFormat.isAgent(v)) {
        var who = document.createElement("span");
        who.className = "who";
        who.textContent = "agent";
        label.appendChild(who);
      }
      var nEl = document.createElement("span");
      nEl.className = "n";
      nEl.textContent = String(n);
      label.appendChild(nEl);
      el.appendChild(label);
    });
  }

  function anyFilter(state) {
    var f = state.filters;
    return f.range !== "24h" || f.search !== "" ||
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
    resetEl.innerHTML = "";
    if (anyFilter(state)) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "reset";
      btn.textContent = "Reset all filters";
      btn.addEventListener("click", function () { actions.resetFilters(); });
      resetEl.appendChild(btn);
    }
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLRail = api;
})(typeof window !== "undefined" ? window : globalThis);
