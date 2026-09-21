"""The per-query frame (P3 task 2): load-order positions, requested fields,
timestamps as epoch microseconds, and a loud failure without an order axis."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PositionalUnsupportedError

pl = pytest.importorskip("polars")

from prismql.plan.frames import leg_frame, query_frame  # noqa: E402

# Load order is NOT lexical id order, and one timestamp is unparseable.
DOCS = [
    {"id": "m10", "user": "a", "page": "P1", "timestamp": "2026-01-01T00:00:00Z"},
    {"id": "m2", "user": "b", "page": "P1", "timestamp": "not a time"},
    {"id": "m1", "user": "a", "timestamp": "2026-01-01T00:00:02Z", "time": 5},
    {
        "id": "m3",
        "user": "c",
        "page": "P2",
        "timestamp": "2026-01-01T00:00:03Z",
        "time": 7,
    },
]


def test_positions_follow_load_order_and_fields_are_read_as_is():
    backend = MemoryBackend(DOCS)
    df = query_frame(
        backend, ["m3", "m1", "m10", "m2"], fields=["user", "page"]
    ).collect()
    assert df["id"].to_list() == ["m10", "m2", "m1", "m3"]
    assert df["position"].to_list() == [0, 1, 2, 3]
    assert df["page"].to_list() == ["P1", "P1", None, "P2"]
    assert df["user"].to_list() == ["a", "b", "a", "c"]


def test_timestamp_axis_from_the_order_index_with_nulls():
    df = query_frame(MemoryBackend(DOCS), ["m10", "m2", "m1"]).collect()
    us = df["timestamp_us"].to_list()
    assert us[0] == 1_767_225_600_000_000
    assert us[1] is None  # unparseable, not span 0
    assert us[2] == us[0] + 2_000_000
    assert df.schema["timestamp_us"] == pl.Int64


def test_timestamp_field_outside_the_index_is_parsed_from_documents():
    df = query_frame(
        MemoryBackend(DOCS), ["m10", "m1", "m3"], timestamp_field="time"
    ).collect()
    assert df["time_us"].to_list() == [None, 5_000_000, 7_000_000]


def test_subset_and_duplicates():
    df = query_frame(MemoryBackend(DOCS), ["m1", "m1", "m3"]).collect()
    assert df["id"].to_list() == ["m1", "m3"]
    assert df["position"].to_list() == [2, 3]


def test_leg_frame_keeps_only_the_requested_ids():
    frame = query_frame(MemoryBackend(DOCS), ["m10", "m2", "m1", "m3"])
    assert leg_frame(frame, ["m3", "m10"]).collect()["id"].to_list() == ["m10", "m3"]
    assert leg_frame(frame, []).collect().height == 0


class NoAxisBackend(MemoryBackend):
    def has_order_axis(self) -> bool:
        return False

    def positions(self, ids):  # type: ignore[override]  # noqa: ARG002
        raise self._no_axis()


def test_backend_without_an_axis_fails_loudly():
    with pytest.raises(PositionalUnsupportedError):
        query_frame(NoAxisBackend(DOCS), ["m1"])
