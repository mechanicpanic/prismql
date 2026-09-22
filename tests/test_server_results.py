"""The server's result store: folded results under ids (graph #65)."""

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
