// PrismQLBoardResize: the two grips between the board's columns (graph
// @aleph/prismql, #118). Drag with the mouse, arrows from the keyboard
// (Shift for bigger steps), double-click for the default width. Widths are
// CSS variables on #app, bounded by board-cols.js, and remembered in this
// viewer's browser only.
(function () {
  "use strict";
  var C = window.PrismQLBoardCols;
  var KEY = "prismql.board.cols";
  var NARROW = "(max-width: 1099px)";

  function read() {
    try { return C.parse(localStorage.getItem(KEY)); } catch (e) { return C.parse(null); }
  }
  function write(cols) {
    try { localStorage.setItem(KEY, JSON.stringify(cols)); } catch (e) { /* not remembered */ }
  }

  function init() {
    var app = document.getElementById("app");
    if (!app) return;
    var cols = read();
    var grips = {};

    function apply(next) {
      cols = C.clamp(next, app.clientWidth, window.matchMedia(NARROW).matches);
      app.style.setProperty("--rail-w", cols.rail + "px");
      app.style.setProperty("--insp-w", cols.insp + "px");
      grips.rail.setAttribute("aria-valuenow", String(cols.rail));
      grips.insp.setAttribute("aria-valuenow", String(cols.insp));
    }

    // dx > 0 moves the grip right: the rail widens, the inspector narrows
    function moved(col, from, dx) {
      var next = { rail: from.rail, insp: from.insp };
      if (col === "rail") next.rail = from.rail + dx;
      else next.insp = from.insp - dx;
      return next;
    }

    ["rail", "insp"].forEach(function (col) {
      var g = document.createElement("div");
      g.className = "colgrip";
      g.dataset.col = col;
      g.tabIndex = 0;
      g.setAttribute("role", "separator");
      g.setAttribute("aria-orientation", "vertical");
      g.setAttribute("aria-label", col === "rail" ? "Resize the filters" : "Resize the inspector");
      g.setAttribute("aria-valuemin", String(col === "rail" ? C.RAIL_MIN : C.INSP_MIN));
      g.setAttribute("aria-valuemax", String(col === "rail" ? C.RAIL_MAX : C.INSP_MAX));
      g.title = "Drag to resize · double-click to reset";
      g.addEventListener("pointerdown", function (e) {
        if (e.button !== 0) return;
        e.preventDefault();
        var x0 = e.clientX, from = { rail: cols.rail, insp: cols.insp };
        g.setPointerCapture(e.pointerId);
        app.classList.add("resizing");
        g.classList.add("on");
        function move(ev) { apply(moved(col, from, ev.clientX - x0)); }
        function up() {
          g.removeEventListener("pointermove", move);
          g.removeEventListener("pointerup", up);
          g.removeEventListener("pointercancel", up);
          app.classList.remove("resizing");
          g.classList.remove("on");
          write(cols);
        }
        g.addEventListener("pointermove", move);
        g.addEventListener("pointerup", up);
        g.addEventListener("pointercancel", up);
      });
      g.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
        e.preventDefault();
        var step = (e.shiftKey ? 64 : 16) * (e.key === "ArrowRight" ? 1 : -1);
        apply(moved(col, cols, step));
        write(cols);
      });
      g.addEventListener("dblclick", function () {
        var next = { rail: cols.rail, insp: cols.insp };
        next[col] = C.DEFAULTS[col];
        apply(next);
        write(cols);
      });
      grips[col] = g;
      app.appendChild(g);
    });

    apply(cols);
    window.addEventListener("resize", function () { apply(cols); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
