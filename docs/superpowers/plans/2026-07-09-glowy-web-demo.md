# Glowy Web Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A live, hosted PrismQL demo (Railway + Aleph's domain): dark glowy single-page frontend over the existing FastAPI server, two real corpora (FCC Gitter chat + Chicago crime slice), dual-dialect editor with a classic ⇄ pipe toggle.

**Architecture:** The FastAPI server (`src/prismql/server/`) grows named-corpus support, a static mount, and a rate limit. The frontend is three hand-written files (`demo/web/`), no build step. One Dockerfile deploys the lot.

**Tech Stack:** Python 3.9+ / FastAPI / uvicorn; vanilla HTML/CSS/JS; Docker; Railway CLI.

## Global Constraints

- Python 3.9 compatibility in `src/prismql/` (module-level type aliases use `Union[...]`; `X | None` OK in annotations via `from __future__ import annotations`).
- Run `uv run ruff format . && uv run ruff check . --fix` and `uv run mypy src/prismql` before every commit; pre-commit hooks enforce both.
- Stage commits with explicit paths only — never `git add -A`.
- Existing single-corpus `prismql.toml` configs MUST keep working unchanged (REPL, MCP, and all current tests depend on the flat `ServerConfig` fields).
- Nothing deploys to Railway / DNS without Aleph's explicit go-ahead.
- Frontend: no framework, no build step, no external CDN assets (self-contained page; system fonts or bundled woff2).

---

### Task 1: Named corpora in ServerConfig

**Files:**
- Modify: `src/prismql/server/config.py`
- Test: `tests/test_server_config.py` (append)

**Interfaces:**
- Produces: `CorpusConfig` dataclass (fields: `backend_type, data, index_path, id_field, timestamp_fields, timestamp_field, text_match, dictionaries` — deliberately the same names `build_engine`/`compute_schema` read, so both accept it unchanged); `ServerConfig.corpora: dict[str, CorpusConfig]` (named EXTRA corpora; the flat fields remain the default corpus); `ServerConfig.default_corpus: str = "default"`; helper `ServerConfig.corpus(name) -> CorpusConfig` returning the named corpus or the flat fields repackaged for the default name.
- Consumes: existing `load_config` path resolution helpers.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_server_config.py`:

```python
class TestNamedCorpora:
    def test_legacy_config_has_default_corpus_only(self, tmp_path):
        cfg_file = tmp_path / "prismql.toml"
        data = tmp_path / "docs.json"
        data.write_text('[{"id": 1, "text": "hi", "user": "a"}]')
        cfg_file.write_text('[backend]\ndata = "docs.json"\n')
        config = load_config(cfg_file)
        assert config.corpora == {}
        default = config.corpus("default")
        assert default.data == str(data)
        assert default.backend_type == "memory"

    def test_named_corpora_parsed(self, tmp_path):
        (tmp_path / "a.json").write_text('[{"id": 1, "text": "hi", "user": "x"}]')
        (tmp_path / "b.json").write_text('[{"id": 1, "type": "THEFT"}]')
        (tmp_path / "prismql.toml").write_text(
            "[corpora.chat]\n"
            'data = "a.json"\n'
            "[corpora.chat.dictionaries]\n"
            'greet = ["hi"]\n'
            "[corpora.events]\n"
            'data = "b.json"\n'
            'timestamp_field = "ts"\n'
        )
        config = load_config(tmp_path / "prismql.toml")
        assert set(config.corpora) == {"chat", "events"}
        assert config.corpus("chat").dictionaries == {"greet": ["hi"]}
        assert config.corpus("events").timestamp_field == "ts"
        # relative data paths resolve against the config dir
        assert config.corpus("chat").data == str(tmp_path / "a.json")

    def test_default_corpus_name_configurable(self, tmp_path):
        (tmp_path / "a.json").write_text('[{"id": 1, "text": "hi"}]')
        (tmp_path / "prismql.toml").write_text(
            '[server]\ndefault_corpus = "chat"\n'
            '[corpora.chat]\ndata = "a.json"\n'
        )
        config = load_config(tmp_path / "prismql.toml")
        assert config.default_corpus == "chat"

    def test_unknown_corpus_raises(self, tmp_path):
        (tmp_path / "a.json").write_text('[{"id": 1}]')
        (tmp_path / "prismql.toml").write_text('[backend]\ndata = "a.json"\n')
        config = load_config(tmp_path / "prismql.toml")
        with pytest.raises(KeyError):
            config.corpus("nope")

    def test_build_engine_accepts_corpus_config(self, tmp_path):
        (tmp_path / "a.json").write_text(
            '[{"id": 1, "text": "hello", "user": "x"}]'
        )
        (tmp_path / "prismql.toml").write_text(
            '[corpora.chat]\ndata = "a.json"\n'
        )
        config = load_config(tmp_path / "prismql.toml")
        engine = build_engine(config.corpus("chat"))
        assert engine.execute("from(x)") == [[1]]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_server_config.py::TestNamedCorpora -v`
Expected: FAIL (`CorpusConfig`/`corpus` not defined — import/attribute errors).

- [ ] **Step 3: Implement**

In `src/prismql/server/config.py`:

```python
@dataclass
class CorpusConfig:
    """One named corpus: everything engine-specific.

    Field names deliberately mirror the flat ServerConfig fields so
    build_engine() and compute_schema() accept either object unchanged.
    """

    backend_type: str = "memory"
    data: str | None = None
    index_path: str | None = None
    id_field: str = "id"
    timestamp_fields: list[str] = field(default_factory=lambda: ["timestamp"])
    timestamp_field: str = "timestamp"
    text_match: str = "substring"
    dictionaries: dict[str, Any] = field(default_factory=dict)
```

Add to `ServerConfig`:

```python
    corpora: dict[str, CorpusConfig] = field(default_factory=dict)
    default_corpus: str = "default"

    def corpus(self, name: str) -> CorpusConfig:
        """The named corpus; the flat legacy fields serve the default name."""
        if name in self.corpora:
            return self.corpora[name]
        if name == self.default_corpus and not self.corpora:
            return CorpusConfig(
                backend_type=self.backend_type,
                data=self.data,
                index_path=self.index_path,
                id_field=self.id_field,
                timestamp_fields=self.timestamp_fields,
                timestamp_field=self.timestamp_field,
                text_match=self.text_match,
                dictionaries=self.dictionaries,
            )
        raise KeyError(
            f"Unknown corpus {name!r}; available: {sorted(self.corpus_names())}"
        )

    def corpus_names(self) -> list[str]:
        return sorted(self.corpora) if self.corpora else [self.default_corpus]
```

In `load_config`, after the existing parsing, add (reusing a small
`_resolve(base, value)` helper extracted from the current inline
path-resolution pattern):

```python
    corpora: dict[str, CorpusConfig] = {}
    for name, section in raw.get("corpora", {}).items():
        corpora[name] = CorpusConfig(
            backend_type=section.get("type", "memory").lower(),
            data=_resolve(base, section.get("data")),
            index_path=_resolve(base, section.get("index_path")),
            id_field=section.get("id_field", "id"),
            timestamp_fields=list(section.get("timestamp_fields", ["timestamp"])),
            timestamp_field=section.get("timestamp_field", "timestamp"),
            text_match=section.get("text_match", "substring"),
            dictionaries=dict(section.get("dictionaries", {})),
        )
```

Pass `corpora=corpora` and
`default_corpus=server.get("default_corpus", "default" if not corpora else sorted(corpora)[0])`
to the `ServerConfig(...)` constructor call. When `[corpora]` is present and
`[server].default_corpus` is absent, the default is the alphabetically first
corpus name (deterministic).

Loosen the annotations `def build_engine(config: ServerConfig)` →
`def build_engine(config: ServerConfig | CorpusConfig)` and
`def compute_schema(engine, config: ServerConfig | CorpusConfig)` (both only
read the mirrored fields; `compute_schema` reads no server-only field —
verify with a quick read before committing).

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_server_config.py -v`
Expected: all pass (old tests prove backwards compat, new class passes).

- [ ] **Step 5: Lint, typecheck, commit**

```bash
uv run ruff format src/prismql/server/config.py tests/test_server_config.py && uv run ruff check --fix src/prismql/server/config.py tests/test_server_config.py && uv run mypy src/prismql
git add src/prismql/server/config.py tests/test_server_config.py
git commit -m "Server config: named [corpora.<name>] sections (legacy flat config = default corpus)"
```

---

### Task 2: Multi-engine ServerState + corpus parameter on the API

**Files:**
- Modify: `src/prismql/server/app.py`
- Test: `tests/test_server_app.py` (append)

**Interfaces:**
- Consumes: `ServerConfig.corpus(name)`, `corpus_names()` from Task 1.
- Produces: `ServerState.engines: dict[str, Any]`, `ServerState.engine_for(name: str | None)`; `EvaluateRequest.corpus: str | None`; `GET /schema?corpus=<name>`; `GET /corpora` returning `{"corpora": [...], "default": "..."}` (the frontend's tab source).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_server_app.py` (follow the file's existing fixture
style for building a TestClient from a config):

```python
class TestMultiCorpus:
    @pytest.fixture
    def client(self, tmp_path):
        (tmp_path / "chat.json").write_text(
            '[{"id": 1, "text": "hello", "user": "ann"},'
            ' {"id": 2, "text": "hi back", "user": "ben"}]'
        )
        (tmp_path / "events.json").write_text(
            '[{"id": 1, "type": "THEFT", "timestamp": 1000},'
            ' {"id": 2, "type": "BATTERY", "timestamp": 1060}]'
        )
        (tmp_path / "prismql.toml").write_text(
            '[corpora.chat]\ndata = "chat.json"\n'
            '[corpora.events]\ndata = "events.json"\n'
        )
        from fastapi.testclient import TestClient
        from prismql.server.app import create_app
        from prismql.server.config import load_config

        return TestClient(create_app(load_config(tmp_path / "prismql.toml")))

    def test_corpora_endpoint(self, client):
        body = client.get("/corpora").json()
        assert body == {"corpora": ["chat", "events"], "default": "chat"}

    def test_evaluate_picks_corpus(self, client):
        r = client.post(
            "/evaluate", json={"query": "field(type, THEFT)", "corpus": "events"}
        ).json()
        assert r["ok"] and r["results"][0]["ids"] == [1]

    def test_evaluate_defaults_to_default_corpus(self, client):
        r = client.post("/evaluate", json={"query": "from(ann)"}).json()
        assert r["ok"] and r["results"][0]["ids"] == [1]

    def test_unknown_corpus_is_422(self, client):
        r = client.post(
            "/evaluate", json={"query": "from(ann)", "corpus": "nope"}
        )
        assert r.status_code == 422
        assert "Unknown corpus" in r.json()["error"]["message"]

    def test_schema_takes_corpus(self, client):
        fields = client.get("/schema", params={"corpus": "events"}).json()["fields"]
        assert "type" in fields
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_server_app.py::TestMultiCorpus -v`
Expected: FAIL (`/corpora` 404, `corpus` field unknown).

- [ ] **Step 3: Implement**

In `src/prismql/server/app.py`:

1. `EvaluateRequest` gains `corpus: str | None = None`.
2. `ServerState.reload` builds every corpus:

```python
    def reload(self) -> None:
        with self.lock:
            self.engines = {
                name: build_engine(self.config.corpus(name))
                for name in self.config.corpus_names()
            }
            self.loaded_at = datetime.now(timezone.utc).isoformat()

    def engine_for(self, name: str | None) -> tuple[Any, CorpusConfig]:
        resolved = name or self.config.default_corpus
        if resolved not in self.engines:
            raise KeyError(
                f"Unknown corpus {resolved!r}; "
                f"available: {sorted(self.engines)}"
            )
        return self.engines[resolved], self.config.corpus(resolved)
```

3. `evaluate()` resolves `engine, corpus_cfg = state.engine_for(req.corpus)`
   inside the lock (KeyError → the existing 422 error JSON shape with
   `type: "runtime"`); the dictionary-overlay branch and `result_to_payload`
   hydration use `corpus_cfg` (its `dictionaries`, `timestamp_field`,
   `text_match`, `id_field`) instead of the flat `config` fields.
   `result_to_payload`'s signature changes from `state` to
   `(result, engine, id_field, hydrate, max_results)` — update its two call
   sites.
4. `/schema` gains `corpus: str | None = None` query param →
   `compute_schema(engine, corpus_cfg)`.
5. New route:

```python
    @app.get("/corpora")
    def corpora() -> dict[str, Any]:
        return {
            "corpora": config.corpus_names(),
            "default": config.default_corpus,
        }
```

6. `/health` reports per-corpus document counts:
   `"documents": {name: eng.search_backend.get_total_documents() ...}`.

- [ ] **Step 4: Run the full server test files**

Run: `uv run pytest tests/test_server_app.py tests/test_server_config.py tests/test_server_mcp.py tests/test_repl_info.py -v`
Expected: all pass (single-corpus configs still work end-to-end).

- [ ] **Step 5: Lint, typecheck, commit**

```bash
uv run ruff format src/prismql/server/app.py tests/test_server_app.py && uv run ruff check --fix src/prismql/server/app.py tests/test_server_app.py && uv run mypy src/prismql
git add src/prismql/server/app.py tests/test_server_app.py
git commit -m "Server: multi-corpus engines; corpus param on /evaluate + /schema; GET /corpora"
```

---

### Task 3: Static frontend mount

**Files:**
- Modify: `src/prismql/server/config.py` (one field), `src/prismql/server/app.py` (mount)
- Test: `tests/test_server_app.py` (append)

**Interfaces:**
- Produces: `[server].static_dir` config key → `ServerConfig.static_dir: str | None` (path resolved against config dir); when set, `app.mount("/", StaticFiles(directory=..., html=True))` registered AFTER all API routes so `/evaluate` etc. win.

- [ ] **Step 1: Failing test**

```python
class TestStaticMount:
    def test_static_dir_serves_index(self, tmp_path):
        web = tmp_path / "web"
        web.mkdir()
        web.joinpath("index.html").write_text("<h1>prism</h1>")
        (tmp_path / "docs.json").write_text('[{"id": 1, "text": "x"}]')
        (tmp_path / "prismql.toml").write_text(
            '[server]\nstatic_dir = "web"\n[backend]\ndata = "docs.json"\n'
        )
        from fastapi.testclient import TestClient
        from prismql.server.app import create_app
        from prismql.server.config import load_config

        client = TestClient(create_app(load_config(tmp_path / "prismql.toml")))
        assert "<h1>prism</h1>" in client.get("/").text
        assert client.get("/health").json()["status"] == "ok"  # API still wins
```

- [ ] **Step 2: Run to verify it fails** — `uv run pytest tests/test_server_app.py::TestStaticMount -v` → FAIL.

- [ ] **Step 3: Implement** — `static_dir: str | None = None` on ServerConfig, resolved in `load_config` with the same `_resolve` helper; at the very end of `create_app`:

```python
    if config.static_dir:
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=config.static_dir, html=True))
```

- [ ] **Step 4: Run** — `uv run pytest tests/test_server_app.py -v` → all pass.
- [ ] **Step 5: Commit**

```bash
uv run ruff format src/prismql/server/ tests/test_server_app.py && uv run ruff check --fix src/prismql/server/ tests/test_server_app.py && uv run mypy src/prismql
git add src/prismql/server/config.py src/prismql/server/app.py tests/test_server_app.py
git commit -m "Server: optional [server].static_dir mounts a frontend at /"
```

---

### Task 4: Per-IP rate limit on /evaluate

**Files:**
- Modify: `src/prismql/server/config.py` (one field), `src/prismql/server/app.py`
- Test: `tests/test_server_app.py` (append)

**Interfaces:**
- Produces: `[server].rate_limit_per_minute` → `ServerConfig.rate_limit_per_minute: int | None = None` (None = off, the default — existing users unaffected). Sliding-window limiter inside `evaluate` only.

- [ ] **Step 1: Failing test**

```python
class TestRateLimit:
    def test_rate_limit_429(self, tmp_path):
        (tmp_path / "docs.json").write_text('[{"id": 1, "text": "x", "user": "a"}]')
        (tmp_path / "prismql.toml").write_text(
            "[server]\nrate_limit_per_minute = 3\n[backend]\ndata = \"docs.json\"\n"
        )
        from fastapi.testclient import TestClient
        from prismql.server.app import create_app
        from prismql.server.config import load_config

        client = TestClient(create_app(load_config(tmp_path / "prismql.toml")))
        for _ in range(3):
            assert client.post("/evaluate", json={"query": "from(a)"}).status_code == 200
        assert client.post("/evaluate", json={"query": "from(a)"}).status_code == 429
```

- [ ] **Step 2: Run to verify it fails** → last request returns 200, assertion FAILs.

- [ ] **Step 3: Implement** — in `create_app`, before the routes:

```python
    from collections import defaultdict, deque

    hits: dict[str, deque[float]] = defaultdict(deque)

    def _rate_limited(client_ip: str) -> bool:
        if not config.rate_limit_per_minute:
            return False
        now = perf_counter()
        window = hits[client_ip]
        while window and now - window[0] > 60.0:
            window.popleft()
        if len(window) >= config.rate_limit_per_minute:
            return True
        window.append(now)
        return False
```

`evaluate` gains `request: Request` (FastAPI injects it) and starts with:

```python
        ip = request.client.host if request.client else "unknown"
        if _rate_limited(ip):
            return JSONResponse(
                status_code=429,
                content={"ok": False, "error": {"type": "rate_limit",
                         "message": "Too many queries — try again in a minute."}},
            )
```

(Railway sits behind a proxy: also honor `request.headers.get("x-forwarded-for", "").split(",")[0]` when present.)

- [ ] **Step 4: Run** — `uv run pytest tests/test_server_app.py -v` → pass.
- [ ] **Step 5: Commit**

```bash
uv run ruff format src/prismql/server/ tests/test_server_app.py && uv run ruff check --fix src/prismql/server/ tests/test_server_app.py && uv run mypy src/prismql
git add src/prismql/server/config.py src/prismql/server/app.py tests/test_server_app.py
git commit -m "Server: optional per-IP rate limit on /evaluate ([server].rate_limit_per_minute)"
```

---

### Task 5: Demo corpora + demo config

**Files:**
- Create: `demo/prepare_demo_data.py`, `demo/prismql.toml`
- Generated (committed): `demo/data/fcc.json`, `demo/data/chicago.json`, `demo/data/README.md`

**Interfaces:**
- Consumes source data (Aleph's machine): `~/Projects/research/prismql-research/benchmarks/fcc-situations/messages.jsonl` (4,145 msgs: id/user/text/timestamp-epoch/topic/sid/cluster) and `.../chicago-crime/data/tier_100k.flink.csv` (headerless: id, primary_type, correlation_key, epoch_ts).
- Produces: `demo/data/fcc.json` (all 4,145 messages; keep id/user/text/timestamp/topic) and `demo/data/chicago.json` (first 50,000 rows → `{"id": int, "type": str, "key": str, "timestamp": int}`). The Chicago column is named `type` in the export — no field_mappings needed (deviation from spec noted: rename-at-export replaces field_mappings; simpler and visible in /schema).

- [ ] **Step 1: Write the script**

```python
"""Export the demo corpora from the research repo's benchmark data.

Run once on Aleph's machine; the outputs are committed. Both sources are
publishable: the FCC subset is Aleph's own annotated dataset, the Chicago
data is public domain (City of Chicago open data).
"""

import csv
import json
from pathlib import Path

RESEARCH = Path.home() / "Projects/research/prismql-research/benchmarks"
OUT = Path(__file__).parent / "data"
CHICAGO_ROWS = 50_000


def export_fcc() -> int:
    src = RESEARCH / "fcc-situations/messages.jsonl"
    docs = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        docs.append(
            {
                "id": m["id"],
                "user": m["user"],
                "text": m["text"],
                "timestamp": m["timestamp"],
                "topic": m["topic"],
            }
        )
    (OUT / "fcc.json").write_text(json.dumps(docs, ensure_ascii=False))
    return len(docs)


def export_chicago() -> int:
    src = RESEARCH / "chicago-crime/data/tier_100k.flink.csv"
    docs = []
    with src.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            docs.append(
                {
                    "id": int(row[0]),
                    "type": row[1],
                    "key": row[2],
                    "timestamp": int(row[3]),
                }
            )
            if len(docs) >= CHICAGO_ROWS:
                break
    (OUT / "chicago.json").write_text(json.dumps(docs))
    return len(docs)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(f"fcc: {export_fcc()} messages")
    print(f"chicago: {export_chicago()} events")
```

- [ ] **Step 2: Run it**

Run: `uv run python demo/prepare_demo_data.py`
Expected: `fcc: 4145 messages` / `chicago: 50000 events`; check sizes with `du -h demo/data/*.json` (expect ~1 MB and ~4 MB).

- [ ] **Step 3: Write `demo/prismql.toml`**

```toml
[server]
host = "0.0.0.0"
port = 8901
max_results = 25
hydrate = true
rate_limit_per_minute = 60
static_dir = "web"
default_corpus = "fcc"

[corpora.fcc]
data = "data/fcc.json"

[corpora.fcc.dictionaries]
# seeded from benchmarks/fcc-situations/dicts_handseed.json at authoring
# time — copy the six situation dictionaries (CodeHelp, FCCBug, JobSearch,
# Meeting, OSSelection, SoftwareSupport) verbatim as inline term lists.

[corpora.chicago]
data = "data/chicago.json"
```

Copy the six dictionaries' term lists out of
`~/Projects/research/prismql-research/benchmarks/fcc-situations/dicts_handseed.json`
into `[corpora.fcc.dictionaries]` (they are small — ≤14 terms each).

- [ ] **Step 4: Boot the server locally and smoke it**

```bash
uv run prismql-server --config demo/prismql.toml &
sleep 2
curl -s localhost:8901/corpora
curl -s localhost:8901/health
curl -s -X POST localhost:8901/evaluate -H 'content-type: application/json' \
  -d '{"query": "is_question() and contains(CodeHelp)", "corpus": "fcc"}' | head -c 400
curl -s -X POST localhost:8901/evaluate -H 'content-type: application/json' \
  -d '{"query": "field(type, THEFT) ~> field(type, BATTERY) |> during(1h)", "corpus": "chicago"}' | head -c 300
kill %1
```

Expected: two corpora listed; both queries return `"ok": true` with results.

- [ ] **Step 5: Commit**

```bash
git add demo/prepare_demo_data.py demo/prismql.toml demo/data/fcc.json demo/data/chicago.json demo/data/README.md
git commit -m "Demo corpora: FCC situations subset + Chicago 50k slice, multi-corpus demo config"
```

(`demo/data/README.md`: three lines on provenance/licensing — FCC = Aleph's
annotated dataset, Chicago = City of Chicago open data, both publishable.)

---

### Task 6: Curated examples with verified dual-dialect pairs

**Files:**
- Create: `demo/web/examples.js`, `demo/verify_examples.py`

**Interfaces:**
- Produces: `window.EXAMPLES = {fcc: [...], chicago: [...]}` where each entry is `{label, blurb, classic, pipe}`. Consumed by Task 7's `app.js`.
- Verifier proves for every example: classic and pipe parse to EQUAL IR (`parse_pipe(pipe) == lower_query(classic)`), and the query returns NON-EMPTY results on the demo corpus (same acceptance style as the eval gold set).

- [ ] **Step 1: Draft the examples** (~6 per corpus; final list is whatever survives the verifier — iterate wording/windows until all pass). Starting set:

FCC: questions about code help (`is_question() and contains(CodeHelp)`); question then answer (`is_question() ~> not is_question() |> within(3)`); same user follows up (`from($u) and is_question() ~>(10) from($u)`); rapid triple burst (`from($u) ~>(1) from($u) ~>(1) from($u)`); bug report near a question within 10 minutes (`is_question() + contains(FCCBug) |> during(10m)`); unanswered help request (`contains(CodeHelp) and is_question() !~> contains(SoftwareSupport) |> within(20)`).

Chicago: theft then battery within an hour (`field(type, THEFT) ~> field(type, BATTERY) |> during(1h)`); assault escalation chain (`field(type, ASSAULT) ~>(1h) field(type, BATTERY)`); thefts per day (`field(type, THEFT) |> group(day(timestamp)) |> count()`); co-occurring narcotics + weapons within 30 minutes (`field(type, NARCOTICS) + field(type, "WEAPONS VIOLATION") |> during(30m)`); count of burglaries (`field(type, BURGLARY) |> count()`).

`examples.js` shape:

```js
window.EXAMPLES = {
  fcc: [
    {
      label: "Questions about code help",
      blurb: "Boolean AND over an annotation dictionary",
      classic: "SELECT is_question() AND contains(CodeHelp)",
      pipe: "is_question() and contains(CodeHelp)",
    },
    // ...
  ],
  chicago: [ /* ... */ ],
};
```

- [ ] **Step 2: Write the verifier** (`demo/verify_examples.py`): parse `examples.js` by extracting the JSON-ish literal (keep the file JSON-compatible inside the assignment — author it as `window.EXAMPLES = {...};` where `{...}` is strict JSON), then for each entry assert IR equality and non-empty execution against the demo engines built from `demo/prismql.toml`:

```python
import json
import re
from pathlib import Path

from prismql.dialects.pipe import parse_pipe
from prismql.engine import PrismQLEngine  # noqa: F401 (engines via config)
from prismql.grammar.generated.PrismQLLexer import PrismQLLexer
from prismql.grammar.generated.PrismQLParser import PrismQLParser
from prismql.ir.lower import lower_query
from prismql.server.config import build_engine, load_config
from antlr4 import CommonTokenStream, InputStream

HERE = Path(__file__).parent
raw = (HERE / "web/examples.js").read_text(encoding="utf-8")
examples = json.loads(re.search(r"=\s*(\{.*\});", raw, re.DOTALL).group(1))
config = load_config(HERE / "prismql.toml")

failures = []
for corpus, entries in examples.items():
    engine = build_engine(config.corpus(corpus))
    for ex in entries:
        parser = PrismQLParser(
            CommonTokenStream(PrismQLLexer(InputStream(ex["classic"])))
        )
        if lower_query(parser.parse().query()) != parse_pipe(ex["pipe"]):
            failures.append((corpus, ex["label"], "IR mismatch"))
            continue
        result = engine.execute(ex["pipe"])
        n = len(result) if hasattr(result, "__len__") else 1
        if n == 0:
            failures.append((corpus, ex["label"], "empty result"))

print(f"failures: {len(failures)}")
for f in failures:
    print(" ", f)
raise SystemExit(1 if failures else 0)
```

- [ ] **Step 3: Run and iterate**

Run: `uv run python demo/verify_examples.py`
Expected: `failures: 0`. Adjust windows/dictionary choices on any empty
result; adjust surface forms on any IR mismatch. Do not ship an example
that fails either check.

- [ ] **Step 4: Commit**

```bash
git add demo/web/examples.js demo/verify_examples.py
git commit -m "Demo examples: dual-dialect pairs, IR-equality + non-empty verified"
```

---

### Task 7: The page (index.html / style.css / app.js)

**Files:**
- Create: `demo/web/index.html`, `demo/web/style.css`, `demo/web/app.js`

**Interfaces:**
- Consumes: `GET /corpora`, `POST /evaluate {query, corpus, max_results}`, `window.EXAMPLES` (Task 6). Error payloads: `{ok: false, error: {type, message, line, column}}`.
- Produces: the demo page. No framework, no CDN.

**Execution note:** invoke the `frontend-design` (or `impeccable:frontend-design`) skill when writing these three files — the design language below is the brief, the skill supplies the craft.

**Design brief (binding):**
- Near-black background (`#0a0a0f`-ish), one spectral gradient accent (violet → cyan, e.g. `#8b5cf6 → #22d3ee`) used for: the prism beam, focused-editor glow, matched-message highlights, the run button. Everything else is muted grays. Restraint over rave.
- Header: inline SVG prism — thin white beam entering a triangle, gradient fan exiting; subtle CSS animation (slow shimmer, no motion sickness; respect `prefers-reduced-motion`).
- Corpus tabs under the header ("freeCodeCamp chat", "Chicago crime"), populated from `/corpora`, switching swaps examples and result renderer.
- Editor: `<textarea>` with a `<pre>` highlight overlay (classic trick: transparent textarea text over colorized mirror). One hand-rolled JS tokenizer for BOTH dialects: token classes = keyword (SELECT/AND/OR/NOT/FOLLOWED_BY/INWINDOW/DURING/and/or/not/within/during/group/count...), arrow/pipe operators (`~>` `<~` `!~>` `!<~` `|>` `+`), condition names before `(`, variables (`$x`), strings, numbers/time units, braces/brackets. Colors from the gradient family.
- Dialect toggle (segmented control "SQL ⇄ pipe"): active while the editor text equals the current example's `classic` or `pipe` form (modulo whitespace); flipping swaps the text and re-runs. On free-form edit the toggle grays out with tooltip "toggle works on curated examples — both forms provably identical".
- Example chips in a horizontal wrap, grouped with tiny captions (Sequences / Temporal / Variables / Negative / Aggregation).
- Run: button + Cmd/Ctrl-Enter. Latency badge shows `elapsed_ms` from the response.
- Results, FCC: chat bubbles (user, text, relative time), matched messages get the gradient border glow; each result group is a card; between-group separation obvious; `truncated: true` shows "showing first N".
- Results, Chicago: vertical timeline of event cards (type badge, timestamp, key); groups as connected segments.
- Aggregate/grouped results: big-number card / simple bar list (no chart library).
- Errors: amber panel rendering `error.message` verbatim (the validator's teachable errors are the content), with line/column when present.
- Footer: one line — "PrismQL · pattern matching for conversational data · <paper link placeholder>".

- [ ] **Step 1: Build the static skeleton** (header, tabs, editor, chips, results container) with the API wiring in `app.js`:

```js
async function runQuery() {
  const query = editor.value.trim();
  if (!query) return;
  setRunning(true);
  const res = await fetch("/evaluate", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query, corpus: state.corpus, max_results: 25 }),
  });
  const body = await res.json();
  setRunning(false);
  body.ok ? renderResults(body) : renderError(body.error);
}
```

- [ ] **Step 2: Verify against the live local server** — `uv run prismql-server --config demo/prismql.toml`, open `http://localhost:8901/`, run every example chip on both corpora and both dialect positions; force a syntax error and confirm the teachable message renders; confirm reduced-motion.

- [ ] **Step 3: Glow pass** — apply the design brief fully (this is where the frontend-design skill earns its keep). Re-verify in browser.

- [ ] **Step 4: Commit**

```bash
git add demo/web/index.html demo/web/style.css demo/web/app.js
git commit -m "Glowy demo frontend: dual-dialect editor, corpus tabs, spectral results"
```

---

### Task 8: Dockerfile + container verification

**Files:**
- Create: `Dockerfile`, `.dockerignore`

**Interfaces:**
- Produces: an image that runs `prismql-server --config demo/prismql.toml` honoring Railway's `PORT` env var.

- [ ] **Step 1: Write the Dockerfile**

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system ".[server]"

COPY demo/prismql.toml demo/
COPY demo/web demo/web
COPY demo/data demo/data

ENV PORT=8901
CMD ["sh", "-c", "prismql-server --config demo/prismql.toml --port ${PORT}"]
```

`prismql-server` currently has no `--port` flag — add one in
`src/prismql/server/app.py:main()` (`parser.add_argument("--port", type=int, default=None)`;
override `config.port` when given) with a one-line test-free change (argparse
plumbing), OR set `port` via the config and Railway's domain targeting.
Prefer the flag: `Railway sets PORT; config stays portable.`

`.dockerignore`: `.git`, `.venv`, `tests`, `docs`, `benchmarks`, `*.pyc`,
`__pycache__`, `demo/data/*.tmp`.

- [ ] **Step 2: Build and run locally**

```bash
docker build -t prismql-demo .
docker run --rm -p 8901:8901 prismql-demo &
sleep 3
curl -s localhost:8901/health
curl -s localhost:8901/ | head -c 200
docker stop $(docker ps -q --filter ancestor=prismql-demo)
```

Expected: health OK with both corpora; index.html served.

- [ ] **Step 3: Commit**

```bash
git add Dockerfile .dockerignore src/prismql/server/app.py
git commit -m "Dockerfile for the demo deployable (Railway PORT honored)"
```

---

### Task 9: Full local E2E, docs, and the (gated) Railway steps

**Files:**
- Modify: `demo/README.md`

- [ ] **Step 1: Full suite** — `uv run pytest -q` → everything green; `uv run mypy src/prismql` → no new errors.

- [ ] **Step 2: E2E checklist in the browser** (against the docker container, not uvicorn): both corpora, six examples each, both dialects, dialect toggle round-trip, error path, rate limit (fire 61 fast queries → visible "try again" message), mobile-width viewport sanity.

- [ ] **Step 3: Update `demo/README.md`**: how to regenerate data, run locally, docker build, deploy. Note that the Streamlit demo remains for local use.

- [ ] **Step 4: Commit**

```bash
git add demo/README.md
git commit -m "Demo README: web demo run/deploy instructions"
```

- [ ] **Step 5 (GATED — Aleph's explicit go-ahead + Aleph at the keyboard for DNS):**

```bash
railway login
railway init            # new project, e.g. "prismql-demo"
railway up              # builds the Dockerfile, deploys
railway domain          # generate railway URL; then add custom domain
# Railway dashboard → Settings → Domains → add Aleph's domain
# At the DNS host: CNAME <sub>.domain → <target>.up.railway.app
```

Verify over HTTPS on the real domain, then update the paper draft's demo
placeholder link (research repo, DRAFT.md §1 footnote).

---

## Self-review notes

- Spec coverage: named corpora (T1–T2), static mount (T3), guardrails (T4 + existing max_results ceiling), data (T5), examples/toggle (T6–T7), page (T7), deploy (T8–T9). Spec's `field_mappings` idea replaced by rename-at-export (T5, noted inline).
- The `--port` flag addition lives in T8 where it's needed.
- Types: `ServerConfig.corpus(name) -> CorpusConfig` consumed in T2/T5/T6 verifier; `EvaluateRequest.corpus: str | None` consumed by frontend (T7) as `corpus` in the POST body — consistent.
