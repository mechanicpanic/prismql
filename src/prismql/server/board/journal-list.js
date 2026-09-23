// PrismQLJournalList: the journal's list — offline banner, the paused
// "N new requests" pill, days newest-first, rows, the two empty states and
// ↑/↓/Enter keyboard nav (graph @aleph/prismql, node #63). tick(), the
// periodic 5s refresh, only patches ".rel" — a rebuild drops focus (#2).
(function (root) {
  "use strict";

  var lastVisible = [];
  var F = window.PrismQLFormat;
  var mk = window.PrismQLBoardUtil.mk;

  function buildRow(entry, state, actions, nowMs) {
    var status = F.status(entry);
    var cls = "row s-" + status + (entry.seq === state.sel ? " sel" : "") + (entry.seq === state.freshSeq ? " fresh" : "");
    var btn = mk("button", cls);
    btn.type = "button";
    btn.dataset.seq = String(entry.seq);
    btn.dataset.ts = entry.ts; // read back by tick() to refresh ".rel" in place
    if (entry.seq === state.sel) btn.setAttribute("aria-current", "true");
    btn.addEventListener("click", function () { actions.select(entry.seq); });
    btn.addEventListener("dblclick", function () { actions.openFull(entry.seq); });

    var time = mk("span", "time");
    time.appendChild(mk("span", "abs", F.hms(entry.ts)));
    var sec = Math.max(0, Math.round((nowMs - new Date(entry.ts).getTime()) / 1000));
    time.appendChild(mk("span", "rel", F.rel(sec)));

    var meta = mk("span", "meta");
    meta.appendChild(mk("span", "kind " + entry.kind, entry.kind));
    meta.appendChild(mk("span", "src", entry.who || ""));
    meta.appendChild(mk("span", "corpus", entry.corpus || ""));
    meta.appendChild(mk("span", "res s-" + status, F.resultLabel(entry)));
    var ms = entry.elapsed_ms;
    meta.appendChild(mk("span", "dur" + (typeof ms === "number" && ms >= 1000 ? " slow" : ""), F.dur(ms)));

    var qline = mk("span", "qline");
    var qtext = entry.query || "";
    if (entry.kind === "evaluate") qline.innerHTML = window.PrismQLLexer.highlight(qtext.replace(/\s*\n\s*/g, " "));
    else qline.textContent = qtext;

    var rmain = mk("span", "rmain");
    rmain.appendChild(meta);
    rmain.appendChild(qline);
    btn.appendChild(time);
    btn.appendChild(rmain);
    return btn;
  }

  function renderBanner(el, state, actions) {
    var banner = mk("div", "banner");
    banner.appendChild(mk("b", null, "Lost the journal stream."));
    var newest = state.entries[0];
    banner.appendChild(mk("span", null,
      (newest ? "Showing what arrived before " + F.hms(newest.ts) + ". " : "") + "Retrying in 4 s."));
    var retry = mk("button", "ghost", "Retry now");
    retry.type = "button";
    retry.style.marginLeft = "auto";
    retry.addEventListener("click", function () { if (actions.reconnect) actions.reconnect(); });
    banner.appendChild(retry);
    el.appendChild(banner);
  }

  function renderPending(el, state, actions) {
    var pill = mk("button", "newpill");
    pill.type = "button";
    pill.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7"></path></svg>';
    pill.appendChild(document.createTextNode(state.pending.length + " new request" + (state.pending.length > 1 ? "s" : "")));
    pill.addEventListener("click", function () { actions.showPending(); });
    el.appendChild(pill);
  }

  function renderEmpty(el, state, actions, anyFilter) {
    var empty = mk("div", "empty");
    empty.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"></path></svg>';
    empty.appendChild(mk("strong", null, state.entries.length === 0 ? "Nothing asked yet" : "No requests match"));
    empty.appendChild(mk("span", null, state.entries.length === 0
      ? "Requests from agents and people show up here as the server receives them."
      : "Nothing in the " + (state.filters.range === "all" ? "whole journal" : "last " + state.filters.range) + " fits these filters."));
    if (anyFilter) {
      var reset = mk("button", "ghost", "Reset all filters");
      reset.type = "button";
      reset.addEventListener("click", function () { actions.resetFilters(); });
      empty.appendChild(reset);
    }
    el.appendChild(empty);
  }

  function wireKeys(el, state, actions) {
    if (el.dataset.wired) return;
    el.dataset.wired = "1";
    el.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        // A reset can outlive the seq it pointed at (fix round 1, #3); a
        // paused run's own match lives only in pending (fix round 2, #1).
        var exists = window.PrismQLBoardUtil.findEntry(state, state.sel) != null;
        if (exists) { e.preventDefault(); actions.openFull(state.sel); }
        return;
      }
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      e.preventDefault();
      var i = lastVisible.findIndex(function (r) { return r.seq === state.sel; });
      var j = e.key === "ArrowDown" ? Math.min(lastVisible.length - 1, i + 1) : Math.max(0, i - 1);
      if (lastVisible[j]) actions.select(lastVisible[j].seq);
    });
  }

  function render(state, actions, visible, nowMs, anyFilter) {
    lastVisible = visible;
    var el = document.getElementById("journal-list");
    var hadFocus = el === document.activeElement || el.contains(document.activeElement);
    el.innerHTML = "";
    if (state.down) renderBanner(el, state, actions);
    if (state.pending.length) renderPending(el, state, actions);
    var lastKey = null, selectedBtn = null;
    visible.forEach(function (entry) {
      var d = F.dayLabel(entry.ts, nowMs);
      if (d.key !== lastKey) {
        lastKey = d.key;
        var day = mk("div", "day");
        day.appendChild(document.createTextNode(d.label + " "));
        day.appendChild(mk("span", null, d.sub));
        el.appendChild(day);
      }
      var row = buildRow(entry, state, actions, nowMs);
      if (entry.seq === state.sel) selectedBtn = row;
      el.appendChild(row);
    });
    if (visible.length === 0) renderEmpty(el, state, actions, anyFilter);
    wireKeys(el, state, actions);
    // A rebuild just dropped focus to <body> — restore it (fix round 1, #2).
    if (hadFocus) (selectedBtn || el).focus({ preventScroll: true });
  }

  function tick(nowMs) { // no rebuild — driven by board.js's 5 s interval
    var el = document.getElementById("journal-list");
    if (!el) return;
    var rows = el.querySelectorAll(".row[data-ts]");
    for (var i = 0; i < rows.length; i++) {
      var relEl = rows[i].querySelector(".rel");
      if (!relEl) continue;
      var sec = Math.max(0, Math.round((nowMs - new Date(rows[i].dataset.ts).getTime()) / 1000));
      relEl.textContent = F.rel(sec);
    }
  }

  var api = { render: render, tick: tick };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLJournalList = api;
})(typeof window !== "undefined" ? window : globalThis);
