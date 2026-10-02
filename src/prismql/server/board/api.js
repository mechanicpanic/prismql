// PrismQLApi: the board's only path to the server (graph @aleph/prismql,
// node #63) — no other file touches fetch or EventSource. Endpoints:
// /activity(+/stream SSE), /results/{rid}(+.jsonl), /corpora, /schema,
// POST /evaluate, /search, /similar.
(function (root) {
  "use strict";

  async function activity(since, limit) {
    const q = "since=" + (since || 0) + "&limit=" + (limit == null ? 200 : limit);
    const r = await fetch("/activity?" + q);
    try {
      return await r.json();
    } catch (e) {
      throw new Error("activity: bad response (" + r.status + ")");
    }
  }

  function stream(since, onEntry, onState, knownBoot) {
    let es = null;
    let lastSeq = since || 0;
    let boot = knownBoot || null;
    let closed = false;
    let retryTimer = null;

    function open() {
      if (closed) return;
      // Per-attempt: readyState can't tell a refused connection from a
      // clean close (Chrome reports CONNECTING for both) — whether the
      // seq handshake ever arrived on THIS attempt can.
      let opened = false;
      es = new EventSource("/activity/stream?since=" + lastSeq);
      es.addEventListener("seq", function (m) {
        opened = true;
        let data;
        try {
          data = JSON.parse(m.data);
        } catch (e) {
          return;
        }
        if (boot && data.boot && data.boot !== boot) {
          // The server's process changed under us — its counter and this
          // connection's "since" filter both reset. Stop; the caller
          // clears, backfills from 0 and reopens with the new boot.
          if (es) es.close();
          es = null;
          closed = true;
          if (onState) onState("reset", data.boot);
          return;
        }
        boot = data.boot;
        if (onState) onState("live");
      });
      es.onmessage = function (m) {
        let entry;
        try {
          entry = JSON.parse(m.data);
        } catch (e) {
          return;
        }
        // Only a delivered row advances lastSeq, never the handshake.
        if (typeof entry.seq === "number") lastSeq = Math.max(lastSeq, entry.seq);
        if (onEntry) onEntry(entry);
      };
      es.onerror = function () {
        // Always close ourselves — never let the browser's own auto-retry
        // run, it can't tell a clean close from a real failure either.
        if (es) es.close();
        es = null;
        if (closed) return;
        if (opened) {
          open(); // reached the handshake, then ended cleanly — retry now
        } else {
          if (onState) onState("down"); // never opened — back off, steady
          retryTimer = setTimeout(open, 4000);
        }
      };
    }
    open();

    return {
      close: function () {
        closed = true;
        if (retryTimer) clearTimeout(retryTimer);
        if (es) es.close();
        es = null;
      },
    };
  }

  async function page(rid, opts) {
    opts = opts || {};
    const params = new URLSearchParams();
    if (opts.offset != null) params.set("offset", opts.offset);
    if (opts.limit != null) params.set("limit", opts.limit);
    if (opts.hydrate != null) params.set("hydrate", opts.hydrate);
    if (opts.fields != null) params.set("fields", opts.fields);
    if (opts.explain) params.set("explain", "true"); // why each event is there (#119)
    const url = "/results/" + encodeURIComponent(rid) + "?" + params.toString();
    const r = await fetch(url);
    if (r.status === 404) return { gone: true };
    try {
      return await r.json();
    } catch (e) {
      return { error: { type: "http", message: "bad response (" + r.status + ")" } };
    }
  }

  function jsonlUrl(rid, hydrate) {
    const params = new URLSearchParams();
    if (hydrate != null) params.set("hydrate", hydrate);
    const qs = params.toString();
    return "/results/" + encodeURIComponent(rid) + ".jsonl" + (qs ? "?" + qs : "");
  }

  async function corpora() {
    const r = await fetch("/corpora");
    let body = null;
    try { body = await r.json(); } catch (e) { /* body stays null */ }
    // A non-2xx or a 2xx body missing "corpora" both reject — never
    // mistaken for real data (fix round 2, #1).
    if (!r.ok || !body || !Array.isArray(body.corpora)) {
      throw new Error("corpora: bad response (" + r.status + ")");
    }
    return body;
  }

  // The corpus schema, computed once per load on the server (graph #86).
  async function schema(corpus) {
    const r = await fetch("/schema?corpus=" + encodeURIComponent(corpus));
    let body = null;
    try { body = await r.json(); } catch (e) { /* body stays null */ }
    if (!r.ok || !body || !body.fields) {
      throw new Error((body && body.error && body.error.message) || "schema: bad response (" + r.status + ")");
    }
    return body;
  }

  // Shared by evaluate/search/similar — finding 3's "Run again" posts a
  // search/similar entry straight to its own endpoint, never /evaluate.
  async function post(path, body) {
    const r = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-PrismQL-Client": "board" },
      body: JSON.stringify(body),
    });
    let parsed = null;
    try { parsed = await r.json(); } catch (e) { parsed = null; }
    return { status: r.status, body: parsed };
  }
  function evaluate(body) { return post("/evaluate", body); }
  function search(body) { return post("/search", body); }
  function similar(body) { return post("/similar", body); }

  const api = {
    activity: activity, stream: stream, page: page,
    jsonlUrl: jsonlUrl, corpora: corpora, evaluate: evaluate,
    search: search, similar: similar, schema: schema,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLApi = api;
})(typeof window !== "undefined" ? window : globalThis);
