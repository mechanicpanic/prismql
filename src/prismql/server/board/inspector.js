// PrismQLInspector: the Request/Editor tabs beside the journal (graph
// @aleph/prismql, node #63). Stub for Task 3 — the shell only; a later task
// fills #inspector-pane from the selected journal row.
(function (root) {
  "use strict";

  function mount() {}
  function show() {}

  const api = { mount: mount, show: show };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspector = api;
})(typeof window !== "undefined" ? window : globalThis);
