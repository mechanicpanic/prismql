"""{n,} needs an explicit ceiling (graph @aleph/prismql #46).

The plan's ``quantify`` enumerates subsets up to an explicit ``max_size``;
an open range on the surface must therefore either be rejected with a
teachable message or be closed by a configured ceiling — never silently
truncated.
"""

import pytest

from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLRuntimeError

DOCS = [{"id": i, "user": "a", "text": "x", "timestamp": 100 + i} for i in range(6)]

OPEN = {
    "classic": "SELECT from(a){2,} INWINDOW 5",
    "pipe": "from(a){2,} |> within(5)",
}
CLOSED = {
    "classic": "SELECT from(a){2,3} INWINDOW 5",
    "pipe": "from(a){2,3} |> within(5)",
}


@pytest.mark.parametrize("dialect", ["classic", "pipe"])
def test_open_range_rejected_without_ceiling(dialect):
    result = QueryValidator().validate(OPEN[dialect])
    assert not result.valid
    issue = result.errors[0]
    assert issue.code == "OPEN_QUANTIFIER"
    assert "{2,m}" in (issue.suggestion or "")
    assert "quantifier_ceiling" in (issue.suggestion or "")


@pytest.mark.parametrize("dialect", ["classic", "pipe"])
@pytest.mark.parametrize("use_ir", [True, False])
def test_open_range_raises_at_runtime_without_ceiling(dialect, use_ir):
    engine = PrismQLEngine(MemoryBackend(DOCS), use_ir=use_ir)
    with pytest.raises(PrismQLRuntimeError, match="quantifier_ceiling"):
        engine.execute(OPEN[dialect])


@pytest.mark.parametrize("dialect", ["classic", "pipe"])
@pytest.mark.parametrize("use_ir", [True, False])
def test_open_range_with_ceiling_means_closed_range(dialect, use_ir):
    engine = PrismQLEngine(MemoryBackend(DOCS), quantifier_ceiling=3, use_ir=use_ir)
    assert engine.execute(OPEN[dialect]) == engine.execute(CLOSED[dialect])
    assert QueryValidator(quantifier_ceiling=3).validate(OPEN[dialect]).valid


@pytest.mark.parametrize("dialect", ["classic", "pipe"])
def test_minimum_above_ceiling_is_rejected(dialect):
    q = {"classic": "SELECT from(a){5,} INWINDOW 5", "pipe": "from(a){5,} |> within(5)"}
    result = QueryValidator(quantifier_ceiling=3).validate(q[dialect])
    assert not result.valid and result.errors[0].code == "OPEN_QUANTIFIER"
    engine = PrismQLEngine(MemoryBackend(DOCS), quantifier_ceiling=3)
    with pytest.raises(PrismQLRuntimeError, match="above quantifier_ceiling"):
        engine.execute(q[dialect])


def test_quoted_text_is_not_a_quantifier():
    assert QueryValidator().validate('SELECT from(a) AS "{2,}" INWINDOW 5').valid
    assert QueryValidator().validate('SELECT contains_phrase("{2,}")').valid


def test_closed_range_never_needs_a_ceiling():
    assert QueryValidator().validate(CLOSED["classic"]).valid
    PrismQLEngine(MemoryBackend(DOCS)).execute(CLOSED["classic"])


def test_server_request_overlay_keeps_the_ceiling(tmp_path):
    fastapi = pytest.importorskip("fastapi")  # noqa: F841
    from fastapi.testclient import TestClient

    from prismql.server.app import create_app
    from prismql.server.config import load_config

    data = tmp_path / "events.jsonl"
    data.write_text(
        "".join(
            f'{{"id": {i}, "user": "a", "text": "x", "timestamp": {100 + i}}}\n'
            for i in range(4)
        )
    )
    cfg = tmp_path / "prismql.toml"
    cfg.write_text(
        '[backend]\ntype = "memory"\ndata = "events.jsonl"\n\n'
        "[engine]\nquantifier_ceiling = 3\n"
    )
    client = TestClient(create_app(load_config(cfg)))
    body = {"query": "SELECT from(a){2,} INWINDOW 3"}
    assert client.post("/evaluate", json=body).status_code == 200
    body["dictionaries"] = {"unused": ["x"]}
    assert client.post("/evaluate", json=body).status_code == 200
    assert client.get("/schema").json()["quantifier_ceiling"] == 3
