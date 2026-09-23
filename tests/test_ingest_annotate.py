"""Annotation lives in the ingest layer, one function for every backend
(graph @aleph/prismql, #106)."""

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.ingest.annotate import indexes_from_columns, is_question, question_ids

DOCS = [
    {"id": 1, "text": "see https://example.org/page?id=7"},
    {"id": 2, "text": "can you check the page?"},
    {"id": 3, "text": "Why is it slow"},
    {"id": 4, "text": None},
    {"id": 5, "text": "done"},
]


def test_is_question():
    assert is_question("really?! ok") and is_question('asked "why?"')
    assert is_question("How does it work")
    assert not is_question("page?id=7 fixed") and not is_question("done")


def test_question_ids_over_text_fields():
    assert question_ids(DOCS, id_field="id", text_fields=["text"]) == {2, 3}


def test_columns_become_indexes():
    docs = [
        {"id": 1, "is_question": True, "entities": ["ORG", "GPE"]},
        {"id": 2, "is_question": False, "entities": []},
        {"id": 3, "is_question": True, "entities": ["ORG"]},
    ]
    idx = indexes_from_columns(docs, id_field="id", kinds=("questions", "entities"))
    assert idx is not None and idx.has_questions_index
    assert idx.questions == {1, 3}
    assert idx.entities == {"ORG": {1, 3}, "GPE": {1}}
    assert indexes_from_columns(docs, id_field="id", kinds=()) is None


@pytest.mark.parametrize("use_ir", [True, False])
def test_every_backend_answers_is_question_the_same(use_ir):
    tantivy = pytest.importorskip("tantivy")  # noqa: F841
    from prismql.backends.tantivy import TantivyBackend

    for backend in (MemoryBackend(DOCS), TantivyBackend(DOCS)):
        engine = PrismQLEngine(backend, use_ir=use_ir)
        assert engine.execute("SELECT is_question()") == [[2], [3]], type(backend)


def _ingest(tmp_path, *extra: str) -> str:
    from prismql.ingest.cli import run

    src = tmp_path / "in.jsonl"
    src.write_text(
        '{"k": 1, "when": "2026-01-01 00:00:00", "text": "why is it slow"}\n'
        '{"k": 2, "when": "2026-01-01 00:00:01", "text": "see a.org/p?id=7"}\n'
        '{"k": 3, "when": "2026-01-01 00:00:02", "text": "done?"}\n'
    )
    dst = tmp_path / "out.parquet"
    args = [
        "table",
        str(src),
        str(dst),
        "--id",
        "k",
        "--time",
        "when",
        "--keep",
        "text",
    ]
    assert run([*args, *extra]) == 0
    return str(dst)


def test_ingest_writes_the_question_column(tmp_path):
    import polars as pl

    out = pl.read_parquet(_ingest(tmp_path, "--annotate", "questions"))
    assert out.get_column("is_question").to_list() == [True, False, True]


def test_the_server_reads_the_column_as_the_index(tmp_path):
    import polars as pl
    import pyarrow.parquet as pq

    from prismql.server.config import ServerConfig, build_engine

    path = _ingest(tmp_path, "--annotate", "questions")
    # the column is authoritative: flip one row (keeping the ingest's stamp),
    # the engine must follow it
    meta = pq.read_schema(path).metadata
    df = pl.read_parquet(path).with_columns(
        pl.Series("is_question", [False, False, True])
    )
    pq.write_table(df.to_arrow().replace_schema_metadata(meta), path)
    engine = build_engine(ServerConfig(backend_type="memory", data=path))
    assert engine.execute("SELECT is_question()") == [[3]]


def test_an_unknown_annotation_is_refused(tmp_path, capsys):
    from prismql.ingest.cli import run

    src = tmp_path / "in.jsonl"
    src.write_text('{"k": 1, "when": "2026-01-01 00:00:00", "text": "x"}\n')
    rc = run(["table", str(src), str(tmp_path / "o.parquet"), "--id", "k",
              "--time", "when", "--annotate", "moods"])  # fmt: skip
    assert rc == 2 and "moods" in capsys.readouterr().err


# --- cold review round 1 (graph #106) ---------------------------------------


def test_a_field_named_like_an_annotation_is_not_one(tmp_path):
    """Only an ingest-stamped file's columns are annotations: a CSV with an
    ordinary 'is_question' of strings, or an 'entities' string, stays a field."""
    from prismql.server.config import ServerConfig, build_engine

    csv = tmp_path / "c.csv"
    csv.write_text(
        "id,timestamp,text,is_question,entities\n"
        "1,1,why is it slow,False,ORG\n2,2,done,True,ORG\n3,3,ok,False,ORG\n"
    )
    engine = build_engine(ServerConfig(backend_type="memory", data=str(csv)))
    # the rule answers, not the strings: only row 1 is a question
    assert engine.execute("SELECT is_question()") == [[1]]
    with pytest.raises(Exception, match="entity"):
        engine.execute("SELECT mentions_org()")


def test_only_true_counts_and_sparse_rows_do_not_hide_the_column():
    docs = [
        {"id": 1, "text": "x"},  # no key on the first row
        {"id": 2, "is_question": True, "entities": ["ORG"]},
        {"id": 3, "is_question": "True"},  # not a bool: not a question
    ]
    idx = indexes_from_columns(docs, id_field="id", kinds=("questions", "entities"))
    assert idx.questions == {2} and idx.entities == {"ORG": {2}}


def test_every_backend_reads_the_same_text_fields():
    pytest.importorskip("tantivy")
    from prismql.backends.tantivy import TantivyBackend

    docs = [{"id": 1, "text": "fine", "content": "is it broken?"}]
    for backend in (
        MemoryBackend(docs),
        TantivyBackend(docs, text_fields=["text"]),
    ):
        assert PrismQLEngine(backend).execute("SELECT is_question()") == [[1]]


def test_an_absent_label_still_refuses_and_names_what_exists():
    """A label no event carries may be one the annotator never assigns (spaCy
    has no URL label): an empty answer would be silent-wrong, so it refuses."""
    from prismql.backends.base import PrecomputedIndexes
    from prismql.exceptions import PrismQLRuntimeError

    engine = PrismQLEngine(
        MemoryBackend([{"id": 1, "text": "Paris"}]),
        precomputed_indexes=PrecomputedIndexes(entities={"GPE": {1}}),
    )
    with pytest.raises(PrismQLRuntimeError, match="GPE"):
        engine.execute("SELECT mentions_org()")


def test_ingest_stamps_what_it_annotated(tmp_path):
    import pyarrow.parquet as pq

    path = _ingest(tmp_path, "--annotate", "questions")
    meta = pq.read_schema(path).metadata or {}
    assert meta.get(b"prismql.annotations") == b"questions"


def test_entities_are_written_by_the_spacy_annotator(tmp_path, monkeypatch):
    import sys
    import types

    import polars as pl

    class _Ent:
        def __init__(self, label: str) -> None:
            self.label_ = label

    class _Nlp:
        def pipe(self, texts: object, batch_size: int = 0) -> object:  # noqa: ARG002
            for t in texts:
                yield types.SimpleNamespace(ents=[_Ent("ORG")] if "slow" in t else [])

    fake = types.SimpleNamespace(load=lambda _model, disable=(): _Nlp())  # noqa: ARG005
    monkeypatch.setitem(sys.modules, "spacy", fake)
    out = pl.read_parquet(_ingest(tmp_path, "--annotate", "entities"))
    assert out.get_column("entities").to_list() == [["ORG"], [], []]
