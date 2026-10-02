"""GROUP BY puts each matched group in one bucket, keyed by its first
event — a temporal unit or a field value, alone or combined; the id is read
through the backend's id_field (graph @aleph/prismql, #147, #148)."""

import warnings

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

BOTH = pytest.mark.parametrize("use_ir", [True, False])


def _engine(docs: list[dict], use_ir: bool = True, **kw: object) -> PrismQLEngine:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(
            MemoryBackend([dict(d) for d in docs], **kw), use_ir=use_ir
        )


DAYS = [
    {"id": 1, "user": "a", "text": "hello", "timestamp": "2024-01-15T10:00:00"},
    {"id": 2, "user": "b", "text": "world", "timestamp": "2024-01-15T10:05:00"},
    {"id": 3, "user": "a", "text": "hello", "timestamp": "2024-01-16T10:00:00"},
    {"id": 4, "user": "b", "text": "world", "timestamp": "2024-01-16T10:01:00"},
]


@BOTH
def test_temporal_group_by_counts_each_match_once(use_ir):
    e = PrismQLEngine(
        MemoryBackend([dict(d) for d in DAYS]),
        user_dictionaries={"hi": ["hello"], "wo": ["world"]},
        use_ir=use_ir,
    )
    q = (
        "SELECT contains(hi) FOLLOWED_BY contains(wo) INWINDOW 3 "
        "GROUP BY DAYS(timestamp) AGGREGATE COUNT()"
    )
    assert e.execute(q).grouped_values == {"2024-01-15": 1, "2024-01-16": 1}


@BOTH
def test_temporal_group_by_beside_a_field_keeps_the_day(use_ir):
    r = _engine(DAYS, use_ir).execute("SELECT from(a) GROUP BY DAYS(timestamp), user")
    assert not any(str(k).startswith("__none__") for k in r.to_dict()["groups"])


def test_group_by_follows_a_custom_id_field():
    docs = [
        {"mid": i, "user": u, "text": "x"} for i, u in [(1, "a"), (2, "b"), (3, "a")]
    ]
    r = _engine(docs, id_field="mid").execute("SELECT from(a) GROUP BY user")
    assert r.to_dict()["groups"] == {"a": [[1], [3]]}
