// PrismQLFormat: pure board logic (statuses, labels, gaps, filters, JSON
// tokenizing lives in the sibling lexjson.js). Ported from the canvas.
(function (root) {
  var DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var ERR_WORDS = { syntax: "syntax error", runtime: "runtime error", rate_limit: "rate limited" };
  var IPV4_RE = /^\d{1,3}(\.\d{1,3}){3}$/;
  function pad(n) { return String(n).padStart(2, "0"); }
  function dayKeyOf(t) { var d = new Date(t);
    return d.getFullYear() + "-" + d.getMonth() + "-" + d.getDate();
  }
  function escapeRe(x) { return x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function hasFlags(o) { return !!o && Object.keys(o).length > 0; }
  // A bare "*" would match everything; drop empty-after-star terms.
  function isBlankTerm(t) { return !t || (t.slice(-1) === "*" && t.slice(0, -1) === ""); }
  function isIp(who) { if (typeof who !== "string") return false;
    return IPV4_RE.test(who) || (who.indexOf(":") >= 0 && /^[0-9a-fA-F:]+$/.test(who));
  }
  function status(entry) {
    if (entry.ok === false) return "error";
    if (entry.total === 0) return "empty";
    if (entry.result === "hits" && entry.count === 0) return "empty";
    return entry.capped ? "capped" : "ok";
  }
  function resultLabel(entry) {
    if (entry.ok === false) {
      var etype = entry.error && entry.error.type;
      return ERR_WORDS[etype] || etype || "error";
    }
    var r = entry.result, label;
    // A GROUP BY ... AGGREGATE answer always carries a total (graph
    // @aleph/prismql, #90), even with no groups; without one the aggregate
    // is plain and simply had nothing to compute (avg over no numbers).
    if (r === "aggregate") {
      label = entry.value != null ? "= " + entry.value
        : typeof entry.total === "number" ? entry.total + " groups" : "= no value";
    } else if (r === "groups" || r === "named") {
      label = entry.total + " groups" + (entry.capped ? " · capped" : "");
    } else if (r === "hits") {
      label = entry.total + " hits" + (entry.threshold != null ? " ≥ " + entry.threshold : "");
    } else if (r === "grouped") {
      label = typeof entry.count === "number" ? entry.count + " groups" : "grouped";
    } else label = String(r || "");
    return entry.output === "file" ? label + " → file" : label;
  }
  function unitDur(sec) {
    if (sec < 60) return sec + " s";
    if (sec < 3600) return Math.floor(sec / 60) + " min";
    if (sec < 86400) return Math.floor(sec / 3600) + " h";
    return Math.floor(sec / 86400) + " d";
  }
  function rel(sec) { return sec < 10 ? "just now" : unitDur(sec) + " ago"; }
  function dur(ms) { if (typeof ms !== "number" || Number.isNaN(ms)) return "—";
    if (ms >= 0 && ms < 1) return "<1 ms";
    var r = Math.round(ms); if (r < 1000) return r + " ms";
    if (r >= 10000) return Math.round(r / 1000) + " s";
    var s = (r / 1000).toFixed(1);
    return s === "10.0" ? "10 s" : s + " s";
  }
  function hms(iso) { var d = new Date(iso);
    return pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
  }
  function dayLabel(iso, nowMs) {
    var t = new Date(iso).getTime(), d = new Date(t), k = dayKeyOf(t);
    var today = dayKeyOf(nowMs) === k, yest = dayKeyOf(nowMs - 86400000) === k;
    var label = today ? "Today" : yest ? "Yesterday" : DOW[d.getDay()];
    var sub = DOW[d.getDay()] + " " + d.getDate() + " " + MON[d.getMonth()];
    return { key: k, label: label, sub: sub };
  }
  // Unordered INWINDOW: Δpos/Δt are signed here, never clamped (graph @aleph/prismql, node #76).
  function gapLabel(prevPos, pos, prevTime, time) { var label = "";
    if (prevPos != null && pos != null) {
      var dp = Math.abs(pos - prevPos);
      label = dp === 0 ? "same event" : (dp - 1) + " event" + (dp - 1 === 1 ? "" : "s") + " between";
    }
    var plus = "";
    if (prevTime != null && time != null) {
      var dt = new Date(time).getTime() - new Date(prevTime).getTime();
      plus = (dt < 0 ? "−" : "+") + unitDur(Math.floor(Math.abs(dt) / 1000));
    }
    return { plus: plus, label: label };
  }
  function span(times) {
    var ms = (times || []).filter(function (x) { return x != null; })
      .map(function (x) { return new Date(x).getTime(); });
    if (!ms.length) return "—";
    return unitDur(Math.floor((Math.max.apply(null, ms) - Math.min.apply(null, ms)) / 1000));
  }
  function isAgent(who) { return typeof who === "string" && who !== "board" && !isIp(who); }
  function highlightParts(text, terms) {
    var clean = (terms || []).filter(function (t) { return !isBlankTerm(t); });
    if (text === "" || !clean.length) return [{ t: text, m: false }];
    var pattern = clean.map(function (t) {
      return t.slice(-1) === "*" ? escapeRe(t.slice(0, -1)) + "\\w*" : escapeRe(t);
    }).join("|");
    var re = new RegExp("(" + pattern + ")", "ig");
    return text.split(re).filter(function (x) { return x; }).map(function (x) {
      var m = re.test(x);
      re.lastIndex = 0;
      return { t: x, m: m };
    });
  }
  function searchTerms(query) {
    var terms = [];
    var rest = query.replace(/"((?:[^"\\]|\\.)*)"/g, function (_, inner) {
      if (inner) terms.push(inner);
      return " ";
    });
    var skip = false;
    rest.split(/\s+/).filter(function (t) { return t; }).forEach(function (raw) {
      if (skip) { skip = false; return; }
      if (raw === "NOT") { skip = true; return; }
      if (raw === "AND" || raw === "OR") return;
      var tok = raw.replace(/^[()+-]+/, "").replace(/[()+-]+$/, "");
      if (!tok) return;
      var ci = tok.indexOf(":"), after = ci >= 0 ? tok.slice(ci + 1) : tok;
      if (!isBlankTerm(after)) terms.push(after);
    });
    return terms;
  }
  function passesFilters(entry, filters, nowMs, skipKey) { filters = filters || {};
    if (filters.range) {
      var sec = Math.max(0, Math.round((nowMs - new Date(entry.ts).getTime()) / 1000));
      if (sec > filters.range) return false;
    }
    if (filters.search) {
      var q = String(filters.search).trim().toLowerCase();
      var hay = [entry.query, entry.who, entry.corpus, resultLabel(entry)].join(" ");
      if (q && hay.toLowerCase().indexOf(q) < 0) return false;
    }
    var k = filters.kinds, s = filters.srcs, c = filters.corpora, st = filters.statuses;
    if (skipKey !== "kinds" && hasFlags(k) && !k[entry.kind]) return false;
    if (skipKey !== "srcs" && hasFlags(s) && !s[entry.who]) return false;
    if (skipKey !== "corpora" && hasFlags(c) && !c[entry.corpus]) return false;
    return skipKey === "statuses" || !hasFlags(st) || !!st[status(entry)];
  }
  function matches(entry, filters, nowMs) { return passesFilters(entry, filters, nowMs, null); }
  function facetCounts(entries, filters, nowMs, key, values) {
    var field = { kinds: "kind", srcs: "who", corpora: "corpus" }[key];
    var out = {};
    values.forEach(function (v) {
      out[v] = entries.filter(function (e) {
        if (!passesFilters(e, filters, nowMs, key)) return false;
        return (key === "statuses" ? status(e) : e[field]) === v;
      }).length;
    });
    return out;
  }
  var api = { status: status, resultLabel: resultLabel, rel: rel, dur: dur,
    hms: hms, dayLabel: dayLabel, gapLabel: gapLabel, span: span, isAgent: isAgent,
    highlightParts: highlightParts, searchTerms: searchTerms, matches: matches,
    facetCounts: facetCounts };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFormat = api;
})(typeof window !== "undefined" ? window : globalThis);
