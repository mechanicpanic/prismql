"""The ingest core: canonical stream out of any table (graph #54)."""

from datetime import UTC, datetime

import polars as pl
import pytest

from prismql.backends.order import epoch_micros
from prismql.ingest import normalize, write
from prismql.loaders import load_table


def test_normalize_sorts_positions_and_parses_time():
    df = pl.DataFrame(
        {
            "i": [3, 1, 2],
            "t": ["2026-09-03 21:55:03.311588", "2026-07-14T08:35:13.992Z", "bad"],
            "x": ["a", "b", "c"],
            "y": [1, 2, 3],
        }
    )
    out = normalize(df, id_col="i", time_col="t", sort="t", keep=["x"])
    assert out.columns == ["position", "id", "time", "x"]
    assert out.get_column("position").to_list() == [0, 1, 2]
    assert out.get_column("id").to_list() == [1, 3, 2]  # by parsed time, null last
    assert out.get_column("time").dtype == pl.Datetime("us", "UTC")
    assert out.get_column("time")[0] == datetime(
        2026, 7, 14, 8, 35, 13, 992000, tzinfo=UTC
    )
    assert out.get_column("time")[2] is None


@pytest.mark.parametrize(
    "value",
    [1784018113992000, 1784018113992, 1784018113.992, "2026-07-14T08:35:13.992Z"],
)
def test_epoch_units_and_strings_agree(value):
    out = normalize(pl.DataFrame({"i": [1], "t": [value]}), id_col="i", time_col="t")
    assert epoch_micros(out.get_column("time")[0]) == 1784018113992000


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="duplicate ids"):
        normalize(pl.DataFrame({"i": [1, 1], "t": [1, 2]}), id_col="i", time_col="t")


def test_written_parquet_round_trips_into_the_engine(tmp_path):
    df = normalize(
        pl.DataFrame(
            {"i": [1, 2], "t": ["2026-01-01T00:00:00Z", "2026-01-01T00:00:05Z"]}
        ),
        id_col="i",
        time_col="t",
    )
    path = write(df, tmp_path / "s.parquet")
    table = load_table(path)
    rows = table.to_pylist()
    assert [r["position"] for r in rows] == [0, 1]
    assert epoch_micros(rows[1]["time"]) - epoch_micros(rows[0]["time"]) == 5_000_000


def test_cli_table(tmp_path, capsys):
    from prismql.ingest.cli import run

    src = tmp_path / "in.jsonl"
    src.write_text(
        '{"k": 2, "when": "2026-01-01 00:00:01", "v": "b"}\n'
        '{"k": 1, "when": "2026-01-01 00:00:00", "v": "a"}\n'
    )
    dst = tmp_path / "out.parquet"
    assert (
        run(
            [
                "table",
                str(src),
                str(dst),
                "--id",
                "k",
                "--time",
                "when",
                "--sort",
                "when",
            ]
        )
        == 0
    )
    out = pl.read_parquet(dst)
    assert out.get_column("id").to_list() == [1, 2]
    assert "2 rows" in capsys.readouterr().out


def test_mixed_epoch_units_are_classified_per_value():
    out = normalize(
        pl.DataFrame(
            {"i": [1, 2, 3], "t": [1784018113, 1784018113992, 1784018113992000000]}
        ),
        id_col="i",
        time_col="t",
    )
    micros = [epoch_micros(v) for v in out.get_column("time").to_list()]
    assert micros == [1784018113000000, 1784018113992000, 1784018113992000]


def test_explicit_time_unit_overrides_the_guess():
    out = normalize(
        pl.DataFrame({"i": [1], "t": [50_000_000_000]}),
        id_col="i",
        time_col="t",
        time_unit="ms",
    )
    assert out.get_column("time")[0].year == 1971
    with pytest.raises(ValueError, match="not numeric"):
        normalize(
            pl.DataFrame({"i": [1], "t": ["x"]}),
            id_col="i",
            time_col="t",
            time_unit="s",
        )


def test_date_only_and_garbage_strings_become_dates_or_nulls():
    out = normalize(
        pl.DataFrame({"i": [1, 2, 3], "t": ["2026-07-14", "nonsense", None]}),
        id_col="i",
        time_col="t",
    )
    assert out.get_column("time")[0] == datetime(2026, 7, 14, tzinfo=UTC)
    assert out.get_column("time").null_count() == 2


def test_canonical_names_in_the_source_are_dropped_not_collided():
    src = pl.DataFrame(
        {
            "rev": [1],
            "t": ["2026-07-14T00:00:00Z"],
            "id": [9],
            "position": [3],
            "x": ["a"],
        }
    )
    out = normalize(src, id_col="rev", time_col="t")
    assert out.columns == ["position", "id", "time", "x"]
    again = normalize(
        out, id_col="id", time_col="time"
    )  # an ingested file, ingested again
    assert again.get_column("id").to_list() == [1]


def test_embed_gives_zero_vectors_to_rows_without_text(monkeypatch):
    from prismql.backends import semantic as semantic_module
    from prismql.ingest.core import embed

    class Fake:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, float(len(t))] for t in texts]

    monkeypatch.setattr(semantic_module, "SentenceTransformerEmbedder", Fake)
    df = pl.DataFrame({"id": [1, 2, 3, 4], "text": ["oil", None, "", "  "]})
    out = embed(df, text="text", model="fake")
    vectors = out.get_column("emb").to_list()
    assert vectors[0] == pytest.approx([0.3162, 0.9487], abs=1e-3)  # unit length
    assert vectors[1:] == [[0.0, 0.0]] * 3


def test_embedded_stream_round_trips_through_parquet_with_textless_rows(
    tmp_path, monkeypatch
):
    """A null inside a fixed-size Array column does not survive Parquet
    (pyarrow: "Expected all lists to be of size=d but index i had size=0");
    textless rows carry zero vectors and the server skips them."""
    from prismql.backends import semantic as semantic_module
    from prismql.ingest.core import embed
    from prismql.server.config import load_corpus

    class Fake:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, float(len(t))] for t in texts]

    monkeypatch.setattr(semantic_module, "SentenceTransformerEmbedder", Fake)
    df = normalize(
        pl.DataFrame({"i": [1, 2, 3], "t": [1, 2, 3], "text": ["oil", None, ""]}),
        id_col="i",
        time_col="t",
    )
    path = write(
        embed(df, text="text", model="fake"), tmp_path / "e.parquet", embed_model="fake"
    )
    docs, vectors, model, _ = load_corpus(path)
    assert model == "fake" and [d["id"] for d in docs] == [1, 2, 3]
    index = semantic_module.SemanticIndex.from_vectors(Fake("fake"), [1, 2, 3], vectors)
    assert len(index) == 1


def test_server_rejects_a_parquet_whose_position_is_not_the_row_order(tmp_path):
    from prismql.server.config import load_corpus

    pl.DataFrame({"position": [1, 0], "id": [1, 2], "time": [1, 2]}).write_parquet(
        tmp_path / "bad.parquet"
    )
    with pytest.raises(ValueError, match="row index"):
        load_corpus(tmp_path / "bad.parquet")
