# Handoff: add a semantic-join operator (`~`) to prismql

**To:** the Claude working in `prismql`
**From:** a design/research session (econmatcher), 2026-06-14
**Status:** scoped, not started

---

## Mission (one sentence)

Make **"about the same thing as"** a first-class, composable predicate in prismql — a semantic-join operator `~` whose matches flow through the existing temporal/logical algebra (`AND`/`OR`/`NOT`, `FOLLOWED_BY`, `WITHIN`). **v1 = threshold-to-set** (ships on the existing engine, zero new theory). **v2 = scores-first ranking algebra** (the publishable contribution).

## Why (the bet)

prismql today matches only on keywords / fields / entities / time. Adding **semantic similarity as a composable operator** turns it into a *ranked semantic-join over streams* — which prior-art research found is an **unbuilt, defensible language package**. The matching engine underneath is **commodity** (any embedder + ANN); the language + ranking algebra is the bet. Defensible claim: *"the first general declarative query language with a ranked semantic-join over streams."* (NOT "first to compose similarity through temporal+logical operators" — HiMu refutes that.)
⚠️ The novelty verdict rests on **unverified 2026 preprints** (HiMu arXiv:2603.18558; VectraFlow arXiv:2604.03855) — confirm before any public claim. Full refs: `newsmatcher/docs/prior-art-references.md`.

## THE CRUX — read before designing

prismql's result model is **set-only**: `QueryResult = list[list[MessageId]]` (`src/prismql/types.py:15`); boolean ops are set algebra over `set[MessageId]`. **There is no per-item score channel.** Semantic similarity is inherently *ranked*. The whole design splits on this:

- **v1 — threshold-to-set:** `~` computes a similarity score, you **threshold it to a boolean** (`~"oil sanctions" > 0.7`) → a `set[MessageId]` → flows through the **existing** boolean/temporal engine untouched. Score discarded. Zero new theory; immediately composable with `FOLLOWED_BY`/`WITHIN`/`AND`. (This is VectraFlow's architecture.)
- **v2 — scores-first:** keep the score, propagate it through the algebra → a continuous top-k *ranked* stream. Requires evolving the result model + the algebra below. The research contribution. Build it **behind the same surface syntax**.

## Architecture facts (don't rediscover)

- **No AST/IR** — the visitor interprets the ANTLR parse tree directly (`src/prismql/engine.py:212` → `visit(tree)`). *(verify on open)*
- Result model set-only (`src/prismql/types.py:15`) — the reason v1 discards score.
- The backend is syntax-agnostic; predicates dispatch through `visitCondition` in `src/prismql/visitors/query_visitor.py`.
- **Blessed zero-grammar-change path exists:** prismql already accepts an injected named set via `PrecomputedIndexes(custom_features: Mapping[str, set[MessageId]])` (`src/prismql/backends/base.py:188,230,249`), queried by the existing `has_feature(name)` predicate (`src/prismql/grammar/PrismQL.g4:252`). So you can validate the *idea* with no grammar work at all (see v1 Option B). *(anchors from analysis — verify on open)*

## v1 build plan (threshold-to-set)

**Option A — real `~` predicate (the language feature):**
1. **Embed prismql's own corpus.** Messages already carry `MessageId`s. Embed message text with a commodity embedder (sentence-transformers locally, or a hosted embedding API) into a vector index **keyed by `MessageId`**. Because prismql owns the IDs, you sidestep the textmatch `corpus_id`-is-an-array-index footgun entirely — similarity search returns `MessageId`s directly.
2. **Grammar:** add a `SIMILAR` / `~` alternative to the condition rule in `src/prismql/grammar/PrismQL.g4` (alongside `contains`/`field`/`from`). Surface form e.g. `similar_to("text", 0.7)` or `~"text" > 0.7`. Regenerate the ANTLR lexer/parser/visitor.
3. **Backend method:** add `search_semantic(query_text, *, threshold | top_k) -> set[MessageId]` to the `SearchBackend` ABC (`src/prismql/backends/base.py`) and implement it in the in-memory backend (embed query → cosine vs index → threshold/top-k → `set[MessageId]`).
4. **Visitor:** new branch in `visitCondition` (`src/prismql/visitors/query_visitor.py`) that calls `search_semantic` and returns the set — exactly like the existing predicate branches. The existing set-algebra + window/sequence merging then handle composition for free.
5. **Result:** `similar_to("oil sanctions") AND from(reuters) FOLLOWED_BY similar_to("retail panic") WITHIN 1h` works, because each `~` leg is just a set.

**Option B — no grammar change (validate first):** an orchestrator computes the semantic set out-of-band (embed + threshold) and injects it as a `custom_features` entry; queries reference it via the existing `has_feature(semantic_intent)`. Zero grammar work. Use this to prove the idea, then promote to Option A's real `~` predicate.

Recommend: **B to validate, A to ship.**

## v2 ranking algebra (the contribution — behind the same surface)

Monotonicity is load-bearing (it's what lets Fagin/HRJN terminate early — pick non-monotone combiners and you forfeit efficiency).

| Operator | Score rule | Grounded in |
|---|---|---|
| `~` | `clamp01(cos)` — treat as **ordinal** (cosine is uncalibrated; Steck WWW'24). Optional Platt/isotonic calibration to license product. | LOTUS `sem_sim_join` |
| `AND` | `min(a,b)` (Gödel t-norm — safe for uncalibrated cosine) | fuzzy t-norm (Fagin) |
| `OR` | `max(a,b)` | dual t-conorm |
| `NOT` | `1−a` | ⚠️ order-*reversing* → breaks TA bounds. **Open problem.** Mitigate: NNF-normalize so `NOT` wraps leaves; treat `NOT ~X` as a fresh monotone leaf score. |
| `FOLLOWED_BY` / `~>` | rank-join over the time window, ranked by `min(s_L, s_R)` | HRJN (Ilyas VLDB'03) + Cayuga/SASE+ temporal |
| `WITHIN` | boolean filter, or monotone time-decay folded into the score | CQL windows |
| terminal `top-k` | Fagin TA/NRA early termination | Fagin-Lotem-Naor JCSS'03 |

- This is where you **evolve the set-only result model** to carry a score — likely the moment to introduce a minimal `Query`/result IR.
- **Open research problems = the contributions:** ranked negation; a scored-NFA accept semantics (`best_confirmed_score ≥ frontier_bound`); continuous top-k over composite path-scores (extends SWOOP's k-skyband, VLDB-J'24); ANN approximate-order → ε-approximate early termination.
- Key refs (see `newsmatcher/docs/prior-art-references.md`): Fagin TA/NRA https://arxiv.org/abs/cs/0204046 · HRJN https://www.vldb.org/conf/2003/papers/S23P01.pdf · RankSQL https://www.cs.ubc.ca/~laks/cpsc504/ranksql-sigmod05-lcis-mar05.pdf · t-norms https://en.wikipedia.org/wiki/T-norm · VectraFlow (the closest semantic-CEP) ⚠️ https://arxiv.org/abs/2604.03855

## Independent of surface syntax

There is a **separate** experiment (`prismql-research/HANDOFF-pipeline-syntax-ab.md`) on whether the surface should stay SQL-flavored or move to a pipeline style. The `~` operator works **regardless** of which surface wins — in SQL-flavored it's `similar_to("…")`; in pipeline it's `|> match("…")` or `a ~ b`. The two tracks can proceed in parallel.

## Scope guardrails

- Ship **v1 threshold-to-set first** — it's a graded leaf predicate on the existing engine. Do not build the scores-first algebra or the IR to get a working `~`.
- Keep the commodity embedder behind the `SearchBackend` interface so it's swappable (local model ↔ hosted API). The engine is not the moat; the language is.
