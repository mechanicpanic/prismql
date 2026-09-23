// PrismQLFullHeader: the full view's `.fhead` (back/kind/status/when/meta/
// k-of-n/open-in-editor/download) and the `.fcenter` summary-only body for
// aggregate/grouped/file/error/empty results (task-7 brief; graph
// @aleph/prismql, node #76).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;

  function relSec(ts, nowMs) { return Math.max(0, Math.round((nowMs - new Date(ts).getTime()) / 1000)); }

  function backBtn(actions) {
    var btn = mk("button", "back");
    btn.type = "button";
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"></path></svg>';
    btn.appendChild(document.createTextNode("Journal"));
    btn.appendChild(mk("span", "kbd", "Esc"));
    btn.addEventListener("click", function () { actions.closeFull(); });
    return btn;
  }
  // .onclick, not addEventListener — patchNav (finding 5) reassigns it.
  function navBtn(path, title, disabled, onClick) {
    var btn = mk("button", "iconbtn");
    btn.type = "button";
    btn.title = title;
    btn.setAttribute("aria-label", title);
    btn.disabled = disabled;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="' + path + '"></path></svg>';
    btn.onclick = onClick;
    return btn;
  }

  // Finding 5: a live arrival patches only the "k of n" count and prev/
  // next, never a full rebuild (which drops scroll/filter selection).
  function patchNav(el, actions, visible, idx) {
    var count = el.querySelector("#fhead-nav-count");
    if (!count) return false;
    count.textContent = idx >= 0 ? (idx + 1) + " of " + visible.length : "";
    var prev = el.querySelector("#fhead-nav-prev");
    prev.disabled = idx <= 0;
    prev.onclick = function () { if (visible[idx - 1]) actions.openFull(visible[idx - 1].seq); };
    var next = el.querySelector("#fhead-nav-next");
    next.disabled = idx < 0 || idx >= visible.length - 1;
    next.onclick = function () { if (visible[idx + 1]) actions.openFull(visible[idx + 1].seq); };
    return true;
  }

  // Fix round 1, #3: opening the editor from the full view closes it first
  // — otherwise the editor tab exists but sits behind the still-open #full
  // overlay (z-index 20), invisible.
  function goToEditor(actions, entry) {
    actions.closeFull();
    actions.openInEditor(entry);
  }

  function build(el, entry, actions, nowMs, visible, idx, hideDownload) {
    var head = mk("div", "fhead");
    head.appendChild(backBtn(actions));
    head.appendChild(mk("div", "vsep"));
    head.appendChild(mk("span", "kind " + entry.kind, entry.kind));
    var status = F.status(entry);
    head.appendChild(mk("span", "badge s-" + status, IF.statusLabel(status)));
    var when = mk("span", "fwhen", IF.whenAbs(entry.ts, nowMs) + " ");
    var rel = mk("span", null, "· " + F.rel(relSec(entry.ts, nowMs)));
    rel.dataset.ts = entry.ts;
    when.appendChild(rel);
    head.appendChild(when);
    var meta = mk("span", "fmeta");
    meta.appendChild(mk("b", null, entry.who || ""));
    meta.appendChild(document.createTextNode(" · " + (entry.corpus || "") + " · " + F.dur(entry.elapsed_ms) + " · "));
    var rid = IF.requestId(entry);
    var idSpan = mk("span", "mono", rid.text);
    if (rid.title) idSpan.title = rid.title;
    meta.appendChild(idSpan);
    head.appendChild(meta);

    var right = mk("div");
    right.style.cssText = "margin-left:auto;display:flex;gap:8px;align-items:center;flex:none";
    var navCount = mk("span", null, idx >= 0 ? (idx + 1) + " of " + visible.length : "");
    navCount.id = "fhead-nav-count";
    right.appendChild(navCount);
    var prevBtn = navBtn("M15 5l-7 7 7 7", "Newer request (←)", idx <= 0, function () {
      if (visible[idx - 1]) actions.openFull(visible[idx - 1].seq);
    });
    prevBtn.id = "fhead-nav-prev";
    right.appendChild(prevBtn);
    var nextBtn = navBtn("M9 5l7 7-7 7", "Older request (→)", idx < 0 || idx >= visible.length - 1, function () {
      if (visible[idx + 1]) actions.openFull(visible[idx + 1].seq);
    });
    nextBtn.id = "fhead-nav-next";
    right.appendChild(nextBtn);
    right.appendChild(mk("div", "vsep"));
    // Every kind opens in the editor, as in the inspector's acts row (#111).
    var editBtn = mk("button", "ghost", "Open in editor");
    editBtn.type = "button";
    editBtn.addEventListener("click", function () { goToEditor(actions, entry); });
    right.appendChild(editBtn);
    if (entry.result_id != null && !hideDownload) {
      var a = document.createElement("a");
      a.className = "ghost";
      a.href = window.PrismQLApi.jsonlUrl(entry.result_id, true);
      a.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"></path></svg>';
      a.appendChild(document.createTextNode("Download .jsonl"));
      right.appendChild(a);
    }
    head.appendChild(right);
    el.appendChild(head);
  }

  var api = { build: build, patchNav: patchNav };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullHeader = api;
})(typeof window !== "undefined" ? window : globalThis);
