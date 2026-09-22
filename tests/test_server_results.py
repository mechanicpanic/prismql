"""The server's result store: folded results under ids (graph #65)."""

from prismql.backends.memory import MemoryBackend
from prismql.server.pages import page_payload
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


def test_ids_are_unique_and_clear_forgets_everything() -> None:
    store = ResultStore(budget_bytes=1 << 20)
    r1 = store.put(StoredResult.from_groups("groups", "c", [[1]]))
    r2 = store.put(StoredResult.from_groups("groups", "c", [[2]]))
    assert r1 != r2 and r1.startswith("r")
    store.clear()
    assert store.get(r1) is None and store.get(r2) is None


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
