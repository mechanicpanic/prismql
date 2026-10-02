"""Who addresses whom: `@` and a name one of the corpus's authors has, the
longest that fits, marks a mention; `mentions_user(name)` finds them and
`mentions_user($y)` binds one mentioned name per group — the one whose
author answers first — so a later link can ask for that author's answer
(graph @aleph/prismql, #121, #138). It used to search the text "$y" and
answer empty."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError
from prismql.mentions import find_mentions, mention_pattern

DOCS = [
    {"id": 1, "agent": "ada", "text": "@bob can you check the build?"},
    {"id": 2, "agent": "bob", "text": "on it"},
    {"id": 3, "agent": "cy", "text": "unrelated, mail me at cy@bob.org"},
    {
        "id": 4,
        "agent": "GPT-5.4",
        "text": "@GPT-5 and @gpt-5.4, thoughts? Also @Claude Opus 4.5.",
    },
    {"id": 5, "agent": "GPT-5", "text": "sure"},
    {"id": 6, "agent": "Claude Opus 4.5", "text": "@ada @bob hello"},
]
BOTH = pytest.mark.parametrize("use_ir", [True, False])


def _engine(use_ir: bool = True, docs: list | None = None) -> PrismQLEngine:
    return PrismQLEngine(
        MemoryBackend([dict(d) for d in (docs or DOCS)]),
        use_ir=use_ir,
        actor_field="agent",
    )


def test_the_longest_known_name_after_an_at_sign():
    rx = mention_pattern(
        ["ada", "bob", "GPT-5", "GPT-5.4", "Claude Opus 4.5", "Claude Opus 4"]
    )
    assert find_mentions(
        "@GPT-5 and @gpt-5.4, thoughts? Also @Claude Opus 4.5.", rx
    ) == [
        "GPT-5",
        "GPT-5.4",
        "Claude Opus 4.5",
    ]
    assert find_mentions("mail me at cy@bob.org", rx) == []  # an address, not a mention
    assert find_mentions("@bobby is not @bob's twin", rx) == ["bob"]
    assert find_mentions("no one here", rx) == []


@BOTH
def test_mentions_user_by_name(use_ir):
    e = _engine(use_ir)
    assert e.execute("SELECT mentions_user(bob)") == [[1], [6]]
    assert e.execute('SELECT mentions_user("GPT-5")') == [[4]]
    assert e.execute("SELECT mentions_user(*)") == [[1], [4], [6]]


@BOTH
def test_a_mention_binds_the_name_it_addresses(use_ir):
    q = "SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) INWINDOW 3"
    # ada asks @bob, bob answers; GPT-5.4 asks @GPT-5 (among others), GPT-5 answers
    assert _engine(use_ir).execute(q) == [[1, 2], [4, 5]]


@BOTH
def test_any_of_several_mentions_can_answer(use_ir):
    q = (
        'SELECT field(agent, "GPT-5.4") AND mentions_user($y) '
        "FOLLOWED_BY field(agent, $y) INWINDOW 2"
    )
    assert _engine(use_ir).execute(q) == [[4, 5]]


@BOTH
def test_not_the_one_addressed(use_ir):
    # after 1 (@bob): bob is excluded, cy is next; after 4 every author in
    # reach (GPT-5, Claude Opus 4.5) was mentioned
    q = "SELECT mentions_user($y) FOLLOWED_BY field(agent, !$y) INWINDOW 2"
    assert _engine(use_ir).execute(q) == [[1, 3]]


@BOTH
def test_a_row_and_one_leg_hold_the_mention_too(use_ir):
    e = _engine(use_ir)
    # 4 addresses GPT-5 and Claude Opus 4.5: both answers are in reach
    assert e.execute("SELECT mentions_user($y), field(agent, $y) INWINDOW 3") == [
        [1, 2],
        [4, 5],
        [4, 6],
    ]
    self_docs = [
        {"id": 1, "agent": "ada", "text": "note to self @ada"},
        {"id": 2, "agent": "bob", "text": "@ada"},
    ]
    e = _engine(use_ir, self_docs)
    assert e.execute("SELECT field(agent, $a) AND mentions_user($a)") == [[1]]


def test_repeats_share_a_mentioned_name():
    e = _engine()
    # two messages close together addressing one person: 1 and 6 both @bob
    assert e.execute("SELECT mentions_user($y){2} INWINDOW 5") == [[1, 6]]
    assert e.execute("SELECT mentions_user($y) INWINDOW 5") == [[1], [4], [6]]
    # a range is the union of its sizes: every mention alone, plus the pair
    assert e.execute("SELECT mentions_user($y){1,2} INWINDOW 5") == [
        [1],
        [4],
        [6],
        [1, 6],
    ]


def test_an_ingested_mentions_column_is_the_answer():
    docs = [dict(d) for d in DOCS]
    docs[0]["mentions"] = ["cy"]  # the column says cy, whatever the text says
    for d in docs[1:]:
        d["mentions"] = []
    e = PrismQLEngine(
        MemoryBackend(docs), actor_field="agent", mentions_column="mentions"
    )
    assert e.execute("SELECT mentions_user(cy)") == [[1]]
    assert e.execute("SELECT mentions_user(bob)") == []


def test_ingest_writes_mentions_and_the_server_reads_them(tmp_path):
    pytest.importorskip("pyarrow")
    import polars as pl

    from prismql.ingest import normalize, write
    from prismql.ingest.annotate import annotate
    from prismql.server.config import ServerConfig, build_engine

    df = normalize(
        pl.DataFrame(
            {
                "i": [1, 2, 3],
                "t": [1, 2, 3],
                "agent": ["ada", "bob", "cy"],
                "text": ["@bob ping", "pong", "x@bob.org"],
            }
        ),
        id_col="i",
        time_col="t",
        keep=["agent", "text"],
    )
    df = annotate(df, ["mentions"], text=None, spacy_model="unused", actor="agent")
    assert df.get_column("mentions").to_list() == [["bob"], [], []]
    path = write(df, tmp_path / "m.parquet", annotations=["mentions"])
    engine = build_engine(ServerConfig(data=str(path), board_fields={"actor": "agent"}))
    q = "SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) INWINDOW 2"
    assert engine.execute(q) == [[1, 2]]


# --- one name per group (cold review): $y is the name a group settles on,
# not the whole list of names a message mentions


@BOTH
def test_a_chain_settles_on_one_addressed_name(use_ir):
    # 4 addresses GPT-5 and Claude Opus 4.5; 5 (GPT-5) answers first, so
    # $y is GPT-5 for the rest of the chain: Claude's 6 cannot be its third
    q = (
        "SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) "
        "FOLLOWED_BY field(agent, $y) INWINDOW 3"
    )
    assert _engine(use_ir).execute(q) == []


@BOTH
def test_a_row_shares_one_name_among_all_its_members(use_ir):
    e = _engine(use_ir)
    q = "SELECT mentions_user($y), field(agent, $y), field(agent, $y) INWINDOW 3"
    assert e.execute(q) == []  # 5 and 6 are two different addressees
    docs = [
        {"id": 1, "agent": "a", "text": "@x @y"},
        {"id": 2, "agent": "b", "text": "@x"},
        {"id": 3, "agent": "c", "text": "@y"},
        {"id": 4, "agent": "x", "text": "."},
        {"id": 5, "agent": "y", "text": "."},
    ]
    # 1, 2 and 3 share no single name (x is not in 3, y is not in 2)
    assert _engine(use_ir, docs).execute("SELECT mentions_user($y){3} INWINDOW 3") == []


@BOTH
def test_not_the_addressed_keeps_out_an_answer_with_no_author(use_ir):
    docs = [
        {"id": 1, "agent": "ada", "text": "@bob ?"},
        {"id": 2, "text": "system notice"},
        {"id": 3, "agent": "bob", "text": "hi"},
    ]
    q = "SELECT mentions_user($y) FOLLOWED_BY field(agent, !$y) INWINDOW 1"
    assert _engine(use_ir, docs).execute(q) == []  # as for any field: null is no value


def test_numeric_authors_are_names_too():
    docs = [
        {"id": 1, "agent": 7, "text": "@8 ping"},
        {"id": 2, "agent": 8, "text": "pong"},
    ]
    q = "SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) INWINDOW 2"
    assert _engine(True, docs).execute(q) == [[1, 2]]


def test_an_unstamped_mentions_field_is_the_users_own():
    docs = [dict(d) for d in DOCS]
    docs[0]["mentions"] = [101, 102]  # some other meaning of the word
    e = PrismQLEngine(MemoryBackend(docs), actor_field="agent")
    assert e.execute("SELECT mentions_user(bob)") == [[1], [6]]
    assert docs[0]["mentions"] == [101, 102]  # left as it was


def test_a_precomputed_index_answers_names_and_star_but_cannot_bind():
    from prismql.backends.base import PrecomputedIndexes

    e = PrismQLEngine(
        MemoryBackend([dict(d) for d in DOCS]),
        precomputed_indexes=PrecomputedIndexes(user_mentions={"bob": {1}}),
        actor_field="agent",
    )
    assert e.execute("SELECT mentions_user(bob)") == [[1]]
    assert e.execute("SELECT mentions_user(*)") == [[1]]
    with pytest.raises(PrismQLRuntimeError, match="user_mentions"):
        e.execute("SELECT mentions_user($y) FOLLOWED_BY field(agent, $y) INWINDOW 3")


def test_a_backend_that_cannot_hold_them_says_so():
    pytest.importorskip("tantivy")
    from prismql.backends.tantivy import TantivyBackend

    e = PrismQLEngine(TantivyBackend([dict(d) for d in DOCS]), actor_field="agent")
    with pytest.raises(PrismQLRuntimeError, match="--annotate mentions"):
        e.execute("SELECT mentions_user(bob)")


@BOTH
def test_a_quoted_from_is_always_a_name(use_ir):
    docs = [{"id": 1, "user": "*", "text": "x"}, {"id": 2, "user": "ada", "text": "y"}]
    e = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir)
    assert e.execute('SELECT from("*")') == [[1]]
    assert e.execute("SELECT from(*)") == [[1], [2]]


def test_quoted_from_lowers_alike_in_both_dialects():
    from prismql.dialects.pipe import parse_pipe

    e = _engine()
    assert parse_pipe('from("*")') == e.to_ir('SELECT from("*")')
