"""The worked examples the agent-facing docs teach must be what the engine does.

Three traps the benchmark agents fell into, each taught with a tiny stream in
the skill and both references: ``count()`` over ``FOLLOWED_BY`` counts match
groups (not entities), ``DURING`` needs a strictly later time while ``INWINDOW``
reads stream position, and the text predicates read only the text fields. Each
test runs the example on both dialects and checks the doc carries the same query
text, so neither the prose nor the behaviour can drift alone.
"""

import warnings
from pathlib import Path

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.config import BackendConfig
from prismql.exceptions import PrismQLRuntimeError

ROOT = Path(__file__).resolve().parents[1]
CLASSIC = (ROOT / "LANGUAGE_REFERENCE.md").read_text()
PIPE = (ROOT / "PIPE_REFERENCE.md").read_text()
SKILL = (ROOT / "skills/prismql/SKILL.md").read_text()
AGENT_USE = (ROOT / "docs/AGENT-USE.md").read_text()
DOCS = pytest.mark.parametrize(
    "doc", [CLASSIC, PIPE, SKILL], ids=["classic", "pipe", "skill"]
)


def flat(doc):
    """The doc with line wraps and code ticks and bold gone, for phrase matching."""
    return " ".join(doc.replace("`", "").replace("**", "").split())


def engine(docs: list[dict], **kw: object) -> PrismQLEngine:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # non-monotone timestamps are on purpose
        return PrismQLEngine(search_backend=MemoryBackend(docs, id_field="id"), **kw)


def value(result):
    return result.to_dict()


# --- count() counts groups --------------------------------------------------

PAGES = [
    {"id": 1, "kind": "delete", "page": "P", "timestamp": 1},
    {"id": 2, "kind": "delete", "page": "P", "timestamp": 2},
    {"id": 3, "kind": "save", "page": "P", "timestamp": 3},
    {"id": 4, "kind": "delete", "page": "Q", "timestamp": 4},
    {"id": 5, "kind": "save", "page": "Q", "timestamp": 5},
]
Q1 = (
    "SELECT field(kind, delete) AND field(page, $p) FOLLOWED_BY "
    "field(kind, save) AND field(page, $p) INWINDOW 10"
)
P1 = (
    "field(kind, delete) and field(page, $p) ~> "
    "field(kind, save) and field(page, $p) |> within(10)"
)


def test_followed_by_count_is_per_start_event_on_both_dialects():
    e = engine(PAGES)
    assert e.execute(Q1) == [[1, 3], [2, 3], [4, 5]] == e.execute(P1)
    assert value(e.execute(Q1 + " AGGREGATE count()"))["value"] == 3
    assert value(e.execute(P1 + " |> count()"))["value"] == 3


def test_count_distinct_group_by_and_flip_answer_the_other_questions():
    e = engine(PAGES)
    assert value(e.execute(Q1 + " AGGREGATE count(DISTINCT page)"))["value"] == 2
    assert value(e.execute(P1 + " |> count_distinct(page)"))["value"] == 2
    per_page = {"P": 2, "Q": 1}
    assert (
        value(e.execute(Q1 + " GROUP BY page AGGREGATE count()"))["grouped_values"]
        == per_page
    )
    assert (
        value(e.execute(P1 + " |> group(page) |> count()"))["grouped_values"]
        == per_page
    )
    flipped = "SELECT field(kind, save) PRECEDED_BY field(kind, delete) INWINDOW 10"
    assert e.execute(flipped) == [[2, 3], [4, 5]]
    pipe_flipped = "field(kind, save) <~ field(kind, delete) |> within(10)"
    assert e.execute(pipe_flipped) == [[2, 3], [4, 5]]


def test_count_distinct_reads_every_leg_group_by_reads_the_first():
    people = [
        {"id": 1, "kind": "ask", "user": "ann", "timestamp": 1},
        {"id": 2, "kind": "answer", "user": "bob", "timestamp": 2},
    ]
    e = engine(people)
    q = "SELECT field(kind, ask) FOLLOWED_BY field(kind, answer) INWINDOW 5"
    assert value(e.execute(q + " AGGREGATE count(DISTINCT user)"))["value"] == 2
    assert value(e.execute(q + " GROUP BY user AGGREGATE count()"))[
        "grouped_values"
    ] == {"ann": 1}


@DOCS
def test_count_examples_are_in_the_docs(doc):
    assert "[1, 3] [2, 3] [4, 5]" in flat(doc)
    assert "match groups" in flat(doc) or "result groups" in flat(doc)


@pytest.mark.parametrize(
    "needle, doc",
    [
        (Q1 + " AGGREGATE count(DISTINCT page)", CLASSIC),
        (Q1 + " GROUP BY page AGGREGATE count()", CLASSIC),
        (P1 + " |> count_distinct(page)", PIPE),
        (P1 + " |> group(page) |> count()", PIPE),
    ],
)
def test_the_queries_the_docs_print_are_the_ones_tested(needle, doc):
    assert needle in doc


# --- DURING is strictly later, INWINDOW is position -------------------------

TIES = [
    {"id": 1, "user": "alice", "timestamp": 100},
    {"id": 2, "user": "bob", "timestamp": 100},
    {"id": 3, "user": "bob", "timestamp": 101},
]


def test_equal_timestamp_is_not_later_on_a_during_link():
    e = engine(TIES)
    assert e.execute("SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 1") == [[1, 2]]
    assert e.execute("from(alice) ~> from(bob) |> within(1)") == [[1, 2]]
    during = "SELECT from(alice) FOLLOWED_BY from(bob) DURING 10 seconds"
    assert e.execute(during) == [[1, 3]]
    assert e.execute("from(alice) ~> from(bob) |> during(10s)") == [[1, 3]]


def test_a_comma_row_during_is_a_span_so_equal_times_pass():
    e = engine(TIES)
    expected = [[1, 2], [1, 3]]
    assert e.execute("SELECT from(alice), from(bob) DURING 10 seconds") == expected
    assert e.execute("from(alice) + from(bob) |> during(10s)") == expected


def test_a_zero_second_sequential_link_matches_nothing():
    e = engine(TIES)
    assert e.execute("SELECT from(alice) FOLLOWED_BY from(bob) DURING 0 seconds") == []
    assert e.execute("from(alice) ~> from(bob) |> during(0s)") == []


def test_ties_go_to_the_nearest_in_the_stream_each_way():
    forward = engine(
        [
            {"id": 1, "user": "alice", "timestamp": 100},
            {"id": 2, "user": "bob", "timestamp": 105},
            {"id": 3, "user": "bob", "timestamp": 105},
        ]
    )
    assert forward.execute(
        "SELECT from(alice) FOLLOWED_BY from(bob) DURING 10 seconds"
    ) == [[1, 2]]
    assert forward.execute("from(alice) ~> from(bob) |> during(10s)") == [[1, 2]]
    backward = engine(
        [
            {"id": 1, "user": "alice", "timestamp": 100},
            {"id": 2, "user": "alice", "timestamp": 100},
            {"id": 3, "user": "bob", "timestamp": 105},
        ]
    )
    assert backward.execute(
        "SELECT from(bob) PRECEDED_BY from(alice) DURING 10 seconds"
    ) == [[2, 3]]
    assert backward.execute("from(bob) <~ from(alice) |> during(10s)") == [[2, 3]]


@DOCS
def test_the_tie_examples_are_in_the_docs(doc):
    text = flat(doc)
    assert "1 alice 100, 2 bob 100, 3 bob 101" in text
    assert "[1, 3]" in text and "[1, 2]" in text


# --- text predicates read the text fields only ------------------------------

NOTES = [
    {"id": 1, "user": "a", "text": "the deploy failed", "body": "hit a timeout"},
    {"id": 2, "user": "b", "text": "ok", "body": "retrying after a timeout"},
    {"id": 3, "user": "a", "text": "a timeout again"},
]
TIMEOUTS = {"timeouts": ["timeout"]}


def test_a_body_column_is_not_searched_by_default():
    e = engine(NOTES, user_dictionaries=TIMEOUTS)
    assert e.execute("SELECT contains(timeouts)") == [[3]]
    assert e.execute('SELECT contains_phrase("timeout")') == [[3]]
    assert e.execute('SELECT field(body, "retrying after a timeout")') == [[2]]
    assert e.execute("contains(timeouts)") == [[3]]


def test_text_fields_names_the_columns_the_text_predicates_read():
    cfg = BackendConfig(text_fields=["text", "body"])
    backend = MemoryBackend(NOTES, id_field="id", config=cfg)
    e = PrismQLEngine(search_backend=backend, user_dictionaries=TIMEOUTS)
    assert e.execute("SELECT contains(timeouts)") == [[1], [2], [3]]


def test_contains_with_a_bare_word_is_an_error_not_a_search():
    e = engine(NOTES, user_dictionaries=TIMEOUTS)
    with pytest.raises(PrismQLRuntimeError, match="Dictionary 'timeout' not found"):
        e.execute("SELECT contains(timeout)")


@DOCS
def test_the_text_field_scope_is_stated(doc):
    assert "text, content" in flat(doc) and "message" in flat(doc)
    assert "not every column" in flat(doc) or "no other column" in flat(doc)


def test_the_agent_use_doc_states_both_traps():
    text = flat(AGENT_USE)
    assert "text, content or message" in text
    assert "count(DISTINCT page)" in text and "match groups" in text


@pytest.mark.parametrize(
    "doc", [CLASSIC, PIPE, SKILL, AGENT_USE], ids=["classic", "pipe", "skill", "use"]
)
def test_the_docs_say_a_text_predicate_refuses_without_its_fields(doc):
    """With none of the fields it reads, a text predicate refuses (graph
    @aleph/prismql, #168); the docs must not promise silence or a setting."""
    text = flat(doc)
    assert "refuse" in text.lower()
    assert "unless your version" not in text
    assert "no setting for" not in text
    assert "returns nothing, silently" not in text
