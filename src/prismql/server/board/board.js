/* PrismQL board — the server's journal, live, with the query editor beside it.
   Agents and people ask through the same endpoints; every request lands here
   as a summary (never the results). No framework, no build. */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const L = window.PrismQLLexer;

  function el(tag, props, children) {
    const n = document.createElement(tag);
    for (const k in props || {}) {
      const v = props[k];
      if (v == null) continue;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (k === "html") n.innerHTML = v;
      else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    for (const c of [].concat(children || [])) {
      if (c != null) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    }
    return n;
  }

  const feed = $("#feed"), status = $("#status"), editor = $("#editor"),
    highlight = $("#highlight"), result = $("#result"), corpusSel = $("#corpus"),
    onlyAgents = $("#only-agents");
  let lastSeq = 0;
  const rows = new Map(); // seq -> element
  const ME = "board";     // the X-PrismQL-Client name a human's runs carry

  // ---------------------------------------------------------------- corpora
  fetch("/corpora").then((r) => r.json()).then((body) => {
    for (const name of body.corpora || []) {
      corpusSel.appendChild(el("option", { value: name, text: name }));
    }
    if (body.default) corpusSel.value = body.default;
  }).catch(() => {});

  // ---------------------------------------------------------------- feed
  function outcome(e) {
    if (!e.ok) return (e.error && e.error.type) + ": " + (e.error && e.error.message);
    if (e.result === "aggregate") return "= " + e.value;
    const n = e.count == null ? "" : e.count + (e.result === "hits" ? " hits" : " groups");
    return n + (e.truncated ? " (capped)" : "") + (e.path ? " → file" : "");
  }

  function render(e, fresh) {
    const row = el("div", { class: "row " + (e.ok ? "" : "err") + (fresh ? " fresh" : ""), "data-seq": e.seq });
    if (e.who !== ME) row.classList.add("agent");
    const head = el("div", { class: "head", onclick: () => row.classList.toggle("open") }, [
      el("span", { class: "kind " + e.kind, text: e.kind }),
      el("span", { class: "who", text: e.who || "?" }),
      el("span", { text: e.corpus || "" }),
      el("span", { text: (e.ts || "").replace("T", " ").slice(5, 19) }),
      el("span", { class: "outcome", text: outcome(e) + (e.elapsed_ms != null ? " · " + Math.round(e.elapsed_ms) + " ms" : "") }),
    ]);
    const q = el("div", { class: "q", html: e.kind === "evaluate" ? L.highlight(e.query || "") : L.escapeHtml(e.query || "") });
    const detail = el("div", { class: "detail" }, [
      e.label ? el("div", {}, ["label: ", el("code", { text: e.label })]) : null,
      e.dictionaries && e.dictionaries.length ? el("div", {}, ["request dictionaries: ", el("code", { text: e.dictionaries.join(", ") })]) : null,
      e.path ? el("div", {}, ["file: ", el("code", { text: e.path })]) : null,
      el("div", { class: "actions" }, [
        el("button", { text: "open", onclick: () => reopen(e) }),
        el("button", { text: "edit", onclick: () => { load(e); editor.focus(); } }),
      ]),
    ]);
    row.append(head, q, detail);
    return row;
  }

  function add(e) {
    if (rows.has(e.seq)) return;
    const node = render(e, true);
    rows.set(e.seq, node);
    feed.prepend(node);
    applyFilter();
    while (feed.children.length > 500) feed.lastChild.remove();
  }

  function applyFilter() {
    const agents = onlyAgents.checked, corpus = corpusSel.value;
    for (const [, node] of rows) {
      const e = node._entry;
      let show = true;
      if (agents && !node.classList.contains("agent")) show = false;
      node.style.display = show ? "" : "none";
    }
  }
  onlyAgents.addEventListener("change", applyFilter);

  async function backfill() {
    const r = await fetch("/activity?since=" + lastSeq + "&limit=200");
    const body = await r.json();
    for (const e of body.entries || []) { add(e); lastSeq = Math.max(lastSeq, e.seq); }
    for (const n of feed.querySelectorAll(".row.fresh")) n.classList.remove("fresh");
  }

  function connect() {
    status.textContent = "connecting…"; status.classList.remove("live");
    const es = new EventSource("/activity/stream?since=" + lastSeq);
    es.onopen = () => { status.textContent = "live"; status.classList.add("live"); };
    es.onmessage = (m) => { const e = JSON.parse(m.data); add(e); lastSeq = Math.max(lastSeq, e.seq); };
    es.onerror = () => { status.textContent = "reconnecting…"; status.classList.remove("live"); es.close(); setTimeout(connect, 2000); };
  }

  // ---------------------------------------------------------------- editor
  function paint() {
    highlight.innerHTML = L.highlight(editor.value);
    highlight.scrollTop = editor.scrollTop;
  }
  editor.addEventListener("input", paint);
  editor.addEventListener("scroll", () => { highlight.scrollTop = editor.scrollTop; });
  editor.addEventListener("keydown", (ev) => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key === "Enter") { ev.preventDefault(); run(); }
  });
  $("#run").addEventListener("click", run);

  function load(e) {
    if (e.kind === "evaluate") { editor.value = e.query || ""; paint(); }
    if (e.corpus) corpusSel.value = e.corpus;
    editor.dataset.kind = e.kind; editor.dataset.text = e.kind === "evaluate" ? "" : (e.query || "");
  }

  async function post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-PrismQL-Client": ME },
      body: JSON.stringify(body),
    });
    return r.json();
  }

  function reopen(e) {
    load(e);
    if (e.kind === "evaluate") return run();
    const body = { corpus: e.corpus, limit: Number($("#max").value) || 20, hydrate: $("#hydrate").checked };
    const path = e.kind === "search" ? "/search" : "/similar";
    body[e.kind === "search" ? "query" : "text"] = e.query;
    result.textContent = "…";
    post(path, body).then(showHits).catch((err) => showError(String(err)));
  }

  function run() {
    const query = editor.value.trim();
    if (!query) return;
    result.textContent = "…";
    post("/evaluate", {
      query, corpus: corpusSel.value || undefined,
      max_results: Number($("#max").value) || 20, hydrate: $("#hydrate").checked,
    }).then(showGroups).catch((err) => showError(String(err)));
  }

  // ---------------------------------------------------------------- results
  function showError(msg) { result.replaceChildren(el("div", { class: "error", text: msg })); }

  function event(ev) {
    const meta = Object.entries(ev).filter(([k, v]) => k !== "text" && v != null && typeof v !== "object")
      .slice(0, 8).map(([k, v]) => k + "=" + String(v).slice(0, 40)).join("  ");
    return el("div", { class: "ev" }, [
      el("div", { class: "meta", text: meta }),
      ev.text != null ? el("div", { class: "text", text: String(ev.text).slice(0, 600) }) : null,
    ]);
  }

  function showGroups(body) {
    if (!body.ok) return showError((body.error && body.error.message) || JSON.stringify(body));
    const frag = document.createDocumentFragment();
    if (body.kind === "aggregate") {
      frag.appendChild(el("div", { class: "summary", text: body.function + " = " + body.value }));
    } else if (body.kind === "grouped") {
      frag.appendChild(el("div", { class: "summary", text: "grouped by " + (body.group_by || []).join(", ") }));
      frag.appendChild(el("pre", { text: JSON.stringify(body.groups, null, 1).slice(0, 4000) }));
    } else if (body.path) {
      frag.appendChild(el("div", { class: "summary", text: body.count + " groups written to " + body.path }));
    } else {
      frag.appendChild(el("div", { class: "summary", text: body.count + " groups" + (body.truncated ? " (capped — raise max)" : "") + " · " + body.elapsed_ms + " ms" }));
      for (const g of body.results || []) {
        frag.appendChild(el("div", { class: "group" }, [
          el("div", { class: "ids", text: (g.ids || []).join("  ") }),
          ...(g.events || []).map(event),
        ]));
      }
    }
    result.replaceChildren(frag);
  }

  function showHits(body) {
    if (!body.ok) return showError((body.error && body.error.message) || JSON.stringify(body));
    const frag = document.createDocumentFragment();
    frag.appendChild(el("div", { class: "summary", text: body.count + " hits" + (body.truncated ? " (capped)" : "") + (body.path ? " → " + body.path : "") }));
    for (const h of body.hits || []) {
      frag.appendChild(el("div", { class: "hit" }, [
        el("span", { class: "score", text: h.score.toFixed(3) + "  " + String(h.id) }),
        h.event ? event(h.event) : null,
      ]));
    }
    result.replaceChildren(frag);
  }

  backfill().then(connect).catch(connect);
})();
