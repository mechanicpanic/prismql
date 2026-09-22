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
