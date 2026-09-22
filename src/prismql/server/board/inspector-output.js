// PrismQLInspectorOutput: the inspector's "output" section — the `.sect`
// header (title, note, full-view button) plus the type-specific body
// (graph @aleph/prismql, node #63; task-5 brief). Groups/named and hits
// need a paged fetch and live in inspector-groups.js/inspector-hits.js;
// everything else here is derived straight from the journal entry.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var IF = window.PrismQLInspectorFormat;

  var TITLE = {
    error: "Error", file: "Output", aggregate: "Value",
    groups: "Groups", hits: "Hits", grouped: "Groups", empty: "Result",
  };

  function big(value, label) {
    var body = document.createElement("div");
    var b = mk("div", "big");
    b.appendChild(mk("b", null, value));
    if (label) b.appendChild(mk("span", null, label));
    body.appendChild(b);
    return { note: "", body: body };
  }

  function renderFile(entry) {
    var body = document.createElement("div");
    var file = mk("div", "file");
    file.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h8l4 4v14H6z"></path><path d="M14 3v4h4"></path></svg>';
    var span = document.createElement("span");
    span.appendChild(document.createTextNode("Written to "));
    span.appendChild(mk("code", null, entry.path || ""));
    file.appendChild(span);
    body.appendChild(file);
    return { note: "", body: body };
  }

  function renderError(entry) {
    var body = document.createElement("div");
    var box = mk("div", "errbox");
    box.appendChild(mk("div", "m", (entry.error && entry.error.message) || ""));
    var err = entry.error || {};
    var where = "";
    if (err.line != null) where += "line " + err.line;
    if (err.column != null) where += (where ? ", " : "") + "column " + err.column;
    if (where) box.appendChild(mk("div", "p", where));
    body.appendChild(box);
    return { note: "", body: body };
  }

  function renderEmpty() {
    var body = document.createElement("div");
    var empty = mk("div", "empty"); empty.style.padding = "24px";
    empty.appendChild(mk("strong", null, "No matches"));
    empty.appendChild(mk("span", null, "The request ran cleanly and found nothing."));
    body.appendChild(empty);
    return { note: "", body: body };
  }

  function buildSect(title, note, entry, actions) {
    var el = mk("div", "sect");
    el.appendChild(document.createTextNode(title));
    el.appendChild(mk("span", "push", note || ""));
    var btn = mk("button", "iconbtn sm");
    btn.type = "button";
    btn.setAttribute("aria-label", "Open output full screen");
    btn.title = "Full view";
    btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"></path></svg>';
    btn.addEventListener("click", function () { actions.openFull(entry.seq); });
    el.appendChild(btn);
    return el;
  }

  function render(wrap, entry, state, actions) {
    var kind = IF.outputKind(entry);
    var result;
    if (kind === "groups") result = window.PrismQLInspectorGroups.render(entry, state, actions);
    else if (kind === "hits") result = window.PrismQLInspectorHits.render(entry, state, actions);
    else if (kind === "aggregate") result = big(entry.value != null ? String(entry.value) : "—");
    else if (kind === "grouped") result = big(typeof entry.count === "number" ? String(entry.count) : "—", "groups");
    else if (kind === "file") result = renderFile(entry);
    else if (kind === "error") result = renderError(entry);
    else result = renderEmpty();
    wrap.appendChild(buildSect(TITLE[kind] || "Result", result.note, entry, actions));
    wrap.appendChild(result.body);
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorOutput = api;
})(typeof window !== "undefined" ? window : globalThis);
