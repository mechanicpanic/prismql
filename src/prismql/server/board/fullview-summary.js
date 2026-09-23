// PrismQLFullSummary: the full view's `.fsum` (highlighted query, copy
// button, tiles) and `.fbar` (view switch, filter box, agent chips, note)
// (task-7 brief; graph @aleph/prismql, node #76).
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var Lex = window.PrismQLLexer;

  var VIEW_LABELS = { timeline: "Timeline", table: "Table", raw: "Raw JSON", summary: "Summary" };
  var ICON_COPY = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"></path></svg>';
  var ICON_SEARCH = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path></svg>';

  function flipTitle(btn, text) {
    btn.title = text;
    setTimeout(function () { btn.title = "Copy query"; }, 1500);
  }
  function copyBtn(text) {
    var btn = mk("button", "iconbtn sm copy");
    btn.type = "button";
    btn.title = "Copy query";
    btn.setAttribute("aria-label", "Copy query");
    btn.innerHTML = ICON_COPY;
    btn.addEventListener("click", function () {
      try {
        navigator.clipboard.writeText(text)
          .then(function () { flipTitle(btn, "Copied"); })
          .catch(function () { flipTitle(btn, "Copy failed"); });
      } catch (e) {
        flipTitle(btn, "Copy failed");
      }
    });
    return btn;
  }

  function buildSum(el, entry, tiles) {
    var sum = mk("div", "fsum");
    var code = mk("div", "code");
    if (entry.kind === "evaluate") code.innerHTML = Lex.highlight(entry.query || "");
    else code.appendChild(document.createTextNode(entry.query || ""));
    code.appendChild(copyBtn(entry.query || ""));
    sum.appendChild(code);
    if (tiles && tiles.length) {
      var box = mk("div", "tiles");
      tiles.forEach(function (t) {
        var tile = mk("div", "tile");
        var val = mk("b", null, t.v);
        // Fix round 2, #4: a long value (a cross-year time range) ellipses
        // in its 148px box — the title attribute still carries it in full.
        val.title = t.v;
        tile.appendChild(val);
        tile.appendChild(mk("span", null, t.l));
        box.appendChild(tile);
      });
      sum.appendChild(box);
    }
    el.appendChild(sum);
  }

  function buildViewSeg(bar, allowed, currentView, vs, onChange) {
    var seg = mk("div", "vseg");
    seg.setAttribute("role", "group");
    seg.setAttribute("aria-label", "View");
    allowed.forEach(function (v) {
      var btn = mk("button", v === currentView ? "on" : "", VIEW_LABELS[v]);
      btn.type = "button";
      btn.setAttribute("aria-pressed", String(v === currentView));
      btn.addEventListener("click", function () { vs.view = v; onChange(); });
      seg.appendChild(btn);
    });
    bar.appendChild(seg);
  }

  function buildFilter(bar, ctx, vs, onChange) {
    var label = mk("label", "searchbox fsearch");
    label.innerHTML = ICON_SEARCH;
    var input = document.createElement("input");
    input.type = "search";
    input.placeholder = "Filter the output";
    input.setAttribute("aria-label", "Filter the output");
    input.value = vs.q;
    input.addEventListener("input", function (e) { vs.q = e.target.value; vs.group = 0; onChange(); });
    label.appendChild(input);
    bar.appendChild(label);

    var chips = mk("div", "achips");
    chips.setAttribute("role", "group");
    chips.setAttribute("aria-label", "Agents");
    ctx.agents.forEach(function (a) {
      var btn = mk("button", "achip" + (a.on ? " on" : ""), a.label);
      btn.type = "button";
      btn.setAttribute("aria-pressed", String(a.on));
      btn.addEventListener("click", function () {
        if (vs.agents[a.label]) delete vs.agents[a.label]; else vs.agents[a.label] = true;
        vs.group = 0;
        onChange();
      });
      chips.appendChild(btn);
    });
    bar.appendChild(chips);
  }

  function buildBar(el, allowed, currentView, ctx, vs, onChange) {
    var bar = mk("div", "fbar");
    buildViewSeg(bar, allowed, currentView, vs, onChange);
    if (ctx.canFilter) buildFilter(bar, ctx, vs, onChange);
    bar.appendChild(mk("span", "fnote", ctx.note || ""));
    el.appendChild(bar);
  }

  var api = { buildSum: buildSum, buildBar: buildBar };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullSummary = api;
})(typeof window !== "undefined" ? window : globalThis);
