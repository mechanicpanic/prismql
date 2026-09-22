// PrismQLApi: the board's only path to the server (graph @aleph/prismql,
// node #63). Every call goes through here — no other file touches fetch or
// EventSource directly. Endpoints: GET /activity, GET /activity/stream (SSE),
// GET /results/{rid}, GET /results/{rid}.jsonl, GET /corpora, POST /evaluate.
(function (root) {
  "use strict";

  async function activity(since) {
    const r = await fetch("/activity?since=" + (since || 0) + "&limit=200");
    try {
      return await r.json();
    } catch (e) {
      throw new Error("activity: bad response (" + r.status + ")");
    }
  }

  function stream(since, onEntry, onState) {
    let es = null;
    let lastSeq = since || 0;
    let closed = false;
    let retryTimer = null;

    function open() {
      if (closed) return;
      es = new EventSource("/activity/stream?since=" + lastSeq);
      es.addEventListener("seq", function (m) {
        const serverSeq = Number(m.data);
        if (!Number.isNaN(serverSeq) && serverSeq < lastSeq) {
          // The server's own counter is behind what we last saw — it
          // restarted. Rebase on its count and tell the caller to clear
          // and backfill rather than stay deaf waiting for seq > lastSeq.
          lastSeq = serverSeq;
          if (onState) onState("reset");
        } else if (!Number.isNaN(serverSeq)) {
          lastSeq = Math.max(lastSeq, serverSeq);
        }
        if (onState) onState("live");
      });
      es.onmessage = function (m) {
        let entry;
        try {
          entry = JSON.parse(m.data);
        } catch (e) {
          return;
        }
        if (typeof entry.seq === "number") lastSeq = Math.max(lastSeq, entry.seq);
        if (onEntry) onEntry(entry);
      };
      es.onerror = function () {
        // Once a connection has opened, EventSource sets readyState back to
        // CONNECTING (and retries on its own) for ANY interruption — the
        // server's own clean end-of-stream (our ttl idle close) included.
        // CLOSED here means the browser gave up — a genuine fatal error
        // (e.g. the initial handshake failed) — and is the only case that
        // should flash "down" and back off (graph @aleph/prismql, node #76).
        const fatal = es && es.readyState === EventSource.CLOSED;
        if (es) es.close();
        es = null;
        if (closed) return;
        if (fatal) {
          if (onState) onState("down");
          retryTimer = setTimeout(open, 4000);
        } else {
          open();
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
    try {
      return await r.json();
    } catch (e) {
      throw new Error("corpora: bad response (" + r.status + ")");
    }
  }

  async function evaluate(body) {
    const r = await fetch("/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-PrismQL-Client": "board" },
      body: JSON.stringify(body),
    });
    let parsed = null;
    try {
      parsed = await r.json();
    } catch (e) {
      parsed = null;
    }
    return { status: r.status, body: parsed };
  }

  const api = {
    activity: activity,
    stream: stream,
    page: page,
    jsonlUrl: jsonlUrl,
    corpora: corpora,
    evaluate: evaluate,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PrismQLApi = api;
})(typeof window !== "undefined" ? window : globalThis);
