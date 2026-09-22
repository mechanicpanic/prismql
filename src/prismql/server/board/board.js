// PrismQL board — entry point: theme, the state every view module reads,
// the actions object they call, and topbar wiring (graph @aleph/prismql,
// node #63 — later tasks attach more actions via window.PrismQLBoard.actions
// rather than growing this file, #10). Live connection and the live/pause
// actions live in board-stream.js (fix round 2, #1 — one place applies the
// entries/pending cap).
(function () {
  "use strict";
  var THEME_KEY = "prismql-board-theme";

  function readTheme() {
    try { return localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark"; }
    catch (e) { return "dark"; }
  }
  function writeTheme(theme) {
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* unavailable — just not remembered */ }
  }
  function setHidden(el, hidden) {
    // SVGElement has no "hidden" IDL attribute — el.hidden is a no-op here.
    if (!el) return;
    if (hidden) el.setAttribute("hidden", ""); else el.removeAttribute("hidden");
  }

  var state = {
    entries: [], seq: 0, boot: null, live: true, pending: [], down: false, freshSeq: null,
    filters: { range: "24h", search: "", kinds: {}, srcs: {}, corpora: {}, statuses: {} },
    sel: null, tab: "details", theme: readTheme(),
    corpora: { corpora: [], default: null, board: {} },
    full: null,
  };

  // "·" is its own aria-hidden span (index.html), so flex gap spaces it
  // (fix round 2, #4). Never shown while reconnecting.
  function updateLiveNote(nowMs) {
    var note = document.getElementById("live-note");
    var sep = document.getElementById("live-sep");
    if (!note) return;
    var newest = state.entries[0];
    var show = !state.down && !!newest;
    setHidden(sep, !show);
    if (!show) { note.textContent = ""; return; }
    var sec = Math.max(0, Math.round((nowMs - new Date(newest.ts).getTime()) / 1000));
    note.textContent = "last request " + window.PrismQLFormat.rel(sec);
  }

  function updateTopbar(nowMs) {
    var btn = document.getElementById("live-toggle");
    if (btn) {
      btn.className = "live" + (state.down ? " down" : state.live ? "" : " off");
      // No aria-pressed (carry-over, Task 4 review): the label already
      // says "live"/"paused"/"reconnecting" and must not drift with the
      // note every 5 s (fix round 2, #4).
      var label = state.down ? "Reconnecting to the live journal" : state.live ? "Pause the live journal" : "Resume the live journal";
      btn.setAttribute("aria-label", label);
      btn.setAttribute("title", label);
    }
    var word = document.getElementById("live-word");
    if (word) word.textContent = state.down ? "reconnecting" : state.live ? "live" : "paused";
    updateLiveNote(nowMs || Date.now());
    var search = document.getElementById("search");
    if (search && search.value !== state.filters.search) search.value = state.filters.search;
  }

  // nowMs threads to every panel (rail's counts, the inspector's "received"
  // time) so a beat and a user-triggered render never disagree on "now".
  function render(nowMs) {
    nowMs = nowMs || Date.now();
    updateTopbar(nowMs);
    if (window.PrismQLJournal) window.PrismQLJournal.render(state, actions, nowMs);
    ["PrismQLInspector", "PrismQLEditor", "PrismQLFull"].forEach(function (name) {
      var mod = window[name];
      if (mod && typeof mod.render === "function") mod.render(state, actions, nowMs);
    });
  }

  var actions = {
    select: function (seq) { state.sel = seq; state.tab = "details"; render(); },
    openFull: function (seq) { state.sel = seq; state.tab = "details"; state.full = seq; render(); },
    setFilter: function (key, value) { state.filters[key] = value; render(); },
    toggleFacet: function (key, value) {
      var o = Object.assign({}, state.filters[key]);
      if (o[value]) delete o[value]; else o[value] = true;
      state.filters[key] = o;
      render();
    },
    resetFilters: function () {
      state.filters = { range: "24h", search: "", kinds: {}, srcs: {}, corpora: {}, statuses: {} };
      render();
    },
    toggleLive: function () { window.PrismQLBoardStream.toggleLive(state, render); },
    showPending: function () { window.PrismQLBoardStream.showPending(state, render); },
    setTab: function (tab) { state.tab = tab; render(); },
    reconnect: function () { window.PrismQLBoardStream.reconnect(state, render); },
    openInEditor: function () {},
    rerun: function () {},
    run: function () {},
    newQuery: function () {},
  };

  // Later tasks attach more actions here instead of editing this file.
  window.PrismQLBoard = { state: state, actions: actions, render: render };

  function applyTheme(app, toggle, sun, moon, theme) {
    app.classList.remove("t-dark", "t-light");
    app.classList.add(theme === "light" ? "t-light" : "t-dark");
    setHidden(sun, theme === "light");
    setHidden(moon, theme !== "light");
    if (toggle) {
      var label = theme === "light" ? "Switch to dark theme" : "Switch to light theme";
      toggle.setAttribute("aria-label", label);
      toggle.setAttribute("title", label);
    }
  }

  function init() {
    var app = document.getElementById("app");
    if (!app) return;
    var toggle = document.getElementById("theme-toggle");
    var sun = document.getElementById("theme-icon-sun");
    var moon = document.getElementById("theme-icon-moon");
    applyTheme(app, toggle, sun, moon, state.theme);
    if (toggle) {
      toggle.addEventListener("click", function () {
        state.theme = state.theme === "light" ? "dark" : "light";
        applyTheme(app, toggle, sun, moon, state.theme);
        writeTheme(state.theme);
      });
    }
    var liveBtn = document.getElementById("live-toggle");
    if (liveBtn) liveBtn.addEventListener("click", function () { actions.toggleLive(); });
    var search = document.getElementById("search");
    if (search) search.addEventListener("input", function (e) { actions.setFilter("search", e.target.value); });
    var newQuery = document.getElementById("new-query");
    if (newQuery) newQuery.addEventListener("click", function () { actions.newQuery(); });
    render();
    // journal.tick() re-checks the range/day signature (fix round 2, #2)
    // and, when unchanged, still routes through render() so every panel
    // reads nowMs (carry-over, graph @aleph/prismql #63).
    setInterval(function () {
      var nowMs = Date.now();
      if (window.PrismQLJournal && window.PrismQLJournal.tick) window.PrismQLJournal.tick(state, actions, nowMs);
      else render(nowMs);
    }, 5000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
  window.PrismQLBoardStream.connect(state, render);
})();
