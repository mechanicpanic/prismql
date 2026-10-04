// PrismQLBoardKeys: the board by keyboard, wherever focus is, except while
// typing — j/k or ↑/↓ walk the journal, Enter/f open the full view, e/n/r
// the editor, c copies the finding, / searches, [ ] page the full view, ?
// lists them. The journal list and the full view keep their own keys
// (arrows, Enter, Esc) when they have focus; this never repeats them.
(function (root) {
  "use strict";

  var KEYS = [
    ["j / ↓", "next request"], ["k / ↑", "previous request"],
    ["Enter / f", "view results"], ["Esc", "close"], ["[ / ]", "previous / next page (full view)"],
    ["e", "open in editor"], ["r", "run again"], ["n", "new query"],
    ["c", "copy finding"], ["/", "search"], ["?", "this list"],
  ];
  var JOURNAL = { j: "next", ArrowDown: "next", k: "prev", ArrowUp: "prev", Enter: "full", f: "full",
    e: "edit", r: "rerun", n: "new", c: "copy", "/": "search", "?": "help", Escape: "close" };
  var FULL = { "[": "pagePrev", "]": "pageNext", "?": "help" };

  // The action a key asks for, or null. Pure: tested under node.
  function keyAction(key, ctx) {
    if (ctx.typing || ctx.modified || ctx.handled) return null;
    if (ctx.help) return key === "Escape" || key === "?" ? "help" : null;
    return (ctx.full ? FULL : JOURNAL)[key] || null;
  }

  function isTyping(el) {
    if (!el) return false;
    var tag = (el.tagName || "").toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select" || !!el.isContentEditable;
  }

  function step(state, actions, by) {
    var rows = root.PrismQLJournalList ? root.PrismQLJournalList.visible() : [];
    if (!rows.length) return;
    var i = rows.findIndex(function (r) { return r.seq === state.sel; });
    var j = i < 0 ? 0 : Math.max(0, Math.min(rows.length - 1, i + by));
    actions.select(rows[j].seq);
    var row = root.document.querySelector('#journal-list [data-seq="' + rows[j].seq + '"]');
    if (row && row.scrollIntoView) row.scrollIntoView({ block: "nearest" });
  }

  function copyFinding(entry) {
    if (!entry || entry.kind !== "evaluate" || !entry.ok || !root.PrismQLFinding) return;
    if (root.PrismQLEditorLogic.hasRequestDictionaries(entry)) return;
    var md = root.PrismQLFinding.findingMarkdown(entry, root.location.origin);
    try { root.navigator.clipboard.writeText(md).catch(function () {}); } catch (e) { /* refused */ }
  }

  function toggleHelp() {
    var box = root.document.getElementById("keys-help");
    if (box) { box.remove(); return; }
    box = root.document.createElement("div");
    box.id = "keys-help";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-label", "Keyboard shortcuts");
    var list = root.document.createElement("dl");
    KEYS.forEach(function (k) {
      var dt = root.document.createElement("dt");
      dt.textContent = k[0];
      var dd = root.document.createElement("dd");
      dd.textContent = k[1];
      list.appendChild(dt);
      list.appendChild(dd);
    });
    box.appendChild(list);
    (root.document.getElementById("app") || root.document.body).appendChild(box);
  }

  function run(name, state, actions) {
    var entry = root.PrismQLBoardUtil.findEntry(state, state.sel);
    var click = function (k) { var b = root.document.querySelector('[data-fkey="' + k + '"]'); if (b && !b.disabled) b.click(); };
    if (name === "next" || name === "prev") step(state, actions, name === "next" ? 1 : -1);
    else if (name === "full" && entry) actions.openFull(state.sel);
    else if (name === "edit" && entry) actions.openInEditor(entry);
    else if (name === "rerun" && entry && !root.PrismQLEditorLogic.hasRequestDictionaries(entry)) actions.rerun(entry);
    else if (name === "new") actions.newQuery();
    else if (name === "copy") copyFinding(entry);
    else if (name === "search") root.document.getElementById("search").focus();
    else if (name === "help") toggleHelp();
    else if (name === "pagePrev") click("prev");
    else if (name === "pageNext") click("next");
    else return false;
    return true;
  }

  function attach(state, actions) {
    root.document.addEventListener("keydown", function (e) {
      var name = keyAction(e.key, {
        typing: isTyping(e.target), modified: e.metaKey || e.ctrlKey || e.altKey,
        handled: e.defaultPrevented, full: !!state.full, help: !!root.document.getElementById("keys-help"),
      });
      if (name && run(name, state, actions)) e.preventDefault();
    });
  }

  var api = { keyAction: keyAction, attach: attach, KEYS: KEYS };
  if (typeof module === "object" && module.exports) module.exports = api;
  else {
    root.PrismQLBoardKeys = api;
    // board.js exposes its state and actions as window.PrismQLBoard
    var go = function () { if (root.PrismQLBoard) attach(root.PrismQLBoard.state, root.PrismQLBoard.actions); };
    if (root.document.readyState === "loading") root.document.addEventListener("DOMContentLoaded", go);
    else go();
  }
})(typeof window !== "undefined" ? window : globalThis);
