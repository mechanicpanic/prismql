# Case study: the MATCH_RECOGNIZE flagship query, in four lines

Zhu, Huang & Chaudhuri open their VLDB 2023 paper on row-pattern
recognition ([*High-Performance Row Pattern Recognition Using Joins*,
PVLDB 16(5)](https://www.vldb.org/pvldb/vol16/p1181-zhu.pdf)) with a
MATCH_RECOGNIZE query over the City of Chicago crime dataset: a ROBBERY
followed by a BATTERY followed by a MOTOR VEHICLE THEFT, spatially
co-located, with the theft within 30 minutes of the robbery. Their
Figure 1 needs ~15 lines and five clauses (`PATTERN`, `DEFINE`,
`MEASURES`, `AFTER MATCH SKIP`, `ORDER BY`) — and its gap tolerance is
expressed by an *undefined* pattern variable, which matches any row by
spec default.

The same pattern in PrismQL, with the spatial box discretized into grid
cells at ingestion (`cell = (lon // 0.05, lat // 0.02)` — Chicago data
also ships pre-binned `beat`/`district` columns):

```prismql
SELECT field(type, "ROBBERY") AND field(cell, $c)
  FOLLOWED_BY field(type, "BATTERY") AND field(cell, $c) DURING 30 minutes
  FOLLOWED_BY field(type, "MOTOR VEHICLE THEFT") AND field(cell, $c) DURING 30 minutes
  DURING 30 minutes
```

Gap tolerance is what `FOLLOWED_BY` means; the trailing `DURING` is the
whole-chain span; `$c` is the correlation key (matching runs
independently per cell — the EQL `sequence by` evaluation shape).

## Results on the full corpus (8,473,715 crime reports, 2001–2026)

| engine | query | matches |
|---|---|---|
| **PrismQL** (Python backend) | **5.1s** | **372** |
| Flink SQL MATCH_RECOGNIZE | 6.8s | 570¹ |
| PrismQL (Rust backend) | 7.5s | 372 |
| DuckDB SQL, paper's bucketization rewrite | 10.1s | 372 |
| Elastic EQL (reference engine) | 20.2s | 556¹ |
| SQLite (row store) | 15.2 min | 372 |
| DuckDB SQL, naive join | DNF (>90 min) | — |

¹ Stream-order tie semantics: Chicago timestamps quantize to the minute,
so "B after R" is ambiguous when timestamps tie. Engines comparing
timestamps strictly (PrismQL, DuckDB, SQLite) agree exactly at 372;
engines using stream order (Flink, EQL) accept tied progressions and
disagree *with each other* on how.

Three observations the numbers make:

1. **The naive SQL formulation — what an analyst would actually write —
   never comes back.** The hash join on the spatial key materializes a
   25-year per-cell cross product before the time filter. The paper's
   contribution (prefilter symbols, bucketize by time, then match) fixes
   it: 376× at the 1M tier. PrismQL's evaluation model — conditions
   resolve to id sets, the sequence merge is time-localized — *is* that
   plan shape by construction, with no rewrite rule needed.
2. **Running the paper's own figure on a real MATCH_RECOGNIZE engine
   (Flink) silently returns zero matches as written.** Three deviations
   are required: greedy `Z*` must become reluctant `Z*?`, a watermark
   delay must be added for tied timestamps, and `WITHIN` is exclusive
   where the paper's predicate is inclusive (3 of 4 matches in one tier
   span exactly 30:00). Pattern queries are far less portable than they
   look.
3. **Pattern semantics are a benchmark dimension of their own**: same
   pattern, seven honest implementations, three distinct match counts —
   all defensible, all driven by tie and boundary handling at the data's
   time resolution.

Full methodology, runners for every engine, and raw numbers live in
[`prismql-research/benchmarks/chicago-crime/`](https://github.com/mechanicpanic/prismql-research).
