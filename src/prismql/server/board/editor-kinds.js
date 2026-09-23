// PrismQLEditorKinds: what differs between the editor's three kinds of
// request — a query (/evaluate), a search (/search, tantivy syntax) and a
// similar text (/similar) — as pure data and one body builder (graph
// @aleph/prismql, #111). No DOM, unit-tested under node.
(function (root) {
  "use strict";
  var L = typeof module === "object" && module.exports
    ? require("./editor-logic.js")
    : root.PrismQLEditorLogic;

  // The editor runs all three kinds of request (graph @aleph/prismql,
  // #111): a query to /evaluate, a search (tantivy syntax) to /search, a
  // similar text to /similar with an optional threshold. No limit is sent:
  // the server keeps its scout depth either way and the board pages the
  // kept result, so a limit would only size a first page nobody sees (#65).
  // A threshold that doesn't read as a number is an error here, never a
  // quietly dropped filter.
  function buildRunBody(ed) {
    var kind = ed.kind || "evaluate";
    if (kind === "evaluate") return { endpoint: "evaluate", body: L.buildEvaluateBody(ed) };
    var text = (ed.query || "").trim();
    if (!text) return { error: "type what to search for" };
    var body = kind === "search" ? { query: text } : { text: text };
    if (kind === "similar") {
      var thText = String(ed.threshold == null ? "" : ed.threshold).trim();
      if (thText !== "") {
        var th = Number(thText);
        if (!isFinite(th) || th < -1 || th > 1) return { error: "threshold must be a number between -1 and 1" };
        body.threshold = th;
      }
    }
    if (ed.corpus) body.corpus = ed.corpus;
    return { endpoint: kind, body: body };
  }

  var KIND_INFO = {
    evaluate: { label: "Query", running: "Evaluating", start: "SELECT ", highlight: true,
      placeholder: "" },
    search: { label: "Search", running: "Searching", start: "", highlight: false,
      placeholder: "words, \"a phrase\", field:term, prefix* — AND / OR / NOT" },
    similar: { label: "Similar", running: "Finding similar", start: "", highlight: false,
      placeholder: "a sentence; events are ranked by meaning, not words" },
  };

  function kindInfo(kind) { return KIND_INFO[kind] || KIND_INFO.evaluate; }

  var api = { buildRunBody: buildRunBody, kindInfo: kindInfo };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorKinds = api;
})(typeof window !== "undefined" ? window : globalThis);
