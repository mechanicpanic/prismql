"""A configurable id_field must be honored on every path, not just at load.

Three internal sites hard-coded doc.get("id"): the Python temporal-link
fallback and both VariableValidator lookups. With any other id_field they
found no documents and returned EMPTY results silently — the release
blocker class (see #18/#21/#23/#41).
"""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

try:
    from prismql.backends.rust_memory import RUST_BACKEND_AVAILABLE, RustMemoryBackend
except ImportError:  # pragma: no cover
    RUST_BACKEND_AVAILABLE = False
    RustMemoryBackend = None

DOCS = [
    {"tick_id": 1, "user": "alice", "text": "a", "timestamp": 1000},
    {"tick_id": 2, "user": "bob", "text": "b", "timestamp": 1060},
    {"tick_id": 3, "user": "alice", "text": "c", "timestamp": 1120},
    {"tick_id": 4, "user": "bob", "text": "d", "timestamp": 5000},
]

BACKENDS = [
    pytest.param(MemoryBackend(documents=DOCS, id_field="tick_id"), id="memory")
]
if RUST_BACKEND_AVAILABLE:
    BACKENDS.append(
        pytest.param(RustMemoryBackend(documents=DOCS, id_field="tick_id"), id="rust")
    )


@pytest.mark.parametrize("backend", BACKENDS)
class TestIdFieldPlumbing:
    def test_pattern_variables_bind_with_custom_id_field(self, backend):
        engine = PrismQLEngine(backend)
        result = engine.execute(
            "SELECT field(user, $u) FOLLOWED_BY field(user, $u) INWINDOW 3"
        )
        # alice(1)->alice(3), bob(2)->bob(4): id distance 2 both
        assert result == [[1, 3], [2, 4]]

    def test_temporal_link_with_custom_id_field(self, backend):
        engine = PrismQLEngine(backend)
        result = engine.execute(
            "SELECT from(alice) FOLLOWED_BY from(bob) DURING 2 minutes"
        )
        assert result == [[1, 2]]
