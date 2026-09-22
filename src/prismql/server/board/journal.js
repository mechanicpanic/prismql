// PrismQLJournal: the rail filters and the journal list (graph
// @aleph/prismql, node #63). Stub for Task 3 — the shell only; a later task
// fills #journal-list and #rail from PrismQLApi.activity/stream.
(function (root) {
  "use strict";

  function mount() {}

  const api = { mount: mount };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLJournal = api;
})(typeof window !== "undefined" ? window : globalThis);
