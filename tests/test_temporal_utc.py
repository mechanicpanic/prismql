"""Numeric-epoch timestamps must be interpreted as UTC everywhere.

Review 2026-07-12, task #44: the Python temporal-link fallback parsed
numeric epochs with local-tz datetime.fromtimestamp(), so DURING results
depended on the host timezone and diverged from the Rust kernels across
DST transitions. These tests run under a DST timezone (America/New_York)
and pin tz-independence, dual-backend agreement, and the get_timestamps
projection contract.
"""

import time
from datetime import UTC, datetime

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

try:
    from prismql.backends.rust_memory import RUST_BACKEND_AVAILABLE, RustMemoryBackend
except ImportError:  # pragma: no cover
    RUST_BACKEND_AVAILABLE = False
    RustMemoryBackend = None

SKIP_RUST = not RUST_BACKEND_AVAILABLE
SKIP_REASON = "prismql_rust not installed"


@pytest.fixture
def eastern_tz():
    """Run the test under a DST timezone, restoring the host tz after."""
    import os

    saved = os.environ.get("TZ")
    os.environ["TZ"] = "America/New_York"
    time.tzset()
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = saved
        time.tzset()


def _utc_epoch(*args: int) -> int:
    return int(datetime(*args, tzinfo=UTC).timestamp())


# US DST fall-back 2026-11-01: 05:30 UTC = 01:30 EDT, 06:30 UTC = 01:30 EST.
# True gap is 60 minutes; naive local projection collapses it to 0.
EPOCH_A = _utc_epoch(2026, 11, 1, 5, 30)
EPOCH_B = _utc_epoch(2026, 11, 1, 6, 30)

DOCS = [
    {"id": 1, "user": "alice", "text": "first", "timestamp": EPOCH_A},
    {"id": 2, "user": "bob", "text": "second", "timestamp": EPOCH_B},
]

QUERY = "SELECT from(alice) FOLLOWED_BY from(bob) DURING 30 minutes"


@pytest.mark.usefixtures("eastern_tz")
class TestNumericEpochsAreUTC:
    def test_during_gap_is_tz_independent(self):
        # The true gap is 60 min; a local-tz parse sees both events at
        # naive 01:30 (gap 0), which breaks the pairing either way.
        engine = PrismQLEngine(MemoryBackend(documents=DOCS))
        assert engine.execute(QUERY) == []

    def test_during_within_true_gap_still_matches(self):
        engine = PrismQLEngine(MemoryBackend(documents=DOCS))
        assert engine.execute(
            "SELECT from(alice) FOLLOWED_BY from(bob) DURING 2 hours"
        ) == [[1, 2]]

    @pytest.mark.skipif(SKIP_RUST, reason=SKIP_REASON)
    def test_memory_and_rust_agree_across_dst(self):
        py_engine = PrismQLEngine(MemoryBackend(documents=DOCS))
        rust_engine = PrismQLEngine(RustMemoryBackend(documents=DOCS))
        for query in (QUERY, "SELECT from(alice) FOLLOWED_BY from(bob) DURING 2 hours"):
            assert py_engine.execute(query) == rust_engine.execute(query), query

    @pytest.mark.skipif(SKIP_RUST, reason=SKIP_REASON)
    def test_rust_get_timestamps_projects_naive_utc(self):
        backend = RustMemoryBackend(documents=DOCS)
        projected = backend.get_timestamps([1, 2], "timestamp")
        assert projected[1] == datetime(2026, 11, 1, 5, 30)
        assert projected[2] == datetime(2026, 11, 1, 6, 30)
        assert (projected[2] - projected[1]).total_seconds() == 3600


@pytest.mark.skipif(SKIP_RUST, reason=SKIP_REASON)
class TestExtremeEpochs:
    """Epochs near the representable bounds must not wrap into a match
    (review 2026-07-12, task #44 minors — kept as an engine-level contract
    now that the temporal kernels are gone)."""

    def test_extreme_epoch_gap_does_not_wrap(self):
        docs = [
            {"id": 1, "user": "a", "text": "x", "timestamp": -8.2e12},
            {"id": 2, "user": "b", "text": "y", "timestamp": 8.2e12},
        ]
        engine = PrismQLEngine(MemoryBackend(documents=docs))
        # True gap ~1.64e19 us overflows i64; a wrap would emit a pair
        # spanning ~520k years. Must match nothing.
        assert engine.execute("SELECT from(a) FOLLOWED_BY from(b) DURING 1 hour") == []
        assert engine.execute("SELECT from(a), from(b) DURING 1 hour") == []


@pytest.mark.skipif(SKIP_RUST, reason=SKIP_REASON)
def test_capability_handshake_covers_all_kernels(monkeypatch):
    """A stale prismql_rust missing any delegated kernel must fail at
    construction with rebuild instructions, not AttributeError mid-query."""
    import prismql.backends.rust_memory as rm

    class StaleBackend:
        pass  # no get_timestamps
        # merge_temporal_link / extend_temporal_link / get_timestamps absent

    monkeypatch.setattr(rm, "_RustMemoryBackend", StaleBackend)
    with pytest.raises(ImportError, match="too old"):
        rm.RustMemoryBackend(documents=DOCS)


@pytest.mark.xfail(
    strict=True,
    reason="an ISO timestamp with an offset is read as UTC wall-clock time, "
    "not converted (backends/order.py epoch_micros)",
)
def test_an_offset_timestamp_is_converted_to_utc():
    from prismql.backends.order import epoch_micros

    assert epoch_micros("2024-01-01T12:00:00+02:00") == epoch_micros(
        "2024-01-01T10:00:00Z"
    )
    # b is 30 minutes after a, written in another zone.
    docs = [
        {"id": 1, "kind": "a", "text": "a", "timestamp": "2024-01-01T10:00:00Z"},
        {"id": 2, "kind": "b", "text": "b", "timestamp": "2024-01-01T12:30:00+02:00"},
    ]
    engine = PrismQLEngine(MemoryBackend(docs))
    q = "SELECT field(kind, a) FOLLOWED_BY field(kind, b) DURING 1 hour"
    assert engine.execute(q) == [[1, 2]]
