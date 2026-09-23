"""A memory corpus answers its text predicates from one tantivy index built
in load order (graph @aleph/prismql, #91), optionally kept on disk with a
fingerprint of the data it was built from — a stale index is never opened."""

import json
import os

import pytest

pytest.importorskip("tantivy")

from prismql.backends.tantivy import TantivyBackend  # noqa: E402
from prismql.server.config import (  # noqa: E402
    ServerConfig,
    build_engine,
    compute_schema,
)

DOCS = [
    {"id": "e1", "text": "deploy failed, rolling back", "timestamp": 1000},
    {"id": "e2", "text": "please sign in again", "timestamp": 1005},
    {"id": "e3", "text": "the deploy succeeded", "timestamp": 1010},
]
DICTS = {"deploys": ["deploy"], "signin": ["sign in"]}
QUERIES = [
    "SELECT contains(deploys)",
    "SELECT contains(signin)",
    "SELECT contains(deploys) FOLLOWED_BY contains(deploys) INWINDOW 3",
]


def _data(tmp_path, docs: list = DOCS) -> str:
    f = tmp_path / "events.jsonl"
    f.write_text("\n".join(json.dumps(d) for d in docs))
    return str(f)


def _cfg(tmp_path, **kw: object) -> ServerConfig:
    return ServerConfig(
        backend_type="memory", data=_data(tmp_path), dictionaries=DICTS, **kw
    )


def _answers(engine) -> list:
    return [engine.execute(q) for q in QUERIES]


def test_a_memory_corpus_gets_a_tantivy_text_index_by_default(tmp_path):
    engine = build_engine(_cfg(tmp_path))
    assert isinstance(engine.search_backend.text_index, TantivyBackend)
    plain = build_engine(_cfg(tmp_path, text_index="memory"))
    assert plain.search_backend.text_index is None
    assert _answers(engine) == _answers(plain)
    assert _answers(engine)[0] == [["e1"], ["e3"]]


def test_the_schema_names_the_text_search_path(tmp_path):
    cfg = _cfg(tmp_path)
    assert compute_schema(build_engine(cfg), cfg)["text_search"] == "tantivy"
    cfg = _cfg(tmp_path, text_index="memory")
    assert compute_schema(build_engine(cfg), cfg)["text_search"] == "memory"


def test_substring_mode_stays_in_python(tmp_path):
    engine = build_engine(_cfg(tmp_path, text_match="substring"))
    assert engine.search_backend.text_index is None
    with pytest.raises(ValueError, match="substring"):
        build_engine(_cfg(tmp_path, text_match="substring", text_index="tantivy"))


def test_an_unknown_text_index_is_refused(tmp_path):
    with pytest.raises(ValueError, match="text_index"):
        build_engine(_cfg(tmp_path, text_index="lucene"))


def test_a_persisted_index_is_reopened_for_the_same_data(tmp_path):
    path = tmp_path / "textidx"
    cfg = _cfg(tmp_path, text_index_path=str(path))
    first = build_engine(cfg)
    meta = path / "_prismql_meta.json"
    stamp = meta.stat().st_mtime_ns
    second = build_engine(cfg)
    assert meta.stat().st_mtime_ns == stamp  # opened, not rebuilt
    assert _answers(second) == _answers(first)


def test_a_persisted_index_is_rebuilt_when_the_data_changed(tmp_path, capsys):
    path = tmp_path / "textidx"
    build_engine(_cfg(tmp_path, text_index_path=str(path)))
    grown = [*DOCS, {"id": "e4", "text": "deploy again", "timestamp": 1020}]
    data = _data(tmp_path, grown)
    os.utime(data, ns=(1, 1))  # a different mtime even within one clock tick
    cfg = ServerConfig(
        backend_type="memory",
        data=data,
        dictionaries=DICTS,
        text_index_path=str(path),
    )
    engine = build_engine(cfg)
    assert engine.execute("SELECT contains(deploys)") == [["e1"], ["e3"], ["e4"]]
    assert "rebuilt" in capsys.readouterr().out


def test_a_foreign_directory_is_never_overwritten(tmp_path):
    path = tmp_path / "notours"
    path.mkdir()
    (path / "keep.txt").write_text("mine")
    with pytest.raises(ValueError, match="not a prismql text index"):
        build_engine(_cfg(tmp_path, text_index_path=str(path)))
    assert (path / "keep.txt").read_text() == "mine"


def test_search_ranks_from_the_corpus_text_index(tmp_path):
    from fastapi.testclient import TestClient

    from prismql.server.app import create_app

    app = create_app(_cfg(tmp_path))
    with TestClient(app) as client:
        body = client.post("/search", json={"query": "deploy"}).json()
        assert body["ok"] and body["total"] == 2
        state = app.state.prismql
        engine, cfg, lock = state.engine_for(None)
        scout = state.scout_for(None, engine, cfg, lock)
        assert scout is engine.search_backend.text_index


def test_a_same_size_same_mtime_rewrite_is_still_rebuilt(tmp_path):
    """cp -p / rsync -a keep size and mtime; the fingerprint is the content."""
    path = tmp_path / "textidx"
    data = _data(tmp_path)
    stat = os.stat(data)
    build_engine(
        ServerConfig(
            backend_type="memory",
            data=data,
            dictionaries=DICTS,
            text_index_path=str(path),
        )
    )
    swapped = [dict(d, text=d["text"].replace("deploy", "zzzzzz")) for d in DOCS]
    _data(tmp_path, swapped)  # same length: "deploy" and "zzzzzz" are 6 letters
    assert os.stat(data).st_size == stat.st_size
    os.utime(data, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    engine = build_engine(
        ServerConfig(
            backend_type="memory",
            data=data,
            dictionaries={"z": ["zzzzzz"]},
            text_index_path=str(path),
        )
    )
    assert engine.execute("SELECT contains(z)") == [["e1"], ["e3"]]


def test_a_full_tantivy_index_is_never_deleted(tmp_path):
    path = tmp_path / "full"
    TantivyBackend(DOCS, index_path=str(path))  # a tantivy backend's own index
    with pytest.raises(ValueError, match="not a text index"):
        build_engine(_cfg(tmp_path, text_index_path=str(path)))
    assert (path / "_prismql_meta.json").exists()


def test_an_index_left_without_its_order_sidecar_is_rebuilt(tmp_path):
    path = tmp_path / "textidx"
    build_engine(_cfg(tmp_path, text_index_path=str(path)))
    (path / "order.parquet").unlink()  # a crash between meta and sidecar
    engine = build_engine(_cfg(tmp_path, text_index_path=str(path)))
    assert _answers(engine)[0] == [["e1"], ["e3"]]


def test_mixed_id_types_keep_the_index_in_memory(tmp_path, capsys):
    docs = [{"id": 1, "text": "deploy one"}, {"id": "b", "text": "deploy two"}]
    cfg = ServerConfig(
        backend_type="memory",
        data=_data(tmp_path, docs),
        dictionaries=DICTS,
        text_index_path=str(tmp_path / "textidx"),
    )
    backend = build_engine(cfg).search_backend
    assert backend.search_stems(["deploy"]) == {1, "b"}
    assert not (tmp_path / "textidx").exists()
    assert "in memory" in capsys.readouterr().out


def test_search_can_scope_to_a_metadata_field(tmp_path):
    from fastapi.testclient import TestClient

    from prismql.server.app import create_app

    docs = [{**d, "kind": "ops" if d["id"] != "e2" else "auth"} for d in DOCS]
    cfg = ServerConfig(backend_type="memory", data=_data(tmp_path, docs))
    with TestClient(create_app(cfg)) as client:
        body = client.post("/search", json={"query": "kind:auth"}).json()
        assert body["ok"] and body["total"] == 1
