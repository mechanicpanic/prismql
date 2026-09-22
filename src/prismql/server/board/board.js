// PrismQL board — entry point. Sets the theme (dark by default, remembered
// in localStorage) and its toggle's icon/label, and keeps the journal's
// stream connected across a server restart by carrying the boot id from
// activity() into stream() (graph @aleph/prismql, node #76). Rendering the
// entries themselves — the journal list, the rail, the inspector — is a
// later task; journal.js is still a no-op stub.
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
    // SVGElement has no "hidden" IDL attribute at all — only HTMLElement
    // does — so el.hidden = ... is a silent no-op on these inline <svg>
    // icons. Toggle the content attribute directly; board.css's own
    // author `[hidden]` rule (not the UA default) is what hides them.
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

  // ------------------------------------------------------------- stream
  function startJournalStream() {
    if (!window.PrismQLApi) return;
    let boot = null;

    function backfillAndConnect() {
      window.PrismQLApi
        .activity(0)
        .then(function (body) {
          boot = body.boot;
          window.PrismQLApi.stream(
            body.seq || 0,
            function () {}, // entries render in a later task
            function (state) {
              if (state === "reset") backfillAndConnect();
            },
            boot
          );
        })
        .catch(function () {
          // Not reachable yet — nothing to connect to until it is; a later
          // task may surface this. stream()'s own retry loop is what
          // handles a connection that opens and then drops.
        });
    }

    backfillAndConnect();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  startJournalStream();
})();
