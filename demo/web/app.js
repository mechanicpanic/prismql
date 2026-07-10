/* ============================================================
   PrismQL demo — dual-dialect editor, corpus tabs, spectral results.
   No framework, no build, no external assets.
   ============================================================ */
(function () {
  "use strict";

  // --------------------------------------------------------
  // tiny DOM helpers
  // --------------------------------------------------------
  const $ = (sel) => document.querySelector(sel);

  /** el("div", {class:"x"}, [children|string]) — text goes via textContent (safe). */
  function el(tag, props, children) {
    const node = document.createElement(tag);
    if (props) {
      for (const k in props) {
        const v = props[k];
        if (v == null) continue;
        if (k === "class") node.className = v;
        else if (k === "text") node.textContent = v;
        else if (k === "html") node.innerHTML = v;
        else if (k.slice(0, 2) === "on" && typeof v === "function")
          node.addEventListener(k.slice(2), v);
        else node.setAttribute(k, v);
      }
    }
    if (children != null) {
      const list = Array.isArray(children) ? children : [children];
      for (const c of list) {
        if (c == null) continue;
        node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
      }
    }
    return node;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // --------------------------------------------------------
  // state + element refs
  // --------------------------------------------------------
  const state = {
    corpus: null,
    corpora: [],
    dialect: "classic", // "classic" | "pipe"
    activeExample: null, // the curated example whose text currently matches
    running: false,
  };

  const editor = $("#editor");
  const highlight = $("#highlight");
  const runBtn = $("#run");
  const latencyEl = $("#latency");
  const tabsEl = $("#corpus-tabs");
  const examplesEl = $("#examples");
  const resultsEl = $("#results");
  const toggleEl = $("#dialect-toggle");

  const EXAMPLES = window.EXAMPLES || { fcc: [], chicago: [] };

  const CORPUS_LABELS = {
    fcc: "freeCodeCamp chat",
    chicago: "Chicago crime",
  };

  // --------------------------------------------------------
  // syntax highlighter — one tokenizer for both dialects
  // --------------------------------------------------------
  const KEYWORDS = new Set([
    // classic
    "select", "and", "or", "not",
    "followed_by", "preceded_by", "not_followed_by", "not_preceded_by",
    "inwindow", "inwin", "during", "within",
    "aggregate", "group", "by", "order", "limit", "as", "asc", "desc",
    // pipe stages / aggregates
    "sort", "top", "skip", "count", "sum", "avg", "min", "max",
  ]);
  const UNITS = new Set([
    "h", "m", "s", "d",
    "hour", "hours", "minute", "minutes", "second", "seconds", "day", "days",
    "min", "mins", "sec", "secs",
  ]);

  const isWord = (c) => /[A-Za-z0-9_]/.test(c);

  function tokenize(src) {
    const out = [];
    let i = 0;
    const n = src.length;
    const push = (cls, val) => out.push({ c: cls, v: val });

    while (i < n) {
      const c = src[i];

      // whitespace
      if (/\s/.test(c)) {
        let j = i + 1;
        while (j < n && /\s/.test(src[j])) j++;
        push(null, src.slice(i, j));
        i = j;
        continue;
      }

      // multi-char arrow / pipe operators (longest first)
      const three = src.slice(i, i + 3);
      if (three === "!~>" || three === "!<~") {
        push("arrow", three);
        i += 3;
        continue;
      }
      const two = src.slice(i, i + 2);
      if (two === "~>" || two === "<~" || two === "|>") {
        push("arrow", two);
        i += 2;
        continue;
      }
      if (c === "+") {
        push("arrow", c);
        i += 1;
        continue;
      }

      // variable
      if (c === "$") {
        let j = i + 1;
        while (j < n && isWord(src[j])) j++;
        push("var", src.slice(i, j));
        i = j;
        continue;
      }

      // double-quoted string
      if (c === '"') {
        let j = i + 1;
        while (j < n && src[j] !== '"') j++;
        if (j < n) j++; // include closing quote
        push("str", src.slice(i, j));
        i = j;
        continue;
      }

      // number (+ attached unit like 1h / 30m)
      if (/[0-9]/.test(c)) {
        let j = i + 1;
        while (j < n && /[0-9]/.test(src[j])) j++;
        while (j < n && /[A-Za-z]/.test(src[j])) j++; // attached unit letters
        push("num", src.slice(i, j));
        i = j;
        continue;
      }

      // identifier / keyword / condition-name / unit-word
      if (/[A-Za-z_]/.test(c)) {
        let j = i + 1;
        while (j < n && isWord(src[j])) j++;
        const word = src.slice(i, j);
        const lower = word.toLowerCase();
        // peek next non-space char to detect a call
        let k = j;
        while (k < n && /\s/.test(src[k])) k++;
        const followedByParen = src[k] === "(";

        if (KEYWORDS.has(lower)) {
          // stage / boolean / aggregate words are always keywords
          push("keyword", word);
        } else if (followedByParen) {
          // condition or bucket function: from(...), contains(...), day(...)
          push("fn", word);
        } else if (UNITS.has(lower)) {
          push("num", word); // bare time unit: "1 hour", "30 minutes"
        } else {
          push(null, word); // bareword arg, dictionary name, field value
        }
        i = j;
        continue;
      }

      // punctuation: brackets, braces, parens, commas
      if ("(){}[],".indexOf(c) !== -1) {
        push("punct", c);
        i += 1;
        continue;
      }

      // anything else
      push(null, c);
      i += 1;
    }
    return out;
  }

  function renderHighlight() {
    const text = editor.value;
    const toks = tokenize(text);
    let html = "";
    for (const t of toks) {
      const esc = escapeHtml(t.v);
      html += t.c ? '<span class="tk-' + t.c + '">' + esc + "</span>" : esc;
    }
    // keep trailing newline visible
    if (text.endsWith("\n")) html += "\n";
    highlight.innerHTML = html;
    highlight.scrollTop = editor.scrollTop;
  }

  // --------------------------------------------------------
  // dialect toggle
  // --------------------------------------------------------
  const normWs = (s) => String(s).replace(/\s+/g, " ").trim();

  function findActiveMatch() {
    const cur = normWs(editor.value);
    if (!cur) return null;
    const list = EXAMPLES[state.corpus] || [];
    for (const ex of list) {
      if (normWs(ex.classic) === cur) return { ex, dialect: "classic" };
      if (normWs(ex.pipe) === cur) return { ex, dialect: "pipe" };
    }
    return null;
  }

  function updateToggleState() {
    const match = findActiveMatch();
    const segs = toggleEl.querySelectorAll(".seg");
    if (match) {
      state.activeExample = match.ex;
      state.dialect = match.dialect;
      toggleEl.classList.remove("disabled");
      toggleEl.removeAttribute("title");
      segs.forEach((b) =>
        b.classList.toggle("active", b.dataset.dialect === match.dialect)
      );
    } else {
      state.activeExample = null;
      toggleEl.classList.add("disabled");
      toggleEl.setAttribute(
        "title",
        "toggle works on curated examples — both forms provably identical"
      );
    }
    highlightActiveChip();
  }

  function setDialect(dialect) {
    if (toggleEl.classList.contains("disabled")) return;
    if (!state.activeExample || dialect === state.dialect) return;
    state.dialect = dialect;
    editor.value = state.activeExample[dialect];
    renderHighlight();
    updateToggleState();
    runQuery();
  }

  // --------------------------------------------------------
  // corpus tabs
  // --------------------------------------------------------
  function buildTabs() {
    tabsEl.innerHTML = "";
    for (const c of state.corpora) {
      const tab = el("button", {
        class: "corpus-tab" + (c === state.corpus ? " active" : ""),
        type: "button",
        text: CORPUS_LABELS[c] || c,
        onclick: () => selectCorpus(c),
      });
      tabsEl.appendChild(tab);
    }
  }

  function selectCorpus(c) {
    if (c === state.corpus) return;
    state.corpus = c;
    buildTabs();
    buildChips();
    // load the first example of the corpus in the current dialect
    const first = (EXAMPLES[c] || [])[0];
    if (first) {
      loadExample(first);
    } else {
      editor.value = "";
      renderHighlight();
      updateToggleState();
      resultsEl.innerHTML = "";
    }
  }

  // --------------------------------------------------------
  // example chips (grouped by category)
  // --------------------------------------------------------
  const CATEGORY_ORDER = [
    "Boolean",
    "Sequences",
    "Variables",
    "Negative",
    "Temporal",
    "Positional",
    "Aggregation",
  ];

  function categorize(ex) {
    const s = (ex.classic || "") + "   " + (ex.pipe || "");
    if (/\bAGGREGATE\b|\bGROUP\s+BY\b|\|>\s*(count|sum|avg|min|max|group)\b|(count|sum|avg|group)\(/i.test(s))
      return "Aggregation";
    if (/NOT_FOLLOWED_BY|NOT_PRECEDED_BY|!~>|!<~/.test(s)) return "Negative";
    if (/\$[A-Za-z_]/.test(s)) return "Variables";
    if (/\bDURING\b|\bduring\(/i.test(s)) return "Temporal";
    if (/FOLLOWED_BY|PRECEDED_BY|~>|<~/.test(s)) return "Sequences";
    if (/\bINWINDOW\b|\bINWIN\b|\bwithin\(/i.test(s)) return "Positional";
    return "Boolean";
  }

  function buildChips() {
    examplesEl.innerHTML = "";
    const list = EXAMPLES[state.corpus] || [];
    const buckets = {};
    for (const ex of list) {
      const cat = categorize(ex);
      (buckets[cat] = buckets[cat] || []).push(ex);
    }
    for (const cat of CATEGORY_ORDER) {
      const items = buckets[cat];
      if (!items || !items.length) continue;
      const row = el("div", { class: "chip-row" });
      for (const ex of items) {
        const chip = el("button", {
          class: "chip",
          type: "button",
          "data-classic": ex.classic,
          onclick: () => loadExample(ex),
        }, [
          el("span", { class: "chip-label", text: ex.label }),
          ex.blurb ? el("span", { class: "chip-blurb", text: ex.blurb }) : null,
        ]);
        row.appendChild(chip);
      }
      const group = el("div", { class: "example-group" }, [
        el("div", { class: "example-caption", text: cat }),
        row,
      ]);
      examplesEl.appendChild(group);
    }
  }

  function highlightActiveChip() {
    const active = state.activeExample;
    examplesEl.querySelectorAll(".chip").forEach((chip) => {
      chip.classList.toggle(
        "active",
        !!active && chip.getAttribute("data-classic") === active.classic
      );
    });
  }

  function loadExample(ex) {
    editor.value = ex[state.dialect] != null ? ex[state.dialect] : ex.classic;
    renderHighlight();
    updateToggleState();
    runQuery();
  }

  // --------------------------------------------------------
  // run query
  // --------------------------------------------------------
  function setRunning(b) {
    state.running = b;
    runBtn.classList.toggle("busy", b);
    runBtn.querySelector(".run-label").textContent = b ? "Running" : "Run";
  }

  async function runQuery() {
    const query = editor.value.trim();
    if (!query || state.running) return;
    setRunning(true);
    latencyEl.hidden = true;
    try {
      const res = await fetch("/evaluate", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ query, corpus: state.corpus, max_results: 25 }),
      });
      const body = await res.json();
      setRunning(false);
      if (body && body.ok) renderResults(body);
      else renderError((body && body.error) || { type: "runtime", message: "Unknown error." }, query);
    } catch (err) {
      setRunning(false);
      renderError(
        { type: "runtime", message: "Could not reach the server. Is it running?\n\n" + (err && err.message ? err.message : String(err)) },
        query
      );
    }
  }

  // --------------------------------------------------------
  // results rendering
  // --------------------------------------------------------
  function showLatency(ms) {
    if (typeof ms !== "number") {
      latencyEl.hidden = true;
      return;
    }
    latencyEl.hidden = false;
    latencyEl.innerHTML = "";
    latencyEl.appendChild(document.createTextNode("evaluated in "));
    latencyEl.appendChild(el("b", { text: ms.toFixed(ms < 10 ? 2 : 1) + " ms" }));
  }

  function resultsHead(kind, countText, note) {
    return el("div", { class: "results-head" }, [
      el("span", { class: "rh-kind", text: kind }),
      countText ? el("span", { class: "rh-count", text: countText }) : null,
      note ? el("span", { class: "rh-note", text: note }) : null,
    ]);
  }

  function renderResults(body) {
    showLatency(body.elapsed_ms);
    const frag = el("div", { class: "fade-in" });

    if (body.kind === "aggregate") {
      renderAggregate(frag, body);
    } else if (body.kind === "grouped") {
      renderGrouped(frag, body);
    } else {
      // "groups" or "named"
      renderMatches(frag, body);
    }

    resultsEl.innerHTML = "";
    resultsEl.appendChild(frag);
  }

  function renderMatches(frag, body) {
    const results = body.results || [];
    const count = body.count != null ? body.count : results.length;
    const note = body.truncated ? "showing first " + results.length : null;
    frag.appendChild(
      resultsHead(
        body.kind === "named" ? "named matches" : "matches",
        count + (count === 1 ? " group" : " groups"),
        note
      )
    );

    if (body.kind === "named" && Array.isArray(body.labels) && body.labels.length) {
      const legend = el("div", { class: "labels-legend" });
      body.labels.forEach((lbl, idx) => {
        legend.appendChild(
          el("span", { class: "lbl", html: "$" + escapeHtml(String(lbl)) + " <b>" + (idx + 1) + "</b>" })
        );
      });
      frag.appendChild(legend);
    }

    if (!results.length) {
      frag.appendChild(emptyState());
      return;
    }

    const isChicago = state.corpus === "chicago";
    results.forEach((group, gi) => {
      frag.appendChild(
        isChicago ? chicagoCard(group, gi) : fccCard(group, gi)
      );
    });
  }

  // ---- FCC: chat bubbles ----
  function fccCard(group, gi) {
    const events = group.events || [];
    const card = el("div", { class: "match" }, [
      el("div", { class: "match-tag" }, [
        el("span", { text: "Match " + (gi + 1) }),
        el("span", { class: "ids", text: "  ·  ids " + (group.ids || []).join(", ") }),
      ]),
    ]);
    events.forEach((ev, i) => {
      if (i > 0) card.appendChild(seqLink());
      card.appendChild(bubble(ev));
    });
    return card;
  }

  function bubble(ev) {
    const ts = ev.timestamp;
    return el("div", { class: "msg" }, [
      el("div", { class: "msg-head" }, [
        el("span", { class: "msg-user", text: ev.user || "unknown" }),
        ev.topic ? el("span", { class: "msg-topic", text: ev.topic }) : null,
        ts != null
          ? el("span", { class: "msg-time", text: relTime(ts), title: fullTime(ts) })
          : null,
      ]),
      el("div", { class: "msg-text", text: ev.text != null ? ev.text : "" }),
    ]);
  }

  function seqLink() {
    return el("div", { class: "seq-link" }, [
      el("span", {
        html:
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="6 13 12 19 18 13"></polyline></svg>',
      }),
      el("span", { text: "then" }),
    ]);
  }

  // ---- Chicago: timeline ----
  function chicagoCard(group, gi) {
    const events = group.events || [];
    const tl = el("div", { class: "timeline" });
    events.forEach((ev) => {
      const ts = ev.timestamp;
      tl.appendChild(
        el("div", { class: "tl-event" }, [
          el("div", { class: "tl-row" }, [
            el("span", { class: "type-badge", text: ev.type || "EVENT" }),
            ts != null
              ? el("span", { class: "tl-time", text: fullTime(ts) })
              : null,
            ev.key ? el("span", { class: "tl-key", text: ev.key }) : null,
          ]),
        ])
      );
    });
    return el("div", { class: "match" }, [
      el("div", { class: "match-tag" }, [
        el("span", { text: "Match " + (gi + 1) }),
        el("span", { class: "ids", text: "  ·  ids " + (group.ids || []).join(", ") }),
      ]),
      tl,
    ]);
  }

  // ---- aggregate ----
  function renderAggregate(frag, body) {
    // grouped aggregate → bar list; simple aggregate → big number
    if (body.grouped_values && typeof body.grouped_values === "object") {
      const entries = Object.entries(body.grouped_values);
      frag.appendChild(
        resultsHead(
          (body.function || "aggregate") + " by bucket",
          entries.length + (entries.length === 1 ? " bucket" : " buckets")
        )
      );
      if (!entries.length) {
        frag.appendChild(emptyState());
        return;
      }
      frag.appendChild(barList(entries, { sortKey: true }));
      return;
    }
    // simple scalar
    const fn = body.function || "aggregate";
    const caption = body.field ? fn + " of " + body.field : fn;
    frag.appendChild(
      el("div", { class: "bignum" }, [
        el("div", { class: "value", text: formatNumber(body.value) }),
        el("div", { class: "caption", text: caption }),
      ])
    );
  }

  // ---- grouped ----
  function renderGrouped(frag, body) {
    const counts = body.group_counts || {};
    const entries = Object.entries(counts);
    const groupBy = Array.isArray(body.group_by) ? body.group_by.join(", ") : "";
    frag.appendChild(
      resultsHead(
        "grouped",
        entries.length + (entries.length === 1 ? " group" : " groups")
      )
    );
    if (groupBy) {
      frag.appendChild(
        el("div", {
          class: "grouped-meta",
          html: "grouped by <code>" + escapeHtml(groupBy) + "</code>",
        })
      );
    }
    if (!entries.length) {
      frag.appendChild(emptyState());
      return;
    }
    frag.appendChild(barList(entries, { sortValue: true }));
  }

  // ---- shared: bar list ----
  function barList(entries, opts) {
    opts = opts || {};
    let rows = entries.slice();
    if (opts.sortValue) rows.sort((a, b) => Number(b[1]) - Number(a[1]));
    else if (opts.sortKey) rows.sort((a, b) => String(a[0]).localeCompare(String(b[0])));
    const max = rows.reduce((m, r) => Math.max(m, Number(r[1]) || 0), 0) || 1;
    const wrap = el("div", { class: "bars" });
    for (const [label, value] of rows) {
      const pct = Math.max(2, (Number(value) / max) * 100);
      wrap.appendChild(
        el("div", { class: "bar" }, [
          el("span", { class: "bar-label", text: String(label), title: String(label) }),
          el("div", { class: "bar-track" }, [
            el("div", { class: "bar-fill", style: "width:" + pct + "%" }),
          ]),
          el("span", { class: "bar-value", text: formatNumber(value) }),
        ])
      );
    }
    return wrap;
  }

  // ---- empty + error ----
  function emptyState() {
    return el("div", { class: "empty" }, [
      el("div", { class: "glyph", text: "◇" }),
      el("div", { class: "headline", text: "No matches" }),
      el("div", {
        class: "sub",
        text: "The query ran cleanly — this corpus just holds nothing that fits the pattern.",
      }),
    ]);
  }

  function renderError(err, query) {
    latencyEl.hidden = true;
    err = err || {};
    const hasLoc = err.line != null && err.column != null;
    const panel = el("div", { class: "error-panel fade-in" });

    const head = el("div", { class: "err-head" }, [
      el("span", { text: (err.type || "error") + " error" }),
      hasLoc
        ? el("span", { class: "loc", text: "line " + err.line + ", col " + err.column })
        : null,
    ]);
    panel.appendChild(head);
    panel.appendChild(
      el("div", { class: "err-msg", text: err.message || "Something went wrong." })
    );

    // caret code-frame when we have a single-line query + column
    if (hasLoc && query && query.indexOf("\n") === -1) {
      const col = Math.max(0, Number(err.column));
      const caret = " ".repeat(col) + "^";
      panel.appendChild(
        el("div", { class: "error-frame" }, [
          el("div", { class: "frame-q", text: query }),
          el("div", { class: "frame-caret", text: caret }),
        ])
      );
    }

    resultsEl.innerHTML = "";
    resultsEl.appendChild(panel);
  }

  // --------------------------------------------------------
  // formatting helpers
  // --------------------------------------------------------
  function formatNumber(v) {
    const n = Number(v);
    if (!isFinite(n)) return String(v);
    if (Number.isInteger(n)) return n.toLocaleString("en-US");
    return n.toLocaleString("en-US", { maximumFractionDigits: 2 });
  }

  function relTime(sec) {
    const diff = Date.now() / 1000 - Number(sec);
    const abs = Math.abs(diff);
    const units = [
      ["y", 31536000],
      ["mo", 2592000],
      ["d", 86400],
      ["h", 3600],
      ["m", 60],
      ["s", 1],
    ];
    for (const [u, size] of units) {
      if (abs >= size) {
        const val = Math.floor(abs / size);
        return diff >= 0 ? val + u + " ago" : "in " + val + u;
      }
    }
    return "just now";
  }

  function fullTime(sec) {
    try {
      const d = new Date(Number(sec) * 1000);
      return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (e) {
      return String(sec);
    }
  }

  // --------------------------------------------------------
  // events + init
  // --------------------------------------------------------
  editor.addEventListener("input", () => {
    renderHighlight();
    updateToggleState();
  });
  editor.addEventListener("scroll", () => {
    highlight.scrollTop = editor.scrollTop;
    highlight.scrollLeft = editor.scrollLeft;
  });
  editor.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      runQuery();
    }
  });

  runBtn.addEventListener("click", runQuery);

  toggleEl.querySelectorAll(".seg").forEach((btn) => {
    btn.addEventListener("click", () => setDialect(btn.dataset.dialect));
  });

  async function init() {
    try {
      const res = await fetch("/corpora");
      const data = await res.json();
      state.corpora = data.corpora || Object.keys(EXAMPLES);
      state.corpus = data.default || state.corpora[0];
    } catch (e) {
      // offline fallback: rely on the bundled examples
      state.corpora = Object.keys(EXAMPLES);
      state.corpus = state.corpora[0] || "fcc";
    }

    buildTabs();
    buildChips();

    const first = (EXAMPLES[state.corpus] || [])[0];
    if (first) {
      editor.value = first.classic;
      renderHighlight();
      updateToggleState();
      runQuery();
    } else {
      renderHighlight();
      updateToggleState();
    }
  }

  init();
})();
