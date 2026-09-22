// PrismQLFull: the #full overlay (timeline, table, raw JSONL) for a
// journal row's result (graph @aleph/prismql, node #63). Stub for Task 3 —
// the shell only; a later task fills #full from PrismQLApi.page/jsonlUrl
// and adds a render(state, actions) that board.js's dispatcher will pick
// up automatically (fix round 1, #9 — named PrismQLFull, not Fullview, to
// match the plan Task 7 was written against).
(function (root) {
  "use strict";

  function open() {}
  function close() {}

  const api = { open: open, close: close };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFull = api;
})(typeof window !== "undefined" ? window : globalThis);
