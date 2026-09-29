# PrismQL in one sitting — the mental model

Not a reference. The references (`LANGUAGE_REFERENCE.md`, `PIPE_REFERENCE.md`)
list everything; this page is what to hold in your head so you never need
to look most of it up. Read once, then do the self-test at the end.
Have a file of events and no PrismQL yet? Start with `USER-GUIDE.md` —
install, config, first query — and come back here.

## 1. The one idea

A query names a **shape in an ordered stream** and returns every **instance**
of that shape — the events themselves, grouped, never a summary.

The stream is ordered twice: by **position** (load order; ids are labels,
never coordinates) and by **time** (a timestamp field). Every distance in the
language is measured on one of those two axes, and you always say which:

| you write | axis | unit |
|---|---|---|
| `INWINDOW 5` · `\|> within(5)` | position | events |
| `DURING 10 minutes` · `\|> during(10m)` | time | wall clock |

That is the whole difference between the two. Positional windows survive
missing or coarse timestamps; temporal windows survive bursts.

## 2. Three levels, one algebra

Everything is built from three kinds of value, and the operators are the
moves between them.

```
predicate  ──►  set of events  ──►  groups of events  ──►  answer
 from(a)         {ids}               [[id, id, …], …]      list / count / named
```

1. **A predicate names a set.** `from(a)`, `field(kind, delete)`,
   `contains(dict)`, `is_question()`, `similar_to("…", 0.7)`. Booleans stay on
   sets: `AND` · `OR` · `NOT` (`and` · `or` · `not` in pipe). No ranking, no
   scores: a set in, a set out.
2. **A window operator turns sets into groups.** Two ways, and this is the
   fork that matters:

   | | unordered | ordered |
   |---|---|---|
   | classic | `A, B INWINDOW n` | `A FOLLOWED_BY B INWINDOW n` |
   | pipe | `A + B \|> within(n)` | `A ~> B \|> within(n)` |
   | meaning | one A and one B within n of each other, either order; `A, B` ≡ `B, A` | B strictly after A; the **nearest** eligible B per A |
   | reverse | — | `PRECEDED_BY` · `<~` |
   | negation | — | `NOT_FOLLOWED_BY` · `!~>` (lhs events with no such B; the B is not in the group) |

   A comma list can have any number of members (`A, B, C INWINDOW n` — all
   pairwise within n, all distinct). A chain can have any number of legs
   (`A FOLLOWED_BY B FOLLOWED_BY C …`): each link is greedy-nearest from the
   previous slot, the group is the whole chain.
3. **The tail shapes the answer.** `AS "name"` labels a slot; `AGGREGATE
   count()` / `|> count()` counts groups (the only way to a total the server
   will not cap); `GROUP BY user` / `|> group(user)`; `BEFORE / AFTER /
   BETWEEN`; `ORDER BY`, `LIMIT`. Booleans do **not** apply to groups — an
   `AND` between two chains is an error, by design.

Once you see the three levels, the syntax rules follow: booleans bind
tighter than windows (`from(a) AND is_question() FOLLOWED_BY from(b)` needs
no parentheses); the **last link of a chain must carry a window**, and one
trailing window distributes to every windowless link; links may mix axes
(`A FOLLOWED_BY B INWINDOW 20 FOLLOWED_BY C DURING 10 minutes`); quantifiers
live on a set, not inside a chain.

## 3. Variables — the same entity again

`$k` inside a predicate argument means "bind here, hold equal there":

```
from($u) AND is_question() FOLLOWED_BY from($u) AND contains(thanks) INWINDOW 5
```
"a user asks, and *that same user* thanks within 5." Bind on the first leg
that names it; every later leg naming `$u` must match. Several variables run
side by side (`field(page,$p) AND from($u)`). `!$u` is "a *different* one"
(both dialects; the validator rejects it when nothing bound `$u` earlier).

Two rules that keep variables honest: the equality is decided **while
choosing the nearest candidate**, not after (otherwise a stranger in between
would drop the group — audit A10, fixed in the plan layer); and on the
excluded side of a negation a variable binds nothing, because that event is
not in the group — it only narrows what counts as excluded to events
agreeing with the left side.

## 4. Quantifiers — enumeration, not counting

`from(a){3}` = every set of three distinct a-events within the window, one
group per set. `{2,4}` = the pairs *and* the triples *and* the quadruples.
`{n,}` has no ceiling to enumerate to, so it needs one: `quantifier_ceiling`
in the config, or write `{n,m}`. (Until P3 the engine runs ranges as their
minimum — A8.)

## 4a. Runs — repeats in a row, counted once

`RUN(from($u)){3,} DURING 5 minutes` = one group per maximal run: $u's
events, each within five minutes of the previous one, three or more. Runs
never overlap and other events between them do not break them. Where a
quantifier over 20 repeats gives every combination (77,520 groups for
`{7}`) and a chain gives one overlapping group per starting event, a run
gives one. The first window is the step, a second `DURING` bounds the whole
run. In a link the step goes inside, `RUN(X, DURING 5 minutes){3,}`, and a
run stands on either side of one arrow: "a request, then a run of retries".

## 5. Subqueries — groups of groups

Brackets make a stage that keeps its own window and its own grouping; the
outer operator then works on **whole groups**:

```
[from(customer) + contains(problem) |> within(3)] ~>(10) [from(support) + contains(fix) |> within(3)]
(SELECT from(customer), contains(problem) INWINDOW 3) FOLLOWED_BY (SELECT from(support), contains(fix) INWINDOW 3) INWINDOW 10
```
"a customer-problem cluster, then within 10 events a support-fix cluster";
the answer is `[c, p, s, f]`, cluster boundaries kept. Between stages the
arrow carries its own inline window; `+` / `;` between stages is unordered.
Do not flatten: `a + b + c |> within(8)` is a different question from
`[a + b |> within(3)] + [c] |> within(8)`.

## 6. Why not SQL (in one breath)

SQL has no *nearest*, no *sequence*, no *group-as-value*: a three-leg chain
is two `LATERAL` subqueries, a variable is a join predicate you must place
correctly, `!$u` is a second query, `NOT_FOLLOWED_BY` is an anti-join rewrite,
"unordered pair" needs two extra predicates to undo the symmetry SQL does not
know about, and every result is one row per chain with timestamps instead of
the events. Each of those is one token here. (Zhu, Huang & Chaudhuri, PVLDB
16(5) 2023, reached the same place from the other side: pattern queries over
history are joins; PrismQL just never bolts an automaton on afterwards.)

## 7. What holds, and where the guarantees end

Since the operator layer (P3, 2026-09-22) the engine *is* the plan: stream
order = load order; `INWINDOW` unordered; slots in axis order; equalities
inside selection; ranges enumerated; strict `>` on time, ties broken by
position. The old audit defects A1–A10 and D2 stand as ordinary contract
tests, not as caveats.

What a query still cannot do: run sequence operators on a backend without
an order axis (a tantivy index built before the axis sidecar — a loud
`PositionalUnsupportedError`, not a wrong answer); enumerate `{n,}` without
a ceiling; name a variable on the excluded side of a negation that the
left side does not bind; carry a
variable across subquery stages. When the engine and `tests/plan` disagree,
the tests win — and that disagreement is a bug to pin, not a caveat to
learn.

## 8. Twelve shapes to recognise on sight

| shape | classic | pipe |
|---|---|---|
| filter | `SELECT from(a) AND is_question()` | `from(a) and is_question()` |
| near each other | `SELECT from(a), from(b) INWINDOW 5` | `from(a) + from(b) \|> within(5)` |
| three near | `SELECT A, B, C DURING 1 hour` | `A + B + C \|> during(1h)` |
| then | `SELECT A FOLLOWED_BY B INWINDOW 5` | `A ~> B \|> within(5)` |
| then, then | `SELECT A FOLLOWED_BY B FOLLOWED_BY C DURING 10 minutes` | `A ~> B ~> C \|> during(10m)` |
| mixed axes | `SELECT A FOLLOWED_BY B INWINDOW 20 FOLLOWED_BY C DURING 10 minutes` | `A ~>(20) B ~>(10m) C` |
| before | `SELECT B PRECEDED_BY A INWINDOW 3` | `B <~ A \|> within(3)` |
| never followed | `SELECT A NOT_FOLLOWED_BY B DURING 1 day` | `A !~> B \|> during(1d)` |
| same entity | `SELECT from($u) FOLLOWED_BY from($u) INWINDOW 5` | `from($u) ~> from($u) \|> within(5)` |
| repeated | `SELECT from(a){3} INWINDOW 10` | `from(a){3} \|> within(10)` |
| staged | `SELECT (SELECT A, B INWINDOW 3) FOLLOWED_BY (SELECT C) INWINDOW 8` | `[A + B \|> within(3)] ~>(8) [C]` |
| how many | `SELECT A FOLLOWED_BY B INWINDOW 5 AGGREGATE count()` | `A ~> B \|> within(5) \|> count()` |

## 9. Self-test (answers at the bottom)

1. `from(b), from(a) INWINDOW 3` and `from(a), from(b) INWINDOW 3` — same answer?
2. Why does `SELECT A FOLLOWED_BY B INWINDOW 2 FOLLOWED_BY C` fail?
3. What does `A ~>(20) B ~>(10m) C` measure on each link?
4. `from($u) NOT_FOLLOWED_BY from($u) INWINDOW 5` — allowed?
5. `from(a){2,} INWINDOW 5` with no ceiling configured — what happens?
6. Two A's, one B between them within the window: how many groups does `A FOLLOWED_BY B INWINDOW 5` return, and can they share the B?
7. `SELECT A, B INWINDOW 5 AND C` — valid?
8. You want the total number of matches from the server, not the first 50. What do you append?
9. Given `[a + b |> within(3)] ~>(8) [c]`, what is in one result group?
10. Timestamps are unreliable for a week of the log. Which window do you use, and why?

<details><summary>Answers</summary>

1. Yes, by definition: comma lists are unordered. (The engine at HEAD says
   no — D2 — which is why it is being replaced.)
2. The final link has no window. Put `INWINDOW n` / `DURING t` at the end;
   it distributes to every windowless link.
3. A→B: at most 20 events apart (position); B→C: at most 10 minutes (time).
4. Yes: `$u` on the excluded side binds nothing, it narrows the excluded
   event to one by the same author — "a message its author did not follow
   up within five". A `$v` the left side does not bind is an error.
5. Rejected with `OPEN_QUANTIFIER`; write `{2,m}` or set
   `quantifier_ceiling`.
6. Two groups, one per A; yes, both may pair with the same B — each A takes
   its own nearest B, the B is not consumed.
7. No: booleans work on sets, `A, B INWINDOW 5` is already groups.
8. `AGGREGATE count()` / `|> count()`; the group cap is `max_results`.
9. `[a, b, c]` — the a–b cluster kept whole, then c within 8 events of the
   cluster's last member.
10. `INWINDOW`: positions come from load order and need no clock; `DURING`
    would silently drop groups with unparseable timestamps.

</details>
