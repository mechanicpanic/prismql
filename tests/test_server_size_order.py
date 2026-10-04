"""The whole-result group-size order behind ``GET /results/{id}?order=size``:
stable on ties, built once however many pages ask first, small in memory,
and already counted in the result's size so the store's tally never drifts."""

import random
import threading
import time
import tracemalloc
from array import array

from prismql.server.results import ResultStore, StoredResult


def _with_sizes(sizes: list[int], kind: str = "groups") -> StoredResult:
    offsets = array("q", [0])
    for s in sizes:
        offsets.append(offsets[-1] + s)
    return StoredResult(
        kind, "c", offsets, array("q", range(offsets[-1])), None, None, len(sizes), 0
    )


def _reference(sizes: list[int]) -> list[int]:
    return sorted(range(len(sizes)), key=lambda i: (-sizes[i], i))


def test_size_order_is_largest_first_with_ties_in_stored_order() -> None:
    sizes = [3, 5, 3, 5, 1, 3]
    assert list(_with_sizes(sizes).size_order()) == [1, 3, 0, 2, 5, 4]


def test_size_order_matches_the_brute_force_order_on_random_sizes() -> None:
    rng = random.Random(7)  # noqa: S311 - a reproducible test stream
    for n, top in [(1, 1), (2, 1), (50, 3), (500, 6), (2_000, 40)]:
        sizes = [rng.randint(1, top) for _ in range(n)]
        assert list(_with_sizes(sizes).size_order()) == _reference(sizes), (n, top)


def test_size_order_edges() -> None:
    assert list(_with_sizes([]).size_order()) == []
    assert list(_with_sizes([4] * 6).size_order()) == list(range(6)), "all tied"
    assert list(_with_sizes([9]).size_order()) == [0]
    # one giant group among small ones: no per-size table indexed by size
    assert list(_with_sizes([2, 1_000_000, 2]).size_order()) == [1, 0, 2]


def test_reverse_of_the_size_order_is_its_exact_mirror_across_pages() -> None:
    sizes = [3, 5, 3, 5, 1, 3, 2, 2]
    r = _with_sizes(sizes)
    fwd = [i for off in range(0, 8, 3) for i in r.display_indices(off, 3, "size")]
    rev = [i for off in range(0, 8, 3) for i in r.display_indices(off, 3, "size", True)]
    assert fwd == _reference(sizes) and rev == fwd[::-1]


def test_concurrent_first_pages_build_the_order_once() -> None:
    r = _with_sizes([3, 1, 2] * 1_000)
    builds: list[int] = []
    real = r._build_size_order

    def slow() -> array[int]:
        builds.append(1)
        time.sleep(0.05)  # wide enough that every thread is waiting for it
        return real()

    r._build_size_order = slow  # type: ignore[method-assign]
    got: list[array[int]] = []
    start = threading.Barrier(16)

    def first_page() -> None:
        start.wait()
        got.append(r.size_order())

    threads = [threading.Thread(target=first_page) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(builds) == 1
    assert len(got) == 16 and all(g is got[0] for g in got)


def test_the_order_is_built_in_a_few_bytes_an_item() -> None:
    n = 300_000
    r = _with_sizes([3 + (i * 7919) % 5 for i in range(n)])
    tracemalloc.start()
    try:
        order = r.size_order()
        kept, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(order) == n
    assert kept < 5 * n, "kept: the 4-byte order, nothing else"
    assert peak < 12 * n, f"peak {peak / n:.1f} bytes an item"


def test_a_million_groups_sort_in_practical_time() -> None:
    r = _with_sizes([3 + (i * 7919) % 5 for i in range(1_000_000)])
    began = time.perf_counter()
    r.size_order()
    assert time.perf_counter() - began < 5


def test_nbytes_reserves_the_order_so_building_it_moves_nothing() -> None:
    r = _with_sizes([3] * 1_000)
    before = r.nbytes
    assert before >= 4 * len(r) + 8 * (len(r) + 1) + 8 * len(r.positions)
    r.size_order()
    assert r.nbytes == before
    hits = StoredResult.from_hits("c", [(0, 1.0), (1, 0.5)], total=2)
    assert hits.nbytes == 8 * 3 + 8 * 2 + 8 * 2, "a hits result is never size-sorted"


def test_the_store_tally_returns_to_zero_after_a_built_order_is_evicted() -> None:
    a, b = _with_sizes([3] * 100), _with_sizes([3] * 100)
    store = ResultStore(budget_bytes=int(a.nbytes * 1.5))
    store.put(a)
    a.size_order()
    store.put(b)  # evicts a
    b.size_order()
    assert store._bytes == b.nbytes
