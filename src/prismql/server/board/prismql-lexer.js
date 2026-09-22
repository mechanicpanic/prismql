/* PrismQL syntax highlighter — one tokenizer for both dialects.
   Shared by the board (/board/) and the demo page; no framework, no build.
   window.PrismQLLexer = { tokenize(src) -> [{c, v}], highlight(src) -> html } */
(function (root) {
  "use strict";

  const KEYWORDS = new Set([
    // classic
    "select", "and", "or", "not",
    "followed_by", "preceded_by", "not_followed_by", "not_preceded_by",
    "inwindow", "inwin", "during", "within",
    "aggregate", "group", "by", "order", "limit", "as", "asc", "desc",
    // pipe stages / aggregates
    "sort", "top", "skip", "count", "sum", "avg", "min", "max",
  ]);
  const UNITS = new Set([
    "h", "m", "s", "d",
    "hour", "hours", "minute", "minutes", "second", "seconds", "day", "days",
    "min", "mins", "sec", "secs",
  ]);

  const isWord = (c) => /[A-Za-z0-9_]/.test(c);

  function tokenize(src) {
    const out = [];
    let i = 0;
    const n = src.length;
    const push = (cls, val) => out.push({ c: cls, v: val });

    while (i < n) {
      const c = src[i];

      if (/\s/.test(c)) {
        let j = i + 1;
        while (j < n && /\s/.test(src[j])) j++;
        push(null, src.slice(i, j));
        i = j;
        continue;
      }

      const three = src.slice(i, i + 3);
      if (three === "!~>" || three === "!<~") { push("arrow", three); i += 3; continue; }
      const two = src.slice(i, i + 2);
      if (two === "~>" || two === "<~" || two === "|>") { push("arrow", two); i += 2; continue; }
      if (c === "+") { push("arrow", c); i += 1; continue; }

      // variable, including the unequal form !$k
      if (c === "$" || (c === "!" && src[i + 1] === "$")) {
        let j = i + (c === "!" ? 2 : 1);
        while (j < n && isWord(src[j])) j++;
        push("var", src.slice(i, j));
        i = j;
        continue;
      }

      if (c === '"') {
        let j = i + 1;
        while (j < n && src[j] !== '"') j++;
        if (j < n) j++;
        push("str", src.slice(i, j));
        i = j;
        continue;
      }

      if (/[0-9]/.test(c)) {
        let j = i + 1;
        while (j < n && /[0-9.]/.test(src[j])) j++;
        while (j < n && /[A-Za-z]/.test(src[j])) j++; // attached unit letters
        push("num", src.slice(i, j));
        i = j;
        continue;
      }

      if (/[A-Za-z_]/.test(c)) {
        let j = i + 1;
        while (j < n && isWord(src[j])) j++;
        const word = src.slice(i, j);
        const lower = word.toLowerCase();
        let k = j;
        while (k < n && /\s/.test(src[k])) k++;
        const followedByParen = src[k] === "(";
        if (KEYWORDS.has(lower)) push("keyword", word);
        else if (followedByParen) push("fn", word);
        else if (UNITS.has(lower)) push("num", word);
        else push(null, word);
        i = j;
        continue;
      }

      if ("(){}[],".indexOf(c) !== -1) { push("punct", c); i += 1; continue; }

      push(null, c);
      i += 1;
    }
    return out;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function highlight(src) {
    let html = "";
    for (const t of tokenize(src)) {
      const esc = escapeHtml(t.v);
      html += t.c ? '<span class="tk-' + t.c + '">' + esc + "</span>" : esc;
    }
    if (src.endsWith("\n")) html += "\n";
    return html;
  }

  root.PrismQLLexer = { tokenize, highlight, escapeHtml };
})(typeof window !== "undefined" ? window : globalThis);
