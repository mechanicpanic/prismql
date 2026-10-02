"""Defects found by the docstring audit of 2026-10-02: each docstring or
comment promised one thing and the code silently did another. Every test
states the behaviour the docstring promised (or a loud refusal where no
behaviour is settled) and stays xfail(strict) until the code is fixed."""

import warnings
from datetime import datetime, timedelta

import pytest

from prismql import PrismQLEngine, QueryValidator
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLError

BOTH = pytest.mark.parametrize("use_ir", [True, False])


def _engine(docs: list[dict], use_ir: bool = True, **kw: object) -> PrismQLEngine:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return PrismQLEngine(
            MemoryBackend([dict(d) for d in docs], **kw), use_ir=use_ir
        )


ALTERNATING = [
    {"id": i, "user": "a" if i % 2 else "b", "text": "x", "timestamp": i * 60}
    for i in range(1, 11)
]


# -- lowering / dialects ------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="a lone RUN with a trailing DURING drops a body WITHIN on the IR "
    "path (ir/lower.py _lone_run_span checks InWindow/During/InWin, not Within)",
)
def test_run_with_during_and_within_agrees_on_both_paths():
    t0 = datetime(2024, 1, 1)
    docs = [
        {
            "id": i,
            "kind": "retry" if i in (1, 2, 3, 7, 8, 9, 20, 21) else "x",
            "text": "x",
            "timestamp": (t0 + timedelta(minutes=30 * i)).isoformat(),
        }
        for i in range(1, 25)
    ]
    q = (
        "SELECT RUN(field(kind, retry), INWINDOW 2){2,} "
        "DURING 5 hours WITHIN 30 minutes"
    )
    assert _engine(docs, True).execute(q) == _engine(docs, False).execute(q)


@pytest.mark.xfail(
    strict=True,
    reason="pipe sets a positional and a temporal body window together and "
    "the executor drops the temporal one; classic refuses the same shape",
)
def test_pipe_refuses_two_body_windows():
    with pytest.raises(PrismQLError):
        _engine(ALTERNATING).execute(
            "from(a) + from(b) |> within(3) |> during(30 minutes)"
        )


@pytest.mark.xfail(
    strict=True, reason="a repeated pipe window stage silently keeps the last"
)
def test_pipe_refuses_a_repeated_window_stage():
    with pytest.raises(PrismQLError):
        _engine(ALTERNATING).execute("from(a) + from(b) |> within(3) |> within(5)")


# -- executor -----------------------------------------------------------------


@BOTH
@pytest.mark.xfail(
    strict=True,
    reason="a quantifier over a whole chain takes the first n chain matches "
    "(visitors/query_visitor.py TODO 'just take the first min_count groups')",
)
def test_a_quantifier_over_a_chain_is_refused_not_truncated(use_ir):
    with pytest.raises(PrismQLError):
        _engine(ALTERNATING, use_ir).execute(
            "SELECT (from(a) FOLLOWED_BY from(b) INWINDOW 3){2}"
        )


@BOTH
@pytest.mark.xfail(
    strict=True,
    reason="semicolon stages turn DURING 1 hour into a hard 600-position "
    "window before the time check and drop the match",
)
def test_semicolon_stages_keep_a_match_inside_the_duration(use_ir):
    t0 = datetime(2024, 1, 15)
    docs = [
        {"id": i, "user": "x", "text": "x", "timestamp": (t0 + timedelta(seconds=i))}
        for i in range(1000)
    ]
    docs[0]["user"], docs[900]["user"] = "a", "b"
    for d in docs:
        d["timestamp"] = d["timestamp"].isoformat()
    q = "SELECT (SELECT from(a)) ; (SELECT from(b)) DURING 1 hour"
    assert _engine(docs, use_ir).execute(q) == [[0, 900]]


@BOTH
@pytest.mark.xfail(
    strict=True,
    reason="`NOT from($user)` with $user bound nowhere answers [] instead of "
    "refusing the unbound variable",
)
def test_an_unbound_variable_under_not_is_refused(use_ir):
    with pytest.raises(PrismQLError, match=r"\$user"):
        _engine(ALTERNATING, use_ir).execute(
            "SELECT from(a), NOT from($user) INWINDOW 3"
        )


@pytest.mark.xfail(
    strict=True,
    reason="get_named_group names members by index in stream order, but a "
    "comma row is unordered (types.py NamedQueryResult)",
)
def test_a_name_labels_the_member_its_condition_matched():
    docs = [
        {"id": 1, "user": "bob", "text": "x"},
        {"id": 2, "user": "alice", "text": "x"},
    ]
    r = _engine(docs).execute('SELECT from(alice) AS "a", from(bob) AS "b" INWINDOW 3')
    assert r.get_named_group(0) == {"a": 2, "b": 1}


# -- aggregation --------------------------------------------------------------

DAYS = [
    {"id": 1, "user": "a", "text": "hello", "timestamp": "2024-01-15T10:00:00"},
    {"id": 2, "user": "b", "text": "world", "timestamp": "2024-01-15T10:05:00"},
    {"id": 3, "user": "a", "text": "hello", "timestamp": "2024-01-16T10:00:00"},
    {"id": 4, "user": "b", "text": "world", "timestamp": "2024-01-16T10:01:00"},
]


@BOTH
@pytest.mark.xfail(
    strict=True,
    reason="temporal GROUP BY files a match once per member event "
    "(aggregators/aggregator.py)",
)
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
@pytest.mark.xfail(
    strict=True,
    reason="a temporal field beside another GROUP BY field loses its value "
    "(keys come out as '__none__|a')",
)
def test_temporal_group_by_beside_a_field_keeps_the_day(use_ir):
    r = _engine(DAYS, use_ir).execute("SELECT from(a) GROUP BY DAYS(timestamp), user")
    assert not any(str(k).startswith("__none__") for k in r.to_dict()["groups"])


@pytest.mark.xfail(
    strict=True,
    reason="plain GROUP BY reads doc['id'], not the backend's id_field",
)
def test_group_by_follows_a_custom_id_field():
    docs = [
        {"mid": i, "user": u, "text": "x"} for i, u in [(1, "a"), (2, "b"), (3, "a")]
    ]
    r = _engine(docs, id_field="mid").execute("SELECT from(a) GROUP BY user")
    assert r.to_dict()["groups"] == {"a": [[1], [3]]}


# -- operator layer -----------------------------------------------------------


RUN_DOCS = [
    {"id": "a", "kind": "retry", "text": "x", "timestamp": "2026-01-01T00:00:10"},
    {"id": "b", "kind": "retry", "text": "x", "timestamp": "2026-01-01T00:00:00"},
    {
        "id": "c",
        "kind": "retry",
        "flag": "y",
        "text": "x",
        "timestamp": "2026-01-01T00:00:05",
    },
    {"id": "d", "kind": "z", "text": "x", "timestamp": "2026-01-01T00:00:30"},
]


@BOTH
@pytest.mark.xfail(
    strict=True,
    reason="the run-link as-of fast path never checks the right event is not "
    "already a member of the left run (plan/runlink.py)",
)
def test_a_run_link_never_puts_one_event_in_a_group_twice(use_ir):
    q = (
        "SELECT RUN(field(kind, retry), DURING 10 seconds){2,} "
        "FOLLOWED_BY field(flag, y) INWINDOW 3"
    )
    assert _engine(RUN_DOCS, use_ir).execute(q) == []


@BOTH
@pytest.mark.xfail(
    strict=True,
    reason="the negative run-link fast path drops the run its own member "
    "would follow (plan/runlink.py)",
)
def test_a_negative_run_link_ignores_its_own_member(use_ir):
    q = (
        "SELECT RUN(field(kind, retry), DURING 10 seconds){2,} "
        "NOT_FOLLOWED_BY field(flag, y) INWINDOW 3"
    )
    assert _engine(RUN_DOCS, use_ir).execute(q) == [["b", "c", "a"]]


# -- validator ----------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="classic validation skips the sequence-under-boolean check the "
    "pipe path runs; the engine then refuses the query (validator.py)",
)
@pytest.mark.parametrize(
    "query",
    [
        "SELECT (from(a) FOLLOWED_BY from(b) INWINDOW 3) AND from(c)",
        "SELECT NOT (from(a) FOLLOWED_BY from(b) INWINDOW 3)",
        "SELECT from(a) FOLLOWED_BY (from(b) FOLLOWED_BY from(c) INWINDOW 2)"
        " INWINDOW 3",
    ],
)
def test_classic_validation_rejects_what_the_engine_rejects(query):
    assert not QueryValidator().validate(query).valid


# -- semantic -----------------------------------------------------------------


class _Constant:
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


@pytest.mark.xfail(
    strict=True,
    reason="SemanticIndex indexes whitespace-only text; ingest embed() gives "
    "it a zero vector, so the two paths give similar_to() different sets",
)
def test_whitespace_text_is_not_indexed_on_either_path():
    from prismql.backends.semantic import SemanticIndex

    docs = [{"id": 1, "text": "oil"}, {"id": 2, "text": "   "}]
    index = SemanticIndex(_Constant(), docs)
    assert index.search("oil", threshold=0.5) == {1}
