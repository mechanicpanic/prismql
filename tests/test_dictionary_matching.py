"""Per-term dictionary routing: phrases auto-phrase, words follow modes.

WSJ-vocab benchmark finding (#26): real lexicons mix single words and
multi-word phrases. Multi-word terms now ALWAYS go through the n-gram
phrase engine (token mode silently matched nothing for them before);
single-word terms use the dictionary's declared `match` mode, falling
back to the engine-wide text_match.
"""

import json

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.backends.rust_memory import RustMemoryBackend
from prismql.engine import PrismQLEngine, normalize_dictionaries

DOCS = [
    {"id": 1, "user": "x", "text": "the firm faced a margin call on tuesday"},
    {"id": 2, "user": "x", "text": "call margin requirements were unchanged"},
    {"id": 3, "user": "x", "text": "new routes to japan announced"},
    {"id": 4, "user": "x", "text": "a complete rout of the bears"},
    {"id": 5, "user": "x", "text": "they emerged from chapter 11 yesterday"},
]


@pytest.fixture(params=[MemoryBackend, RustMemoryBackend])
def backend(request):
    return request.param(documents=DOCS)


class TestPhraseAutoRouting:
    def test_phrases_match_in_substring_mode(self, backend):
        engine = PrismQLEngine(backend, user_dictionaries={"crisis": ["margin call"]})
        # order-sensitive: doc 2 has both words, wrong order
        assert engine.execute("SELECT contains(crisis)") == [[1]]

    def test_phrases_match_in_token_mode(self, backend):
        # The old behavior: token mode pushed "margin call" through the
        # token index and silently matched NOTHING.
        engine = PrismQLEngine(
            backend,
            user_dictionaries={"crisis": ["margin call"]},
            text_match="token",
        )
        assert engine.execute("SELECT contains(crisis)") == [[1]]

    def test_four_word_phrase(self, backend):
        engine = PrismQLEngine(
            backend,
            user_dictionaries={"crisis": ["emerged from chapter 11"]},
            text_match="token",
        )
        assert engine.execute("SELECT contains(crisis)") == [[5]]


class TestPerDictionaryMode:
    def test_token_mode_dictionary_kills_substring_false_positive(self, backend):
        engine = PrismQLEngine(
            backend,
            user_dictionaries={
                "crisis": {"terms": ["rout", "margin call"], "match": "token"}
            },
        )
        # "rout" must NOT match "routes" (doc 3); the phrase still fires
        assert engine.execute("SELECT contains(crisis)") == [[1], [4]]

    def test_substring_dictionary_alongside_token_dictionary(self, backend):
        engine = PrismQLEngine(
            backend,
            user_dictionaries={
                "exact": {"terms": ["rout"], "match": "token"},
                "stems": ["rout"],  # engine default: substring
            },
        )
        assert engine.execute("SELECT contains(exact)") == [[4]]
        assert engine.execute("SELECT contains(stems)") == [[3], [4]]

    def test_dictionary_mode_overrides_engine_default(self, backend):
        engine = PrismQLEngine(
            backend,
            user_dictionaries={"stems": {"terms": ["rout"], "match": "substring"}},
            text_match="token",
        )
        assert engine.execute("SELECT contains(stems)") == [[3], [4]]

    def test_legacy_haswordofdict_routes_identically(self, backend):
        engine = PrismQLEngine(
            backend,
            user_dictionaries={
                "crisis": {"terms": ["rout", "margin call"], "match": "token"}
            },
        )
        assert engine.execute("SELECT haswordofdict(crisis)") == [[1], [4]]


class TestShapesAndValidation:
    def test_normalize_both_shapes(self):
        terms, modes = normalize_dictionaries(
            {"a": ["x"], "b": {"terms": ["y"], "match": "token"}}
        )
        assert terms == {"a": ["x"], "b": ["y"]}
        assert modes == {"b": "token"}

    def test_invalid_mode_is_loud(self):
        with pytest.raises(ValueError, match="match must be"):
            normalize_dictionaries({"a": {"terms": ["x"], "match": "regex"}})

    def test_add_dictionary_with_match(self, backend):
        engine = PrismQLEngine(backend)
        engine.add_dictionary("crisis", ["rout"], match="token")
        assert engine.execute("SELECT contains(crisis)") == [[4]]
        engine.add_dictionary("crisis", ["rout"])  # re-add without mode
        assert engine.execute("SELECT contains(crisis)") == [[3], [4]]

    def test_validator_accepts_long_form(self):
        from prismql import QueryValidator

        v = QueryValidator(
            user_dictionaries={"crisis": {"terms": ["rout"], "match": "token"}}
        )
        assert v.validate("SELECT contains(crisis)").valid


class TestServerSurfaces:
    @pytest.fixture
    def client(self, tmp_path):
        fastapi = pytest.importorskip("fastapi")  # noqa: F841
        from fastapi.testclient import TestClient

        from prismql.server.app import create_app
        from prismql.server.config import ServerConfig

        data = tmp_path / "events.jsonl"
        data.write_text("\n".join(json.dumps(d) for d in DOCS))
        cfg = ServerConfig(
            backend_type="memory",
            data=str(data),
            dictionaries={"crisis": {"terms": ["rout"], "match": "token"}},
        )
        return TestClient(create_app(cfg))

    def test_toml_long_form_parses(self, tmp_path):
        from prismql.server.config import load_config

        cfg_path = tmp_path / "prismql.toml"
        cfg_path.write_text(
            '[backend]\ntype = "memory"\ndata = "x.jsonl"\n\n'
            '[dictionaries]\nstems = ["tumble"]\n\n'
            "[dictionaries.crisis]\n"
            'match = "token"\nterms = ["rout", "margin call"]\n'
        )
        cfg = load_config(cfg_path)
        assert cfg.dictionaries["stems"] == ["tumble"]
        assert cfg.dictionaries["crisis"]["match"] == "token"

    def test_config_long_form_applies(self, client):
        r = client.post("/evaluate", json={"query": "SELECT contains(crisis)"})
        assert [g["ids"] for g in r.json()["results"]] == [[4]]

    def test_overlay_long_form(self, client):
        r = client.post(
            "/evaluate",
            json={
                "query": "SELECT contains(probe)",
                "dictionaries": {
                    "probe": {"terms": ["rout", "margin call"], "match": "token"}
                },
            },
        )
        assert [g["ids"] for g in r.json()["results"]] == [[1], [4]]

    def test_schema_counts_long_form(self, client):
        assert client.get("/schema").json()["dictionaries"] == {"crisis": 1}
