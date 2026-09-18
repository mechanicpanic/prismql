"""Every backend exposes the order contract; those without an axis fail
loudly with PositionalUnsupportedError (never reconstruct order from ids)."""

# ruff: noqa: ARG002 - the stub backend ignores its arguments on purpose

from datetime import UTC, datetime

import pytest

from prismql.backends.base import SearchBackend
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PositionalUnsupportedError

DOCS = [
    {"id": 10, "user": "a", "text": "x", "timestamp": 1_000},
    {"id": 3, "user": "b", "text": "y", "timestamp": "2024-01-01T00:00:00"},
    {"id": 7, "user": "c", "text": "z"},  # no timestamp
]


class NoAxisBackend(SearchBackend):
    def search_text(self, terms, field="text", operator="OR"):  # noqa: ANN001, ANN201
        return set()

    def search_by_field(self, field, value, exact=True):  # noqa: ANN001, ANN201
        return set()

    def get_total_documents(self):  # noqa: ANN201
        return 0

    def get_all_document_ids(self, limit=None):  # noqa: ANN001, ANN201
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
        with pytest.raises(PositionalUnsupportedError, match="no stream-order axis"):
            call()


def test_memory_backend_positions_follow_load_order_not_id_value():
    b = MemoryBackend(documents=DOCS)
    assert b.has_order_axis()
    assert b.positions([7, 10, 3]) == [2, 0, 1]
    assert b.sorted_positions([7, 10]) == [0, 2]
    assert b.ids_at([1]) == [3]


def test_memory_backend_timestamps_are_utc_micros_per_position():
    b = MemoryBackend(documents=DOCS)
    micros_2024 = int(datetime(2024, 1, 1, tzinfo=UTC).timestamp() * 1_000_000)
    assert b.timestamps_at([0, 1, 2], "timestamp") == [1_000_000_000, micros_2024, None]


def test_memory_backend_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="duplicate id"):
        MemoryBackend(documents=[{"id": 1, "text": "a"}, {"id": 1, "text": "b"}])


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
        assert rs.timestamps_at([0, 1, 2], "timestamp") == py.timestamps_at(
            [0, 1, 2], "timestamp"
        )

    def test_unknown_id_raises_key_error(self):
        with pytest.raises(KeyError):
            RustMemoryBackend(documents=RUST_DOCS).positions([99])

    def test_duplicate_ids_rejected(self):
        with pytest.raises(ValueError, match="duplicate id"):
            RustMemoryBackend(
                documents=[{"id": 1, "text": "a"}, {"id": 1, "text": "b"}]
            )
