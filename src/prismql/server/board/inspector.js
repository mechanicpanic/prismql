// PrismQLInspector: the "Request" tab of the inspector aside — header, the
// highlighted query with a copy button, actions (Full view/Open in editor/
// Run again/.jsonl), the source/corpus/received/duration/result kv list,
// and the output section (delegated to inspector-output.js). Ports the
// canvas markup ≈336-397 and its `renderVals` detail logic ≈734-764
// (graph @aleph/prismql, node #63; task-5 brief, fix round 1). The
// "Editor" tab's pane content belongs to editor.js (Task 6); this module
// only owns the three tab buttons themselves (Request/Editor/Corpus), since
// all live in the one `.insp` aside.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;
  var UI = window.PrismQLInspectorUI;

  var TABS = { "tab-details": "details", "tab-editor": "editor", "tab-corpus": "corpus" };
  function wireTabs(actions) {
    Object.keys(TABS).forEach(function (id) {
      var el = document.getElementById(id);
      if (el && !el.dataset.wired) {
        el.dataset.wired = "1";
        el.addEventListener("click", function () { actions.setTab(TABS[id]); });
      }
    });
  }
  function updateTabs(state) {
    Object.keys(TABS).forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.className = "tab" + (state.tab === TABS[id] ? " on" : "");
      el.setAttribute("aria-selected", String(state.tab === TABS[id]));
    });
  }

  function buildHeader(wrap, entry, nowMs) {
    var dhead = mk("div", "dhead");
    dhead.appendChild(mk("span", "kind " + entry.kind, entry.kind));
    var status = F.status(entry);
    dhead.appendChild(mk("span", "badge s-" + status, IF.statusLabel(status)));
    var rid = IF.requestId(entry);
    var id = mk("span", null, rid.text);
    if (rid.title) id.title = rid.title;
    id.style.marginLeft = "auto";
    id.style.font = "11px 'JetBrains Mono', monospace";
    id.style.color = "var(--faint)";
    dhead.appendChild(id);
    wrap.appendChild(dhead);

    var when = document.createElement("p");
    when.className = "when";
    when.appendChild(document.createTextNode(IF.whenAbs(entry.ts, nowMs) + " "));
    var rel = mk("span", null, "· " + F.rel(relSec(entry.ts, nowMs)));
    rel.dataset.ts = entry.ts; // read back by tick() to patch this in place, no rebuild
    when.appendChild(rel);
    wrap.appendChild(when);
  }
  function relSec(ts, nowMs) {
    return Math.max(0, Math.round((nowMs - new Date(ts).getTime()) / 1000));
  }

  function buildCode(wrap, entry) {
    var code = mk("div", "code");
    // shown with a line per link and clause (#84); Copy takes the query as sent
    var shown = window.PrismQLQueryFormat.breakLines(entry.query || "");
    if (entry.kind === "evaluate") code.innerHTML = window.PrismQLQueryFormat.numberedHtml(shown, entry.slots); // ①② (#85)
    else code.appendChild(document.createTextNode(entry.query || ""));
    var btn = mk("button", "iconbtn sm copy");
    btn.type = "button";
    btn.setAttribute("aria-label", "Copy query");
    btn.title = "Copy query";
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"></path></svg>';
    btn.addEventListener("click", function () { copyQuery(btn, entry.query || ""); });
    code.appendChild(btn);
    wrap.appendChild(code);
  }
  // The title only flips to "Copied" once writeText actually resolves,
  // and to "Copy failed" if it rejects or throws synchronously (no
  // Clipboard API, no permission) — fix round 1, #8.
  function copyQuery(btn, text) {
    try {
      navigator.clipboard.writeText(text)
        .then(function () { flipTitle(btn, "Copied"); })
        .catch(function () { flipTitle(btn, "Copy failed"); });
    } catch (e) {
      flipTitle(btn, "Copy failed");
    }
  }
  function flipTitle(btn, text) {
    btn.title = text;
    setTimeout(function () { btn.title = "Copy query"; }, 1500);
  }

  function render(state, actions, nowMs) {
    nowMs = nowMs || Date.now();
    if (window.PrismQLInspectorCorpora) window.PrismQLInspectorCorpora.ensure(state);
    wireTabs(actions);
    updateTabs(state);
    var pane = document.getElementById("inspector-pane");
    if (!pane) return;
    // The Editor tab's content is editor.js's (Task 6): it owns #inspector-pane
    // entirely while state.tab === "editor" and must not be nuked out from
    // under it on every render — clearing happens on the Details and Corpus
    // paths, never the Editor's.
    if (state.tab === "corpus") {
      pane.innerHTML = "";
      window.PrismQLInspectorCorpus.render(pane, state);
      return;
    }
    if (state.tab !== "details") return;
    pane.innerHTML = "";
    // entries first, then pending — a paused run's own match never merges
    // into entries (fix round 2, #1).
    var entry = window.PrismQLBoardUtil.findEntry(state, state.sel);
    if (!entry) {
      pane.appendChild(UI.emptyBlock("Nothing selected", "Pick a request in the journal to see its query, timing and results.", { icon: UI.ICON_EMPTY_CURSOR }));
      return;
    }
    buildHeader(pane, entry, nowMs);
    buildCode(pane, entry);
    window.PrismQLInspectorDetail.buildActs(pane, entry, actions, state);
    window.PrismQLInspectorDetail.buildKv(pane, entry);
    window.PrismQLInspectorOutput.render(pane, entry, state, actions);
  }

  // The 5 s beat's cheap path (journal.js's tick(), unchanged signature):
  // patch the header's relative time in place — never a rebuild, so
  // nothing in the pane (a focused button, a text selection) is disturbed
  // (fix round 1, #1).
  function tick(nowMs) {
    var rel = document.querySelector("#inspector-pane .when span[data-ts]");
    if (!rel) return;
    rel.textContent = "· " + F.rel(relSec(rel.dataset.ts, nowMs));
  }

  var api = { render: render, tick: tick };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspector = api;
})(typeof window !== "undefined" ? window : globalThis);
