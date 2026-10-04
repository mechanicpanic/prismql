// PrismQLFullFocus: preserves keyboard focus and scroll position across a
// full-view rebuild (task-7 brief; graph @aleph/prismql, node #76) — the
// filter input, a focused nav item, a keyed pager/sort/toggle control, or the section itself; the loaded-nav/
// group-detail/table/raw scrollers. A rebuild happens on every filter
// keystroke and every page/sort/toggle change, so losing either would be constant, not
// occasional.
(function (root) {
  "use strict";
  var SCROLLERS = [".gnav", ".gdetail", ".tbl", ".raw"];

  function captureFocus(el) {
    var active = document.activeElement;
    if (!active || !el.contains(active)) return null;
    if (active.matches && active.matches(".fsearch input")) {
      return { kind: "filter", start: active.selectionStart, end: active.selectionEnd };
    }
    // any control carrying a data-fkey (pager, sort, reverse, group toggles)
    if (active.dataset && active.dataset.fkey) {
      return { kind: "key", key: active.dataset.fkey, alt: active.dataset.falt || null, start: active.selectionStart, end: active.selectionEnd };
    }
    if (active.classList && active.classList.contains("gitem")) {
      return { kind: "gitem", index: Array.prototype.indexOf.call(active.parentNode.children, active) };
    }
    return { kind: "shell" };
  }
  function restoreFocus(el, saved) {
    if (!saved) return;
    if (saved.kind === "filter") {
      var input = el.querySelector(".fsearch input");
      if (input) {
        input.focus({ preventScroll: true });
        try { input.setSelectionRange(saved.start, saved.end); } catch (e) { /* not selectable, ignore */ }
      }
      return;
    }
    if (saved.kind === "key") {
      var byKey = function (k) {
        var nodes = el.querySelectorAll("[data-fkey]");
        for (var i = 0; i < nodes.length; i++) if (nodes[i].dataset.fkey === k) return nodes[i];
        return null;
      };
      var node = byKey(saved.key);
      // a Prev/Next that just reached its end is disabled: focus its twin
      if ((!node || node.disabled) && saved.alt) node = byKey(saved.alt);
      if (!node || node.disabled) { el.focus({ preventScroll: true }); return; }
      node.focus({ preventScroll: true });
      if (saved.start != null) {
        try { node.setSelectionRange(saved.start, saved.end); } catch (e) { /* number/select: no selection */ }
      }
      return;
    }
    if (saved.kind === "gitem") {
      var items = el.querySelectorAll(".gitem");
      (items[saved.index] || el).focus({ preventScroll: true });
      return;
    }
    el.focus({ preventScroll: true });
  }
  function captureScroll(el) {
    var out = {};
    SCROLLERS.forEach(function (sel) { var n = el.querySelector(sel); if (n) out[sel] = n.scrollTop; });
    return out;
  }
  function restoreScroll(el, saved) {
    SCROLLERS.forEach(function (sel) { var n = el.querySelector(sel); if (n && saved[sel] != null) n.scrollTop = saved[sel]; });
  }

  var api = {
    captureFocus: captureFocus, restoreFocus: restoreFocus,
    captureScroll: captureScroll, restoreScroll: restoreScroll,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullFocus = api;
})(typeof window !== "undefined" ? window : globalThis);
