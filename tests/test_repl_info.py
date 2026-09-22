"""Tests for REPL corpus introspection: \\schema, banner, prismql.toml loading.

The REPL and the server share ServerConfig + compute_schema, so what
\\schema prints is exactly what GET /schema reports for the same config.
"""

import json

from prismql.backends.memory import MemoryBackend
from prismql.repl import PrismQLRepl
from prismql.server.config import ServerConfig, build_engine, compute_schema

DOCS = [
    {"id": 1, "user": "tick_a", "text": "price spike", "timestamp": 1000},
    {"id": 2, "user": "tick_a", "text": "reversal", "timestamp": 1010},
    {"id": 3, "user": "tick_b", "text": "calm seas", "timestamp": 1015},
    {"id": 4, "user": "tick_a", "text": "recovery", "timestamp": 1020},
]


def _toml_config(tmp_path, **extra: str) -> ServerConfig:
    data = tmp_path / "events.jsonl"
    data.write_text("\n".join(json.dumps(d) for d in DOCS))
    return ServerConfig(
        backend_type="memory",
        data=str(data),
        dictionaries={"spikes": ["spike"]},
        **extra,
    )


def test_repl_from_server_config(tmp_path):
    cfg = _toml_config(tmp_path)
    repl = PrismQLRepl(engine=build_engine(cfg), server_config=cfg)
    assert repl.engine.search_backend.get_total_documents() == 4
    # queries actually run against the loaded corpus
    result = repl.engine.execute("SELECT contains(spikes)")
    assert result == [[1]]


def test_corpus_banner_shows_data_and_dictionaries(tmp_path):
    cfg = _toml_config(tmp_path)
    repl = PrismQLRepl(engine=build_engine(cfg), server_config=cfg)
    banner = repl.corpus_banner()
    assert "4 documents" in banner
    assert "MemoryBackend" in banner
    assert "events.jsonl" in banner
    assert "1 dictionary" in banner


def test_show_schema_prints_fields_and_dictionaries(tmp_path, capsys):
    cfg = _toml_config(tmp_path)
    repl = PrismQLRepl(engine=build_engine(cfg), server_config=cfg)
    repl.show_schema()
    out = capsys.readouterr().out
    assert "Corpus: 4 documents" in out
    assert "id_field: id" in out
    assert "text_match: stem" in out
    assert "user" in out
    assert "tick_a, tick_b" in out  # categorical examples
    assert "spikes (1 term)" in out


def test_schema_matches_server_endpoint_payload(tmp_path):
    # Same function, same config object -> byte-identical schema with /schema
    cfg = _toml_config(tmp_path)
    repl = PrismQLRepl(engine=build_engine(cfg), server_config=cfg)
    schema = compute_schema(repl.engine, repl.server_config)
    assert schema["documents"] == 4
    assert schema["fields"]["user"]["examples"] == ["tick_a", "tick_b"]
    assert schema["dictionaries"] == {"spikes": 1}


def test_server_config_synthesized_without_one(capsys):
    # Library-style construction (no toml): \schema still works, reflecting
    # the engine's own settings.
    repl = PrismQLRepl(
        search_backend=MemoryBackend(documents=DOCS),
        user_dictionaries={"spikes": ["spike"], "calms": ["calm"]},
    )
    assert repl.server_config.id_field == "id"
    assert repl.server_config.text_match == "stem"
    repl.show_schema()
    out = capsys.readouterr().out
    assert "Corpus: 4 documents" in out
    assert "spikes (1 term)" in out
    assert "calms (1 term)" in out


def test_repl_requires_backend_or_engine():
    import pytest

    with pytest.raises(ValueError, match="search_backend or engine"):
        PrismQLRepl()


def test_help_mentions_schema_and_canonical_operators(capsys):
    repl = PrismQLRepl(search_backend=MemoryBackend(documents=DOCS))
    repl.show_help()
    out = capsys.readouterr().out
    assert "\\schema" in out
    assert "INWINDOW" in out
    assert "DURING" in out
    # deprecated spellings no longer taught
    assert "INWIN N" not in out
    assert "WITHIN" not in out
