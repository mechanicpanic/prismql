// PrismQLFull: the #full overlay — wires `state.full` to the header, the
// summary/view-bar and the per-view body; owns keyboard, focus/scroll
// preservation and its own ephemeral view state (graph @aleph/prismql, node #76).
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
  var Nav = window.PrismQLFullNav;

  var PAGE = FL.PAGE; // fix round 1, #8: one shared constant, not a literal per file
  var vs = freshView(null);
  var wasOpen = false;
  var stateRef = null, actionsRef = null;
  var lastFiltered = []; // this render's filtered groups (Timeline), for ↑/↓ nav
  var lastBodySig = null; // finding 5: what the body was last built from

  // A page at a time: page/order/reverse/open groups are view state, reset
  // with every entry like the filter (fullview-nav-logic.js).
  function freshView(seq) {
    return Object.assign({ seq: seq, view: null, group: 0, q: "", agents: {} }, Nav.initial(PAGE));
  }
  function resetView(seq) { vs = freshView(seq); }

  // The single door into the full view: a fresh view/filter/group state
  // greets every entry it lands on, same request or not.
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
    if (Nav.keepsArrow(t, e.key)) return; // the control's own arrows (Sort select, pager buttons)
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
      var full = document.getElementById("full"); // focus/scroll follow the new nav button
      var current = full && full.querySelector(".gnav .gitem.on");
      if (current) {
        current.focus({ preventScroll: true });
        current.scrollIntoView({ block: "nearest" });
      }
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
      lastBodySig = null;
      return;
    }
    if (entry.seq !== vs.seq) resetView(entry.seq);
    wireKeys(el);
    var visible = window.PrismQLJournal ? window.PrismQLJournal._visibleEntries(state, nowMs) : [];
    var idx = visible.findIndex(function (r) { return r.seq === entry.seq; });
    var bf = PF.boardFieldsFor(state, entry.corpus);
    var outputKind = IF.outputKind(entry);
    // ctx before the header: a gone result must never offer a download.
    var ctx = bf.blocked ? null : Data.buildContext(entry, bf.board, outputKind, vs, actions, bf.idField);
    // vs.view resolved (null -> allowed[0]) BEFORE bodySig, not after — else
    // the sig stored on the build that resolved it ("null") never matches
    // the next render's sig (now resolved), forcing a spurious rebuild on
    // the first live arrival after opening. A blocked (gone/error) body
    // only ever allows Summary/Raw.
    // The store may hold fewer pages than the view asks for (a page past
    // the end answers empty): step back to the last real one.
    if (ctx && ctx.nav && ctx.nav.got === 0 && !ctx.pending && !ctx.blocker && ctx.nav.page >= ctx.nav.pageCount && vs.page > 0) {
      Nav.goPage(vs, ctx.nav.pageCount - 1);
      return render(state, actions, nowMs);
    }
    var allowed = bf.blocked ? null : (ctx.blocker ? ["summary", "raw"] : FL.viewsFor(outputKind));
    if (allowed && allowed.indexOf(vs.view) < 0) vs.view = allowed[0];
    // Finding 5: a live arrival elsewhere changes visible/idx but not the
    // body's own inputs — patch the header's nav and stop.
    var bodySig = [
      entry.seq, vs.view, vs.group, vs.q, JSON.stringify(vs.agents),
      vs.page, vs.order, vs.reverse, JSON.stringify(vs.shown),
      ctx ? ctx.loaded.length + ":" + ctx.pending + ":" + ctx.filtered.length + ":" + !!ctx.blocker : "blocked",
    ].join("|");
    if (bodySig === lastBodySig && wasOpen && Header.patchNav(el, actions, visible, idx)) return;
    lastBodySig = bodySig;
    var saved = Focus.captureFocus(el);
    var scroll = Focus.captureScroll(el);
    el.innerHTML = "";
    Header.build(el, entry, actions, nowMs, visible, idx, !!(ctx && ctx.gone));
    if (bf.blocked) {
      el.appendChild(mk("div", "fsum"));
      var loading = mk("div", "fbody");
      loading.appendChild(PF.loadingBlock());
      el.appendChild(loading);
      lastFiltered = [];
    } else {
      Summary.buildSum(el, entry, ctx.tiles);
      Summary.buildBar(el, allowed, vs.view, ctx, vs, function () { render(state, actions); });
      lastFiltered = Body.build(el, entry, ctx, outputKind, bf.board, vs, actions,
        function () { render(state, actions); },
        function (i) { vs.group = i; render(state, actions); });
    }
    // a new page / order starts at the top; any other rebuild keeps its place
    if (!vs.resetScroll) Focus.restoreScroll(el, scroll);
    else if (ctx && !ctx.pending) vs.resetScroll = false;
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
