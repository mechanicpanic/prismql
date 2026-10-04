// PrismQLFullPager: the full view's result navigation controls — the sort
// and reverse buttons in the bar, and the footer under the body: collapse/
// expand all, Prev/Next, the page indicator and a jump-to-page box. Plain
// buttons and a form, so Tab/Enter/Space work as everywhere else; each
// control carries a data-fkey so a rebuild puts focus back on it
// (fullview-focus.js). Only state and callbacks: the view state itself is
// fullview-nav-logic.js's.
(function (root) {
  "use strict";
  var mk = window.PrismQLBoardUtil.mk;
  var Nav = window.PrismQLFullNav;

  function keyed(btn, key, alt) {
    btn.type = "button";
    btn.dataset.fkey = key;
    if (alt) btn.dataset.falt = alt; // where focus goes if this one just became disabled
    return btn;
  }

  // Sort (groups only: a size means something there) and Reverse (any paged
  // result) — over the WHOLE result, not the loaded page.
  function buildOrder(bar, ctx, vs, onChange) {
    var box = mk("div", "forder");
    box.setAttribute("role", "group");
    box.setAttribute("aria-label", "Order");
    if (ctx.kind === "groups") {
      var label = mk("label", "fsort");
      label.appendChild(mk("span", null, "Sort"));
      var sel = document.createElement("select");
      sel.dataset.fkey = "sort";
      sel.setAttribute("aria-label", "Sort groups");
      Nav.ORDERS.forEach(function (o) {
        var opt = mk("option", null, o.label);
        opt.value = o.value;
        opt.selected = o.value === vs.order;
        sel.appendChild(opt);
      });
      sel.addEventListener("change", function () { Nav.setOrder(vs, sel.value); onChange(); });
      label.appendChild(sel);
      box.appendChild(label);
    }
    var rev = keyed(mk("button", "ghost sm" + (vs.reverse ? " on" : ""), "Reverse"), "reverse");
    rev.title = "Show the order flipped, over the whole result";
    rev.setAttribute("aria-pressed", String(vs.reverse));
    rev.addEventListener("click", function () { Nav.toggleReverse(vs); onChange(); });
    box.appendChild(rev);
    bar.appendChild(box);
  }

  function step(vs, delta, onChange) {
    if (Nav.goPage(vs, vs.page + delta)) onChange();
  }
  function jumpForm(nav, vs, onChange) {
    var form = mk("form", "fjump");
    var input = document.createElement("input");
    input.type = "number"; input.min = "1"; input.max = String(nav.pageCount);
    input.placeholder = "page";
    input.dataset.fkey = "jump";
    input.setAttribute("aria-label", "Go to page (1 to " + nav.pageCount + ")");
    var go = keyed(mk("button", "ghost sm", "Go"), "jump-go");
    go.type = "submit";
    form.appendChild(input);
    form.appendChild(go);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (input.value !== "" && Nav.goPage(vs, Number(input.value) - 1)) onChange();
    });
    return form;
  }

  // The footer of a paged body: shown while the page is loading too (the
  // page number is known), never over a gone result.
  function buildFooter(ctx, vs, onChange) {
    var nav = ctx.nav;
    var foot = mk("div", "fpager");
    foot.setAttribute("role", "navigation");
    foot.setAttribute("aria-label", "Result pages");
    var open = mk("div", "fall");
    var verbose = ctx.kind === "groups" && vs.view !== "raw" &&
      (ctx.filtered || []).some(function (g) { return Nav.isVerbose(g.ids.length); });
    if (verbose) {
      [["Collapse all", "close"], ["Expand all", "open"]].forEach(function (b) {
        var btn = keyed(mk("button", "ghost sm", b[0]), "all-" + b[1]);
        btn.title = "Every verbose group on this page";
        btn.addEventListener("click", function () { Nav.setAll(vs, ctx.filtered, b[1]); onChange(); });
        open.appendChild(btn);
      });
    }
    foot.appendChild(open);
    var prev = keyed(mk("button", "ghost sm", "‹ Prev"), "prev", "next");
    prev.setAttribute("aria-label", "Previous page");
    prev.disabled = nav.page <= 0;
    prev.addEventListener("click", function () { step(vs, -1, onChange); });
    var next = keyed(mk("button", "ghost sm", "Next ›"), "next", "prev");
    next.setAttribute("aria-label", "Next page");
    next.disabled = nav.page >= nav.pageCount - 1;
    next.addEventListener("click", function () { step(vs, 1, onChange); });
    var status = mk("span", "fpage", "Page " + (nav.page + 1) + " of " + nav.pageCount);
    status.setAttribute("role", "status");
    foot.appendChild(prev);
    foot.appendChild(status);
    foot.appendChild(next);
    if (nav.pageCount > 1) foot.appendChild(jumpForm(nav, vs, onChange));
    return foot;
  }

  var api = { buildOrder: buildOrder, buildFooter: buildFooter };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFullPager = api;
})(typeof window !== "undefined" ? window : globalThis);
