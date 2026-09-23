// PrismQLQueryFormat: line breaks for reading a query (graph @aleph/prismql,
// node #84) — a link, a window, a clause or a pipe stage starts its own line,
// at the top level only (never inside parentheses or strings). A query the
// author already broke into lines is left as written. Tokens come from the
// shared lexer; this module never changes what the query means, only where
// its whitespace falls. Tested by tests/board/query-format.test.mjs.
(function (root) {
  "use strict";
  var LINKS = { followed_by: 1, preceded_by: 1, not_followed_by: 1, not_preceded_by: 1, aggregate: 1, limit: 1 };
  var PAIRED = { group: "by", order: "by" }; // GROUP BY, ORDER BY
  var WINDOWS = { inwindow: 1, inwin: 1, during: 1, within: 1 };
  var PIPE_LINKS = { "~>": 1, "<~": 1, "!~>": 1, "!<~": 1, "|>": 1 };

  function nextWord(toks, i) {
    for (var j = i + 1; j < toks.length; j++) {
      if (!/^\s+$/.test(toks[j].v)) return toks[j].v.toLowerCase();
    }
    return "";
  }

  function breakFor(t, toks, i, prev) {
    var w = t.v.toLowerCase();
    if (prev && prev.c === "arrow" && prev.v === "|>") return null; // |> within(5)
    if (t.c === "keyword" && LINKS[w]) return "\n";
    if (t.c === "keyword" && PAIRED[w] && nextWord(toks, i) === PAIRED[w]) return "\n";
    if (t.c === "keyword" && WINDOWS[w]) return "\n  ";
    if (t.c === "arrow" && PIPE_LINKS[t.v]) return "\n";
    return null;
  }

  function breakLines(src, lexer) {
    lexer = lexer || root.PrismQLLexer;
    if (!src || !lexer || src.indexOf("\n") !== -1) return src;
    var toks = lexer.tokenize(src);
    var out = [];
    var depth = 0;
    var prev = null; // the last token that is not whitespace
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i];
      var brk = depth === 0 && out.length ? breakFor(t, toks, i, prev) : null;
      if (!/^\s+$/.test(t.v)) prev = t;
      if (t.c === "punct" && t.v === "(") depth++;
      if (t.c === "punct" && t.v === ")") depth = Math.max(0, depth - 1);
      if (brk) {
        while (out.length && /^\s+$/.test(out[out.length - 1])) out.pop();
        out.push(brk);
      }
      out.push(t.v);
    }
    return out.join("");
  }

  // The editor's Format button: the author asked, so their own line breaks
  // give way — whitespace outside strings collapses, then the breaks apply.
  function formatQuery(src, lexer) {
    lexer = lexer || root.PrismQLLexer;
    if (!src || !lexer) return src;
    var flat = lexer.tokenize(src.trim()).map(function (t) {
      return /^\s+$/.test(t.v) ? " " : t.v;
    }).join("");
    return breakLines(flat, lexer);
  }

  var api = { breakLines: breakLines, formatQuery: formatQuery };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLQueryFormat = api;
})(typeof window !== "undefined" ? window : globalThis);
