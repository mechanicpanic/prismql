"""Asymmetric embedders (embeddinggemma, Qwen3) encode a query and a document
with different prompts. The ingest stamps both prompts beside the model, and
the server encodes query text with the stamped query prompt — a query encoded
as a document silently ranks worse (graph @aleph/prismql, #96)."""

import polars as pl
import pytest

from prismql.ingest import normalize, write

pytest.importorskip("pyarrow")


class Fake:
    """Records the prompt it was built with; the vector says which prompt."""

    built: list[str | None] = []

    def __init__(self, _name: str, prompt: str | None = None) -> None:
        self.prompt = prompt
        Fake.built.append(prompt)

    def encode(self, texts: list[str]) -> list[list[float]]:
        # a prompted encoder points elsewhere: the query must match the docs
        return [[1.0, 0.0] if self.prompt else [0.0, 1.0] for _ in texts]


@pytest.fixture
def fake(monkeypatch):
    from prismql.backends import semantic as semantic_module

    Fake.built = []
    monkeypatch.setattr(semantic_module, "SentenceTransformerEmbedder", Fake)
    return Fake


def _stream() -> pl.DataFrame:
    return normalize(
        pl.DataFrame({"i": [1, 2], "t": [1, 2], "text": ["oil", "gas"]}),
        id_col="i",
        time_col="t",
    )


def test_ingest_encodes_documents_with_the_doc_prompt_and_stamps_both(tmp_path, fake):
    from prismql.ingest.core import embed
    from prismql.server.config import load_corpus

    df = embed(_stream(), text="text", model="m", prompt="title: none | text: ")
    assert fake.built == ["title: none | text: "]
    path = write(
        df,
        tmp_path / "e.parquet",
        embed_model="m",
        embed_doc_prompt="title: none | text: ",
        embed_query_prompt="task: search result | query: ",
    )
    _, _, stamp = load_corpus(path)
    assert stamp is not None
    assert stamp.model == "m" and stamp.text == "text"
    assert stamp.doc_prompt == "title: none | text: "
    assert stamp.query_prompt == "task: search result | query: "


def test_server_encodes_the_query_with_the_stamped_query_prompt(tmp_path, fake):
    from prismql.ingest.core import embed
    from prismql.server.config import ServerConfig, build_engine

    df = embed(_stream(), text="text", model="m", prompt="doc: ")
    path = write(
        df,
        tmp_path / "e.parquet",
        embed_model="m",
        embed_doc_prompt="doc: ",
        embed_query_prompt="query: ",
    )
    engine = build_engine(ServerConfig(data=str(path)))
    assert fake.built[-1] == "query: "
    assert engine.execute('SELECT similar_to("anything", 0.9)') == [[1], [2]]


def test_an_unprompted_stamp_keeps_the_plain_encoder(tmp_path, fake):
    from prismql.ingest.core import embed
    from prismql.server.config import ServerConfig, build_engine

    path = write(
        embed(_stream(), text="text", model="m"),
        tmp_path / "e.parquet",
        embed_model="m",
    )
    engine = build_engine(ServerConfig(data=str(path)))
    assert fake.built == [None, None]
    assert engine.execute('SELECT similar_to("anything", 0.9)') == [[1], [2]]


def test_cli_passes_prompts_through(tmp_path, fake):
    from prismql.ingest.cli import run
    from prismql.server.config import load_corpus

    src = tmp_path / "s.csv"
    pl.DataFrame({"i": [1, 2], "t": [1, 2], "text": ["oil", "gas"]}).write_csv(src)
    dst = tmp_path / "o.parquet"
    code = run(
        [
            "table", str(src), str(dst), "--id", "i", "--time", "t",
            "--embed", "text", "--model", "m",
            "--doc-prompt", "doc: ", "--query-prompt", "query: ",
        ]
    )  # fmt: skip
    assert code == 0
    assert fake.built == ["doc: "]
    _, _, stamp = load_corpus(dst)
    assert stamp is not None
    assert (stamp.doc_prompt, stamp.query_prompt) == ("doc: ", "query: ")


def test_sentence_transformer_embedder_hands_the_prompt_to_the_model():
    from prismql.backends.semantic import SentenceTransformerEmbedder

    seen: dict = {}

    class Model:
        def encode(self, texts: list[str], **kwargs: object) -> list[list[float]]:
            seen.update(kwargs)
            return [[1.0] for _ in texts]

    embedder = SentenceTransformerEmbedder.__new__(SentenceTransformerEmbedder)
    embedder.model = Model()
    embedder.prompt = "query: "
    embedder.encode(["x"])
    assert seen == {"prompt": "query: "}
    embedder.prompt = None
    seen.clear()
    embedder.encode(["x"])
    assert seen == {}
