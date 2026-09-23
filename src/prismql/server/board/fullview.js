// PrismQLFull: the #full overlay — wires `state.full` to the header
// (fullview-header.js), the summary/view-bar (fullview-summary.js), the
// per-view body (fullview-body.js) and data assembly (fullview-data.js);
// owns keyboard (Esc/←→/↑↓), focus/scroll preservation across a rebuild,
// and its own ephemeral view state — which view/group/filter is picked,
// same pattern as inspector-groups.js's local `shown` (task-7 brief; graph
// @aleph/prismql, node #76).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;
  var PF = window.PrismQLInspectorFetch;
  var FL = window.PrismQLFullLogic;
  var Data = window.PrismQLFullData;
  var Header = window.PrismQLFullHeader;
  var Summary = window.PrismQLFullSummary;
  var Body = window.PrismQLFullBody;
  var Focus = window.PrismQLFullFocus;

  var PAGE = FL.PAGE; // fix round 1, #8: one shared constant, not a literal per file
  var vs = { seq: null, view: null, group: 0, q: "", agents: {}, loadTo: PAGE };
  var wasOpen = false;
  var stateRef = null, actionsRef = null;
  var lastFiltered = []; // this render's filtered groups (Timeline), for ↑/↓ nav

  function resetView(seq) { vs = { seq: seq, view: null, group: 0, q: "", agents: {}, loadTo: PAGE }; }

  // The single door into the full view — the journal's dblclick/Enter, the
  // header's ←/→ neighbor buttons and this module's own ArrowLeft/Right all
  // call this (through board.js's `openFull` action), so a fresh view/
  // filter/group state greets every entry it lands on, same request or not
  // (design canvas: both `openFull` and its own `goTo` always reset
  // fview/fgroup/fq/fagents — never just on a changed seq).
  function open(state, render, seq) {
    state.sel = seq;
    state.tab = "details";
    state.full = seq;
    resetView(seq);
    render();
  }

  function onFullKey(e) {
    var state = stateRef, actions = actionsRef;
    if (!state || !actions) return;
    var t = e.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) {
      if (e.key === "Escape") t.blur();
      return;
    }
    if (e.key === "Escape") { e.preventDefault(); actions.closeFull(); return; }
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      var visible = window.PrismQLJournal._visibleEntries(state, Date.now());
      var idx = visible.findIndex(function (r) { return r.seq === state.full; });
      if (idx < 0) return;
      var j = e.key === "ArrowLeft" ? idx - 1 : idx + 1;
      if (visible[j]) { e.preventDefault(); actions.openFull(visible[j].seq); }
      return;
    }
    if ((e.key === "ArrowDown" || e.key === "ArrowUp") && vs.view === "timeline" && lastFiltered.length) {
      e.preventDefault();
      var gi = Math.min(vs.group, lastFiltered.length - 1);
      vs.group = e.key === "ArrowDown" ? Math.min(lastFiltered.length - 1, gi + 1) : Math.max(0, gi - 1);
      render(state, actions);
      // Fix round 1, #10: focus follows the selection to the newly
      // current nav button, not left behind on the #full section.
      var full = document.getElementById("full");
      var current = full && full.querySelector(".gnav .gitem.on");
      if (current) current.focus({ preventScroll: true });
    }
  }
  function wireKeys(el) {
    if (el.dataset.wired) return;
    el.dataset.wired = "1";
    el.addEventListener("keydown", onFullKey);
  }

  function render(state, actions, nowMs) {
    nowMs = nowMs || Date.now();
    stateRef = state; actionsRef = actions;
    var el = document.getElementById("full");
    if (!el) return;
    var entry = state.full != null ? window.PrismQLBoardUtil.findEntry(state, state.full) : null;
    if (!entry) {
      if (!el.hidden) el.hidden = true;
      // Esc (or a vanished selection) closes back to the journal — focus
      // follows it there, never left stranded on a hidden section.
      if (wasOpen) {
        var list = document.getElementById("journal-list");
        if (list) (list.querySelector(".row.sel") || list).focus({ preventScroll: true });
      }
      wasOpen = false;
      return;
    }
    if (entry.seq !== vs.seq) resetView(entry.seq);
    wireKeys(el);
    var saved = Focus.captureFocus(el);
    var scroll = Focus.captureScroll(el);
    el.innerHTML = "";
    var visible = window.PrismQLJournal ? window.PrismQLJournal._visibleEntries(state, nowMs) : [];
    var idx = visible.findIndex(function (r) { return r.seq === entry.seq; });
    var bf = PF.boardFieldsFor(state, entry.corpus);
    var outputKind = IF.outputKind(entry);
    // ctx is built before the header (fix round 1, #9): a gone result must
    // never offer "Download .jsonl" for a file the store no longer holds.
    var ctx = bf.blocked ? null : Data.buildContext(entry, bf.board, outputKind, vs, actions);
    Header.build(el, entry, actions, nowMs, visible, idx, !!(ctx && ctx.gone));
    if (bf.blocked) {
      el.appendChild(mk("div", "fsum"));
      var loading = mk("div", "fbody");
      loading.appendChild(PF.loadingBlock());
      el.appendChild(loading);
      lastFiltered = [];
    } else {
      var allowed = FL.viewsFor(outputKind);
      if (allowed.indexOf(vs.view) < 0) vs.view = allowed[0];
      Summary.buildSum(el, entry, ctx.tiles);
      Summary.buildBar(el, allowed, vs.view, ctx, vs, function () { render(state, actions); });
      lastFiltered = Body.build(el, entry, ctx, outputKind, bf.board, vs, actions,
        function () { render(state, actions); },
        function (i) { vs.group = i; render(state, actions); });
    }
    Focus.restoreScroll(el, scroll);
    Focus.restoreFocus(el, saved);
    if (el.hidden) el.hidden = false;
    if (!wasOpen) el.focus({ preventScroll: true });
    wasOpen = true;
  }

  // The 5 s beat: patch only the header's relative time, same as
  // inspector.js's tick() — never a rebuild (no focus loss, no scroll
  // reset, no dropped keystroke mid-filter).
  function tick(nowMs) {
    var rel = document.querySelector("#full .fwhen span[data-ts]");
    if (!rel) return;
    rel.textContent = "· " + F.rel(Math.max(0, Math.round((nowMs - new Date(rel.dataset.ts).getTime()) / 1000)));
  }

  var api = { render: render, tick: tick, open: open };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFull = api;
})(typeof window !== "undefined" ? window : globalThis);
