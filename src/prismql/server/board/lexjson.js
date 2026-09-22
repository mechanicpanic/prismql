// PrismQLLexJson: JSON syntax tokenizer for the board's result viewer.
// Ported from the Claude Design canvas (docs/superpowers/specs/board-design/
// Main.dc.html, lexJson ≈ lines 542-552). Split out of format.js to keep
// that file under its line budget (graph @aleph/prismql, node #76).
// Plain ES2020, no dependencies, no DOM access.
(function (root) {
  function lexJson(text) {
    var out = [];
    // Built from parts (not one long literal) to stay under 100 chars per
    // line; .source reproduces each alternative exactly, so joining with
    // "|" is byte-for-byte the original pattern — same groups, same order.
    var STR = /("(?:[^"\\]|\\.)*")(\s*:)?/;
    var NUM = /(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/;
    var KEY = /(true|false|null)/;
    var PUNCT = /([{}[\],:])/;
    var WS = /(\s+)/;
    var ANY = /([\s\S])/;
    var parts = [STR, NUM, KEY, PUNCT, WS, ANY];
    var re = new RegExp(parts.map(function (p) { return p.source; }).join("|"), "g");
    var m;
    while ((m = re.exec(text))) {
      if (m[1]) {
        out.push({ t: m[1], c: m[2] ? "tk-fn" : "tk-str" });
        if (m[2]) out.push({ t: ": ", c: "tk-punct" });
      } else if (m[3]) {
        out.push({ t: m[3], c: "tk-num" });
      } else if (m[4]) {
        out.push({ t: m[4], c: "tk-keyword" });
      } else if (m[5]) {
        out.push({ t: m[5] === "," ? ", " : m[5] === ":" ? ": " : m[5], c: "tk-punct" });
      } else {
        out.push({ t: m[0], c: "" });
      }
    }
    return out;
  }

  var api = { lexJson: lexJson };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLLexJson = api;
})(typeof window !== "undefined" ? window : globalThis);
