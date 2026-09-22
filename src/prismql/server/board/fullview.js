// PrismQLFullview: the #full overlay (timeline, table, raw JSONL) for a
// journal row's result (graph @aleph/prismql, node #63). Stub for Task 3 —
// the shell only; a later task fills #full from PrismQLApi.page/jsonlUrl.
(function (root) {
  "use strict";

  function open() {}
  function close() {}

  const api = { open: open, close: close };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullview = api;
})(typeof window !== "undefined" ? window : globalThis);
