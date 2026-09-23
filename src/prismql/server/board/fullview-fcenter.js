// PrismQLFullFcenter: the full view's `.fcenter` — the summary-only body
// for aggregate/grouped/file/error/empty results (split out of
// fullview-header.js to stay under the 150-line budget; graph
// @aleph/prismql, node #76).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var PL = window.PrismQLInspectorPageLogic;

  // Fix round 1, #3: opening the editor from the full view closes it first
  // — otherwise the editor tab exists but sits behind the still-open #full
  // overlay (z-index 20), invisible.
  function goToEditor(actions, entry) {
    actions.closeFull();
    actions.openInEditor(entry);
  }

  function build(entry, outputKind, actions) {
    var box = mk("div", "fcenter");
    if (outputKind === "aggregate") {
      box.appendChild(mk("div", "huge", PL.aggregateValueText(entry.value)));
      box.appendChild(mk("div", "lbl", "the aggregate value"));
    } else if (outputKind === "grouped") {
      box.appendChild(mk("div", "huge", typeof entry.count === "number" ? String(entry.count) : "—"));
      box.appendChild(mk("div", "lbl", "groups"));
    } else if (outputKind === "error") {
      var errbox = mk("div", "errbox");
      errbox.appendChild(mk("div", "m", (entry.error && entry.error.message) || ""));
      var err = entry.error || {}, where = "";
      if (err.line != null) where += "line " + err.line;
      if (err.column != null) where += (where ? ", " : "") + "column " + err.column;
      if (where) errbox.appendChild(mk("div", "p", where));
      box.appendChild(errbox);
      // Round 2 (found in verification): only evaluate has query text to
      // fix — same rule as the header's own "Open in editor" nav button.
      if (entry.kind === "evaluate") {
        var fixBtn = mk("button", "primary", "Fix in editor");
        fixBtn.type = "button";
        fixBtn.addEventListener("click", function () { goToEditor(actions, entry); });
        box.appendChild(fixBtn);
      }
    } else if (outputKind === "file") {
      var file = mk("div", "file");
      file.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"></path><path d="M14 3v4h4"></path></svg>';
      var span = document.createElement("span");
      span.appendChild(document.createTextNode("Written to "));
      span.appendChild(mk("code", null, entry.path || ""));
      file.appendChild(span);
      box.appendChild(file);
      box.appendChild(mk("div", "lbl", "The board keeps no preview of file output."));
    } else {
      box.appendChild(mk("strong", null, "No matches"));
      box.appendChild(mk("div", "lbl", "The request ran cleanly and found nothing."));
    }
    return box;
  }

  var api = { build: build };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullFcenter = api;
})(typeof window !== "undefined" ? window : globalThis);
