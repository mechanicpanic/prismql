// PrismQL board — entry point. For Task 3 this only sets the theme (dark by
// default, remembered in localStorage) and its toggle's icon/label; the
// journal/editor/inspector wiring lands in later tasks (graph
// @aleph/prismql, node #63).
(function () {
  "use strict";
  const KEY = "prismql-board-theme";

  function readTheme() {
    try {
      const v = localStorage.getItem(KEY);
      return v === "light" ? "light" : "dark";
    } catch (e) {
      return "dark";
    }
  }

  function writeTheme(theme) {
    try {
      localStorage.setItem(KEY, theme);
    } catch (e) {
      // storage unavailable (private window, blocked site data) — theme
      // still applies for this load, just isn't remembered.
    }
  }

  function setHidden(el, hidden) {
    // el.hidden = ... does not reliably reflect onto the "hidden" content
    // attribute for inline <svg> children in every engine — set the
    // attribute directly so the board.css `[hidden]` rule always applies.
    if (!el) return;
    if (hidden) el.setAttribute("hidden", "");
    else el.removeAttribute("hidden");
  }

  function apply(app, toggle, sun, moon, theme) {
    app.classList.remove("t-dark", "t-light");
    app.classList.add(theme === "light" ? "t-light" : "t-dark");
    // The icon shown is the affordance for the theme a click switches TO
    // (sun while dark — switches to light; moon while light — switches to
    // dark), matching the canvas (Main.dc.html ~261-262).
    setHidden(sun, theme === "light");
    setHidden(moon, theme !== "light");
    if (toggle) {
      const label = theme === "light" ? "Switch to dark theme" : "Switch to light theme";
      toggle.setAttribute("aria-label", label);
      toggle.setAttribute("title", label);
    }
  }

  function init() {
    const app = document.getElementById("app");
    if (!app) return;
    const toggle = document.getElementById("theme-toggle");
    const sun = document.getElementById("theme-icon-sun");
    const moon = document.getElementById("theme-icon-moon");
    let theme = readTheme();
    apply(app, toggle, sun, moon, theme);
    if (toggle) {
      toggle.addEventListener("click", function () {
        theme = theme === "light" ? "dark" : "light";
        apply(app, toggle, sun, moon, theme);
        writeTheme(theme);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
