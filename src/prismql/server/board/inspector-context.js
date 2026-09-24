// PrismQLInspectorContext: the "context" button on an event and the list of
// its neighbours it opens — the same actor within ten minutes before and
// after, or every event (graph @aleph/prismql, #120). State lives here, not
// in the DOM, so an open list survives the inspector's re-renders.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var C = window.PrismQLContextLogic;
  var IF = window.PrismQLInspectorFormat;

  var open = {};  // event key -> {sameActor}
  var cache = {}; // request key -> {status, body|error}

  function eventKey(corpus, id) { return corpus + "|" + String(id); }
  function rerender() { if (window.PrismQLBoard) window.PrismQLBoard.render(); }

  function fetchContext(p) {
    return fetch("/context?" + new URLSearchParams(p).toString(), {
      headers: { "X-PrismQL-Client": "board" },
    }).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (body) {
        return { status: r.status, body: body };
      });
    });
  }

  var RETRY_MS = 10000; // a failure (429, network) is retried, not kept

  function load(p) {
    var k = C.key(p);
    var hit = cache[k];
    if (hit && !(hit.status === "error" && Date.now() - hit.at > RETRY_MS)) return hit;
    var rec = { status: "loading" };
    cache[k] = rec;
    fetchContext(p).then(function (res) {
      if (res.status === 200 && res.body && res.body.ok) { rec.status = "done"; rec.body = res.body; }
      else { rec.status = "error"; rec.at = Date.now(); rec.error = (res.body && res.body.error && res.body.error.message) || "HTTP " + res.status; }
      rerender();
    }).catch(function (e) { rec.status = "error"; rec.at = Date.now(); rec.error = String((e && e.message) || e); rerender(); });
    return rec;
  }

  // The toggle that sits on an event's line.
  function button(corpus, id) {
    var k = eventKey(corpus, id);
    var btn = mk("button", "ctxbtn" + (open[k] ? " on" : ""), "context");
    btn.type = "button";
    btn.title = "Events around this one, ±" + C.MINUTES + " min";
    btn.setAttribute("aria-expanded", open[k] ? "true" : "false");
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      if (open[k]) delete open[k];
      else open[k] = { sameActor: true };
      rerender();
    });
    return btn;
  }

  function row(ev, board) {
    var r = mk("div", "ctxrow" + (ev.offset === 0 ? " here" : ""));
    r.appendChild(mk("span", "o", C.offsetLabel(ev.offset)));
    var t = mk("span", "t", ev.time ? window.PrismQLFormat.hms(ev.time) : "");
    if (ev.time) t.title = IF.localDateTime(ev.time);
    r.appendChild(t);
    var e = ev.event || {};
    var what = mk("span", "w");
    if (board.kind && e[board.kind] != null) what.appendChild(mk("span", "k", String(e[board.kind])));
    if (board.actor && e[board.actor] != null) what.appendChild(mk("span", "a", String(e[board.actor])));
    r.appendChild(what);
    var text = e.text != null ? String(e.text) : "";
    var x = mk("span", "x", text);
    x.title = text;
    r.appendChild(x);
    return r;
  }

  // The list under an open event, or null when it is closed.
  function block(corpus, id, board) {
    var k = eventKey(corpus, id);
    var st = open[k];
    if (!st) return null;
    var p = C.params(corpus, id, board.actor, st.sameActor);
    var rec = load(p);
    var wrap = mk("div", "ctx");
    var head = mk("div", "ctxhead");
    head.appendChild(mk("span", null, rec.status === "done" ? C.heading(rec.body, board.actor, st.sameActor) : "±" + C.MINUTES + " min"));
    if (board.actor) {
      var sw = mk("button", "ghost", st.sameActor ? "all events" : "same " + board.actor);
      sw.type = "button";
      sw.addEventListener("click", function () { st.sameActor = !st.sameActor; rerender(); });
      head.appendChild(sw);
    }
    wrap.appendChild(head);
    if (rec.status === "loading") wrap.appendChild(mk("div", "ctxnote", "loading…"));
    else if (rec.status === "error") wrap.appendChild(mk("div", "ctxnote err", rec.error));
    else rec.body.events.forEach(function (ev) { wrap.appendChild(row(ev, board)); });
    return wrap;
  }

  // A server restart makes positions and ids of the old load meaningless
  // (board-stream.js calls this when the boot id changes).
  function clear() { cache = {}; }

  var api = { button: button, block: block, clear: clear };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorContext = api;
})(typeof window !== "undefined" ? window : globalThis);
