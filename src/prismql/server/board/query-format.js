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

  // The query cut where each link of a top-level chain starts, each piece
  // with the number of the event its link gave (``slots``, from the server:
  // graph @aleph/prismql, #85; null for a NOT_ link). Null when the text's
  // links and the layout disagree — then the board shows no numbers.
  var SEQ = {
    followed_by: 1, preceded_by: 1, not_followed_by: 1, not_preceded_by: 1,
    followedby: 1, precededby: 1, notfollowedby: 1, notprecededby: 1,
  };
  var SEQ_ARROWS = { "~>": 1, "<~": 1, "!~>": 1, "!<~": 1 };
  function numberedLegs(src, slots, lexer) {
    lexer = lexer || root.PrismQLLexer;
    // the board's lexer has no single-quoted strings: a link word or a
    // parenthesis inside one would move a number — show none instead
    if (!src || !lexer || !slots || !slots.length || src.indexOf("'") !== -1) return null;
    var toks = lexer.tokenize(src), starts = [], at = 0, depth = 0, open = true, win = false;
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i], w = t.v.toLowerCase(), blank = /^\s+$/.test(t.v);
      // a pipe link's own window, `~>(5)`, is not where its link starts
      var skip = win && t.c === "punct" && t.v === "(";
      if (!blank) win = false;
      if (depth === 0 && open && !blank && !skip && !(t.c === "keyword" && w === "select")) {
        starts.push(at);
        open = false;
      }
      if (t.c === "punct" && t.v === "(") depth++;
      if (t.c === "punct" && t.v === ")") depth = Math.max(0, depth - 1);
      if (depth === 0 && ((t.c === "keyword" && SEQ[w]) || (t.c === "arrow" && SEQ_ARROWS[t.v]))) {
        open = true;
        win = t.c === "arrow";
      }
      at += t.v.length;
    }
    if (starts.length !== slots.length) return null;
    var pieces = [{ text: src.slice(0, starts[0]), n: null }];
    for (var k = 0; k < starts.length; k++) {
      pieces.push({ text: src.slice(starts[k], k + 1 < starts.length ? starts[k + 1] : src.length), n: slots[k] });
    }
    return pieces;
  }

  // The query highlighted, a link's event number ①② in front of it.
  function numberedHtml(src, slots, lexer) {
    lexer = lexer || root.PrismQLLexer;
    var pieces = numberedLegs(src, slots, lexer);
    if (!pieces) return lexer.highlight(src);
    return pieces.map(function (p) {
      var no = p.n == null ? "" : '<span class="slotno" title="event ' + p.n + ' of each group">'
        + (p.n <= 20 ? String.fromCharCode(0x245f + p.n) : "(" + p.n + ")") + "</span>";
      return no + lexer.highlight(p.text);
    }).join("");
  }

  var api = { breakLines: breakLines, formatQuery: formatQuery, numberedLegs: numberedLegs, numberedHtml: numberedHtml };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLQueryFormat = api;
})(typeof window !== "undefined" ? window : globalThis);
