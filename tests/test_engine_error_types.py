"""The engine hands back its own error types unwrapped: a caller catches
PositionalUnsupportedError by type, not by reading a message."""

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PositionalUnsupportedError


class NoAxis(MemoryBackend):
    def has_order_axis(self) -> bool:
        return False

    def positions(self, ids):  # type: ignore[override]  # noqa: ARG002
        raise self._no_axis()


def test_positional_unsupported_survives_the_engine_wrapper():
    engine = PrismQLEngine(NoAxis([{"id": 1, "user": "a", "text": "x"}]))
    with pytest.raises(PositionalUnsupportedError):
        engine.execute("SELECT from(a), from(a) INWINDOW 2")
