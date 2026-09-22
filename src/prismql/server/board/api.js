// PrismQLApi: the board's only path to the server (graph @aleph/prismql,
// node #63). Every call goes through here — no other file touches fetch or
// EventSource directly. Endpoints: GET /activity, GET /activity/stream (SSE),
// GET /results/{rid}, GET /results/{rid}.jsonl, GET /corpora, POST /evaluate.
(function (root) {
  "use strict";

  async function activity(since) {
    const r = await fetch("/activity?since=" + (since || 0) + "&limit=200");
    return r.json();
  }

  function stream(since, onEntry, onState) {
    let es = null;
    let lastSeq = since || 0;
    let closed = false;
    let retryTimer = null;

    function open() {
      if (closed) return;
      es = new EventSource("/activity/stream?since=" + lastSeq);
      es.addEventListener("seq", function () {
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
        if (onState) onState("down");
        if (es) es.close();
        es = null;
        if (!closed) retryTimer = setTimeout(open, 4000);
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
    return r.json();
  }

  function jsonlUrl(rid, hydrate) {
    const params = new URLSearchParams();
    if (hydrate != null) params.set("hydrate", hydrate);
    const qs = params.toString();
    return "/results/" + encodeURIComponent(rid) + ".jsonl" + (qs ? "?" + qs : "");
  }

  async function corpora() {
    const r = await fetch("/corpora");
    return r.json();
  }

  async function evaluate(body) {
    const r = await fetch("/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-PrismQL-Client": "board" },
      body: JSON.stringify(body),
    });
    return { status: r.status, body: await r.json() };
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
