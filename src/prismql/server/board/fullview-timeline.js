// PrismQLFullTimeline: the Timeline view's DOM — the left nav of loaded
// (filtered) groups and the selected group's vertical timeline of events
// and gaps (task-7 brief; graph @aleph/prismql, node #76). Item shaping is
// fullview-rows.js's job; this only builds elements from what it returns.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var FR = window.PrismQLFullRows;
  var UI = window.PrismQLInspectorUI;

  function navButton(item, i, selected, onPick) {
    var btn = mk("button", "gitem" + (selected ? " on" : ""));
    btn.type = "button";
    btn.setAttribute("aria-current", String(selected));
    var top = mk("span", "top");
    top.appendChild(mk("b", null, "group " + item.n));
    top.appendChild(mk("span", "ag", item.actor));
    top.appendChild(mk("span", "sp", item.span));
    btn.appendChild(top);
    btn.appendChild(mk("span", "sn", item.snip));
    btn.appendChild(mk("span", "dt", item.date));
    btn.addEventListener("click", function () { onPick(i); });
    return btn;
  }

  function eventCard(it) {
    var row = mk("div", "tev");
    var tm = mk("div", "tm");
    tm.appendChild(mk("b", null, it.hms));
    tm.appendChild(mk("span", null, it.date));
    row.appendChild(tm);
    var rl = mk("div", "rl");
    rl.appendChild(document.createElement("i"));
    row.appendChild(rl);
    var card = mk("div", "card");
    var l = mk("div", "l");
    if (it.kind != null) l.appendChild(mk("span", "k", String(it.kind)));
    if (it.actor != null) l.appendChild(mk("span", "a", String(it.actor)));
    l.appendChild(mk("span", "e", "event " + it.n));
    card.appendChild(l);
    if (it.text != null) card.appendChild(mk("div", "x", String(it.text)));
    row.appendChild(card);
    return row;
  }
  function gapRow(it) {
    var row = mk("div", "tgap");
    row.appendChild(mk("span", "dur", it.plus));
    var rl = mk("div", "rl");
    rl.appendChild(document.createElement("em"));
    row.appendChild(rl);
    row.appendChild(mk("div", "lab", it.label));
    return row;
  }

  function renderNav(el, groups, board, selectedIndex, onPick) {
    groups.forEach(function (g, i) {
      el.appendChild(navButton(FR.navItemFor(g, board), i, i === selectedIndex, onPick));
    });
  }

  function renderDetail(el, group, total, board) {
    if (!group) {
      el.appendChild(UI.emptyBlock("No groups match", "Clear the filter or pick other agents.", { compact: true }));
      return;
    }
    var info = FR.groupHeaderInfo(group, total, board);
    var gdh = mk("div", "gdh");
    gdh.appendChild(mk("h3", null, "Group " + info.n + " of " + info.total));
    var bits = [];
    if (info.actor) bits.push(info.actor);
    bits.push("span " + info.span);
    if (info.range) bits.push(info.range);
    gdh.appendChild(mk("span", null, bits.join(" · ")));
    el.appendChild(gdh);
    FR.timelineItems(group, board).forEach(function (it) {
      el.appendChild(it.isGap ? gapRow(it) : eventCard(it));
    });
  }

  var api = { renderNav: renderNav, renderDetail: renderDetail };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullTimeline = api;
})(typeof window !== "undefined" ? window : globalThis);
