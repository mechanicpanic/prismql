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

from collections.abc import Mapping, Sequence
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
    carry: Sequence[str] = (),
) -> Any:
    """Extend every group of a result frame by one slot: the nearest ``rhs``
    strictly after the group's last slot (forward) / before its first slot
    (backward), within ``window`` on ``axis``.

    ``corpus`` supplies the anchor's axis/key columns by ``position``. A
    message already in the group is never eligible (distinctness across
    axes — the engine's A7 defect is fixed here by construction). ``key``
    is equality between the anchor and the new slot. Groups with no
    eligible candidate are dropped; the others keep their group number.

    ``carry`` names extra columns of ``seqs`` (constant within a group —
    bound pattern-variable values, ``_v_<var>``) that ride on the anchor
    as ``l_<name>`` so ``eligible`` can compare the candidate against them,
    and are copied onto the added slot so the schema stays whole.
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
            *[pl.col(c).first().alias(c) for c in carry],
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
        *[pl.col(f"l_{c}").alias(c) for c in carry],
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


def _distinct_member(pl: Any, i: int, ascending: bool | set[int]) -> Any:
    """Member ``i`` differs from every earlier member; for a quantified copy
    its position also ascends (combinations, not permutations)."""
    members = [pl.col(f"p{m}") for m in range(i)]
    distinct = pl.all_horizontal([pl.col(f"p{i}") != m for m in members])
    if ascending is True or (isinstance(ascending, set) and i in ascending):
        distinct = distinct & (pl.col(f"p{i}") > pl.col(f"p{i - 1}"))
    return distinct


def cooccur(
    frames: list[Any],
    *,
    axis: str,
    window: int,
    key: str | None = None,
    fields: Sequence[str] = (),
    eligible: Any | None = None,
    bindings: Mapping[str, tuple[int, str]] | None = None,
    ascending: bool | set[int] = False,
) -> Any:
    """Unordered co-occurrence (INWINDOW / DURING over a comma list): every
    combination of one row per frame whose members are pairwise distinct
    and whose axis span ``max - min <= window``; ``key`` requires equality
    across all members. Restriction order is irrelevant by definition
    (spec D2): each group is canonicalized by ``(axis, position)`` and
    deduplicated as a set, so ``cooccur([A, B]) == cooccur([B, A])``.

    Slots are ranks in that canonical order; groups are ordered by their
    canonical ``(axis, position)`` tuples.

    ``fields`` are projected per member as ``f<i>_<field>`` and ``eligible``
    is an expression over them, evaluated on every assignment *before*
    canonicalization and set-dedup — the second pattern variable of a
    comma list lives here (``f0_page == f1_page``), where a post-filter on
    the canonical group could not tell the slots apart.

    ``bindings`` maps a variable name to ``(member index, field)``: the
    value that member's field has in the assignment comes out as a
    ``_v_<var>`` column, constant within the group — read from the member
    that binds it, *before* canonicalization forgets which member was
    which. Two assignments with the same member set but different
    bindings are different groups.

    ``ascending`` is for copies of one frame (a quantifier): ``True`` admits
    only assignments whose positions increase slot by slot; a set of member
    indices ``i`` requires ``p_i > p_{i-1}`` for those members only (a
    quantified item inside a longer comma list). Combinations, not the
    ``k!`` permutations that would be enumerated and then deduplicated —
    that blow-up was an out-of-memory kill in CI.
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
        cols += [pl.col(f).alias(f"f{i}_{f}") for f in fields]
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
        distinct = _distinct_member(pl, i, ascending)
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
    if eligible is not None:
        g = g.filter(eligible)
    bind_cols = [f"_v_{v}" for v in (bindings or {})]
    g = g.with_columns(
        [pl.col(f"f{i}_{f}").alias(f"_v_{v}") for v, (i, f) in (bindings or {}).items()]
    ).drop(["_lo", "_hi"])
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
    if bind_cols:
        keyed = keyed.join(g.select("_row", *bind_cols), on="_row", how="left")
    # Group order = the canonical (axis, position) pairs compared slot by slot.
    order_cols: list[str] = []
    for i in range(k):
        keyed = keyed.with_columns(
            pl.col("_axs").list.get(i).alias(f"_oa{i}"),
            pl.col("_pos").list.get(i).alias(f"_op{i}"),
        )
        order_cols += [f"_oa{i}", f"_op{i}"]
    keyed = (
        keyed.unique(subset=["_pos", *bind_cols], keep="first")
        .sort(order_cols)
        .with_row_index("group")
    )
    return (
        long.join(keyed.select("_row", "group", *bind_cols), on="_row", how="inner")
        .select("group", "slot", "position", "id", *bind_cols)
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
            parts.append(
                cooccur([frame] * n, axis=axis, window=window, key=key, ascending=True)
            )
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


# ------------------------------------------------------------ group-level


def _group_bounds(result: Any, corpus: Any, axis: str, prefix: str) -> Any:
    """One row per group: first/last slot position and axis value, the
    member list, the slot count, and every carried ``_v_`` column."""
    pl = _pl()
    carry = [c for c in result.collect_schema().names() if c.startswith("_v_")]
    ax = corpus.select("position", pl.col(axis).alias("_ax"))
    rows = result.join(ax, on="position", how="left").sort(["group", "slot"])
    return (
        rows.group_by("group", maintain_order=True)
        .agg(
            pl.col("position").first().alias(f"{prefix}first_pos"),
            pl.col("position").last().alias(f"{prefix}last_pos"),
            pl.col("_ax").first().alias(f"{prefix}first_ax"),
            pl.col("_ax").last().alias(f"{prefix}last_ax"),
            pl.col("_ax").null_count().alias(f"{prefix}nulls"),
            pl.col("position").alias(f"{prefix}members"),
            pl.len().alias(f"{prefix}n"),
            *[pl.col(c).first().alias(f"{prefix}{c}") for c in carry],
        )
        .rename({"group": f"{prefix}group"})
    )


def _group_pairs(
    pl: Any,
    lb: Any,
    rb: Any,
    *,
    window: int,
    forward: bool,
    eligible: Any | None,
) -> Any:
    """Left groups x nearest eligible right groups (all right groups whose
    boundary is that nearest message), strictly ordered, within window,
    members disjoint. Forward: left.last -> right.first; backward:
    left.first <- right.last."""
    l_ax = "l_last_ax" if forward else "l_first_ax"
    r_ax = "r_first_ax" if forward else "r_last_ax"
    r_pos = "r_first_pos" if forward else "r_last_pos"
    w = max(window, 1)
    lb = lb.filter(pl.col(l_ax).is_not_null())
    rb = rb.filter(pl.col(r_ax).is_not_null())
    offsets = [0, 1] if forward else [0, -1]
    left = pl.concat(
        [lb.with_columns(((pl.col(l_ax) // w) + d).alias("_b")) for d in offsets]
    )
    right = rb.with_columns((pl.col(r_ax) // w).alias("_b"))
    pairs = left.join(right, on="_b", how="inner").drop("_b")
    dist = (pl.col(r_ax) - pl.col(l_ax)) if forward else (pl.col(l_ax) - pl.col(r_ax))
    disjoint = pl.col("l_members").list.set_intersection("r_members").list.len() == 0
    cond = (dist > 0) & (dist <= window) & disjoint
    if eligible is not None:
        cond = cond & eligible
    pairs = pairs.filter(cond).with_columns(dist.alias("_dist"))
    # The nearest boundary message per left group: min distance, then the
    # (axis, position) tie-break; every right group starting there expands.
    best = pairs.sort(
        ["l_group", "_dist", r_pos], descending=[False, False, not forward]
    )
    best = best.unique(subset=["l_group"], keep="first", maintain_order=True).select(
        "l_group", pl.col("_dist").alias("_best"), pl.col(r_pos).alias("_best_pos")
    )
    return (
        pairs.join(best, on="l_group", how="inner")
        .filter(
            (pl.col("_dist") == pl.col("_best"))
            & (pl.col(r_pos) == pl.col("_best_pos"))
        )
        .drop(["_dist", "_best", "_best_pos"])
    )


def _expand_pairs(pl: Any, pairs: Any, left: Any, right: Any, forward: bool) -> Any:
    """Matched (l_group, r_group) pairs -> a result frame: left slots then
    right slots (forward) or right then left (backward); new group numbers
    in the order of the pairs frame."""
    l_carry = [c for c in left.collect_schema().names() if c.startswith("_v_")]
    r_carry = [c for c in right.collect_schema().names() if c.startswith("_v_")]
    numbered = pairs.with_row_index("_new").collect().lazy()  # one numbering
    l_rows = left.rename({"group": "l_group"}).join(
        numbered.select("l_group", "r_group", "_new", "l_n", "r_n"),
        on="l_group",
        how="inner",
    )
    r_rows = (
        right.rename({"group": "r_group"})
        .drop([c for c in r_carry if c in l_carry])
        .join(
            numbered.select("l_group", "r_group", "_new", "l_n", "r_n"),
            on="r_group",
            how="inner",
        )
    )
    if forward:
        r_rows = r_rows.with_columns((pl.col("slot") + pl.col("l_n")).cast(pl.UInt32))
    else:
        l_rows = l_rows.with_columns((pl.col("slot") + pl.col("r_n")).cast(pl.UInt32))
    # Bindings: left's ride on every row; right's new ones are broadcast.
    cols = ["_new", "slot", "position", "id"]
    l_part = l_rows.select(*cols, *l_carry)
    r_only = [c for c in r_carry if c not in l_carry]
    if l_carry:
        r_rows = r_rows.join(
            l_rows.select("_new", *l_carry).unique(subset=["_new"]),
            on="_new",
            how="left",
        )
    r_part = r_rows.select(*cols, *l_carry, *r_only)
    if r_only:
        l_part = l_part.join(
            r_rows.select("_new", *r_only).unique(subset=["_new"]),
            on="_new",
            how="left",
        )
    out = pl.concat(
        [
            l_part.select(*cols, *l_carry, *r_only),
            r_part.select(*cols, *l_carry, *r_only),
        ]
    )
    return (
        out.rename({"_new": "group"})
        .with_columns(
            pl.col("group").cast(pl.UInt32), pl.col("position").cast(pl.Int64)
        )
        .sort(["group", "slot"])
    )


def link_groups(
    corpus: Any,
    left: Any,
    right: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    eligible: Any | None = None,
) -> Any:
    """``[A] FOLLOWED_BY [B]`` (forward) / ``PRECEDED_BY`` (backward) between
    whole groups: for each left group the nearest right group whose first
    slot (forward) / last slot (backward) lies strictly after / before the
    left group's last / first slot within ``window`` on ``axis``; every
    right group starting at that same nearest message expands; members
    must be disjoint; a group with a null axis value on its boundary
    cannot be placed and is dropped. The result concatenates the groups
    in axis order and carries both sides' bindings (``eligible`` may
    compare ``l__v_x`` with ``r__v_x``)."""
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    if window == 0:
        return _empty_result(left)
    lb = _group_bounds(left, corpus, axis, "l_")
    rb = _group_bounds(right, corpus, axis, "r_")
    pairs = _group_pairs(pl, lb, rb, window=window, forward=forward, eligible=eligible)
    # Left groups keep their own order (already by axis); among the right
    # groups that expand at one boundary, by their first slot's position,
    # then their group number.
    pairs = pairs.sort(["l_group", "r_first_pos", "r_group"])
    return _expand_pairs(pl, pairs, left, right, forward)


def anti_link_groups(
    corpus: Any,
    left: Any,
    right: Any,
    *,
    axis: str,
    window: int,
    forward: bool,
    eligible: Any | None = None,
) -> Any:
    """``[A] NOT_FOLLOWED_BY [B]`` / ``NOT_PRECEDED_BY``: the left groups with
    no eligible right group strictly after / before within ``window``
    (members disjoint). A left group with a null boundary axis value is
    dropped (graph #47); ``window == 0`` keeps every placeable left group."""
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    lb = _group_bounds(left, corpus, axis, "l_")
    bound_ax = "l_last_ax" if forward else "l_first_ax"
    keep = lb.filter(pl.col(bound_ax).is_not_null())
    if window > 0:
        rb = _group_bounds(right, corpus, axis, "r_")
        matched = _group_pairs(
            pl, lb, rb, window=window, forward=forward, eligible=eligible
        )
        keep = keep.join(matched.select("l_group").unique(), on="l_group", how="anti")
    order = ["l_last_ax", "l_last_pos"] if forward else ["l_first_ax", "l_first_pos"]
    keep = keep.sort(order).select("l_group").with_row_index("_new")
    return (
        left.rename({"group": "l_group"})
        .join(keep, on="l_group", how="inner")
        .drop("l_group")
        .rename({"_new": "group"})
        .with_columns(pl.col("group").cast(pl.UInt32))
        .sort(["group", "slot"])
    )


def cooccur_groups(
    corpus: Any,
    results: list[Any],
    *,
    axis: str,
    window: int,
) -> Any:
    """``[A] + [B] (+ ...) INWINDOW n``: one group from each stage, members
    pairwise disjoint, the union's axis span ``max - min <= window``;
    stages are unordered (any order, set-deduplicated by the member set).
    The result is the union in axis order; bindings of every stage ride
    along (a variable two stages both bind must agree)."""
    pl = _pl()
    if window < 0:
        raise ValueError(f"window must be >= 0, got {window}")
    if not results:
        raise ValueError("cooccur_groups needs at least one stage")
    k = len(results)
    bounds = [_group_bounds(r, corpus, axis, f"s{i}_") for i, r in enumerate(results)]
    bounds = [
        b.filter(pl.col(f"s{i}_nulls") == 0).select(
            pl.col(f"s{i}_group"),
            pl.col(f"s{i}_first_ax").alias(f"s{i}_lo"),
            pl.col(f"s{i}_last_ax").alias(f"s{i}_hi"),
            pl.col(f"s{i}_members"),
            *[
                pl.col(c)
                for c in b.collect_schema().names()
                if c.startswith(f"s{i}__v_")
            ],
        )
        for i, b in enumerate(bounds)
    ]
    g = bounds[0].with_columns(
        pl.col("s0_lo").alias("_lo"),
        pl.col("s0_hi").alias("_hi"),
        pl.col("s0_members").alias("_all"),
    )
    w = max(window, 1)
    for i in range(1, k):
        right = bounds[i].with_columns((pl.col(f"s{i}_lo") // w).alias("_b"))
        b_lo = (pl.col("_hi") - window) // w
        b_hi = (pl.col("_lo") + window) // w
        left = g.with_columns(pl.int_ranges(b_lo, b_hi + 1).alias("_b")).explode("_b")
        j = left.join(right, on="_b", how="inner").drop("_b")
        fits = (
            pl.max_horizontal("_hi", f"s{i}_hi") - pl.min_horizontal("_lo", f"s{i}_lo")
        ) <= window
        disjoint = pl.col("_all").list.set_intersection(f"s{i}_members").list.len() == 0
        cond = fits & disjoint
        # A variable both stages bind must agree.
        for c in j.collect_schema().names():
            if c.startswith(f"s{i}__v_"):
                var = c[len(f"s{i}__v_") :]
                for m in range(i):
                    if f"s{m}__v_{var}" in j.collect_schema().names():
                        cond = cond & (pl.col(c) == pl.col(f"s{m}__v_{var}"))
        g = j.filter(cond).with_columns(
            pl.min_horizontal("_lo", f"s{i}_lo").alias("_lo"),
            pl.max_horizontal("_hi", f"s{i}_hi").alias("_hi"),
            pl.col("_all").list.concat(f"s{i}_members").alias("_all"),
        )
    # Set-dedup by the member set; order by the sorted member positions.
    g = g.with_columns(pl.col("_all").list.sort().alias("_key")).unique(
        subset=["_key"], keep="first"
    )
    # Materialize before numbering: ``g`` is read once per stage below, and
    # a lazy unique() may order rows differently on each evaluation — the
    # numbering must be one fact, not one per read.
    g = g.with_row_index("_new").collect().lazy()
    # Expand: every stage's rows, renumbered; slots by (axis, position).
    parts = []
    for i, r in enumerate(results):
        parts.append(
            r.rename({"group": f"s{i}_group"})
            .join(g.select(f"s{i}_group", "_new"), on=f"s{i}_group", how="inner")
            .select("_new", "position", "id")
        )
    long = pl.concat(parts).join(
        corpus.select("position", pl.col(axis).alias("_ax")), on="position", how="left"
    )
    long = long.sort(["_new", "_ax", "position"]).with_columns(
        pl.int_range(pl.len()).over("_new").cast(pl.UInt32).alias("slot")
    )
    # Bindings: one value per variable per new group.
    bind_cols = sorted(
        {c.split("__v_", 1)[1] for c in g.collect_schema().names() if "__v_" in c}
    )
    binds = g.select("_new")
    for var in bind_cols:
        srcs = [c for c in g.collect_schema().names() if c.endswith(f"__v_{var}")]
        binds = binds.join(
            g.select("_new", pl.coalesce([pl.col(c) for c in srcs]).alias(f"_v_{var}")),
            on="_new",
            how="left",
        )
    # Group order: lexicographic over the canonical (axis, position) pairs —
    # the same rule as cooccur, so two unions sharing a first member still
    # order deterministically.
    keyed = long.group_by("_new", maintain_order=True).agg(
        pl.concat_str(
            [
                pl.col("_ax").cast(pl.Int64).cast(pl.Utf8).str.zfill(20),
                pl.col("position").cast(pl.Utf8).str.zfill(12),
            ],
            separator=":",
        )
        .str.join(",")
        .alias("_ord")
    )
    renum = keyed.sort("_ord").select("_new").with_row_index("group")
    return (
        long.join(renum, on="_new", how="inner")
        .join(binds, on="_new", how="left")
        .drop(["_new", "_ax"])
        .select("group", "slot", "position", "id", *[f"_v_{v}" for v in bind_cols])
        .with_columns(pl.col("position").cast(pl.Int64))
        .sort(["group", "slot"])
    )


__all__ = [
    "RESULT_COLUMNS",
    "anti_link",
    "anti_link_groups",
    "body_span_filter",
    "cooccur",
    "cooccur_groups",
    "extend_link",
    "inequality",
    "link_groups",
    "nearest_link",
    "quantify",
]
