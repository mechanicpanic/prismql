"""A query that measures time on a corpus with no time in its field is an
error, not an empty answer; and a config that names no time field finds the
one the file has (graph @aleph/prismql, #117, owner's word). `prismql
ingest` writes the time column as `time` where the default was `timestamp`,
so every DURING query on an ingested file answered empty without a word."""

import json

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError

DOCS = [
    {"id": 1, "user": "a", "text": "x", "time": "2024-01-01T00:00:00Z"},
    {"id": 2, "user": "b", "text": "y", "time": "2024-01-01T00:01:00Z"},
]

TIMED = [
    "SELECT from(a) FOLLOWED_BY from(b) DURING 5 minutes",
    "SELECT from(a), from(b) DURING 5 minutes",
    'SELECT from(a) AFTER("2023-01-01")',
    "from(a) ~> from(b) |> during(5 minutes)",
]


def _engine(use_ir: bool = True) -> PrismQLEngine:
    # timestamp_field left at its default, "timestamp": no event has it
    return PrismQLEngine(MemoryBackend(DOCS, timestamp_fields=["time"]), use_ir=use_ir)


@pytest.mark.parametrize("use_ir", [True, False])
@pytest.mark.parametrize("query", TIMED)
def test_a_timed_query_on_a_missing_time_field_is_loud(query, use_ir):
    with pytest.raises(PrismQLRuntimeError, match="'timestamp'.*'time'"):
        _engine(use_ir).execute(query)


def test_a_positional_query_needs_no_time():
    assert _engine().execute("SELECT from(a) FOLLOWED_BY from(b) INWINDOW 2") == [
        [1, 2]
    ]


def test_the_right_field_answers():
    engine = PrismQLEngine(
        MemoryBackend(DOCS, timestamp_fields=["time"]), timestamp_field="time"
    )
    assert engine.execute(TIMED[0]) == [[1, 2]]


def _config(tmp_path, data_name: str, body: str) -> str:
    cfg = tmp_path / "prismql.toml"
    cfg.write_text(f'[corpora.c]\ndata = "{data_name}"\n{body}')
    return str(cfg)


def _write_ingested(tmp_path) -> str:
    pytest.importorskip("pyarrow")
    import polars as pl

    from prismql.ingest import normalize, write

    df = normalize(
        pl.DataFrame({"i": [1, 2], "t": [0, 60], "user": ["a", "b"]}),
        id_col="i",
        time_col="t",
        time_unit="s",
        keep=["user"],
    )
    write(df, tmp_path / "e.parquet")
    return "e.parquet"


def test_a_config_without_time_keys_finds_an_ingested_files_time(tmp_path):
    from prismql.server.config import build_engine, load_config

    cfg = load_config(_config(tmp_path, _write_ingested(tmp_path), ""))
    corpus = cfg.corpus("c")
    assert (corpus.timestamp_fields, corpus.timestamp_field) == (["time"], "time")
    assert build_engine(corpus).execute(TIMED[0]) == [[1, 2]]


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ('timestamp_fields = ["time"]', (["time"], "time")),
        ('timestamp_field = "time"', (["time"], "time")),
        ('timestamp_fields = ["time", "edited"]', (["time", "edited"], "time")),
    ],
)
def test_one_time_key_gives_the_other(tmp_path, body, expected):
    from prismql.server.config import load_config

    cfg = load_config(_config(tmp_path, _write_ingested(tmp_path), body))
    corpus = cfg.corpus("c")
    assert (corpus.timestamp_fields, corpus.timestamp_field) == expected


def test_a_timestamp_column_stays_the_default(tmp_path):
    from prismql.server.config import load_config

    (tmp_path / "e.jsonl").write_text(
        json.dumps({"id": 1, "timestamp": 5, "time": "noon"}) + "\n"
    )
    corpus = load_config(_config(tmp_path, "e.jsonl", "")).corpus("c")
    assert corpus.timestamp_field == "timestamp"


def test_the_flat_form_infers_too(tmp_path):
    from prismql.server.config import load_config

    name = _write_ingested(tmp_path)
    cfg_path = tmp_path / "flat.toml"
    cfg_path.write_text(f'[backend]\ndata = "{name}"\n')
    cfg = load_config(str(cfg_path))
    assert (cfg.timestamp_fields, cfg.timestamp_field) == (["time"], "time")
