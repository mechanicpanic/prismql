"""contains_link() answers from one link rule — the tokenizer's URL shape —
annotated at ingest (`--annotate links`, column `has_link`) or once at load,
like is_question() (graph @aleph/prismql, #115). It used to look up a URL
entity label no tagger in the package sets, so it always refused."""

import polars as pl
import pytest

from prismql.backends.base import PrecomputedIndexes
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError
from prismql.ingest.annotate import has_link

DOCS = [
    {"id": 1, "user": "a", "text": "see https://example.org/a?b=1 please"},
    {"id": 2, "user": "a", "text": "no link here, just http talk"},
    {"id": 3, "user": "b", "text": "www.example.com is not a URL token"},
    {"id": 4, "user": "b", "content": "HTTP://SHOUTING.example/x"},
]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("see https://example.org/a?b=1", True),
        ("http://x", True),
        ("HTTP://SHOUTING.example/x", True),
        ("just http talk", False),
        ("www.example.com", False),
        ("", False),
    ],
)
def test_the_link_rule_is_the_tokenizers_url_shape(text, expected):
    assert has_link(text) is expected


@pytest.mark.parametrize("use_ir", [True, False])
def test_an_unannotated_corpus_is_annotated_once(use_ir):
    engine = PrismQLEngine(MemoryBackend(documents=DOCS), use_ir=use_ir)
    assert engine.execute("SELECT contains_link()") == [[1], [4]]


def test_a_computed_empty_links_index_is_authoritative():
    engine = PrismQLEngine(
        MemoryBackend(documents=DOCS),
        precomputed_indexes=PrecomputedIndexes(links=set()),
    )
    assert engine.execute("SELECT contains_link()") == []


def test_an_extractors_url_entities_still_answer():
    engine = PrismQLEngine(
        MemoryBackend(documents=DOCS),
        precomputed_indexes=PrecomputedIndexes(entities={"URL": {3}}),
    )
    assert engine.execute("SELECT contains_link()") == [[3]]


def test_a_text_index_without_documents_says_how_to_annotate():
    pytest.importorskip("tantivy")
    from prismql.backends.tantivy import TantivyBackend

    engine = PrismQLEngine(TantivyBackend(DOCS, store_documents=False))
    with pytest.raises(PrismQLRuntimeError, match="--annotate links"):
        engine.execute("SELECT contains_link()")


def test_ingest_writes_has_link_and_the_server_reads_the_column(tmp_path):
    pytest.importorskip("pyarrow")
    from prismql.ingest import normalize, write
    from prismql.ingest.annotate import annotate
    from prismql.server.config import ServerConfig, build_engine

    df = normalize(
        pl.DataFrame(
            {"i": [1, 2], "t": [1, 2], "text": ["https://a.example", "plain"]}
        ),
        id_col="i",
        time_col="t",
    )
    df = annotate(df, ["links"], text=None, spacy_model="unused")
    assert df.get_column("has_link").to_list() == [True, False]
    # the column is the answer, not a re-read of the text
    df = df.with_columns(pl.Series("has_link", [False, True]))
    path = write(df, tmp_path / "l.parquet", annotations=["links"])
    engine = build_engine(ServerConfig(data=str(path)))
    assert engine.execute("SELECT contains_link()") == [[2]]
