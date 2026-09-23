// PrismQLInspectorFormat: pure helpers for the inspector's detail pane
// (graph @aleph/prismql, node #63) — kept separate from format.js (already
// at its 150-line budget) and from inspector.js/inspector-output.js (DOM
// code) so these stay unit-testable without a fake window.
(function (root) {
  "use strict";
  var F = typeof module === "object" && module.exports
    ? require("./format.js")
    : root.PrismQLFormat;

  var STATUS_LABEL = { ok: "ok", capped: "capped", error: "failed", empty: "no matches" };

  function pad(n) { return String(n).padStart(2, "0"); }

  // Local "YYYY-MM-DD HH:MM:SS" — the kv list's "Received" and each
  // chain event's time (design canvas's `d.iso` / `e.time`).
  function localDateTime(iso) {
    var d = new Date(iso);
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + F.hms(iso);
  }

  // "Wed 23 Sep, 15:15:34" — the header's absolute "when".
  function whenAbs(iso, nowMs) {
    return F.dayLabel(iso, nowMs).sub + ", " + F.hms(iso);
  }

  // "board" is a person via the board's own editor; any other non-agent
  // "who" (an IP address) is a person reaching the server directly
  // (global-constraints.md: "A human's source is board").
  function srcKind(who) {
    if (who === "board") return "person, via board";
    return F.isAgent(who) ? "agent" : "person";
  }

  function statusLabel(status) { return STATUS_LABEL[status] || status; }

  // Which output section a journal entry needs, resolved from the entry
  // alone (no fetch) — "file" and "aggregate"/"empty" never need a page;
  // "groups"/"hits" still need one, fetched by the caller.
  function outputKind(entry) {
    if (entry.ok === false) return "error";
    if (entry.output === "file") return "file";
    if (entry.result === "aggregate") return "aggregate";
    if (entry.result === "hits") return entry.count === 0 ? "empty" : "hits";
    if (entry.result === "groups" || entry.result === "named") {
      return entry.total === 0 ? "empty" : "groups";
    }
    if (entry.result === "grouped") return "grouped";
    return "empty";
  }

  // "+<Δt> · <Δpos-1> events between" (global-constraints.md); either half
  // is dropped when its inputs are null.
  function gapText(prevPos, pos, prevTime, time) {
    var g = F.gapLabel(prevPos, pos, prevTime, time);
    if (g.plus && g.label) return g.plus + " · " + g.label;
    return g.plus || g.label || "";
  }

  // A request's name on the board is its journal #seq; result_id only keys
  // stored results (groups/hits), so it rides along as a tooltip.
  function requestId(entry) {
    return {
      text: "#" + entry.seq,
      title: entry.result_id != null ? "result " + entry.result_id : "",
    };
  }

  var api = {
    requestId: requestId,
    localDateTime: localDateTime, whenAbs: whenAbs, srcKind: srcKind,
    statusLabel: statusLabel, outputKind: outputKind, gapText: gapText,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorFormat = api;
})(typeof window !== "undefined" ? window : globalThis);
