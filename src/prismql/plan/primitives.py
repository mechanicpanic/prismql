"""Sequence/window primitives as Polars operations (spec 2026-09-18, P2).

Each function is ONE statement over frames of corpus rows; the operator
layer (P3) composes them. Shared semantics: greedy nearest match per left
row, strict ``>`` on the axis, ties broken by ``(axis, position)`` — the
lowest position forward, the highest backward — one match per left row,
right rows reusable.

Two execution paths implement the same statement:

* **asof** (``eligible is None``): ``join_asof`` with the key shifted by
  one axis unit and ``tolerance = window - 1``; ``key`` becomes ``by=``.
* **candidates** (``eligible`` given): bucketize the axis by ``window``,
  equi-join adjacent buckets, filter the exact window and the eligibility
  predicate, then keep the nearest candidate per left row. Eligibility
  takes part in *choosing* the match (P2 review, finding 1): a filter after
  asof would drop a later eligible match.

The candidate path is the internal oracle for the asof path: with
``eligible=pl.lit(True)`` both must agree on every fixture.
"""

from __future__ import annotations

from typing import Any

from . import _pl

RESULT_COLUMNS = ("group", "slot", "position", "id")


def _prefixed(frame: Any, prefix: str, axis: str, key: str | None) -> Any:
    """Corpus rows -> the same rows with every column prefixed; null axis or
    key values cannot take part in a link and are dropped."""
    drop = [axis] + ([key] if key else [])
    frame = frame.drop_nulls(drop)
    return frame.rename({c: f"{prefix}{c}" for c in frame.collect_schema().names()})


def _empty_result(lhs: Any) -> Any:
    pl = _pl()
    id_dtype = lhs.collect_schema()["id"]
    return pl.LazyFrame(
        schema={
            "group": pl.UInt32,
            "slot": pl.UInt32,
            "position": pl.Int64,
            "id": id_dtype,
        }
    )


def _result(joined: Any, legs: list[tuple[str, str]], order: list[str]) -> Any:
    """Explode leg columns ``[(position_col, id_col), ...]`` into the result
    schema; groups are numbered in ``order``."""
    pl = _pl()
    frame = joined.sort(order).with_row_index("group")
    parts = [
        frame.select(
            pl.col("group"),
            pl.lit(i, dtype=pl.UInt32).alias("slot"),
            pl.col(pcol).cast(pl.Int64).alias("position"),
            pl.col(icol).alias("id"),
        )
        for i, (pcol, icol) in enumerate(legs)
    ]
    return pl.concat(parts).sort(["group", "slot"])


def nearest_link(
    lhs: Any,
    rhs: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
    eligible: Any | None = None,
) -> Any:
    """Greedy nearest ``rhs`` strictly after (forward) / before (backward)
    each ``lhs`` row, within ``window`` units of ``axis``.

    ``lhs``/``rhs`` are LazyFrames of corpus rows (``position``, ``id``,
    the axis column, any fields). ``key`` requires equality on that column.
    ``eligible`` is a Polars expression over the joined pair, where lhs
    columns are prefixed ``l_`` and rhs columns ``r_`` (e.g.
    ``pl.col("r_user") != pl.col("l_user")`` for ``!$u``); it is evaluated
    before the nearest candidate is chosen.

    Returns the result frame ``(group, slot, position, id)`` with slot 0 the
    earlier element on the axis, groups ordered by the lhs row's
    ``(axis, position)``.
    """
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    if window == 0:
        # Strict '>' leaves nothing within distance 0. Polars would accept
        # tolerance=-1 and match everything — never reach it.
        return _empty_result(lhs)

    l_ax, r_ax = f"l_{axis}", f"r_{axis}"
    left = _prefixed(lhs, "l_", axis, key)
    right = _prefixed(rhs, "r_", axis, key)
    joined = _link(pl, left, right, l_ax, r_ax, window, forward, key, eligible)
    legs = [("l_position", "l_id"), ("r_position", "r_id")]
    if not forward:
        legs.reverse()
    return _result(joined, legs, order=[l_ax, "l_position"])


def extend_link(
    corpus: Any,
    seqs: Any,
    rhs: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
    eligible: Any | None = None,
) -> Any:
    """Extend every group of a result frame by one slot: the nearest ``rhs``
    strictly after the group's last slot (forward) / before its first slot
    (backward), within ``window`` on ``axis``.

    ``corpus`` supplies the anchor's axis/key columns by ``position``. A
    message already in the group is never eligible (distinctness across
    axes — the engine's A7 defect is fixed here by construction). ``key``
    is equality between the anchor and the new slot. Groups with no
    eligible candidate are dropped; the others keep their group number.
    """
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    if window == 0:
        return _empty_result(seqs)
    seqs = seqs.sort(["group", "slot"])
    edge = pl.col("slot").max() if forward else pl.col("slot").min()
    anchors = (
        seqs.group_by("group", maintain_order=True)
        .agg(
            pl.col("position").filter(pl.col("slot") == edge).first().alias("position"),
            pl.col("position").alias("_members"),
            pl.col("slot").max().alias("_max_slot"),
        )
        .join(corpus, on="position", how="inner")
    )
    l_ax, r_ax = f"l_{axis}", f"r_{axis}"
    left = _prefixed(anchors, "l_", axis, key)
    right = _prefixed(rhs, "r_", axis, key)
    distinct = ~pl.col("r_position").is_in(pl.col("l__members"))
    eligible = distinct if eligible is None else (distinct & eligible)
    joined = _link(pl, left, right, l_ax, r_ax, window, forward, key, eligible)
    new_slot = (pl.col("l__max_slot") + 1) if forward else pl.lit(0, dtype=pl.UInt32)
    added = joined.select(
        pl.col("l_group").alias("group"),
        new_slot.cast(pl.UInt32).alias("slot"),
        pl.col("r_position").cast(pl.Int64).alias("position"),
        pl.col("r_id").alias("id"),
    )
    survivors = added.select("group")
    kept = seqs.join(survivors, on="group", how="semi")
    if not forward:
        kept = kept.with_columns((pl.col("slot") + 1).cast(pl.UInt32))
    return pl.concat([kept, added]).sort(["group", "slot"])


def anti_link(
    lhs: Any,
    rhs: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    key: str | None = None,
    eligible: Any | None = None,
) -> Any:
    """NOT_FOLLOWED_BY / NOT_PRECEDED_BY: the ``lhs`` rows for which no
    eligible ``rhs`` lies strictly after (forward) / before (backward)
    within ``window`` on ``axis``. One slot per group, ordered by the lhs
    row's ``(axis, position)``.

    An lhs row with a null axis value cannot be shown to have no follower
    and is dropped (the engine keeps it — recorded as a divergence).
    ``window == 0`` keeps every lhs row: nothing lies within distance 0.
    """
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    l_ax = f"l_{axis}"
    left = _prefixed(lhs, "l_", axis, key)
    if window > 0:
        right = _prefixed(rhs, "r_", axis, key)
        matched = _link(
            pl, left, right, l_ax, f"r_{axis}", window, forward, key, eligible
        )
        left = left.join(matched.select("l_position"), on="l_position", how="anti")
    return _result(left, [("l_position", "l_id")], order=[l_ax, "l_position"])


def cooccur(
    frames: list[Any],
    *,
    axis: str,
    window: int,
    key: str | None = None,
) -> Any:
    """Unordered co-occurrence (INWINDOW / DURING over a comma list): every
    combination of one row per frame whose members are pairwise distinct
    and whose axis span ``max - min <= window``; ``key`` requires equality
    across all members. Restriction order is irrelevant by definition
    (spec D2): each group is canonicalized by ``(axis, position)`` and
    deduplicated as a set, so ``cooccur([A, B]) == cooccur([B, A])``.

    Slots are ranks in that canonical order; groups are ordered by their
    canonical ``(axis, position)`` tuples.
    """
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    if not frames:
        raise ValueError("cooccur needs at least one frame")
    k = len(frames)

    def leg(i: int) -> Any:
        cols = [
            pl.col("position").alias(f"p{i}"),
            pl.col(axis).alias(f"a{i}"),
            pl.col("id").alias(f"i{i}"),
        ]
        if key:
            cols.append(pl.col(key).alias(f"k{i}"))
        drop = [axis] + ([key] if key else [])
        return frames[i].drop_nulls(drop).select(cols)

    g = leg(0).with_columns(pl.col("a0").alias("_lo"), pl.col("a0").alias("_hi"))
    # window == 0 still admits equal axis values on distinct messages
    # (ties): bucket by max(window, 1) so the join key is well defined.
    w = max(window, 1)
    for i in range(1, k):
        right = leg(i).with_columns((pl.col(f"a{i}") // w).alias("_b"))
        b_lo = (pl.col("_hi") - window) // w
        b_hi = (pl.col("_lo") + window) // w
        left = g.with_columns(pl.int_ranges(b_lo, b_hi + 1).alias("_b")).explode("_b")
        on, right_on = ["_b"], ["_b"]
        if key:
            on.append("k0")
            right_on.append(f"k{i}")
        j = left.join(right, left_on=on, right_on=right_on, how="inner")
        members = [pl.col(f"p{m}") for m in range(i)]
        distinct = pl.all_horizontal([pl.col(f"p{i}") != m for m in members])
        fits = (pl.col(f"a{i}") >= pl.col("_hi") - window) & (
            pl.col(f"a{i}") <= pl.col("_lo") + window
        )
        g = (
            j.filter(distinct & fits)
            .with_columns(
                pl.min_horizontal("_lo", f"a{i}").alias("_lo"),
                pl.max_horizontal("_hi", f"a{i}").alias("_hi"),
            )
            .drop("_b")
        )
    g = g.drop(["_lo", "_hi"])
    # Canonical order inside a group: (axis, position); dedupe as a set.
    g = g.with_row_index("_row")
    long = pl.concat(
        [
            g.select(
                "_row",
                pl.col(f"a{i}").alias("_ax"),
                pl.col(f"p{i}").cast(pl.Int64).alias("position"),
                pl.col(f"i{i}").alias("id"),
            )
            for i in range(k)
        ]
    ).sort(["_row", "_ax", "position"])
    long = long.with_columns(
        pl.int_range(pl.len()).over("_row").cast(pl.UInt32).alias("slot")
    )
    keyed = long.group_by("_row").agg(
        pl.col("_ax").alias("_axs"),
        pl.col("position").alias("_pos"),
    )
    # Group order = the canonical (axis, position) pairs compared slot by slot.
    order_cols: list[str] = []
    for i in range(k):
        keyed = keyed.with_columns(
            pl.col("_axs").list.get(i).alias(f"_oa{i}"),
            pl.col("_pos").list.get(i).alias(f"_op{i}"),
        )
        order_cols += [f"_oa{i}", f"_op{i}"]
    keyed = (
        keyed.unique(subset=["_pos"], keep="first")
        .sort(order_cols)
        .with_row_index("group")
    )
    return (
        long.join(keyed.select("_row", "group"), on="_row", how="inner")
        .select("group", "slot", "position", "id")
        .sort(["group", "slot"])
    )


def quantify(
    frame: Any,
    *,
    axis: str,
    window: int,
    n_min: int,
    n_max: int | None,
    key: str | None = None,
    max_size: int = 6,
) -> Any:
    """A quantified restriction ``{n_min,n_max}``: every subset of ``n``
    distinct matches of ``frame`` (``n_min <= n <= n_max``) whose axis span
    is within ``window`` — one group per subset, canonical
    ``(axis, position)`` order, set-deduplicated. This is enumeration, not
    counting: ``{2,3}`` yields the pairs AND the triples (the engine runs
    ranges as their minimum — audit A8).

    ``{n,}`` has no natural ceiling — the caller passes ``n_max=None`` and
    ``max_size`` bounds the enumeration explicitly (subsets grow as
    ``C(matches_in_window, n)``); exceeding it silently would be the
    silent-wrong class this project forbids, so it is a hard cap, not a
    default guess.
    """
    pl = _pl()
    if n_min < 1:
        raise ValueError("quantifier minimum must be >= 1")
    top = max_size if n_max is None else n_max
    if top > max_size:
        raise ValueError(f"quantifier upper bound {top} exceeds max_size={max_size}")
    if top < n_min:
        raise ValueError(f"quantifier range {{{n_min},{top}}} is empty")
    parts = []
    for n in range(n_min, top + 1):
        if n == 1:
            one = frame.drop_nulls([axis] + ([key] if key else [])).sort(
                [axis, "position"]
            )
            parts.append(_result(one, [("position", "id")], order=[axis, "position"]))
        else:
            parts.append(cooccur([frame] * n, axis=axis, window=window, key=key))
    # Renumber groups across sizes: smaller subsets first, then canonical order.
    out = []
    for i, part in enumerate(parts):
        out.append(
            part.with_columns((pl.col("group").cast(pl.Int64) + i * 10**12).alias("_g"))
        )
    merged = pl.concat(out).sort(["_g", "slot"])
    groups = merged.select("_g").unique(maintain_order=True).with_row_index("group")
    return (
        merged.drop("group")
        .join(groups, on="_g", how="inner")
        .select("group", "slot", "position", "id")
        .sort(["group", "slot"])
    )


def inequality(key: str) -> Any:
    """The ``!$k`` eligibility for ``nearest_link`` / ``extend_link`` /
    ``anti_link``: the candidate's ``key`` differs from the anchor's."""
    pl = _pl()
    return pl.col(f"r_{key}") != pl.col(f"l_{key}")


def body_span_filter(result: Any, corpus: Any, *, axis: str, span: int) -> Any:
    """Keep groups whose ``max(axis) - min(axis) <= span``; a group with a
    null axis value on any slot is rejected (not treated as span 0)."""
    pl = _pl()
    ax = corpus.select("position", pl.col(axis).alias("_ax"))
    spans = (
        result.join(ax, on="position", how="left")
        .group_by("group")
        .agg(
            (pl.col("_ax").max() - pl.col("_ax").min()).alias("_span"),
            pl.col("_ax").null_count().alias("_nulls"),
        )
        .filter((pl.col("_nulls") == 0) & (pl.col("_span") <= span))
        .select("group")
    )
    return result.join(spans, on="group", how="semi").sort(["group", "slot"])


def _link(
    pl: Any,
    left: Any,
    right: Any,
    l_ax: str,
    r_ax: str,
    window: int,
    forward: bool,
    key: str | None,
    eligible: Any | None,
) -> Any:
    if eligible is None:
        return _asof(pl, left, right, l_ax, r_ax, window, forward, key)
    return _candidates(pl, left, right, l_ax, r_ax, window, forward, key, eligible)


def _asof(
    pl: Any,
    left: Any,
    right: Any,
    l_ax: str,
    r_ax: str,
    window: int,
    forward: bool,
    key: str | None,
) -> Any:
    shift = 1 if forward else -1
    left = left.with_columns((pl.col(l_ax) + shift).alias("_k")).sort(
        ["_k", "l_position"]
    )
    # Ascending position within equal keys: forward asof takes the first
    # row (lowest position), backward takes the last (highest) — the
    # (axis, position) tie-break in both directions.
    right = right.with_columns(pl.col(r_ax).alias("_k")).sort(["_k", "r_position"])
    kw: dict[str, Any] = {
        "on": "_k",
        "strategy": "forward" if forward else "backward",
        "tolerance": window - 1,
    }
    if key:
        kw["by_left"] = f"l_{key}"
        kw["by_right"] = f"r_{key}"
        # Both sides are sorted by _k globally, hence within every by-group;
        # Polars cannot verify that with `by` and would only warn.
        kw["check_sortedness"] = False
    return left.join_asof(right, **kw).drop_nulls("r_id").drop("_k")


def _candidates(
    pl: Any,
    left: Any,
    right: Any,
    l_ax: str,
    r_ax: str,
    window: int,
    forward: bool,
    key: str | None,
    eligible: Any,
) -> Any:
    # Every rhs strictly within (l, l + window] lies in the lhs bucket or
    # the next one (backward: the previous one).
    left = left.with_row_index("_l_row")
    lb = pl.col(l_ax) // window
    offsets = [0, 1] if forward else [0, -1]
    left = pl.concat([left.with_columns((lb + d).alias("_b")) for d in offsets])
    right = right.with_columns((pl.col(r_ax) // window).alias("_b"))
    on = ["_b"] + ([f"l_{key}"] if key else [])
    right_on = ["_b"] + ([f"r_{key}"] if key else [])
    pairs = left.join(right, left_on=on, right_on=right_on, how="inner")
    dist = (pl.col(r_ax) - pl.col(l_ax)) if forward else (pl.col(l_ax) - pl.col(r_ax))
    pairs = pairs.filter((dist > 0) & (dist <= window) & eligible)
    # Nearest by axis distance, then by position (lowest forward, highest backward).
    pairs = pairs.with_columns(dist.alias("_dist")).sort(
        ["_l_row", "_dist", "r_position"], descending=[False, False, not forward]
    )
    return pairs.unique(subset=["_l_row"], keep="first", maintain_order=True).drop(
        ["_l_row", "_b", "_dist"]
    )


__all__ = [
    "RESULT_COLUMNS",
    "anti_link",
    "body_span_filter",
    "extend_link",
    "nearest_link",
]
