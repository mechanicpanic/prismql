"""Tests for prismql.server.config — no fastapi dependency required."""

import json
from pathlib import Path

import pytest

from prismql.server.config import (
    ServerConfig,
    build_engine,
    load_config,
    load_documents,
)


def test_load_config_full(tmp_path):
    (tmp_path / "dicts.json").write_text(json.dumps({"spikes": ["spike"]}))
    cfg_file = tmp_path / "prismql.toml"
    cfg_file.write_text(
        """
[server]
host = "0.0.0.0"
port = 9000
max_results = 25
hydrate = false

[backend]
type = "rust_memory"
data = "ticks.jsonl"
timestamp_fields = ["ts"]
id_field = "tick_id"

[engine]
timestamp_field = "ts"

[dictionaries]
file = "dicts.json"
"""
    )
    cfg = load_config(cfg_file)
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 9000
    assert cfg.max_results == 25
    assert cfg.hydrate is False
    assert cfg.backend_type == "rust_memory"
    # relative data path resolves against the config file's directory
    assert cfg.data == str(tmp_path / "ticks.jsonl")
    assert cfg.timestamp_fields == ["ts"]
    assert cfg.id_field == "tick_id"
    assert cfg.timestamp_field == "ts"
    assert cfg.dictionaries == {"spikes": ["spike"]}


def test_load_config_defaults(tmp_path):
    cfg_file = tmp_path / "min.toml"
    cfg_file.write_text('[backend]\ntype = "memory"\ndata = "d.json"\n')
    cfg = load_config(cfg_file)
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8901
    assert cfg.max_results == 50
    assert cfg.hydrate is True
    assert cfg.timestamp_fields == ["timestamp"]
    assert cfg.timestamp_field == "timestamp"
    assert cfg.id_field == "id"
    assert cfg.dictionaries == {}


def test_load_config_inline_dictionaries(tmp_path):
    cfg_file = tmp_path / "c.toml"
    cfg_file.write_text(
        '[backend]\ntype = "memory"\ndata = "d.json"\n\n'
        '[dictionaries]\nspikes = ["spike", "surge"]\n'
    )
    cfg = load_config(cfg_file)
    assert cfg.dictionaries == {"spikes": ["spike", "surge"]}


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/prismql.toml")


def test_load_documents_json(tmp_path):
    f = tmp_path / "d.json"
    f.write_text(json.dumps([{"id": 1, "text": "a"}]))
    assert load_documents(f) == [{"id": 1, "text": "a"}]


def test_load_documents_jsonl(tmp_path):
    f = tmp_path / "d.jsonl"
    f.write_text('{"id": 1, "text": "a"}\n\n{"id": 2, "text": "b"}\n')
    assert load_documents(f) == [{"id": 1, "text": "a"}, {"id": 2, "text": "b"}]


def test_load_documents_csv_coerces_id(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("id,user,text\n1,a,hi\n2,b,yo\n")
    docs = load_documents(f)
    assert docs[0]["id"] == 1 and docs[1]["id"] == 2
    assert docs[0]["user"] == "a"


def test_load_documents_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_documents(tmp_path / "nope.json")


def test_load_documents_unknown_format(tmp_path):
    f = tmp_path / "d.xml"
    f.write_text("<x/>")
    with pytest.raises(ValueError, match="Unsupported data format"):
        load_documents(f)


def _write_events(tmp_path) -> Path:
    f = tmp_path / "events.jsonl"
    docs = [
        {"id": 1, "user": "a", "text": "price spike", "timestamp": 1000},
        {"id": 2, "user": "b", "text": "calm", "timestamp": 1005},
    ]
    f.write_text("\n".join(json.dumps(d) for d in docs))
    return f


def test_build_engine_memory(tmp_path):
    cfg = ServerConfig(
        backend_type="memory",
        data=str(_write_events(tmp_path)),
        dictionaries={"spikes": ["spike"]},
    )
    engine = build_engine(cfg)
    assert engine.execute("SELECT contains(spikes)") == [[1]]


def test_build_engine_requires_data():
    cfg = ServerConfig(backend_type="memory", data=None)
    with pytest.raises(ValueError, match="data"):
        build_engine(cfg)


def test_build_engine_rejects_db_backends():
    cfg = ServerConfig(backend_type="postgres", data="dsn://x")
    with pytest.raises(ValueError, match="library API"):
        build_engine(cfg)


def test_text_match_config(tmp_path):
    f = _write_events(tmp_path)
    cfg_file = tmp_path / "c.toml"
    cfg_file.write_text(
        f'[backend]\ntype = "memory"\ndata = "{f.name}"\n\n'
        '[engine]\ntext_match = "token"\n\n'
        '[dictionaries]\nlabour = ["work"]\n'
    )
    cfg = load_config(cfg_file)
    assert cfg.text_match == "token"
    engine = build_engine(cfg)
    # token mode: "work" does not match "working"... no "working" doc here,
    # but "spike" must not match "spiked" -- use the actual fixture text
    assert engine.execute("SELECT contains(labour)") == []


def test_text_match_defaults_to_substring(tmp_path):
    cfg_file = tmp_path / "min.toml"
    cfg_file.write_text('[backend]\ntype = "memory"\ndata = "d.json"\n')
    assert load_config(cfg_file).text_match == "substring"
