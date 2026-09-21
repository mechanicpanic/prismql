# Ordinal Axis P3 — one operator layer over the plan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every sequence/window operator of the language is executed by exactly one code path — the Polars plan primitives of P2 — on both dialects and both `use_ir` paths; the legacy builders, the backtracking merger, the post-hoc variable validator and the Rust operator kernels are deleted; the pinned audit defects A1–A10 and D2 are fixed by construction and their `xfail(strict)` markers removed.

**Architecture:** A new module `prismql/plan/operators.py` turns the *evaluated predicate sets* the executor already produces (`set[MessageId]` per leg) into result frames by calling the P2 primitives; a per-query frame (`prismql/plan/frames.py`) is built from the backend's order axis plus the documents of the ids that take part, so no backend needs to expose its whole corpus. The IR executor and the legacy visitor call this layer through the four shared helpers they already share (`_apply_sequential_link`, `_apply_negative_link`, `_merge_restrictions`, `_merge_subqueries_positional`) and through a new co-occurrence path; the trailing `DURING` becomes a body-span filter on the frame. Predicate evaluation (dictionaries, fields, questions, NER, semantic) is untouched — it stays on the backends.

**Tech Stack:** Python ≥ 3.12, polars 1.44.x (`[plan]` extra becomes a core dependency in Task 9), pyarrow, pytest. No Rust on the operator path.

**Spec:** `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` — "P3 — the single operator layer", the review amendments (strict temporal inequality; `(ts, pos)` only orders candidates; backend temporal APIs stay id-based), and audit A1–A10. Decisions taken for this plan (graph `@aleph/prismql`): **#46** `{n,}` without a ceiling is rejected at validation, `[engine] quantifier_ceiling = m` turns it into `{n,m}`; **#47** an lhs row without an axis value on a negative link is not in the result. Defects it closes: #12 (D2), #16 (A7/A8), #29 (A9), #44 (A10). Kriya **#11**; transformation **#15**.

## Global Constraints

- Silent-wrong is the enemy: every task ends with `make check` green and, from Task 4 on, with the xfail markers it makes pass **removed in the same commit** (a strict xfail that passes fails the suite — that is the signal).
- Stream order = load order; ids are labels (spec). Positional distance is `position` arithmetic, never id arithmetic.
- Temporal links are strict (`>` on the axis); `(axis, position)` only breaks ties.
- Both dialects lower to one IR; the classic/pipe IR-equality tests and `use_ir` on/off equality tests stay green at every step.
- Chicago 372 (temporal, full corpus, owner's word only) and the 100k/1m tiers (`PRISMQL_TIERS`) are the benchmark gates; positional queries are gated on the tiers by full tuple equality against `tests/plan` oracles.
- Stage commits with explicit paths; the owner pushes.
- Every task: graph reconnaissance is done (this plan); a decision born mid-task lands in the graph before session end.

## File Structure

| File | Responsibility |
|---|---|
| `src/prismql/plan/frames.py` (new) | `query_frame(backend, ids, *, fields, timestamp_field)` → LazyFrame `(position, id, <fields>, <ts>_us)` for the ids of one query, from the backend's `OrderIndex` and `get_documents`. `leg_frame(frame, ids)` → the rows of one predicate set. |
| `src/prismql/plan/operators.py` (new) | The operator layer: `Leg`, `link`, `negative_link`, `cooccur_row`, `quantified_row`, `chain_groups`, `body_span`, `to_groups`. Pure functions on frames + leg descriptors; no backend access. |
| `src/prismql/plan/primitives.py` | +`link_groups` (group-to-group nearest link for subquery chains). Everything else unchanged. |
| `src/prismql/plan/__init__.py` | export the operator layer; `_pl()` stays. |
| `src/prismql/ir/executor.py` | `execute_restrictions`/`execute_restriction`/`execute_body` call the operator layer; `PartialSequence` stays as the "no window yet" carrier; variable constraints become leg descriptors, no post-hoc validator. |
| `src/prismql/visitors/query_visitor.py` | Shared helpers delegate to the operator layer; the `_create_sequential_pairs*`, `_extend_sequences_*`, `_apply_followed_by/preceded_by/not_*`, `_apply_link_partitioned`, `_merge_*`, `_generate_all_combinations`, `_temporal_link_kernel`, `_positional_universe` bodies are deleted. |
| `src/prismql/processors/window.py`, `processors/variables.py` | Deleted (Task 7). `processors/temporal.py` keeps parse/filter_by_time_range (BEFORE/AFTER/BETWEEN); `filter_by_time_window` deleted. |
| `src/prismql/backends/rust_memory.py`, `backends/factory.py`, `backends/memory.py` | Rust operator kernels no longer dispatched; `RustMemoryBackend` stays as a search-only backend if its suite passes without kernels, else removed (Task 7 decides by the tests, records in the graph). `merge_within_time_window` / `filter_by_time_window` backend methods deleted. |
| `src/prismql/validator.py`, `server/config.py`, `engine.py` | `quantifier_ceiling` (Task 1). |
| `src/prismql/grammar/PrismQL.g4`, `dialects/pipe.py`, `ir/nodes.py`, `ir/lower.py` | `!$k` (Task 8). |
| `tests/plan/test_frames.py`, `tests/plan/test_operators.py`, `tests/plan/test_link_groups.py` (new) | Oracles for the new module and primitive. |
| `tests/test_ordinal_axis_contract.py`, `tests/test_engine_defects_pinned.py`, `tests/test_positional_path_parity.py`, `tests/test_quantifier_fix.py` | xfail markers removed as they pass; tests kept as contracts. |
| `LANGUAGE_REFERENCE.md`, `PIPE_REFERENCE.md`, `CHANGELOG.md`, `STATE.md`, `AGENTS.md`, `skills/prismql/SKILL.md` | Task 9. |

## Task 1: `{n,}` needs a ceiling (decision #46)

**Files:** Modify `src/prismql/validator.py` (`_check_ir_expr`, the `NamedRestriction` branch), `src/prismql/engine.py` (`__init__` gets `quantifier_ceiling: int | None = None`), `src/prismql/server/config.py` (`[engine] quantifier_ceiling`), `src/prismql/ir/executor.py` (`execute_restrictions`: `max_count is None` → `self.quantifier_ceiling` or raise). Test: `tests/test_quantifier_ceiling.py`.

**Interfaces:** Produces `PrismQLEngine(..., quantifier_ceiling=None)`, `ValidationIssue` code `OPEN_QUANTIFIER`, runtime `PrismQLRuntimeError` with the same message when validation is bypassed.

- [ ] **Step 1: failing test**

```python
import pytest
from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

DOCS = [{"id": i, "user": "a", "text": "x", "timestamp": 100 + i} for i in range(6)]


def test_open_range_rejected_without_ceiling():
    r = QueryValidator().validate("SELECT from(a){2,} INWINDOW 5")
    assert not r.valid and r.errors[0].code == "OPEN_QUANTIFIER"
    assert "{2,m}" in r.errors[0].suggestion
    with pytest.raises(PrismQLRuntimeError, match="quantifier_ceiling"):
        PrismQLEngine(MemoryBackend(DOCS)).execute("SELECT from(a){2,} INWINDOW 5")


def test_open_range_with_ceiling_means_closed_range():
    e = PrismQLEngine(MemoryBackend(DOCS), quantifier_ceiling=3)
    assert e.execute("SELECT from(a){2,} INWINDOW 5") == e.execute(
        "SELECT from(a){2,3} INWINDOW 5"
    )
```

- [ ] **Step 2:** `uv run pytest tests/test_quantifier_ceiling.py -v` → FAIL (no such code / no such kwarg).
- [ ] **Step 3:** implement: validator emits `OPEN_QUANTIFIER` with suggestion `"Write {n,m} with an explicit upper bound, or set [engine] quantifier_ceiling = m"`; engine stores the ceiling and passes it to both executors; `execute_restrictions` substitutes `max_count = ceiling` or raises the same message. Server config parses `[engine] quantifier_ceiling` (int, optional) and `GET /schema` reports it.
- [ ] **Step 4:** test passes; `make check-fast` green (the A8 xfail in `test_engine_defects_pinned.py` may now *error* instead of fail — if so change its query to `{2,4}` so it still pins "ranges run as their minimum").
- [ ] **Step 5:** both references: quantifier section says `{n,}` needs the ceiling setting. Commit: `Quantifiers: an open range needs an explicit ceiling (graph #46)`.

## Task 2: the per-query frame

**Files:** Create `src/prismql/plan/frames.py`; test `tests/plan/test_frames.py`.

**Interfaces:**
```python
def query_frame(backend, ids: Iterable[MessageId], *, fields: Sequence[str], timestamp_field: str) -> pl.LazyFrame
    # columns: position (Int64), id, <fields>..., f"{timestamp_field}_us" (Int64, null if missing/unparseable)
    # raises PositionalUnsupportedError if backend.has_order_axis() is False
def leg_frame(frame: pl.LazyFrame, ids: Iterable[MessageId]) -> pl.LazyFrame   # rows of one predicate set
```

- [ ] **Step 1: failing test** — `MemoryBackend` with string ids in non-lexical load order and one unparseable timestamp; assert positions equal load order, the `_us` column is null for the bad row, `leg_frame` keeps only the requested ids, and a backend with `has_order_axis() == False` raises `PositionalUnsupportedError`.
- [ ] **Step 2:** run → FAIL (module missing).
- [ ] **Step 3:** implement with `backend.positions(ids)` (order-preserving) + `backend.get_documents(ids)`; timestamps through `epoch_micros`; `fields` restricted to what the query's legs reference (variables' fields) — the frame is small by construction. Build with `pl.DataFrame({...}).lazy()`; never `pl.from_dicts` on free-form documents (schema inference — graph #26 style trap).
- [ ] **Step 4:** pass; `make check-fast`.
- [ ] **Step 5:** commit `Plan: the per-query frame from the order axis and the participating ids`.

## Task 3: the operator layer, against the P2 oracles

**Files:** Create `src/prismql/plan/operators.py`; test `tests/plan/test_operators.py` (reuse `brute`, `brute_chain`, `brute_anti`, `brute_cooccur`, `brute_quantify` from `tests/plan/`).

**Interfaces:**
```python
@dataclass(frozen=True)
class Leg:
    ids: frozenset[MessageId]                 # the evaluated predicate set
    equal: tuple[tuple[str, str], ...] = ()   # (variable, field) this leg binds/must equal
    unequal: tuple[tuple[str, str], ...] = () # (variable, field) this leg must differ from  (!$k, Task 8)
    name: str | None = None                   # AS "name"

Window = int | tuple[int, str]                # INWINDOW n | DURING (value, unit)

def link(frame, seqs: pl.LazyFrame | None, lhs: Leg, rhs: Leg, *, window: Window, forward: bool, timestamp_field) -> pl.LazyFrame
    # seqs None: nearest_link(lhs, rhs); else extend_link(frame, seqs, rhs). key = the single shared (var, field) if exactly one, else None; eligible = conjunction of equalities/inequalities across ALL bound legs (A10 fixed here), computed on the prefixed columns.
def negative_link(frame, lhs: Leg, rhs: Leg, *, window, forward, timestamp_field) -> pl.LazyFrame   # anti_link; null-axis lhs dropped (#47)
def cooccur_row(frame, legs: list[Leg], *, window: Window, timestamp_field) -> pl.LazyFrame        # unordered, k-way (D2 fixed here); variables via key/eligible
def quantified_row(frame, leg: Leg, *, n_min, n_max, window, timestamp_field) -> pl.LazyFrame     # quantify
def body_span(frame, result, *, window: tuple[int,str], timestamp_field) -> pl.LazyFrame          # body_span_filter for the trailing DURING on comma rows
def to_groups(result) -> list[list[MessageId]]                                                     # slots in axis order (A9 fixed here)
```
Axis selection: `int` window → `axis="position"`; tuple → `axis=f"{timestamp_field}_us"` with the window converted to microseconds.

- [ ] **Step 1: failing tests** — one per function, on the hostile fixtures of `tests/plan/conftest.py` (gapped ids, string ids, ties, nulls), against the brute oracles; plus the A10 fixture from `tests/test_ordinal_axis_contract.py` (`TWO_VARS`, `SKIPPED_LEG`) expecting `[[2,5]]` / `[[2,3,5]]`.
- [ ] **Step 2:** FAIL (module missing).
- [ ] **Step 3:** implement as thin composition over the primitives; variables: collect `(var, field)` pairs across legs, `key` only when one pair is shared by every leg of the link, everything else into `eligible` as `pl.col(f"r_{field}") == pl.col(f"l_{field}")` — for legs beyond the two of the current link the earlier slot's value must be carried on the seqs frame (`extend_link` anchors on the last slot only): carry bound values as extra columns `_v_<var>` on the result frame at the moment they bind, and compare against them.
- [ ] **Step 4:** pass; `make check-fast`.
- [ ] **Step 5:** commit `Plan: the operator layer — links, negation, co-occurrence, quantifiers over the primitives`.

## Task 4: group-to-group links for subquery chains

**Files:** `src/prismql/plan/primitives.py` (+`link_groups`), `tests/plan/test_link_groups.py`, `operators.py` (+`chain_groups`).

**Interfaces:**
```python
def link_groups(corpus, left: result, right: result, *, axis, window, forward) -> result
    # for each left group, the nearest right group whose first slot (forward) / last slot (backward) lies strictly after the left group's last / before its first slot within window; when several right groups share the nearest boundary all expand (visitor:1393 behaviour, spec amendment 4); members distinct across groups.
```

- [ ] **Step 1:** failing test against a brute oracle (enumerate all left×right pairs, pick by the rule) on tiny corpora, including the shared-boundary case and a right group overlapping the left group (must be excluded).
- [ ] **Step 2–4:** implement via boundaries (`group_by group → min/max slot position`) + `nearest_link` on the boundary frames with `eligible` = "no member overlap" (`is_in` over member lists), then re-expand; pass.
- [ ] **Step 5:** commit `Plan: link_groups — subquery chains as group-to-group nearest links`.

## Task 5: wire the IR executor

**Files:** `src/prismql/ir/executor.py`; tests: the whole suite; `tests/test_ordinal_axis_contract.py`, `tests/test_engine_defects_pinned.py`, `tests/test_positional_path_parity.py`, `tests/test_quantifier_fix.py` (markers), `tests/plan/test_primitives_vs_engine.py` (HEAD is no longer the oracle: retarget its parity assertions at the brute oracles or delete the HEAD side — decide per test, note in the file docstring).

- [ ] **Step 1:** write the failing end-to-end tests first: the six A-contracts and D2 through `PrismQLEngine(use_ir=True)` on the contract fixtures **without** xfail (new file `tests/test_operator_layer_e2e.py`, parametrized over dialect).
- [ ] **Step 2:** FAIL.
- [ ] **Step 3:** in `execute_body`: build `frame = query_frame(backend, union of all leg ids, fields=variable fields, timestamp_field)` once per body; `execute_restriction` returns `Leg`/result frames instead of sets/lists for sequence links; comma rows with a window → `cooccur_row`; quantified restrictions → `quantified_row`; trailing `DURING` on comma rows → `body_span`; `SubqueryChain` positional continuations → `chain_groups`; `to_groups` at the edge. `VariableValidator` call removed (equalities are inside selection). Keep `NamedQueryResult`, aggregation, GROUP BY, ORDER BY, LIMIT on the group lists as today. Backends without an order axis: `PositionalUnsupportedError` surfaces unchanged.
- [ ] **Step 4:** `make check` — every strict xfail that now passes is removed in this commit; anything that still fails is a defect to fix here, not to re-pin.
- [ ] **Step 5:** commit `IR executor runs every operator through the plan; A2 A3 A7 A8 A9 A10 D2 contracts pass`.

## Task 6: the legacy visitor rides the same layer

**Files:** `src/prismql/visitors/query_visitor.py`; tests: the `use_ir` on/off equality tests (must stay green) and the e2e file from Task 5 parametrized over `use_ir`.

- [ ] **Step 1:** parametrize `tests/test_operator_layer_e2e.py` over `use_ir=[True, False]` → FAIL on `False`.
- [ ] **Step 2:** make the four shared helpers delegate: `_apply_sequential_link` → `operators.link`, `_apply_negative_link` → `negative_link`, `_merge_restrictions` → `cooccur_row`, `_merge_subqueries_positional` → `chain_groups`; the visitor's body builds the same `query_frame`. `visitBody`'s temporal branch (`merge_within_time_window`) → `cooccur_row` + `body_span`.
- [ ] **Step 3:** pass; commit `Legacy visitor runs the same operator layer`.

## Task 7: delete the second owner of semantics

**Files:** delete `processors/window.py`, `processors/variables.py`; in `query_visitor.py` delete the builders listed in *File Structure*; in `backends/memory.py`, `backends/base.py`, `backends/rust_memory.py` delete `merge_within_time_window`, `filter_by_time_window`, the positional/temporal kernel entry points; `backends/factory.py` drops the kernel capability handshake; `tests/test_rust_memory_backend.py` shrinks to search-only or is deleted with the backend.

- [ ] **Step 1:** `grep -rn "RUST_.*AVAILABLE\|_temporal_link_kernel\|merge_within_time_window\|filter_by_time_window\|VariableValidator\|WindowProcessor" src tests` — the list is the deletion list.
- [ ] **Step 2:** delete; `make check` green; `uv run python -c "import prismql_rust"` absent → suite identical (Task 7 is the proof that Rust is off the operator path).
- [ ] **Step 3:** decision recorded in the graph on #41 (Rust contour): kept as search-only or retired — by what the tests said.
- [ ] **Step 4:** commit `Delete the legacy merge builders, the variable validator and the Rust operator kernels`.

## Task 8: `!$k` on the surface

**Files:** `src/prismql/grammar/PrismQL.g4` (variable token accepts a leading `!`), `./scripts/generate_parser.sh`, `src/prismql/ir/nodes.py` (`Variable(name, negated: bool = False)`), `src/prismql/ir/lower.py`, `src/prismql/dialects/pipe.py` (`_TOKEN_RE`, `parse_condition`), `src/prismql/ir/executor.py` (`Leg.unequal`), `validator.py` (`!$k` must be bound by an earlier leg; rejected on a negative link's rhs like `$k`), tests `tests/test_pipe_dialect.py` (IR equality pair), `tests/test_operator_layer_e2e.py` (`from($u) FOLLOWED_BY from(!$u) INWINDOW 3` on the A10 fixture → `[[2, 4]]`).

- [ ] **Step 1:** failing IR-equality + e2e tests. **Step 2:** FAIL. **Step 3:** implement; `eligible` gets `!=` for `unequal`. **Step 4:** `make check`. **Step 5:** both references, same commit: `Open !$k in both dialects`.

## Task 9: gates, docs, graph

- [ ] **Step 1:** `tests/plan/test_chicago_tiers.py` gains the engine-vs-oracle full-tuple assertions through `PrismQLEngine` on 100k/1m (`PRISMQL_TIERS=100k,1m make check`); a positional tier query is added. Full tier only on the owner's word (graph #27).
- [ ] **Step 2:** `pyproject.toml`: polars + pyarrow move from `[plan]` to core dependencies (the engine cannot run sequences without them); `[plan]` extra kept as an empty alias for one release; `PlanUnavailableError` stays for the import guard.
- [ ] **Step 3:** `LANGUAGE_REFERENCE.md` + `PIPE_REFERENCE.md`: INWINDOW truly unordered; positional distance = stream distance; string ids; `{n,}` ceiling; `!$k`; negative link drops axis-less lhs. `CHANGELOG.md` Unreleased: the semantic changes by name. `STATE.md`: P3 shipped, A1–A10/D2 closed, "HEAD is a valid oracle only…" paragraph deleted. `AGENTS.md`: Rust rows removed from Commands; `skills/prismql/SKILL.md`: "Known-wrong today" section deleted.
- [ ] **Step 4:** graph: #11 modes → pratyakshita/vartamana; #8 (single operator layer) realized; #6 (two owners) → atita; #12 #16 #29 #44 `addressed_by` #11 and released on the verifier's verdict; #14 (speed risk) answered by the tier numbers; #43 seed rewritten to "what stands now"; #41 by Task 7's decision.
- [ ] **Step 5:** cold review (`reviewer` sub-agent, separate worktree) on the whole branch diff; verifier on the claim "Chicago 100k/1m tuples equal the oracle and 372 stands" before anything is released in the graph.

## Self-review

- Spec coverage: operator layer (T3–T6), both paths (T5, T6), deletion (T7), INWINDOW unordered (T3 `cooccur_row`), `!$k` (T8), xfails removed (T5), subquery boundaries on positions (T4), docs with the phase (T9). Temporal strictness and `(ts,pos)` tie-break are inherited from the primitives (P2, proven). `quantifier_ceiling` (T1) is the one surface decision the spec left open.
- Placeholder scan: T4 step 2–4 and T8 steps are compressed but name the exact functions and files; the executor may expand them in place.
- Type consistency: `Leg`, `Window`, `link`, `negative_link`, `cooccur_row`, `quantified_row`, `chain_groups`, `body_span`, `to_groups`, `query_frame`, `leg_frame`, `link_groups` are used with the same names in T3–T8.
- Known risk (graph #14): Python-side group assembly on 8.5M rows. T9 step 1 measures it; if the tiers regress, `to_groups` becomes a single `group_by(...).agg(pl.col("id"))` + `to_list()` rather than a Python loop before anything else is tried.
