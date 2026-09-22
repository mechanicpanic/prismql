// PrismQLInspectorGroups: the chain view for groups/named results — group
// titles, gap lines and per-slot event cards, paged 2 at a time with "Show
// 2 more" (graph @aleph/prismql, node #63; task-5 brief, fix round 1).
// Fetching, the corpora-readiness gate and the shared blocker blocks
// (gone/error/loading) live in inspector-fetch.js.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var F = window.PrismQLFormat;
  var IF = window.PrismQLInspectorFormat;
  var UI = window.PrismQLInspectorUI;
  var PL = window.PrismQLInspectorPageLogic;
  var PF = window.PrismQLInspectorFetch;

  // "Show 2 more" only advances how many groups THIS seq wants shown; a
  // fresh selection starts back at 2 (design canvas's `select()`).
  var shown = { seq: null, n: 2 };
  function shownFor(seq) {
    if (shown.seq !== seq) {
      shown.seq = seq;
      shown.n = 2;
    }
    return shown.n;
  }
  function bumpShown(seq) {
    if (shown.seq !== seq) return;
    shown.n += 2;
    if (window.PrismQLBoard) window.PrismQLBoard.render();
  }

  function evDiv(n, event, timeIso, board) {
    var div = mk("div", "ev");
    div.appendChild(mk("div", "n", String(n)));
    var right = document.createElement("div");
    right.style.minWidth = "0";
    var l = mk("div", "l");
    UI.kindActorSpans(l, event, board);
    l.appendChild(mk("span", "t", timeIso ? IF.localDateTime(timeIso) : ""));
    right.appendChild(l);
    var text = event && event.text;
    if (text) right.appendChild(mk("div", "x", String(text)));
    div.appendChild(right);
    return div;
  }
  function gapDiv(prevPos, pos, prevTime, time) {
    var div = mk("div", "gapl");
    div.appendChild(document.createElement("i"));
    div.appendChild(mk("span", null, IF.gapText(prevPos, pos, prevTime, time)));
    return div;
  }
  function chainDiv(g, i, board) {
    var div = mk("div", "chain");
    var title = mk("div", "gtitle");
    title.appendChild(mk("span", null, "group " + (i + 1)));
    title.appendChild(mk("span", null, "·"));
    title.appendChild(mk("span", null, "span " + F.span(g.times)));
    div.appendChild(title);
    var ids = g.ids || [], positions = g.positions || [], times = g.times || [];
    var slots = PL.pairEventsToSlots(ids, g.events); // by id — the server can drop an id it couldn't hydrate, shifting `events`' own index (fix round 1, #7)
    for (var j = 0; j < ids.length; j++) {
      if (j > 0) div.appendChild(gapDiv(positions[j - 1], positions[j], times[j - 1], times[j]));
      div.appendChild(evDiv(j + 1, slots[j], times[j], board));
    }
    return div;
  }

  function render(entry, state, actions) {
    var rid = entry.result_id, total = entry.total;
    var bf = PF.boardFieldsFor(state, entry.corpus);
    if (bf.blocked) return { note: "", body: PF.loadingBlock() };
    var fields = PL.fieldsFor(bf.board);
    var target = shownFor(entry.seq);
    var groups = [], pending = false, blocker = null;
    for (var o = 0; o < target && o < total && !blocker; o += 2) {
      var rec = PF.fetchPage(rid, o, 2, fields);
      if (rec.status === "loading") {
        pending = true;
        break;
      }
      if (rec.data.gone) {
        blocker = PF.goneBlock(actions, entry);
        break;
      }
      if (rec.data.error) {
        blocker = PF.errorBlock(rec.data.error.message);
        break;
      }
      (rec.data.results || []).forEach(function (g) { groups.push(g); });
    }
    if (blocker) return { note: "", body: blocker };
    if (pending && groups.length === 0) return { note: "", body: PF.loadingBlock() };
    var body = document.createElement("div");
    groups.forEach(function (g, i) { body.appendChild(chainDiv(g, i, bf.board)); });
    var more = mk("div", "more");
    more.appendChild(mk("span", null, pending ? "loading…" : PL.groupsMoreLabel(groups.length, total)));
    if (!pending && groups.length < total) {
      var btn = mk("button", "ghost", "Show 2 more");
      btn.type = "button";
      btn.addEventListener("click", function () { bumpShown(entry.seq); });
      more.appendChild(btn);
    }
    body.appendChild(more);
    return { note: total + " total", body: body };
  }

  var api = { render: render };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLInspectorGroups = api;
})(typeof window !== "undefined" ? window : globalThis);
