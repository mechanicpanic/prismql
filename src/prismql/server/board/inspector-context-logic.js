// PrismQLContextLogic: what the inspector's "context" asks the server for
// (GET /context, graph @aleph/prismql, #120) and how an answer's rows read.
// Pure, unit-tested under node; inspector-context.js does the DOM.
(function (root) {
  "use strict";

  var MINUTES = 10;

  // Same actor when the corpus names one (the board's `actor` field) and
  // the view asks for it; otherwise every event.
  function params(corpus, id, actorField, sameActor) {
    var p = { corpus: corpus, id: String(id), minutes: String(MINUTES) };
    if (sameActor && actorField) p.same = actorField;
    return p;
  }

  function key(p) {
    return [p.corpus, p.id, p.same || "", p.minutes].join("|");
  }

  // "-3" … "0" … "+2": the row's place relative to the event asked about.
  function offsetLabel(offset) {
    if (offset === 0) return "0";
    return (offset > 0 ? "+" : "") + String(offset);
  }

  function heading(body, actorField, sameActor) {
    var who = sameActor && body.same_value != null
      ? actorField + " " + body.same_value
      : "all events";
    var n = body.events ? body.events.length - 1 : 0;
    return "±" + MINUTES + " min · " + who + " · " + n + (n === 1 ? " neighbour" : " neighbours");
  }

  var api = { MINUTES: MINUTES, params: params, key: key, offsetLabel: offsetLabel, heading: heading };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLContextLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
