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
  // similar text to /similar. `top` is how many ranked hits the server
  // keeps; `threshold` (similar only) is optional. A field that doesn't
  // read as a number is an error here, never a quietly dropped filter.
  var DEFAULT_TOP = 50;

  function buildRunBody(ed) {
    var kind = ed.kind || "evaluate";
    if (kind === "evaluate") return { endpoint: "evaluate", body: L.buildEvaluateBody(ed) };
    var text = (ed.query || "").trim();
    if (!text) return { error: "type what to search for" };
    var topText = String(ed.top == null ? "" : ed.top).trim();
    var top = topText === "" ? DEFAULT_TOP : Number(topText);
    if (!Number.isInteger(top) || top < 1) return { error: "top must be a whole number of at least 1" };
    var body = kind === "search" ? { query: text, limit: top } : { text: text, limit: top };
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

  var api = { buildRunBody: buildRunBody, DEFAULT_TOP: DEFAULT_TOP, kindInfo: kindInfo };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditorKinds = api;
})(typeof window !== "undefined" ? window : globalThis);
