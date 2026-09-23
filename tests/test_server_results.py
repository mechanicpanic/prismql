"""The server's result store: folded results under ids (graph #65)."""

import re
import tracemalloc
from collections.abc import Callable
from typing import Any

from prismql.backends.memory import MemoryBackend
from prismql.server.pages import page_payload, rows_page_payload
from prismql.server.results import ResultStore, StoredResult


def test_groups_are_folded_and_windowed() -> None:
    r = StoredResult.from_groups("groups", "c", [[0, 5], [7, 9], [12, 30]])
    assert len(r) == 3 and r.total == 3 and r.kind == "groups"
    assert r.window(1, 5) == [([7, 9], None), ([12, 30], None)]
    assert r.window(3, 5) == []


def test_hits_keep_scores_and_the_true_total() -> None:
    r = StoredResult.from_hits("c", [(4, 0.9), (1, 0.5)], total=17)
    assert len(r) == 2 and r.total == 17 and r.kind == "hits"
    assert r.window(0, 1) == [([4], 0.9)]


def test_rows_are_kept_in_the_engine_order_with_function_and_field() -> None:
    r = StoredResult.from_rows(
        "c", [("alice", 3), ("bob", 1)], function="count", field_name=None
    )
    assert len(r) == 2 and r.total == 2 and r.kind == "rows"
    assert r.function == "count" and r.field_name is None
    assert r.rows_window(0, 1) == [("alice", 3)]
    assert r.rows_window(1, 5) == [("bob", 1)]
    assert r.rows_window(5, 5) == []


def _measure_build_bytes(build: Callable[[], list[Any]]) -> int:
    # tracemalloc's own delta around building the rows list, the canonical
    # carrier for "how much memory these rows really hold" (graph
    # @aleph/prismql, #90 fix round 1, #4: a JSON-length estimate undercounts
    # by ~4x for (str, int) rows — CPython object headers cost bytes JSON
    # never serializes).
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        built = build()
        after = tracemalloc.get_traced_memory()[0]
        assert built  # keep it alive until measured
        return after - before
    finally:
        tracemalloc.stop()


def test_rows_nbytes_is_within_2x_of_a_tracemalloc_measurement_str_int() -> None:
    n = 2000
    rows = [(f"user{i}", i + 10_000) for i in range(n)]
    measured = _measure_build_bytes(
        lambda: [(f"user{i}", i + 10_000) for i in range(n)]
    )
    estimate = StoredResult.from_rows("c", rows, "count", None).nbytes
    assert measured / 2 <= estimate <= measured * 2, (measured, estimate)


def test_rows_nbytes_is_within_2x_of_a_tracemalloc_measurement_distinct_lists() -> None:
    # Distinct list values are the case the brief calls out as worse for a
    # JSON-length estimate.
    n = 500
    rows = [(f"user{i}", [f"v{i}-{j}" for j in range(5)]) for i in range(n)]
    measured = _measure_build_bytes(
        lambda: [(f"user{i}", [f"v{i}-{j}" for j in range(5)]) for i in range(n)]
    )
    estimate = StoredResult.from_rows("c", rows, "distinct", "agent").nbytes
    assert measured / 2 <= estimate <= measured * 2, (measured, estimate)


def test_rows_page_payload_pages_and_reports_total() -> None:
    r = StoredResult.from_rows(
        "c",
        [("a", 3), ("b", [1, 2]), ("c", 0)],
        function="distinct",
        field_name="agent",
    )
    p = rows_page_payload(r, offset=0, limit=2)
    assert p["kind"] == "rows"
    assert p["function"] == "distinct" and p["field"] == "agent"
    assert p["total"] == 3 and p["count"] == 2 and p["truncated"] is True
    assert p["rows"] == [{"key": "a", "value": 3}, {"key": "b", "value": [1, 2]}]
    tail = rows_page_payload(r, offset=2, limit=2)
    assert tail["rows"] == [{"key": "c", "value": 0}] and tail["truncated"] is False


def test_store_evicts_oldest_over_budget_but_keeps_the_newest() -> None:
    one = StoredResult.from_groups("groups", "c", [[i] for i in range(100)])
    store = ResultStore(budget_bytes=one.nbytes * 2)
    a, b, c = (
        store.put(StoredResult.from_groups("groups", "c", [[i] for i in range(100)]))
        for _ in range(3)
    )
    assert store.get(a) is None and store.get(b) and store.get(c)
    huge = StoredResult.from_groups("groups", "c", [[i] for i in range(10_000)])
    h = store.put(huge)  # bigger than the whole budget: kept alone
    assert store.get(h) is huge and store.get(c) is None


def test_from_groups_and_from_hits_carry_the_load_generation() -> None:
    # positions are only valid for the load they were computed on
    # (fix round 1, item 1): the store must remember which one that was.
    g = StoredResult.from_groups("groups", "c", [[0]], load=3)
    h = StoredResult.from_hits("c", [(0, 1.0)], total=1, load=5)
    assert g.load == 3 and h.load == 5
    assert StoredResult.from_groups("groups", "c", [[0]]).load == 0


def test_ids_are_unique_and_clear_forgets_everything() -> None:
    store = ResultStore(budget_bytes=1 << 20)
    r1 = store.put(StoredResult.from_groups("groups", "c", [[1]]))
    r2 = store.put(StoredResult.from_groups("groups", "c", [[2]]))
    assert r1 != r2 and r1.startswith("r")
    store.clear()
    assert store.get(r1) is None and store.get(r2) is None


def test_ids_carry_an_opaque_hex_suffix_that_differs_across_puts() -> None:
    # The counter alone repeats from 1 in every process (fix round 2, #1):
    # after a restart an id held from before it would page a DIFFERENT
    # query's result with ok:true. The hex half is drawn fresh per result —
    # practically never repeats across processes and is not guessable.
    store = ResultStore(budget_bytes=1 << 20)
    r1 = store.put(StoredResult.from_groups("groups", "c", [[1]]))
    r2 = store.put(StoredResult.from_groups("groups", "c", [[2]]))
    assert re.fullmatch(r"r\d+-[0-9a-f]{8}", r1)
    assert re.fullmatch(r"r\d+-[0-9a-f]{8}", r2)
    assert r1.split("-", 1)[1] != r2.split("-", 1)[1]


DOCS = [
    {"id": "a", "text": "one", "kind": "x", "timestamp": "2026-06-03T18:02:11Z"},
    {"id": "b", "text": "two", "kind": "y", "timestamp": "2026-06-03T18:19:40Z"},
    {"id": "c", "text": "three", "kind": "x", "timestamp": "2026-06-03T18:30:00Z"},
]


def _backend() -> MemoryBackend:
    return MemoryBackend(DOCS, id_field="id", timestamp_fields=["timestamp"])


def test_group_page_carries_positions_times_and_projected_events():
    r = StoredResult.from_groups("groups", "c", [[0, 2], [1]])
    p = page_payload(
        r,
        _backend(),
        id_field="id",
        time_field="timestamp",
        offset=0,
        limit=1,
        hydrate=True,
        fields=["text"],
    )
    assert p["total"] == 2 and p["count"] == 1 and p["truncated"] is True
    g = p["results"][0]
    assert g["ids"] == ["a", "c"] and g["positions"] == [0, 2]
    assert g["times"] == [
        "2026-06-03T18:02:11+00:00",
        "2026-06-03T18:30:00+00:00",
    ]
    assert g["events"] == [{"id": "a", "text": "one"}, {"id": "c", "text": "three"}]


def test_unhydrated_page_has_no_events_and_unknown_time_field_is_null():
    r = StoredResult.from_groups("groups", "c", [[1]])
    p = page_payload(
        r,
        _backend(),
        id_field="id",
        time_field="nope",
        offset=0,
        limit=10,
        hydrate=False,
        fields=None,
    )
    assert "events" not in p["results"][0]
    assert p["results"][0]["times"] == [None] and p["truncated"] is False


def test_hit_page_reports_kept_and_total():
    r = StoredResult.from_hits("c", [(2, 0.9), (0, 0.4)], total=5)
    p = page_payload(
        r,
        _backend(),
        id_field="id",
        time_field="timestamp",
        offset=1,
        limit=10,
        hydrate=False,
        fields=None,
    )
    assert p["kind"] == "hits" and p["kept"] == 2 and p["total"] == 5
    assert p["hits"] == [
        {"id": "a", "position": 0, "score": 0.4, "time": "2026-06-03T18:02:11+00:00"}
    ]
    assert (
        p["truncated"] is False
    )  # 3 more were found but not kept: kept < total says so


def test_hit_paging_terminates_once_all_kept_hits_are_seen() -> None:
    r = StoredResult.from_hits("c", [(2, 0.9), (0, 0.4)], total=5)
    offset = 0
    seen = 0
    truncated = True
    for _ in range(5):  # guard: a non-terminating loop would hang, not just fail
        p = page_payload(
            r,
            _backend(),
            id_field="id",
            time_field="timestamp",
            offset=offset,
            limit=1,
            hydrate=False,
            fields=None,
        )
        seen += p["count"]
        truncated = p["truncated"]
        offset += p["count"]
        if not truncated:
            break
    assert seen == 2
    assert truncated is False
    assert p["kept"] == 2 and p["total"] == 5
