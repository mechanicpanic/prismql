// PrismQLInspectorDetail: the inspector's actions row and kv list — split
// out of inspector.js to stay under the 150-line budget (graph
// @aleph/prismql, node #63; task-5 brief).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;
  var UI = window.PrismQLInspectorUI;
  var L = window.PrismQLEditorLogic;

  function actBtn(label, icon, onClick, title) {
    var btn = mk("button", "ghost");
    btn.type = "button";
    if (title) btn.title = title;
    btn.innerHTML = icon;
    btn.appendChild(document.createTextNode(label));
    btn.addEventListener("click", onClick);
    return btn;
  }
  var ICON_EDIT = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20h4L19 9l-4-4L4 16z"></path></svg>';
  var ICON_RERUN = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 1 1-2.3-5.6M20 4v5h-5"></path></svg>';
  var ICON_FILE = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"></path></svg>';

  // "Open in editor" is offered for every kind: the editor runs queries,
  // searches and similars alike (#111). A request
  // that carried its own dictionaries can't be replayed by either path (the
  // board never held their terms), so "Run again" is disabled with a
  // visible note; "Open in editor" stays offered, with the same note, so
  // the query text is still reachable.
  function buildActs(wrap, entry, actions, state) {
    var acts = mk("div", "acts");
    acts.appendChild(actBtn("Full view", UI.ICON_FULL, function () { actions.openFull(entry.seq); }, "Open the output full screen (Enter)"));
    var dictBlocked = L.hasRequestDictionaries(entry);
    acts.appendChild(actBtn("Open in editor", ICON_EDIT, function () { actions.openInEditor(entry); }));
    var rerunBtn = actBtn("Run again", ICON_RERUN, function () { actions.rerun(entry); });
    if (dictBlocked) { rerunBtn.disabled = true; rerunBtn.title = L.DICT_NOTE; }
    acts.appendChild(rerunBtn);
    if (entry.result_id != null) {
      var a = document.createElement("a");
      a.className = "ghost";
      a.style.marginLeft = "auto";
      a.href = window.PrismQLApi.jsonlUrl(entry.result_id, true);
      a.innerHTML = ICON_FILE;
      a.appendChild(document.createTextNode(".jsonl"));
      acts.appendChild(a);
    }
    wrap.appendChild(acts);
    if (dictBlocked) wrap.appendChild(mk("div", "dict-note", L.DICT_NOTE));
    // Round 2, #4: a search/similar rerun's failure, surfaced — never
    // fire-and-forget. Keyed by seq so it only shows for the entry it
    // actually answers, and clears itself once that stops matching.
    var err = state && state.rerunError;
    if (err && err.seq === entry.seq) wrap.appendChild(mk("div", "inline-err", err.message));
  }

  function addKv(dl, label, fill, cls) {
    dl.appendChild(mk("dt", null, label));
    var dd = document.createElement("dd");
    if (cls) dd.className = cls;
    if (typeof fill === "function") fill(dd);
    else dd.textContent = fill;
    dl.appendChild(dd);
  }

  function buildKv(wrap, entry) {
    var dl = document.createElement("dl");
    dl.className = "kv";
    addKv(dl, "Source", function (dd) {
      dd.appendChild(document.createTextNode(entry.who || ""));
      var s = mk("span", null, " · " + IF.srcKind(entry.who));
      s.style.color = "var(--faint)";
      dd.appendChild(s);
    });
    addKv(dl, "Corpus", entry.corpus || "");
    addKv(dl, "Received", IF.localDateTime(entry.ts), "mono");
    addKv(dl, "Duration", F.dur(entry.elapsed_ms), "mono");
    addKv(dl, "Result", F.resultLabel(entry));
    wrap.appendChild(dl);
  }

  var api = { buildActs: buildActs, buildKv: buildKv };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorDetail = api;
})(typeof window !== "undefined" ? window : globalThis);
