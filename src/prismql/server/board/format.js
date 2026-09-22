// PrismQLFormat: the board's pure logic (statuses, labels, gaps, filters).
// Ported from the Claude Design canvas (docs/superpowers/specs/board-design/
// Main.dc.html, rel/durFmt/highlight/lexJson/pass()/facet()), adapted to real
// /activity journal entries. Plain ES2020, no dependencies, no DOM access.
(function (root) {
  var DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var ERROR_WORDS = { syntax: "syntax error", runtime: "runtime error", rate_limit: "rate limited" };
  var IPV4_RE = /^\d{1,3}(\.\d{1,3}){3}$/;

  function pad(n) { return String(n).padStart(2, "0"); }
  function dayKeyOf(t) { var d = new Date(t); return d.getFullYear() + "-" + d.getMonth() + "-" + d.getDate(); }
  function escapeRe(x) { return x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function hasFlags(o) { return !!o && Object.keys(o).length > 0; }
  function isIp(w) { return IPV4_RE.test(w) || (w.indexOf(":") >= 0 && /^[0-9a-fA-F:]+$/.test(w)); }

  function status(entry) {
    if (entry.ok === false) return "error";
    if (entry.total === 0) return "empty";
    if (entry.result === "hits" && entry.count === 0) return "empty";
    if (entry.truncated) return "capped";
    return "ok";
  }

  function resultLabel(entry) {
    if (entry.ok === false) { var etype = entry.error && entry.error.type; return ERROR_WORDS[etype] || etype; }
    var label;
    if (entry.result === "aggregate") label = "= " + entry.value;
    else if (entry.result === "groups" || entry.result === "named") label = entry.total + " groups" + (entry.truncated ? " · capped" : "");
    else if (entry.result === "hits") label = entry.total + " hits" + (entry.threshold != null ? " ≥ " + entry.threshold : "");
    else label = String(entry.result || "");
    return entry.output === "file" ? label + " → file" : label;
  }

  function rel(sec) {
    if (sec < 10) return "just now";
    if (sec < 60) return sec + " s ago";
    if (sec < 3600) return Math.floor(sec / 60) + " min ago";
    if (sec < 86400) return Math.floor(sec / 3600) + " h ago";
    return Math.floor(sec / 86400) + " d ago";
  }

  function dur(ms) { return ms >= 1000 ? (ms / 1000).toFixed(ms >= 10000 ? 0 : 1) + " s" : ms + " ms"; }
  function hms(iso) { var d = new Date(iso); return pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds()); }

  function dayLabel(iso, nowMs) {
    var t = new Date(iso).getTime(), d = new Date(t), k = dayKeyOf(t);
    var today = dayKeyOf(nowMs) === k, yest = dayKeyOf(nowMs - 86400000) === k;
    return { key: k, label: today ? "Today" : yest ? "Yesterday" : DOW[d.getDay()], sub: DOW[d.getDay()] + " " + d.getDate() + " " + MON[d.getMonth()] };
  }

  function gapDur(sec) {
    if (sec < 60) return sec + " s";
    if (sec < 3600) return Math.floor(sec / 60) + " min";
    if (sec < 86400) return Math.floor(sec / 3600) + " h";
    return Math.floor(sec / 86400) + " d";
  }

  function gapLabel(prevPos, pos, prevTime, time) {
    var n = Math.max(0, pos - prevPos - 1);
    var plus = prevTime == null || time == null ? "" :
      "+" + gapDur(Math.max(0, Math.floor((new Date(time).getTime() - new Date(prevTime).getTime()) / 1000)));
    return { plus: plus, label: n + " events between" };
  }

  function span(times) {
    if (!times || !times.length) return "—";
    var first = new Date(times[0]).getTime(), last = new Date(times[times.length - 1]).getTime();
    return gapDur(Math.max(0, Math.floor((last - first) / 1000)));
  }

  function isAgent(who) { return who !== "board" && !isIp(who); }

  function highlightParts(text, terms) {
    if (!terms || !terms.length) return [{ t: text, m: false }];
    var re = new RegExp("(" + terms.map(escapeRe).join("|") + ")", "ig");
    return text.split(re).filter(function (x) { return x; }).map(function (x) {
      var m = re.test(x);
      re.lastIndex = 0;
      return { t: x, m: m };
    });
  }

  function searchTerms(query) {
    var terms = [];
    var rest = query.replace(/"((?:[^"\\]|\\.)*)"/g, function (_, inner) { terms.push(inner); return " "; });
    rest.split(/\s+/).forEach(function (tok) {
      if (!tok || tok === "AND" || tok === "OR" || tok === "NOT") return;
      var ci = tok.indexOf(":");
      if (ci >= 0) { var after = tok.slice(ci + 1); if (after) terms.push(after); return; }
      terms.push(tok);
    });
    return terms;
  }

  function passesFilters(entry, filters, nowMs, skipKey) {
    filters = filters || {};
    if (filters.range) {
      var sec = Math.max(0, Math.round((nowMs - new Date(entry.ts).getTime()) / 1000));
      if (sec > filters.range) return false;
    }
    if (filters.search) {
      var q = String(filters.search).trim().toLowerCase();
      if (q && [entry.query, entry.who, entry.corpus, resultLabel(entry)].join(" ").toLowerCase().indexOf(q) < 0) return false;
    }
    if (skipKey !== "kinds" && hasFlags(filters.kinds) && !filters.kinds[entry.kind]) return false;
    if (skipKey !== "srcs" && hasFlags(filters.srcs) && !filters.srcs[entry.who]) return false;
    if (skipKey !== "corpora" && hasFlags(filters.corpora) && !filters.corpora[entry.corpus]) return false;
    if (skipKey !== "statuses" && hasFlags(filters.statuses) && !filters.statuses[status(entry)]) return false;
    return true;
  }

  function matches(entry, filters, nowMs) { return passesFilters(entry, filters, nowMs, null); }

  function facetCounts(entries, filters, nowMs, key, values) {
    var field = { kinds: "kind", srcs: "who", corpora: "corpus" }[key];
    var out = {};
    values.forEach(function (v) {
      out[v] = entries.filter(function (e) {
        return passesFilters(e, filters, nowMs, key) && (key === "statuses" ? status(e) : e[field]) === v;
      }).length;
    });
    return out;
  }

  function lexJson(text) {
    var out = [];
    var re = /("(?:[^"\\]|\\.)*")(\s*:)?|(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)|(true|false|null)|([{}[\],:])|(\s+)|([\s\S])/g;
    var m;
    while ((m = re.exec(text))) {
      if (m[1]) { out.push({ t: m[1], c: m[2] ? "tk-fn" : "tk-str" }); if (m[2]) out.push({ t: ": ", c: "tk-punct" }); }
      else if (m[3]) out.push({ t: m[3], c: "tk-num" });
      else if (m[4]) out.push({ t: m[4], c: "tk-keyword" });
      else if (m[5]) out.push({ t: m[5] === "," ? ", " : m[5] === ":" ? ": " : m[5], c: "tk-punct" });
      else out.push({ t: m[0], c: "" });
    }
    return out;
  }

  var api = {
    status: status, resultLabel: resultLabel, rel: rel, dur: dur, hms: hms,
    dayLabel: dayLabel, gapLabel: gapLabel, span: span, isAgent: isAgent,
    highlightParts: highlightParts, searchTerms: searchTerms, matches: matches,
    facetCounts: facetCounts, lexJson: lexJson,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLFormat = api;
})(typeof window !== "undefined" ? window : globalThis);
