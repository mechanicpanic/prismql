// PrismQL board — entry point. For Task 3 this only sets the theme (dark by
// default, remembered in localStorage); the journal/editor/inspector wiring
// lands in later tasks (graph @aleph/prismql, node #63).
(function () {
  "use strict";
  var KEY = "prismql-board-theme";

  function readTheme() {
    try {
      var v = localStorage.getItem(KEY);
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

  function apply(app, theme) {
    app.classList.remove("t-dark", "t-light");
    app.classList.add(theme === "light" ? "t-light" : "t-dark");
  }

  function init() {
    var app = document.getElementById("app");
    if (!app) return;
    var theme = readTheme();
    apply(app, theme);
    var toggle = document.getElementById("theme-toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        theme = theme === "light" ? "dark" : "light";
        apply(app, theme);
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
