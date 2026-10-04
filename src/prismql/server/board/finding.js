// PrismQLFinding: one journal entry as a finding anyone can rerun — the
// corpus, the query, what it found and a ready curl to the same server — in
// Markdown for a writeup or a report (graph @aleph/prismql, #174). Pure.
(function (root) {
  "use strict";

  function shellQuote(s) {
    return "'" + String(s).replace(/'/g, "'\\''") + "'";
  }

  function countLine(entry) {
    if (entry.result === "aggregate" || entry.value != null) return "value " + JSON.stringify(entry.value);
    var n = entry.total != null ? entry.total : entry.count;
    return n == null ? "" : n + (n === 1 ? " group" : " groups");
  }

  function findingMarkdown(entry, origin) {
    var title = entry.label ? entry.label : "Finding";
    var found = countLine(entry);
    var head = "**" + title + "** — corpus `" + entry.corpus + "`" + (found ? ", " + found : "")
      + (entry.ts ? " (" + String(entry.ts).slice(0, 16).replace("T", " ") + " UTC)" : "");
    var body = { query: entry.query, corpus: entry.corpus };
    // A reader reruns against their own server, never this one: the
    // address is a variable, the corpus is named, ours is a comment.
    var curl = "curl -s \"$PRISMQL_SERVER_URL/evaluate\" -H 'content-type: application/json' "
      + "-H 'X-PrismQL-Client: <your name>' -d " + shellQuote(JSON.stringify(body));
    var lines = [head, "", "```prismql", entry.query, "```", "",
      "Rerun on a PrismQL server with the `" + entry.corpus + "` corpus loaded:", "", "```bash",
      "# PRISMQL_SERVER_URL: that server's address (ours was " + origin + ")", curl, "```"];
    if (entry.seq != null) lines.push("", "On our board: " + origin + "/board/#q" + entry.seq);
    return lines.concat([""]).join("\n");
  }

  var api = { findingMarkdown: findingMarkdown, shellQuote: shellQuote };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFinding = api;
})(typeof window !== "undefined" ? window : globalThis);
