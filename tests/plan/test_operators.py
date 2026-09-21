"""The operator layer (P3 task 3) against the P2 oracles and the pinned
audit fixtures. Legs are evaluated predicate sets, as the executor will
hand them over; the frame is the per-query frame."""

import pytest

from prismql.backends.memory import MemoryBackend

pl = pytest.importorskip("polars")

from prismql.plan.frames import query_frame  # noqa: E402
from prismql.plan.operators import (  # noqa: E402
    Leg,
    body_span,
    cooccur_row,
    groups,
    link,
    negative_link,
    quantified_row,
    variable_fields,
)
from tests.plan.conftest import random_corpus  # noqa: E402
from tests.plan.test_anti_link import brute_anti  # noqa: E402
from tests.plan.test_chains import brute_chain  # noqa: E402
from tests.plan.test_cooccur import brute_cooccur  # noqa: E402
from tests.plan.test_quantify import brute_quantify  # noqa: E402

TS = "timestamp"


def _frame(docs: list[dict], legs: list[Leg]) -> object:
    backend = MemoryBackend(docs)
    ids = {m for leg in legs for m in leg.ids}
    return query_frame(backend, ids, fields=variable_fields(legs), timestamp_field=TS)


def _ids(docs: list[dict], **eq: object) -> frozenset:
    return frozenset(d["id"] for d in docs if all(d.get(k) == v for k, v in eq.items()))


def _win(axis: str, w: int) -> int | tuple[int, str]:
    """The operator takes DURING in units; the brute oracles take the axis
    itself (microseconds) — `_brute_w` scales for them."""
    return w if axis == "position" else (w, "seconds")


def _brute_w(axis: str, w: int) -> int:
    return w if axis == "position" else w * 1_000_000


# --- the pinned A10 fixture ------------------------------------------------

DISTRACTOR = [
    {"id": 1, "user": "x", "kind": "save", "page": "P1", "timestamp": 100},
    {"id": 2, "user": "a", "kind": "save", "page": "P1", "timestamp": 200},
    {"id": 3, "user": "adm", "kind": "delete", "page": "P1", "timestamp": 300},
    {"id": 4, "user": "y", "kind": "save", "page": "P1", "timestamp": 400},
    {"id": 5, "user": "a", "kind": "save", "page": "P1", "timestamp": 500},
]


def test_two_variables_on_a_leg_select_the_nearest_eligible():
    save_u_p = Leg(_ids(DISTRACTOR, kind="save"), equal=(("u", "user"), ("p", "page")))
    frame = _frame(DISTRACTOR, [save_u_p])
    res = link(
        frame,
        None,
        save_u_p,
        save_u_p,
        window=(1, "day"),
        forward=True,
        timestamp_field=TS,
    )
    assert groups(res) == [[2, 5]]
    df = res.collect()
    assert df["_v_u"].to_list() == ["a", "a"] and df["_v_p"].to_list() == ["P1", "P1"]


def test_a_variable_that_skips_a_leg_is_held_by_the_carried_binding():
    save_u = Leg(_ids(DISTRACTOR, kind="save"), equal=(("u", "user"),))
    delete = Leg(_ids(DISTRACTOR, kind="delete"))
    frame = _frame(DISTRACTOR, [save_u, delete])
    s1 = link(
        frame, None, save_u, delete, window=(1, "day"), forward=True, timestamp_field=TS
    )
    assert groups(s1) == [[1, 3], [2, 3]]
    s2 = link(
        frame, s1, None, save_u, window=(1, "day"), forward=True, timestamp_field=TS
    )
    assert groups(s2) == [[2, 3, 5]]


def test_unequal_variable_takes_the_nearest_other_user():
    save_u = Leg(_ids(DISTRACTOR, kind="save"), equal=(("u", "user"),))
    save_not_u = Leg(_ids(DISTRACTOR, kind="save"), unequal=(("u", "user"),))
    frame = _frame(DISTRACTOR, [save_u])
    res = link(
        frame, None, save_u, save_not_u, window=3, forward=True, timestamp_field=TS
    )
    assert groups(res) == [[1, 2], [2, 4], [4, 5]]


def test_unequal_needs_an_earlier_binding():
    save_not_u = Leg(_ids(DISTRACTOR, kind="save"), unequal=(("u", "user"),))
    plain = Leg(_ids(DISTRACTOR, kind="save"))
    frame = _frame(DISTRACTOR, [plain])
    from prismql.exceptions import PrismQLRuntimeError

    with pytest.raises(PrismQLRuntimeError, match="no earlier leg binds"):
        link(frame, None, plain, save_not_u, window=3, forward=True, timestamp_field=TS)


# --- the review's co-occurrence case ---------------------------------------


def test_cooccur_holds_a_second_variable_before_canonicalization():
    docs = [
        {"id": 1, "user": "a", "page": "P1", "timestamp": 1},
        {"id": 2, "user": "a", "page": "P2", "timestamp": 2},
        {"id": 3, "user": "a", "page": "P1", "timestamp": 3},
    ]
    leg = Leg(_ids(docs), equal=(("u", "user"), ("p", "page")))
    frame = _frame(docs, [leg])
    assert groups(cooccur_row(frame, [leg, leg], window=3, timestamp_field=TS)) == [
        [1, 3]
    ]
    one_var = Leg(_ids(docs), equal=(("u", "user"),))
    assert groups(
        cooccur_row(frame, [one_var, one_var], window=3, timestamp_field=TS)
    ) == [[1, 2], [1, 3], [2, 3]]


# --- parity with the P2 oracles on hostile corpora ---------------------------


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("axis,window", [("position", 3), ("timestamp_us", 3600)])
@pytest.mark.parametrize("forward", [True, False])
def test_three_leg_chain_with_key_matches_brute(seed, axis, window, forward):
    docs = random_corpus(
        seed, gapped_ids=True, monotone_time=False, ties=True, nulls=True
    )
    legs = [
        Leg(_ids(docs, kind="X"), equal=(("u", "user"),)),
        Leg(_ids(docs, kind="Y"), equal=(("u", "user"),)),
        Leg(_ids(docs, kind="Z"), equal=(("u", "user"),)),
    ]
    frame = _frame(docs, legs)
    res = link(
        frame,
        None,
        legs[0],
        legs[1],
        window=_win(axis, window),
        forward=forward,
        timestamp_field=TS,
    )
    res = link(
        frame,
        res,
        None,
        legs[2],
        window=_win(axis, window),
        forward=forward,
        timestamp_field=TS,
    )
    preds = [
        lambda r: r["kind"] == "X",
        lambda r: r["kind"] == "Y",
        lambda r: r["kind"] == "Z",
    ]
    expected = brute_chain(
        docs,
        preds,
        axis=axis,
        window=_brute_w(axis, window),
        forward=forward,
        key="user",
    )
    assert expected  # the fixture must exercise the oracle
    assert groups(res) == expected


@pytest.mark.parametrize("seed", range(4))
@pytest.mark.parametrize("axis,window", [("position", 4), ("timestamp_us", 60)])
def test_cooccur_row_without_variables_matches_brute(seed, axis, window):
    docs = random_corpus(seed, gapped_ids=True, ties=True, nulls=True)
    legs = [
        Leg(_ids(docs, kind="X")),
        Leg(_ids(docs, kind="Y")),
        Leg(_ids(docs, kind="Z")),
    ]
    frame = _frame(docs, legs)
    res = cooccur_row(frame, legs, window=_win(axis, window), timestamp_field=TS)
    preds = [
        lambda r: r["kind"] == "X",
        lambda r: r["kind"] == "Y",
        lambda r: r["kind"] == "Z",
    ]
    expected = brute_cooccur(docs, preds, axis=axis, window=_brute_w(axis, window))
    assert expected
    assert groups(res) == expected


@pytest.mark.parametrize("seed", range(3))
def test_quantified_row_matches_brute(seed):
    docs = random_corpus(seed, n=60, ties=True)
    leg = Leg(_ids(docs, kind="X"), equal=(("u", "user"),))
    frame = _frame(docs, [leg])
    res = quantified_row(frame, leg, n_min=2, n_max=3, window=5, timestamp_field=TS)
    expected = brute_quantify(
        docs,
        lambda r: r["kind"] == "X",
        axis="position",
        window=5,
        n_min=2,
        n_max=3,
        key="user",
    )
    assert groups(res) == expected


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("forward", [True, False])
def test_negative_link_matches_brute(seed, forward):
    docs = random_corpus(seed, gapped_ids=True, nulls=True)
    lhs, rhs = Leg(_ids(docs, kind="X")), Leg(_ids(docs, kind="Y"))
    frame = _frame(docs, [lhs, rhs])
    res = negative_link(
        frame, lhs, rhs, window=(60, "seconds"), forward=forward, timestamp_field=TS
    )
    expected = brute_anti(
        docs,
        lambda r: r["kind"] == "X",
        lambda r: r["kind"] == "Y",
        axis="timestamp_us",
        window=60 * 1_000_000,
        forward=forward,
    )
    assert groups(res) == expected


def test_body_span_rejects_null_timestamps_and_wide_groups():
    docs = [
        {"id": 1, "user": "a", "timestamp": 10},
        {"id": 2, "user": "b", "timestamp": 15},
        {"id": 3, "user": "a", "timestamp": None},
        {"id": 4, "user": "b", "timestamp": 400},
    ]
    a, b = Leg(_ids(docs, user="a")), Leg(_ids(docs, user="b"))
    frame = _frame(docs, [a, b])
    res = cooccur_row(frame, [a, b], window=3, timestamp_field=TS)
    assert groups(res) == [[1, 2], [1, 4], [2, 3], [3, 4]]
    assert groups(
        body_span(frame, res, window=(10, "seconds"), timestamp_field=TS)
    ) == [[1, 2]]


def test_slots_follow_the_axis_not_the_id():
    docs = [
        {"id": 9, "user": "a", "timestamp": 100},
        {"id": 1, "user": "b", "timestamp": 200},
    ]
    a, b = Leg(_ids(docs, user="a")), Leg(_ids(docs, user="b"))
    frame = _frame(docs, [a, b])
    res = link(frame, None, a, b, window=(1, "day"), forward=True, timestamp_field=TS)
    assert groups(res) == [[9, 1]]  # A9: the engine would print [1, 9]
