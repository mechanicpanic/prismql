"""Several streams into one corpus with a provenance column (graph
@aleph/prismql, #54): the engine does not join, the ingest unites."""

from pathlib import Path

import polars as pl
import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.ingest.cli import run


def _write(tmp_path: Path) -> tuple[Path, Path]:
    reports = tmp_path / "urlquery.csv"
    reports.write_text(
        "id,time,family,class\n"
        "1,2026-06-18T13:00:00Z,sec-county,source_request\n"
        "2,2026-06-18T15:00:00Z,sec-county,custom_program\n"
    )
    wiki = tmp_path / "wiki.jsonl"
    wiki.write_text(
        '{"id": 1, "time": "2026-06-18T14:10:00Z", "family": "sec-county",'
        ' "page": "P"}\n'
        '{"id": 2, "time": "2026-06-18T20:00:00Z", "family": "aihw", "page": "Q"}\n'
    )
    return reports, wiki


def test_streams_unite_in_time_order_with_their_source(tmp_path):
    reports, wiki = _write(tmp_path)
    dst = tmp_path / "union.parquet"
    args = ["table", str(reports), f"wiki={wiki}", str(dst), "--id", "id"]
    args += ["--time", "time", "--sort", "time", "--source-col", "source"]
    assert run(args) == 0
    out = pl.read_parquet(dst)
    assert out.get_column("source").to_list() == [
        "urlquery",
        "wiki",
        "urlquery",
        "wiki",
    ]
    # ids collide across files, so each is prefixed with its source
    assert out.get_column("id").to_list() == [
        "urlquery:1",
        "wiki:1",
        "urlquery:2",
        "wiki:2",
    ]
    # columns one file lacks are null on the other's rows
    assert out.get_column("page").to_list() == [None, "P", None, "Q"]
    assert out.get_column("class").to_list()[0] == "source_request"


def test_the_united_corpus_answers_a_lead_lag_question(tmp_path):
    reports, wiki = _write(tmp_path)
    dst = tmp_path / "union.parquet"
    run(
        [
            "table",
            str(reports),
            f"wiki={wiki}",
            str(dst),
            "--id",
            "id",
            "--time",
            "time",
            "--sort",
            "time",
            "--source-col",
            "source",
        ]
    )
    docs = pl.read_parquet(dst).to_dicts()
    engine = PrismQLEngine(MemoryBackend(docs), timestamp_field="time")
    q = (
        "SELECT field(source, urlquery) AND field(family, $f)"
        " FOLLOWED_BY field(source, wiki) AND field(family, $f) DURING 6 hours"
    )
    assert engine.execute(q) == [["urlquery:1", "wiki:1"]]


def test_several_sources_need_a_provenance_column(tmp_path, capsys):
    reports, wiki = _write(tmp_path)
    code = run(
        [
            "table",
            str(reports),
            str(wiki),
            str(tmp_path / "o.parquet"),
            "--id",
            "id",
            "--time",
            "time",
        ]
    )
    assert code == 2
    assert "--source-col" in capsys.readouterr().err


def test_one_source_keeps_its_ids(tmp_path):
    reports, _ = _write(tmp_path)
    dst = tmp_path / "one.parquet"
    run(
        [
            "table",
            str(reports),
            str(dst),
            "--id",
            "id",
            "--time",
            "time",
            "--source-col",
            "source",
        ]
    )
    out = pl.read_parquet(dst)
    assert out.get_column("id").to_list() == [1, 2]
    assert out.get_column("source").unique().to_list() == ["urlquery"]


@pytest.mark.parametrize("bad", ["=x.csv", "a=b=c"])
def test_a_malformed_label_is_refused(tmp_path, bad):
    assert (
        run(
            [
                "table",
                bad,
                str(tmp_path / "o.parquet"),
                "--id",
                "id",
                "--time",
                "time",
                "--source-col",
                "s",
            ]
        )
        == 2
    )
