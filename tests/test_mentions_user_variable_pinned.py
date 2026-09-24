"""`mentions_user($y)` does not bind: the variable's text "$y" is searched
as a word and the answer is empty, with no error (graph @aleph/prismql, the
vimarsha on it). "Who addresses whom" — an @name answered by that agent —
is what the construct is for."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

DOCS = [
    {"id": 1, "agent": "ada", "text": "@bob can you check the build?"},
    {"id": 2, "agent": "bob", "text": "on it"},
    {"id": 3, "agent": "cy", "text": "unrelated"},
]


@pytest.mark.xfail(strict=True, reason="mentions_user($y) searches the text '$y'")
@pytest.mark.parametrize("use_ir", [True, False])
def test_a_mention_binds_the_name_it_addresses(use_ir):
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    q = "SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) INWINDOW 3"
    assert engine.execute(q) == [[1, 2]]
