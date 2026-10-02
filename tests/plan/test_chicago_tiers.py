"""Chicago tiers as a gate for the plan primitives (P2 task 7).

Rebuilds the spike's three queries through the primitives and asserts
tuple-for-tuple equality with the engine. Q3 (co-occurrence) is compared
unordered with the engine; only its committed spike count is the ordered
subset (ROBBERY first), from the D2-era engine. Since P3 the engine is the
plan, so the committed counts are the independent oracle (see COMMITTED
below). Runs on 100k by default; `PRISMQL_TIERS=100k,1m`
adds 1m. The full tier is never run here (owner's word only).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pl = pytest.importorskip("polars")
pq = pytest.importorskip("pyarrow.parquet")

from prismql.backends.memory import MemoryBackend  # noqa: E402
from prismql.engine import PrismQLEngine  # noqa: E402
from prismql.plan.corpus import corpus_frame, to_groups  # noqa: E402
from prismql.plan.primitives import (  # noqa: E402
    body_span_filter,
    cooccur,
    extend_link,
    nearest_link,
)

DATA = Path(
    "~/Projects/research/prismql-research/benchmarks/chicago-crime/data"
).expanduser()
TIERS = os.environ.get("PRISMQL_TIERS", "100k").split(",")
MIN30 = 30 * 60 * 1_000_000

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(
        not (DATA / "tier_100k.parquet").exists(), reason="Chicago tiers absent"
    ),
]


def _backend(records: list[dict]) -> object:
    try:
        from prismql.backends.rust_memory import RustMemoryBackend

        return RustMemoryBackend(documents=records, timestamp_fields=["timestamp"])
    except ImportError:  # pragma: no cover
        return MemoryBackend(documents=records)


@pytest.fixture(scope="module", params=TIERS)
def tier(request):
    table = pq.read_table(DATA / f"tier_{request.param}.parquet")
    engine = PrismQLEngine(_backend(table.to_pylist()), timestamp_field="timestamp")
    return corpus_frame(table), engine


def _sel(lf: object, t: str) -> object:
    return lf.filter(pl.col("type") == t)


def _tuples(groups: list[list[int]]) -> list[tuple[int, ...]]:
    return sorted(tuple(g) for g in groups)


def test_q1_followed_by_positional(tier):
    lf, engine = tier
    got = nearest_link(
        _sel(lf, "ROBBERY"),
        _sel(lf, "BATTERY"),
        axis="position",
        window=5,
        forward=True,
    )
    want = engine.execute(
        'SELECT field(type, "ROBBERY") FOLLOWED_BY field(type, "BATTERY") INWINDOW 5'
    )
    assert _tuples(to_groups(got.collect())) == _tuples(want)
    assert want


def test_q2_correlated_temporal_chain_with_body_window(tier):
    lf, engine = tier
    r, b, m = _sel(lf, "ROBBERY"), _sel(lf, "BATTERY"), _sel(lf, "MOTOR VEHICLE THEFT")
    pairs = nearest_link(
        r, b, axis="timestamp_us", window=MIN30, forward=True, key="cell"
    )
    chain = extend_link(
        lf, pairs, m, axis="timestamp_us", window=MIN30, forward=True, key="cell"
    )
    body = body_span_filter(chain, lf, axis="timestamp_us", span=MIN30)
    want = engine.execute(
        'SELECT field(type, "ROBBERY") AND field(cell, $c) '
        'FOLLOWED_BY field(type, "BATTERY") AND field(cell, $c) DURING 30 minutes '
        'FOLLOWED_BY field(type, "MOTOR VEHICLE THEFT") AND field(cell, $c) '
        "DURING 30 minutes "
        "DURING 30 minutes"
    )
    assert _tuples(to_groups(body.collect())) == _tuples(want)
    assert want


# Tuple counts committed by the Polars spike (prismql-research/experiments/
# polars-spike/RESULTS.md): the independent oracle now that the engine *is*
# the plan. Q3's committed count is the ordered subset (the spike compared
# against the D2-era engine); the full unordered result is checked against
# the primitive.
COMMITTED = {
    "100k": {"q1": 1288, "q2": 4, "q3_ordered": 1966},
    "1m": {"q1": 20831, "q2": 28, "q3_ordered": 30832},
}


def test_q3_cooccurrence_unordered(tier, request):
    lf, engine = tier
    name = request.node.callspec.id
    got = to_groups(
        cooccur([_sel(lf, "ROBBERY"), _sel(lf, "BATTERY")], axis="position", window=5)
    )
    want = engine.execute(
        'SELECT field(type, "ROBBERY"), field(type, "BATTERY") INWINDOW 5'
    )
    assert _tuples(got) == _tuples(want)
    robbery = set(
        lf.filter(pl.col("type") == "ROBBERY").select("id").collect()["id"].to_list()
    )
    assert len([g for g in want if g[0] in robbery]) == COMMITTED[name]["q3_ordered"]


def test_committed_counts(tier, request):
    """Q1 and Q2 through the engine equal the counts the spike committed."""
    _, engine = tier
    name = request.node.callspec.id
    q1 = engine.execute(
        'SELECT field(type, "ROBBERY") FOLLOWED_BY field(type, "BATTERY") INWINDOW 5'
    )
    q2 = engine.execute(
        'SELECT field(type, "ROBBERY") AND field(cell, $c) '
        'FOLLOWED_BY field(type, "BATTERY") AND field(cell, $c) DURING 30 minutes '
        'FOLLOWED_BY field(type, "MOTOR VEHICLE THEFT") AND field(cell, $c) '
        "DURING 30 minutes "
        "DURING 30 minutes"
    )
    assert len(q1) == COMMITTED[name]["q1"]
    assert len(q2) == COMMITTED[name]["q2"]
