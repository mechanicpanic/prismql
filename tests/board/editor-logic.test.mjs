// Pins the editor's pure helpers (graph @aleph/prismql, node #63; task-6
// brief, fix round 1): the /evaluate body it actually sends (just query +
// corpus), the 422 → inline-error shape (line:column for syntax,
// message-only for runtime, joined messages for FastAPI's own
// {"detail": [...]} validation 422), which journal entry a finished run
// resolves to — by seq, no clocks — the paused-journal select-or-just-clear
// decision, unknown-corpus detection, and the recent-queries list.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const L = require("../../src/prismql/server/board/editor-logic.js");

test("buildEvaluateBody: just query when no corpus is set", () => {
  assert.deepEqual(L.buildEvaluateBody({ query: "SELECT $a", corpus: "" }), { query: "SELECT $a" });
});

test("buildEvaluateBody: carries corpus, and only query/corpus — no max_results, no hydrate", () => {
  const body = L.buildEvaluateBody({ query: "SELECT $a", corpus: "village" });
  assert.deepEqual(body, { query: "SELECT $a", corpus: "village" });
});

test("describeError: a syntax 422 carries line:column", () => {
  const d = L.describeError(422, { error: { type: "syntax", message: "unexpected token", line: 3, column: 12 } });
  assert.deepEqual(d, { pos: "3:12", message: "unexpected token" });
});

test("describeError: a runtime 422 has no position", () => {
  const d = L.describeError(422, { error: { type: "runtime", message: "unknown corpus 'x'" } });
  assert.deepEqual(d, { pos: null, message: "unknown corpus 'x'" });
});

test("describeError: FastAPI's own request-validation 422 ({detail: [...]}) joins the messages", () => {
  const d = L.describeError(422, {
    detail: [{ loc: ["body", "query"], msg: "field required", type: "value_error.missing" }],
  });
  assert.deepEqual(d, { pos: null, message: "field required" });
});

test("describeError: FastAPI detail with several entries joins them", () => {
  const d = L.describeError(422, { detail: [{ msg: "a" }, { msg: "b" }] });
  assert.equal(d.message, "a; b");
});

test("describeError: any other status describes itself with status + message", () => {
  const d = L.describeError(429, { error: { type: "rate_limit", message: "Too many queries — try again in a minute." } });
  assert.equal(d.pos, null);
  assert.equal(d.message, "HTTP 429 · Too many queries — try again in a minute.");
});

test("describeError: no body at all (network failure) still describes itself", () => {
  const d = L.describeError(0, null);
  assert.equal(d.pos, null);
  assert.match(d.message, /request failed/);
});

test("findPendingMatch: seq-only — an aggregate with a badly skewed clock still matches (ts never read)", () => {
  const entries = [
    { who: "board", result_id: null, query: "SELECT count($a)", seq: 12, ts: "1970-01-01T00:00:00Z" },
    { who: "board", result_id: null, query: "SELECT count($a)", seq: 5, ts: "2099-01-01T00:00:00Z" }, // below baseline
  ];
  const found = L.findPendingMatch(entries, { resultId: null, query: "SELECT count($a)", baselineSeq: 10 });
  assert.equal(found, entries[0]);
});

test("findPendingMatch: two identical board runs — each matches only the entry above its own baseline", () => {
  const entries = [
    { who: "board", result_id: null, query: "SELECT contains(x)", seq: 20 },
    { who: "board", result_id: null, query: "SELECT contains(x)", seq: 10 },
  ];
  const firstRun = L.findPendingMatch(entries, { resultId: null, query: "SELECT contains(x)", baselineSeq: 0 });
  assert.equal(firstRun, entries[1], "the first run's own baseline (0) is answered by the lower-seq entry");
  const secondRun = L.findPendingMatch(entries, { resultId: null, query: "SELECT contains(x)", baselineSeq: 10 });
  assert.equal(secondRun, entries[0], "the second run's baseline (10) excludes the first run's own entry");
});

test("findPendingMatch: result_id wins over query, and ignores who !== board", () => {
  const entries = [
    { who: "10.0.0.1", result_id: "r1", seq: 5 },
    { who: "board", result_id: "r2", seq: 6 },
    { who: "board", result_id: "r1", seq: 7 },
  ];
  const found = L.findPendingMatch(entries, { resultId: "r1", query: "x", baselineSeq: 0 });
  assert.equal(found, entries[2]);
});

test("findPendingMatch: an entry that arrived before the POST resolved (already in the array) still matches", () => {
  const entries = [{ who: "board", result_id: "r9", seq: 3 }];
  const found = L.findPendingMatch(entries, { resultId: "r9", query: "x", baselineSeq: 0 });
  assert.equal(found, entries[0]);
});

test("findPendingMatch: no pending run means no match", () => {
  assert.equal(L.findPendingMatch([{ who: "board" }], null), null);
});

test("resolvePendingRun: unresolved while absent from both the live and the paused journal", () => {
  assert.equal(L.resolvePendingRun([], [], { resultId: "r1", query: "x", baselineSeq: 0 }, "x"), null);
});

test("resolvePendingRun: found only in the paused queue (state.pending) still resolves", () => {
  const pendingQueue = [{ who: "board", result_id: "r1", seq: 4 }];
  const r = L.resolvePendingRun([], pendingQueue, { resultId: "r1", query: "x", baselineSeq: 0 }, "x");
  assert.equal(r.entry, pendingQueue[0]);
  assert.equal(r.select, true);
});

test("resolvePendingRun: select is true when the editor text is unchanged since the run started", () => {
  const entries = [{ who: "board", result_id: null, query: "SELECT $a", seq: 5 }];
  const r = L.resolvePendingRun(entries, [], { resultId: null, query: "SELECT $a", baselineSeq: 0 }, "SELECT $a");
  assert.equal(r.select, true);
});

test("resolvePendingRun: select is false once the user has typed something else — no tab flip, no focus steal", () => {
  const entries = [{ who: "board", result_id: null, query: "SELECT $a", seq: 5 }];
  const r = L.resolvePendingRun(entries, [], { resultId: null, query: "SELECT $a", baselineSeq: 0 }, "SELECT $b now");
  assert.equal(r.entry, entries[0], "the marker still resolves — the caller clears it");
  assert.equal(r.select, false);
});

test("unknownCorpus: false before /corpora has loaded at all — absence proves nothing yet", () => {
  assert.equal(L.unknownCorpus({ corpus: "village" }, null), false);
});

test("unknownCorpus: false when no corpus is chosen", () => {
  assert.equal(L.unknownCorpus({ corpus: null }, { corpora: ["village"] }), false);
});

test("unknownCorpus: false when the corpus is among the loaded names", () => {
  assert.equal(L.unknownCorpus({ corpus: "village" }, { corpora: ["village", "wiki"] }), false);
});

test("unknownCorpus: true once /corpora has loaded and the corpus isn't in it", () => {
  assert.equal(L.unknownCorpus({ corpus: "gone" }, { corpora: ["village", "wiki"] }), true);
});

test("recentQueries: only who === board, newest first, capped at 5", () => {
  const entries = [
    { who: "board", seq: 6 }, { who: "agent-1", seq: 5 }, { who: "board", seq: 4 },
    { who: "board", seq: 3 }, { who: "board", seq: 2 }, { who: "board", seq: 1 }, { who: "board", seq: 0 },
  ];
  const rec = L.recentQueries(entries);
  assert.deepEqual(rec.map((e) => e.seq), [6, 4, 3, 2, 1]);
});

test("singleLine: collapses a multi-line query for the compact list", () => {
  assert.equal(L.singleLine("SELECT $a\n  FOLLOWED_BY $b\nWITHIN 5m"), "SELECT $a FOLLOWED_BY $b WITHIN 5m");
});

// --- fix round 2 -----------------------------------------------------

test("findPendingMatch: a restart before the POST resolved — old baseline (500) is void, a fresh low seq (3) matches", () => {
  const entries = [{ who: "board", result_id: null, query: "SELECT $a", corpus: "village", seq: 3 }];
  const pending = { resultId: null, query: "SELECT $a", corpus: "village", baselineSeq: 500, boot: "old-boot" };
  const found = L.findPendingMatch(entries, pending, "new-boot");
  assert.equal(found, entries[0], "boot mismatch -> baseline treated as 0, not the stale 500");
});

test("findPendingMatch: boot unchanged — the old baseline still applies normally", () => {
  const entries = [{ who: "board", result_id: null, query: "SELECT $a", corpus: "village", seq: 3 }];
  const pending = { resultId: null, query: "SELECT $a", corpus: "village", baselineSeq: 500, boot: "same-boot" };
  assert.equal(L.findPendingMatch(entries, pending, "same-boot"), null, "seq 3 is below the still-valid baseline of 500");
});

test("findPendingMatch: a restart doesn't cause a late hijack — matching rules still apply past the reset baseline", () => {
  // Two board entries land after a restart; only one carries the pending's
  // own query — the reset baseline (now 0) must not make the OTHER one,
  // which arrived first, match just because it's also above baseline 0.
  const entries = [
    { who: "board", result_id: null, query: "SELECT count(y)", corpus: "village", seq: 2 }, // unrelated, arrived first
    { who: "board", result_id: null, query: "SELECT count(x)", corpus: "village", seq: 1 }, // ours, even though lower seq
  ];
  const pending = { resultId: null, query: "SELECT count(x)", corpus: "village", baselineSeq: 500, boot: "old-boot" };
  const found = L.findPendingMatch(entries, pending, "new-boot");
  assert.equal(found, entries[1], "still gated by query equality — the reset only changes the baseline, not the rules");
});

test("findPendingMatch: a result_id match also survives a boot mismatch", () => {
  const entries = [{ who: "board", result_id: "r1", seq: 2 }];
  const pending = { resultId: "r1", query: "x", baselineSeq: 500, boot: "old-boot" };
  assert.equal(L.findPendingMatch(entries, pending, "new-boot"), entries[0]);
});

test("findPendingMatch: an aggregate match also requires the same corpus (fix round 2, #3)", () => {
  const entries = [{ who: "board", result_id: null, query: "SELECT count($a)", corpus: "wiki", seq: 5 }];
  const pending = { resultId: null, query: "SELECT count($a)", corpus: "village", baselineSeq: 0 };
  assert.equal(L.findPendingMatch(entries, pending), null, "same query, different corpus — not a match");
});

test("findPendingMatch: an aggregate matches once both query and corpus agree", () => {
  const entries = [
    { who: "board", result_id: null, query: "SELECT count($a)", corpus: "wiki", seq: 4 },
    { who: "board", result_id: null, query: "SELECT count($a)", corpus: "village", seq: 5 },
  ];
  const pending = { resultId: null, query: "SELECT count($a)", corpus: "village", baselineSeq: 0 };
  assert.equal(L.findPendingMatch(entries, pending), entries[1]);
});

test("resolvePendingRun: threads currentBoot through to both the live and paused lookups", () => {
  const pendingQueue = [{ who: "board", result_id: null, query: "x", corpus: "v", seq: 2 }];
  const pending = { resultId: null, query: "x", corpus: "v", baselineSeq: 500, boot: "old" };
  const r = L.resolvePendingRun([], pendingQueue, pending, "x", "new");
  assert.equal(r.entry, pendingQueue[0]);
});

// --- fix round 3 -------------------------------------------------------
// An aggregate run sent before /corpora loaded (or when it failed) has
// pending.corpus === null, but the server always journals a real corpus
// name (req.corpus or its own default_corpus) — the strict corpus check
// from fix round 2 then never matched, and the run never resolved. A null
// pending.corpus skips the comparison instead of requiring corpus === null.

test("findPendingMatch: a null pending corpus skips the corpus check — matches an entry on the default corpus", () => {
  const entries = [{ who: "board", result_id: null, query: "SELECT count($a)", corpus: "wiki", seq: 5 }];
  const pending = { resultId: null, query: "SELECT count($a)", corpus: null, baselineSeq: 0 };
  assert.equal(L.findPendingMatch(entries, pending), entries[0]);
});

// --- finding 3: Run again / Open in editor dispatch by kind ---

test("hasRequestDictionaries: false when the entry carries no dictionaries", () => {
  assert.equal(L.hasRequestDictionaries({ kind: "evaluate", dictionaries: [] }), false);
  assert.equal(L.hasRequestDictionaries({ kind: "evaluate" }), false);
});

test("hasRequestDictionaries: true when the entry used request-scoped dictionaries", () => {
  assert.equal(L.hasRequestDictionaries({ kind: "evaluate", dictionaries: ["spikes"] }), true);
});

test("rerunBody: evaluate has no rerun body — it goes through the editor instead", () => {
  assert.equal(L.rerunBody({ kind: "evaluate", query: "SELECT from(a)" }), null);
});

test("rerunBody: search reruns via POST /search {query, corpus, limit}", () => {
  const body = L.rerunBody({ kind: "search", query: "spike OR calm", corpus: "village", total: 7 });
  assert.deepEqual(body, { query: "spike OR calm", corpus: "village", limit: 7 });
});

test("rerunBody: search without a total falls back to a sane default limit", () => {
  const body = L.rerunBody({ kind: "search", query: "spike", corpus: null, total: 0 });
  assert.deepEqual(body, { query: "spike", limit: 20 });
});

test("rerunBody: similar reruns via POST /similar {text, corpus, threshold, limit}", () => {
  const body = L.rerunBody({ kind: "similar", query: "calm seas", corpus: "village", total: 3, threshold: 0.5 });
  assert.deepEqual(body, { text: "calm seas", corpus: "village", threshold: 0.5, limit: 3 });
});

test("rerunBody: similar without a threshold omits it", () => {
  const body = L.rerunBody({ kind: "similar", query: "calm seas", corpus: null, total: 3 });
  assert.deepEqual(body, { text: "calm seas", limit: 3 });
});
