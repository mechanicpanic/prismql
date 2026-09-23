// PrismQLInspector: the "Request" tab of the inspector aside — header, the
// highlighted query with a copy button, actions (Full view/Open in editor/
// Run again/.jsonl), the source/corpus/received/duration/result kv list,
// and the output section (delegated to inspector-output.js). Ports the
// canvas markup ≈336-397 and its `renderVals` detail logic ≈734-764
// (graph @aleph/prismql, node #63; task-5 brief, fix round 1). The
// "Editor" tab's pane content belongs to editor.js (Task 6); this module
// only owns the two tab buttons themselves, since both live in the one
// `.insp` aside.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;
  var UI = window.PrismQLInspectorUI;

  function wireTabs(actions) {
    var d = document.getElementById("tab-details");
    var e = document.getElementById("tab-editor");
    if (d && !d.dataset.wired) {
      d.dataset.wired = "1";
      d.addEventListener("click", function () { actions.setTab("details"); });
    }
    if (e && !e.dataset.wired) {
      e.dataset.wired = "1";
      e.addEventListener("click", function () { actions.setTab("editor"); });
    }
  }
  function updateTabs(state) {
    var d = document.getElementById("tab-details");
    var e = document.getElementById("tab-editor");
    if (d) {
      d.className = "tab" + (state.tab === "details" ? " on" : "");
      d.setAttribute("aria-selected", String(state.tab === "details"));
    }
    if (e) {
      e.className = "tab" + (state.tab === "editor" ? " on" : "");
      e.setAttribute("aria-selected", String(state.tab === "editor"));
    }
  }

  function buildHeader(wrap, entry, nowMs) {
    var dhead = mk("div", "dhead");
    dhead.appendChild(mk("span", "kind " + entry.kind, entry.kind));
    var status = F.status(entry);
    dhead.appendChild(mk("span", "badge s-" + status, IF.statusLabel(status)));
    var id = mk("span", null, entry.result_id != null ? String(entry.result_id) : "#" + entry.seq);
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
    if (entry.kind === "evaluate") code.innerHTML = window.PrismQLLexer.highlight(entry.query || "");
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
    // under it on every render — clearing only happens on the Details path.
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
    window.PrismQLInspectorDetail.buildActs(pane, entry, actions);
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
