// PrismQLEditor: the query editor pane, highlighted with prismql-lexer.js
// (graph @aleph/prismql, node #63). Stub for Task 3 — the shell only; a
// later task wires it to PrismQLApi.evaluate.
(function (root) {
  "use strict";

  function mount() {}
  function run() {}

  const api = { mount: mount, run: run };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLEditor = api;
})(typeof window !== "undefined" ? window : globalThis);
