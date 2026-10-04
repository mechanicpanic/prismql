// PrismQLExplainFormat: an event's explanation (graph @aleph/prismql, #119)
// as the board shows it — the matched spans of its text marked, the
// similarity scores, and terms matched in fields the board does not show.
// Pure, unit-tested under node.
(function (root) {
  "use strict";

  // The text split into {t, m} parts, m = inside a matched span. Spans come
  // from the server's offsets on the `text` field; overlaps merge. The
  // server counts characters (code points), JS strings count UTF-16 units:
  // the text is cut as an array of code points, or every emoji before a
  // match would shift its mark.
  function textParts(text, why) {
    var chars = Array.from(text == null ? "" : String(text));
    text = { length: chars.length, slice: function (a, b) { return chars.slice(a, b).join(""); } };
    var spans = [];
    (why || []).forEach(function (p) {
      (p.matches || []).forEach(function (m) {
        if (m.field === "text" && m.end > m.start && m.end <= text.length) spans.push([m.start, m.end]);
      });
    });
    if (!spans.length) return [{ t: text.slice(0), m: false }];
    spans.sort(function (a, b) { return a[0] - b[0] || a[1] - b[1]; });
    var merged = [spans[0].slice()];
    for (var i = 1; i < spans.length; i++) {
      var last = merged[merged.length - 1];
      if (spans[i][0] <= last[1]) last[1] = Math.max(last[1], spans[i][1]);
      else merged.push(spans[i].slice());
    }
    var parts = [], at = 0;
    merged.forEach(function (s) {
      if (s[0] > at) parts.push({ t: text.slice(at, s[0]), m: false });
      parts.push({ t: text.slice(s[0], s[1]), m: true });
      at = s[1];
    });
    if (at < text.length) parts.push({ t: text.slice(at), m: false });
    return parts;
  }

  // "0.612" for each similar_to the event satisfies.
  function scores(why) {
    return (why || []).filter(function (p) { return p.score != null; })
      .map(function (p) { return Number(p.score).toFixed(3); });
  }

  // Terms that matched outside `text` ("content: sign in"), which the
  // marked text cannot show.
  function elsewhere(why) {
    var out = [];
    (why || []).forEach(function (p) {
      (p.matches || []).forEach(function (m) {
        if (m.field !== "text") out.push(m.field + ": " + m.term);
      });
    });
    return out;
  }

  // What the engine bound the query's $variables to in one group (graph
  // @aleph/prismql, #167, #173): "$a = ann, $y = bob"; several assignments
  // "·"-joined, at most three shown. null is the engine binding nothing for
  // this group (a subquery's stages), said so; no field (a query without
  // variables) and [] read "".
  function bindingsText(bindings, truncated) {
    if (bindings === null) return "variables not bound in this group";
    if (!bindings || !bindings.length) return "";
    var one = function (a) {
      return Object.keys(a).sort().map(function (k) { return "$" + k + " = " + a[k]; }).join(", ");
    };
    var shown = bindings.slice(0, 3).map(one).join("  ·  ");
    var more = bindings.length - 3;
    if (truncated) shown += "  ·  +" + Math.max(more, 0) + " or more";
    else if (more > 0) shown += "  ·  +" + more + " more";
    return shown;
  }

  var api = { textParts: textParts, scores: scores, elsewhere: elsewhere, bindingsText: bindingsText };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLExplainFormat = api;
})(typeof window !== "undefined" ? window : globalThis);
