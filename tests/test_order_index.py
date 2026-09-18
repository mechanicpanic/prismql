"""OrderIndex: the explicit stream-order axis (spec 2026-09-18, layer 2b)."""

import warnings

import pytest

from prismql.backends.order import OrderIndex


def test_positions_are_load_order_and_order_preserving():
    idx = OrderIndex(ids=[10, "b", 3])
    assert idx.size() == 3
    assert idx.positions([3, 10]) == [2, 0]  # NOT sorted
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
