// PrismQLFullTimeline: the Timeline view's DOM — the left nav of loaded
// (filtered) groups and the selected group's vertical timeline of events
// and gaps (task-7 brief; graph @aleph/prismql, node #76). Item shaping is
// fullview-rows.js's job; this only builds elements from what it returns.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var FR = window.PrismQLFullRows;
  var UI = window.PrismQLInspectorUI;
  var Nav = window.PrismQLFullNav;

  function navButton(item, i, selected, onPick) {
    var btn = mk("button", "gitem" + (selected ? " on" : ""));
    btn.type = "button";
    btn.setAttribute("aria-current", String(selected));
    var top = mk("span", "top");
    top.appendChild(mk("b", null, "group " + item.n));
    top.appendChild(mk("span", "ct", item.count + (item.count === 1 ? " event" : " events")));
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
    l.appendChild(mk("span", "e", it.label || "event " + it.n));
    card.appendChild(l);
    if (it.text != null) {
      // matched spans marked (#119)
      var x = mk("div", "x");
      window.PrismQLExplainFormat.textParts(it.text, it.why).forEach(function (p) {
        x.appendChild(p.m ? mk("mark", null, p.t) : document.createTextNode(p.t));
      });
      card.appendChild(x);
    }
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

  // The open/close controls of a verbose group — the same two buttons above
  // and (when events are still hidden) below its cards. Each carries a
  // data-fkey so a rebuild puts keyboard focus back on it.
  function toggleBar(group, shown, onToggle, where) {
    var tx = Nav.toggleText(group.ids.length, shown);
    var bar = mk("div", "gtoggle " + where);
    bar.appendChild(mk("span", "gcount", tx.seen + " of " + group.ids.length + " events shown"));
    [["more", "open", tx.more], ["close", "close", tx.close]].forEach(function (b) {
      if (!b[2] || (where === "bottom" && b[0] === "close")) return;
      var btn = mk("button", "ghost sm", b[2]);
      btn.type = "button";
      btn.dataset.fkey = "grp-" + b[0] + "-" + where + ":" + group.idx;
      // if this one is gone after the click (all shown / back to preview), focus its twin
      btn.dataset.falt = "grp-" + (b[0] === "more" ? "close" : "more") + "-top:" + group.idx;
      btn.setAttribute("aria-expanded", String(b[0] === "close"));
      btn.addEventListener("click", function () { onToggle(group.idx, group.ids.length, b[1]); });
      bar.appendChild(btn);
    });
    return bar;
  }

  // `shownMap` is vs.shown ({stored index: events open}); a group reads its own.
  function renderDetail(el, group, total, board, labels, shownMap, onToggle) {
    if (!group) {
      el.appendChild(UI.emptyBlock("No groups match", "Clear the filter (it covers this page only) or pick other agents.", { compact: true }));
      return;
    }
    var info = FR.groupHeaderInfo(group, total, board);
    var gdh = mk("div", "gdh");
    gdh.appendChild(mk("h3", null, "Group " + info.n + " of " + info.total));
    var bits = [];
    if (info.actor) bits.push(info.actor);
    bits.push(info.count + (info.count === 1 ? " event" : " events"));
    bits.push("span " + info.span);
    if (info.range) bits.push(info.range);
    gdh.appendChild(mk("span", null, bits.join(" · ")));
    // what the engine bound each $variable to here (#173)
    var bound = window.PrismQLExplainFormat.bindingsText(group.bindings, group.bindingsCut);
    if (bound) gdh.appendChild(mk("span", "bindings", bound));
    el.appendChild(gdh);
    var shown = (shownMap || {})[group.idx];
    var verbose = Nav.isVerbose(info.count);
    var seen = Nav.visibleCount(info.count, shown);
    if (verbose) el.appendChild(toggleBar(group, shown, onToggle, "top"));
    FR.timelineItems(group, board, labels, seen).forEach(function (it) {
      el.appendChild(it.isGap ? gapRow(it) : eventCard(it));
    });
    if (verbose && seen > Nav.PREVIEW && seen < info.count) el.appendChild(toggleBar(group, shown, onToggle, "bottom"));
  }

  var api = { renderNav: renderNav, renderDetail: renderDetail };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullTimeline = api;
})(typeof window !== "undefined" ? window : globalThis);
