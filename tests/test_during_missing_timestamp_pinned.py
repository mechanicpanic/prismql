"""DURING on a corpus whose events lack the configured timestamp field
returns nothing and says nothing (graph @aleph/prismql, the vimarsha on
it). `prismql ingest` writes the time column as `time`, the server's default
timestamp_field is `timestamp`: a config that omits it answers every
DURING query with an empty set — a silent-wrong result."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLError

DOCS = [
    {"id": 1, "user": "a", "text": "x", "time": "2024-01-01T00:00:00Z"},
    {"id": 2, "user": "b", "text": "y", "time": "2024-01-01T00:01:00Z"},
]


@pytest.mark.xfail(strict=True, reason="DURING on a missing time field is empty")
@pytest.mark.parametrize("use_ir", [True, False])
def test_during_on_a_missing_timestamp_field_is_loud(use_ir):
    engine = PrismQLEngine(
        MemoryBackend(DOCS, timestamp_fields=["time"]), use_ir=use_ir
    )  # timestamp_field left at its default, "timestamp"
    with pytest.raises(PrismQLError, match="timestamp"):
        engine.execute("SELECT from(a) FOLLOWED_BY from(b) DURING 5 minutes")
