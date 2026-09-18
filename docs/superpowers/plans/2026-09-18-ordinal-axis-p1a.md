# Ordinal Axis P1a — the axis, the backend contract, the Arrow table — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every backend an explicit, immutable stream-order axis (position ↔ id ↔ timestamp), make corpora loadable as ordered Arrow tables, and reject duplicate ids at load — without changing any query semantics yet.

**Architecture:** A small `OrderIndex` (pure Python, built from the document sequence at load) becomes the single source of positions for `MemoryBackend`; `RustMemoryBackend` exposes the same contract from its existing `id_to_index` and timestamp caches through three new FFI methods; every other backend inherits a default that raises `PositionalUnsupported`. `load_table()` returns a pyarrow Table with `position = row index`; backends accept a Table or `list[dict]`. Nothing in the executor changes in this plan (that is P3).

**Tech Stack:** Python 3.9+ (uv), pyarrow (new optional extra `arrow`), Rust/PyO3 0.25 in `../prismql-rust` (maturin), pytest.

**Spec:** `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md` — sections "Design (revision 2)", "Layer 1 — the corpus is an ordered Arrow table", "Backend contract (layer 2b)", "Migration → P1".

## Global Constraints

- Python floor 3.9: module-level runtime type aliases use `Union[...]`; `X | None` only in annotations under `from __future__ import annotations` (existing convention).
- `MessageId = Union[int, str]` (`src/prismql/types.py`) — keep; no "any hashable".
- Rust ids are `usize` today; string ids on Rust are P4, NOT this plan — `RustMemoryBackend` still rejects non-int ids.
- Gate before every commit: `uv run ruff format . && uv run ruff check . --fix && uv run mypy src/prismql` (zero NEW mypy errors; 11 baseline in repl.py/tantivy.py) and `uv run pytest -m "not slow"`.
- Rust rebuild: `PATH="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH" uv sync --reinstall-package prismql-rust --dev --extra server --extra repl --extra highlighting --extra mcp --extra tantivy` (cargo is not on PATH on this machine); Rust unit tests: `cargo test --lib` with the same PATH prefix, from `../prismql-rust`.
- Commits: plain imperative subject, body explains why; trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; stage explicit paths only; never push.
- No query-semantics change in this plan: the three `xfail(strict)` files (`tests/test_ordinal_axis_contract.py`, `tests/test_positional_path_parity.py::test_inwindow_is_commutative`) must STAY xfailed (strict xfail fails the run if one starts passing).

---

## File map

- Create `src/prismql/backends/order.py` — `OrderIndex`: positions, ids, per-field timestamps; duplicate-id rejection; timestamp-monotone warning. One responsibility: the axis.
- Create `src/prismql/exceptions.py` addition — `PositionalUnsupported(PrismQLRuntimeError)`.
- Modify `src/prismql/backends/base.py` — five contract methods on `SearchBackend` with default `raise PositionalUnsupported`.
- Modify `src/prismql/backends/memory.py` — build `OrderIndex` in `__init__`, implement the contract by delegation, accept a pyarrow Table.
- Modify `src/prismql/backends/rust_memory.py` — implement the contract over new FFI methods; extend the capability handshake; accept a pyarrow Table (via `to_pylist()` in this plan; zero-copy ingest is plan P1b).
- Modify `../prismql-rust/src/backend.rs` — `positions_of`, `ids_at`, `timestamps_at`; duplicate-id rejection in the constructor.
- Create `src/prismql/loaders.py` — `load_table(path) -> pyarrow.Table` (position column); `server/config.py::load_documents` unchanged.
- Modify `pyproject.toml` — extra `arrow = ["pyarrow>=15"]`, added to `all`.
- Tests: `tests/test_order_index.py`, `tests/test_backend_order_contract.py`, `tests/test_load_table.py`.
- Docs: `AGENTS.md` gotchas (id contract), `CHANGELOG.md`.

---

### Task 1: `PositionalUnsupported` and `OrderIndex`

**Files:**
- Modify: `src/prismql/exceptions.py` (append one class)
- Create: `src/prismql/backends/order.py`
- Test: `tests/test_order_index.py`

**Interfaces:**
- Produces: `class PositionalUnsupported(PrismQLRuntimeError)`;
  `class OrderIndex` with `__init__(self, ids: Sequence[MessageId], timestamps: Mapping[str, Sequence[Optional[int]]] = {})`, `size() -> int`, `positions(ids: Iterable[MessageId]) -> list[int]` (order-preserving; unknown id → `KeyError`), `sorted_positions(ids) -> list[int]`, `ids_at(positions: Iterable[int]) -> list[MessageId]` (out of range → `IndexError`), `timestamps_at(positions, field: str) -> list[Optional[int]]` (unknown field → `KeyError`), `has_timestamp_field(field) -> bool`, `monotone_violations(field) -> int`.
  Timestamps are epoch **microseconds** UTC or `None`, one per position.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_order_index.py
"""OrderIndex: the explicit stream-order axis (spec: layer 2b)."""
import warnings

import pytest

from prismql.backends.order import OrderIndex


def test_positions_are_load_order_and_order_preserving():
    idx = OrderIndex(ids=[10, "b", 3])
    assert idx.size() == 3
    assert idx.positions([3, 10]) == [2, 0]          # NOT sorted
    assert idx.sorted_positions([3, 10]) == [0, 2]
    assert idx.ids_at([1, 0]) == ["b", 10]


def test_unknown_id_and_bad_position_raise():
    idx = OrderIndex(ids=[1, 2])
    with pytest.raises(KeyError):
        idx.positions([99])
    with pytest.raises(IndexError):
        idx.ids_at([2])


def test_duplicate_ids_are_rejected_at_build():
    with pytest.raises(ValueError, match="duplicate id"):
        OrderIndex(ids=[1, 2, 1])


def test_timestamps_at_by_field_in_micros():
    idx = OrderIndex(ids=[1, 2, 3], timestamps={"ts": [100, None, 300]})
    assert idx.has_timestamp_field("ts")
    assert not idx.has_timestamp_field("other")
    assert idx.timestamps_at([2, 0, 1], "ts") == [300, 100, None]
    with pytest.raises(KeyError):
        idx.timestamps_at([0], "other")


def test_timestamp_length_must_match_ids():
    with pytest.raises(ValueError, match="length"):
        OrderIndex(ids=[1, 2], timestamps={"ts": [1]})


def test_monotone_violations_counted_and_warned():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        idx = OrderIndex(ids=[1, 2, 3], timestamps={"ts": [100, 50, 300]})
    assert idx.monotone_violations("ts") == 1
    assert any("not monotone" in str(x.message) for x in w)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_order_index.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'prismql.backends.order'`

- [ ] **Step 3: Add the exception**

Append to `src/prismql/exceptions.py` (after `PrismQLRuntimeError`):

```python
class PositionalUnsupported(PrismQLRuntimeError):
    """The backend has no stream-order axis, so positional and sequential
    operators cannot run on it. Boolean/set queries still work.

    Raised by SearchBackend's order-contract defaults; backends that carry
    an OrderIndex (memory, rust_memory) override them.
    """
```

- [ ] **Step 4: Write `OrderIndex`**

```python
# src/prismql/backends/order.py
"""The ordinal axis: stream order as data (spec 2026-09-18, layer 2b).

Position = load order, full stop. Ids are labels. The index is immutable
after construction; timestamps are epoch microseconds (UTC) per
configured field, one entry per position, ``None`` when unparseable.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable, Mapping, Sequence
from typing import Optional

from ..types import MessageId


class OrderIndex:
    def __init__(
        self,
        ids: Sequence[MessageId],
        timestamps: Optional[Mapping[str, Sequence[Optional[int]]]] = None,
    ) -> None:
        self._ids: list[MessageId] = list(ids)
        self._pos: dict[MessageId, int] = {}
        for pos, mid in enumerate(self._ids):
            if mid in self._pos:
                raise ValueError(
                    f"duplicate id {mid!r} at positions {self._pos[mid]} and {pos}: "
                    "ids must be unique — the ordinal axis is a bijection"
                )
            self._pos[mid] = pos
        self._ts: dict[str, list[Optional[int]]] = {}
        for field, values in (timestamps or {}).items():
            col = list(values)
            if len(col) != len(self._ids):
                raise ValueError(
                    f"timestamp column {field!r} has length {len(col)}, "
                    f"expected {len(self._ids)} (one per position)"
                )
            self._ts[field] = col
            bad = self.monotone_violations(field)
            if bad:
                warnings.warn(
                    f"timestamp field {field!r} is not monotone in load order "
                    f"({bad} descents): positional windows follow load order, "
                    "temporal windows follow timestamps — they will disagree.",
                    stacklevel=2,
                )

    def size(self) -> int:
        return len(self._ids)

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        """Order-preserving; unknown id raises KeyError."""
        return [self._pos[mid] for mid in ids]

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        return sorted(self.positions(ids))

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        out: list[MessageId] = []
        for p in positions:
            if p < 0 or p >= len(self._ids):
                raise IndexError(f"position {p} out of range [0, {len(self._ids)})")
            out.append(self._ids[p])
        return out

    def has_timestamp_field(self, field: str) -> bool:
        return field in self._ts

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[Optional[int]]:
        col = self._ts[field]  # KeyError for unknown field is the contract
        return [col[p] for p in positions]

    def monotone_violations(self, field: str) -> int:
        col = self._ts[field]
        prev: Optional[int] = None
        bad = 0
        for v in col:
            if v is None:
                continue
            if prev is not None and v < prev:
                bad += 1
            prev = v
        return bad
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_order_index.py -q`
Expected: `6 passed`

- [ ] **Step 6: Gate and commit**

```bash
uv run ruff format . && uv run ruff check . --fix && uv run mypy src/prismql | tail -1
git add src/prismql/exceptions.py src/prismql/backends/order.py tests/test_order_index.py
git commit -m "Add OrderIndex, the explicit stream-order axis

Position = load order; ids are labels and must be unique; per-field
timestamps in epoch micros, one per position. Warns when a timestamp
field is not monotone in load order (positional and temporal windows
would disagree). Nothing uses it yet — spec 2026-09-18, P1.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Backend contract with `PositionalUnsupported` default; `MemoryBackend` wires the axis

**Files:**
- Modify: `src/prismql/backends/base.py` (after `search_semantic`, ~line 108)
- Modify: `src/prismql/backends/memory.py` (`__init__` ~lines 20–95; append methods)
- Test: `tests/test_backend_order_contract.py`

**Interfaces:**
- Consumes: `OrderIndex`, `PositionalUnsupported` (Task 1); `TemporalProcessor._coerce_timestamp` (`src/prismql/processors/temporal.py:85`, returns naive-UTC `datetime` or `None`).
- Produces on `SearchBackend`: `positions(ids) -> list[int]`, `sorted_positions(ids) -> list[int]`, `ids_at(positions) -> list[MessageId]`, `timestamps_at(positions, field) -> list[Optional[int]]`, `has_order_axis() -> bool`. `MemoryBackend.order: OrderIndex`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_backend_order_contract.py
"""Every backend exposes the order contract; those without an axis fail
loudly with PositionalUnsupported (never reconstruct order from ids)."""
from datetime import datetime, timezone

import pytest

from prismql.backends.base import SearchBackend
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PositionalUnsupported

DOCS = [
    {"id": 10, "user": "a", "text": "x", "timestamp": 1_000},
    {"id": 3, "user": "b", "text": "y", "timestamp": "2024-01-01T00:00:00"},
    {"id": 7, "user": "c", "text": "z"},  # no timestamp
]


class NoAxisBackend(SearchBackend):
    def search_text(self, terms, field="text", operator="OR"):
        return set()

    def search_by_field(self, field, value, exact=True):
        return set()

    def get_total_documents(self):
        return 0

    def get_all_document_ids(self, limit=None):
        return set()


def test_default_contract_raises_positional_unsupported():
    b = NoAxisBackend()
    assert b.has_order_axis() is False
    for call in (
        lambda: b.positions([1]),
        lambda: b.sorted_positions([1]),
        lambda: b.ids_at([0]),
        lambda: b.timestamps_at([0], "timestamp"),
    ):
        with pytest.raises(PositionalUnsupported, match="no stream-order axis"):
            call()


def test_memory_backend_positions_follow_load_order_not_id_value():
    b = MemoryBackend(documents=DOCS)
    assert b.has_order_axis()
    assert b.positions([7, 10, 3]) == [2, 0, 1]
    assert b.sorted_positions([7, 10]) == [0, 2]
    assert b.ids_at([1]) == [3]


def test_memory_backend_timestamps_are_utc_micros_per_position():
    b = MemoryBackend(documents=DOCS)
    micros_2024 = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)
    assert b.timestamps_at([0, 1, 2], "timestamp") == [1_000_000_000, micros_2024, None]


def test_memory_backend_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="duplicate id"):
        MemoryBackend(documents=[{"id": 1, "text": "a"}, {"id": 1, "text": "b"}])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_backend_order_contract.py -q`
Expected: FAIL — `AttributeError: 'NoAxisBackend' object has no attribute 'has_order_axis'`

- [ ] **Step 3: Add the contract defaults to `SearchBackend`**

Insert into `src/prismql/backends/base.py` after `search_semantic` (before `@abstractmethod def search_by_field`):

```python
    # ------------------------------------------------------------------
    # Order contract (spec 2026-09-18, layer 2b). Position = load order.
    # Backends without an axis MUST fail loudly here; order is never
    # reconstructed from id values.
    # ------------------------------------------------------------------
    def has_order_axis(self) -> bool:
        return False

    def _no_axis(self) -> PositionalUnsupported:
        return PositionalUnsupported(
            f"{type(self).__name__} has no stream-order axis: positional "
            "(INWINDOW, FOLLOWED_BY, ...) and temporal-sequence operators "
            "cannot run on it. Use a backend with an OrderIndex (memory, "
            "rust_memory) or load the corpus with a persisted position column."
        )

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        raise self._no_axis()

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        raise self._no_axis()

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        raise self._no_axis()

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[Optional[int]]:
        raise self._no_axis()
```

and at the top of `base.py`: `from collections.abc import Iterable, Mapping, Sequence` (extend the existing import) and `from ..exceptions import PositionalUnsupported`.

- [ ] **Step 4: Build the axis in `MemoryBackend`**

In `src/prismql/backends/memory.py`, add imports:

```python
from datetime import timezone

from ..processors.temporal import TemporalProcessor
from .order import OrderIndex
```

At the end of `__init__` (after `if self.config.enable_ngrams: self._build_ngram_indexes(doc_tokens)`), add:

```python
        # The ordinal axis: load order, ids as labels (spec 2026-09-18).
        # Built last so a duplicate id fails before any index is trusted.
        self.order = OrderIndex(
            ids=[doc[id_field] for doc in self.documents],
            timestamps={
                "timestamp": [self._epoch_micros(doc.get("timestamp")) for doc in self.documents]
            },
        )
```

and these methods (place after `get_all_document_ids`):

```python
    @staticmethod
    def _epoch_micros(value: object) -> Optional[int]:
        """Naive-UTC datetime from _coerce_timestamp -> epoch micros."""
        dt = TemporalProcessor._coerce_timestamp(value) if value is not None else None
        if dt is None:
            return None
        return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1_000_000)

    def has_order_axis(self) -> bool:
        return True

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        return self.order.positions(ids)

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        return self.order.sorted_positions(ids)

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        return self.order.ids_at(positions)

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[Optional[int]]:
        return self.order.timestamps_at(positions, field)
```

Add `Iterable` to the `collections.abc` import in memory.py. Note: the duplicate-id `ValueError` from `OrderIndex` replaces today's silent overwrite in `_id_to_doc` (`memory.py:59`); the existing loop stays as is — the axis check runs after it and raises.

The timestamp field is `"timestamp"` here because `MemoryBackend` has no `timestamp_fields` parameter today; P3 threads the engine's `timestamp_field` through. Document this in the docstring.

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_backend_order_contract.py tests/test_order_index.py -q`
Expected: `10 passed`

- [ ] **Step 6: Run the full suite — nothing else may change**

Run: `uv run pytest -q -m "not slow"`
Expected: same pass count as before this task (+4), the 6 xfails still xfailed. If any existing test constructs a `MemoryBackend` with duplicate ids it now fails — fix that test's fixture (duplicates were never a supported input), do not weaken the check.

- [ ] **Step 7: Gate and commit**

```bash
uv run ruff format . && uv run ruff check . --fix && uv run mypy src/prismql | tail -1
git add src/prismql/backends/base.py src/prismql/backends/memory.py tests/test_backend_order_contract.py
git commit -m "Expose the order contract on backends; MemoryBackend gets an axis

positions/sorted_positions/ids_at/timestamps_at/has_order_axis on
SearchBackend, defaulting to PositionalUnsupported so a backend without
an axis fails loudly instead of order being reconstructed from ids.
MemoryBackend builds an OrderIndex at load (positions = load order,
duplicate ids rejected, timestamps as UTC epoch micros). No executor
uses it yet — spec 2026-09-18, P1.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: `RustMemoryBackend` implements the contract over new FFI methods

**Files:**
- Modify: `../prismql-rust/src/backend.rs` (add three `#[pymethods]`; duplicate-id check in `new`, ~lines 195–209)
- Modify: `src/prismql/backends/rust_memory.py` (handshake ~line 84; new methods after `get_timestamps`)
- Test: `tests/test_backend_order_contract.py` (append), `../prismql-rust/src/backend.rs` unit test

**Interfaces:**
- Consumes: contract names from Task 2.
- Produces (Rust, on `RustMemoryBackend`): `positions_of(ids: Vec<usize>) -> Vec<Option<usize>>` (None for unknown), `ids_at(positions: Vec<usize>) -> PyResult<Vec<usize>>` (IndexError out of range), `timestamps_at(positions: Vec<usize>, field: &str) -> PyResult<Vec<Option<i64>>>` (ValueError unknown field; micros). Constructor raises `ValueError("duplicate id ...")`.

- [ ] **Step 1: Write the failing Python tests** (append to `tests/test_backend_order_contract.py`)

```python
try:
    from prismql.backends.rust_memory import RUST_BACKEND_AVAILABLE, RustMemoryBackend
except ImportError:  # pragma: no cover
    RUST_BACKEND_AVAILABLE = False

RUST_DOCS = [
    {"id": 10, "user": "a", "text": "x", "timestamp": 1_000},
    {"id": 3, "user": "b", "text": "y", "timestamp": "2024-01-01T00:00:00"},
    {"id": 7, "user": "c", "text": "z"},
]


@pytest.mark.skipif(not RUST_BACKEND_AVAILABLE, reason="prismql_rust not installed")
class TestRustOrderContract:
    def test_matches_memory_backend(self):
        py = MemoryBackend(documents=RUST_DOCS)
        rs = RustMemoryBackend(documents=RUST_DOCS)
        assert rs.has_order_axis()
        assert rs.positions([7, 10, 3]) == py.positions([7, 10, 3]) == [2, 0, 1]
        assert rs.sorted_positions([7, 10]) == [0, 2]
        assert rs.ids_at([1, 2]) == py.ids_at([1, 2]) == [3, 7]
        assert rs.timestamps_at([0, 1, 2], "timestamp") == py.timestamps_at([0, 1, 2], "timestamp")

    def test_unknown_id_raises_key_error(self):
        rs = RustMemoryBackend(documents=RUST_DOCS)
        with pytest.raises(KeyError):
            rs.positions([99])

    def test_duplicate_ids_rejected(self):
        with pytest.raises(ValueError, match="duplicate id"):
            RustMemoryBackend(documents=[{"id": 1, "text": "a"}, {"id": 1, "text": "b"}])
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_backend_order_contract.py -q -k Rust`
Expected: FAIL — `AttributeError: 'RustMemoryBackend' object has no attribute 'has_order_axis'` (and duplicate test: no error raised)

- [ ] **Step 3: Rust — duplicate-id rejection in the constructor**

In `../prismql-rust/src/backend.rs` constructor loop (the block containing `backend.id_to_index.insert(doc_id, idx);`, ~line 208), replace that line with:

```rust
            if let Some(prev) = backend.id_to_index.insert(doc_id, idx) {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "duplicate id {} at positions {} and {}: ids must be unique",
                    doc_id, prev, idx
                )));
            }
```

- [ ] **Step 4: Rust — the three methods** (add inside the `#[pymethods] impl RustMemoryBackend` block, next to `get_timestamps`, ~line 384)

```rust
    /// Load-order position of each id; None for unknown ids.
    fn positions_of(&self, ids: Vec<MessageId>) -> Vec<Option<usize>> {
        ids.iter().map(|id| self.id_to_index.get(id).copied()).collect()
    }

    /// Ids at load-order positions; IndexError when out of range.
    fn ids_at(&self, positions: Vec<usize>) -> PyResult<Vec<MessageId>> {
        let n = self.documents.len();
        positions
            .iter()
            .map(|&p| {
                self.documents.get(p).map(|d| d.id).ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyIndexError, _>(format!(
                        "position {} out of range [0, {})", p, n
                    ))
                })
            })
            .collect()
    }

    /// Epoch microseconds (UTC) at positions for a cached timestamp field;
    /// None where unparseable; ValueError for a field not cached.
    fn timestamps_at(&self, positions: Vec<usize>, field: &str) -> PyResult<Vec<Option<i64>>> {
        let cache = self.timestamp_caches.get(field).ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "Timestamp field '{}' was not indexed; pass it via timestamp_fields at construction",
                field
            ))
        })?;
        positions
            .iter()
            .map(|&p| {
                cache.get(p).map(|e| e.parsed().map(|ts| ts.timestamp_micros())).ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyIndexError, _>(format!(
                        "position {} out of range [0, {})", p, cache.len()
                    ))
                })
            })
            .collect()
    }
```

(`self.documents` is the `Vec<Document>` the constructor fills in load order — position is its index, which is exactly what `id_to_index` stores.)

- [ ] **Step 5: Rust unit test** (append inside the existing `#[cfg(test)] mod tests` in `backend.rs`; if the module builds backends only through Python, skip this step and rely on the Python tests — do not invent a Rust-only constructor)

- [ ] **Step 6: Rebuild the extension**

Run:
```bash
cd ../prismql-rust && PATH="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH" cargo test --lib 2>&1 | tail -3
cd ../prismql && PATH="$HOME/.rustup/toolchains/stable-aarch64-apple-darwin/bin:$PATH" uv sync --reinstall-package prismql-rust --dev --extra server --extra repl --extra highlighting --extra mcp --extra tantivy 2>&1 | tail -1
```
Expected: Rust tests pass; `~ prismql-rust==0.1.0` reinstalled.

- [ ] **Step 7: Python wrapper**

In `src/prismql/backends/rust_memory.py`, extend the handshake tuple (Task from 2026-09-18 commit dc46d17) to:

```python
        required_kernels = (
            "merge_within_time_window",
            "merge_temporal_link",
            "extend_temporal_link",
            "get_timestamps",
            "positions_of",
            "ids_at",
            "timestamps_at",
        )
```

Add after `get_timestamps`:

```python
    # -- order contract (spec 2026-09-18) ---------------------------------
    def has_order_axis(self) -> bool:
        return True

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        wanted = list(ids)
        found = self._backend.positions_of([i for i in wanted if self._valid_id(i)])
        out: list[int] = []
        it = iter(found)
        for mid in wanted:
            pos = next(it) if self._valid_id(mid) else None
            if pos is None:
                raise KeyError(mid)
            out.append(pos)
        return out

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        return sorted(self.positions(ids))

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        return list(self._backend.ids_at(list(positions)))

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[Optional[int]]:
        return list(self._backend.timestamps_at(list(positions), field))
```

Add `Iterable` to the `collections.abc` import.

- [ ] **Step 8: Run tests**

Run: `uv run pytest tests/test_backend_order_contract.py tests/test_temporal_utc.py tests/test_rust_memory_backend.py -q`
Expected: all pass (the handshake test in `test_temporal_utc.py` still passes: its stub lacks the new kernels too, so it still raises `ImportError("too old")`).

- [ ] **Step 9: Gate and commit — two repos**

```bash
cd ../prismql-rust && git add src/backend.rs && git commit -m "Expose load-order positions and reject duplicate ids

positions_of / ids_at / timestamps_at expose the existing id_to_index
and timestamp caches as the ordinal-axis contract (prismql spec
2026-09-18, P1). The constructor now rejects duplicate ids instead of
silently overwriting the mapping.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
cd ../prismql && uv run ruff format . && uv run ruff check . --fix && uv run mypy src/prismql | tail -1
git add src/prismql/backends/rust_memory.py tests/test_backend_order_contract.py
git commit -m "RustMemoryBackend implements the order contract

Delegates to the new positions_of / ids_at / timestamps_at kernels;
the capability handshake now requires them. Parity-tested against
MemoryBackend.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `load_table()` — the corpus as an ordered Arrow table; backends accept a Table

**Files:**
- Modify: `pyproject.toml` (extras)
- Create: `src/prismql/loaders.py`
- Modify: `src/prismql/backends/memory.py` (`__init__` first lines), `src/prismql/backends/rust_memory.py` (`__init__`)
- Test: `tests/test_load_table.py`

**Interfaces:**
- Produces: `load_table(path: str | Path, id_field: str = "id") -> pyarrow.Table` with a `position` int64 column equal to row index and a unique `id_field` column; `ImportError` with install hint when pyarrow is missing. `MemoryBackend(documents=<Table>)` and `RustMemoryBackend(documents=<Table>)` accept a Table (converted with `to_pylist()` — zero-copy Rust ingest is plan P1b).

- [ ] **Step 1: Add the extra**

In `pyproject.toml` `[project.optional-dependencies]` add `arrow = ["pyarrow>=15"]` and include `arrow` in the `all` list. Then `uv sync --extra arrow` (plus the usual extras) so the local venv has it.

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_load_table.py
"""A corpus is an ordered Arrow table: position = row index (spec, layer 1)."""
import json

import pytest

pa = pytest.importorskip("pyarrow")

from prismql.backends.memory import MemoryBackend  # noqa: E402
from prismql.loaders import load_table  # noqa: E402

DOCS = [
    {"id": 10, "user": "a", "text": "x", "timestamp": 1000},
    {"id": 3, "user": "b", "text": "y", "timestamp": 1060},
]


@pytest.fixture
def jsonl(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text("\n".join(json.dumps(d) for d in DOCS))
    return p


def test_load_table_adds_position_as_row_index(jsonl):
    t = load_table(jsonl)
    assert t.column("position").to_pylist() == [0, 1]
    assert t.column("id").to_pylist() == [10, 3]  # load order, not sorted


def test_load_table_rejects_duplicate_ids(tmp_path):
    p = tmp_path / "d.jsonl"
    p.write_text("\n".join(json.dumps({"id": 1, "text": s}) for s in "ab"))
    with pytest.raises(ValueError, match="duplicate id"):
        load_table(p)


def test_load_table_roundtrips_parquet(jsonl, tmp_path):
    t = load_table(jsonl)
    import pyarrow.parquet as pq

    out = tmp_path / "c.parquet"
    pq.write_table(t, out)
    again = load_table(out)
    assert again.column("position").to_pylist() == [0, 1]
    assert again.column("id").to_pylist() == [10, 3]


def test_memory_backend_accepts_table(jsonl):
    b = MemoryBackend(documents=load_table(jsonl))
    assert b.get_total_documents() == 2
    assert b.positions([3]) == [1]
```

- [ ] **Step 3: Run to verify they fail**

Run: `uv run pytest tests/test_load_table.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'prismql.loaders'`

- [ ] **Step 4: Write `loaders.py`**

```python
# src/prismql/loaders.py
"""Corpus loading as an ordered Arrow table (spec 2026-09-18, layer 1).

``position`` = row index in load order. Anything that produces the table
(DuckDB, Polars, pandas, a JSONL file) owns joins and stream order; the
engine never joins.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _pa() -> Any:
    try:
        import pyarrow

        return pyarrow
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "load_table requires pyarrow: uv pip install 'prismql[arrow]'"
        ) from e


def load_table(path: str | Path, id_field: str = "id") -> Any:
    """Read .json / .jsonl / .csv / .parquet into a Table with ``position``.

    An existing ``position`` column is validated (must equal the row
    index) rather than trusted blindly; duplicate ids are rejected.
    """
    pa = _pa()
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".parquet":
        import pyarrow.parquet as pq

        table = pq.read_table(p)
    elif suffix in (".jsonl", ".json"):
        from .server.config import load_documents

        table = pa.Table.from_pylist(load_documents(p))
    elif suffix == ".csv":
        import pyarrow.csv as pacsv

        table = pacsv.read_csv(p)
    else:
        raise ValueError(f"Unsupported data format {suffix!r}")

    n = table.num_rows
    if "position" in table.column_names:
        if table.column("position").to_pylist() != list(range(n)):
            raise ValueError("'position' column must equal the row index (load order)")
    else:
        table = table.append_column("position", pa.array(range(n), type=pa.int64()))

    ids = table.column(id_field).to_pylist()
    seen: set[Any] = set()
    for pos, mid in enumerate(ids):
        if mid in seen:
            raise ValueError(f"duplicate id {mid!r} at position {pos}: ids must be unique")
        seen.add(mid)
    return table
```

- [ ] **Step 5: Backends accept a Table**

At the very top of `MemoryBackend.__init__` (before `self.documents = list(documents)`), and identically at the top of `RustMemoryBackend.__init__` (before the handshake), insert:

```python
        # A corpus may arrive as an ordered Arrow table (spec, layer 1).
        # Row order is load order; to_pylist() preserves it. (Zero-copy
        # ingest on the Rust side is plan P1b.)
        if hasattr(documents, "to_pylist") and hasattr(documents, "num_rows"):
            documents = documents.to_pylist()  # type: ignore[union-attr]
```

`documents` is typed `Sequence[Document]`; widen both signatures to `documents: Sequence[Document] | Any` with `from typing import Any` — the duck-typed check avoids importing pyarrow in core.

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_load_table.py tests/test_backend_order_contract.py -q`
Expected: pass.

- [ ] **Step 7: Gate and commit**

```bash
uv run ruff format . && uv run ruff check . --fix && uv run mypy src/prismql | tail -1
git add pyproject.toml src/prismql/loaders.py src/prismql/backends/memory.py src/prismql/backends/rust_memory.py tests/test_load_table.py
git commit -m "Load a corpus as an ordered Arrow table

load_table() returns a pyarrow Table with position = row index (the
ordinal axis as data), validates an existing position column, rejects
duplicate ids, and reads json/jsonl/csv/parquet. Backends accept a
Table (converted with to_pylist() for now; zero-copy Rust ingest is
plan P1b). pyarrow ships as the new [arrow] extra; core stays
dependency-free. Spec 2026-09-18, layer 1.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

uv.lock changes from the new extra are dependency work — commit them in this task.

---

### Task 5: Record the contract — docs and CHANGELOG

**Files:**
- Modify: `AGENTS.md` (Gotchas list), `CHANGELOG.md` (top, Unreleased)

- [ ] **Step 1: AGENTS.md gotcha** — replace the bullet "Rust kernels run only for numeric message ids; string ids fall back to Python. Timestamp tie-break differs…" with:

```markdown
  - **Stream order is the load order** (spec `docs/superpowers/specs/2026-09-18-ordinal-axis-design.md`). Ids are labels and must be unique (duplicates are a load error). Backends expose `positions/sorted_positions/ids_at/timestamps_at`; backends without an axis raise `PositionalUnsupported`. Until P3 lands, positional operators still measure id distance on the Rust path and list index on the Python fallback — see the xfail(strict) contract tests; do not "fix" them piecemeal.
  - Rust kernels run only for numeric message ids; string ids fall back to Python (until P4). Timestamp tie-break differs (rust: ascending id; python: set order) until P3.
```

- [ ] **Step 2: CHANGELOG.md** — under Unreleased:

```markdown
- Ordinal axis P1: `OrderIndex`, backend order contract (`positions`, `sorted_positions`, `ids_at`, `timestamps_at`, `has_order_axis`), `PositionalUnsupported` for backends without an axis, duplicate ids rejected at load (memory and rust), `load_table()` + `[arrow]` extra (corpus as an ordered Arrow table with `position` = row index). No query semantics changed.
```

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md CHANGELOG.md
git commit -m "Document the ordinal-axis contract and P1 changes

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Not in this plan (next plans)

- **P1b — zero-copy Arrow ingest in Rust** (`from_arrow(table, ...)` via `pyo3-arrow`, column-wise indexing replacing `index_document_from_pydict`; needs a read of that function first). Separate plan.
- **P2 — primitives** (`nearest_after/before`, `window_product`, Python reference + Rust twins + property tests).
- **P3 — the single operator layer** (deletes the dual paths; the xfail(strict) tests flip).
- **P4 — gates** (Chicago tuple equality, positional benchmark, relabeled corpora); **P5** docs per phase.
