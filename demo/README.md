# PrismQL Demo

The live demo is a FastAPI server (`prismql.server.app`) serving a static
frontend (`demo/web/`) and the `/evaluate` API over two named corpora
(`fcc`, `chicago`), in both the classic and pipe dialects.

## Regenerate the demo data

`demo/data/*.json` are committed exports from the research repo's
benchmarks. Regenerate only if the source data changes:

```bash
uv run python demo/prepare_demo_data.py   # requires ../prismql-research checked out
```

## Run locally

```bash
uv sync --extra server
uv run prismql-server --config demo/prismql.toml
# -> http://localhost:8901
```

`demo/prismql.toml` defines both corpora, the dictionaries, rate limiting
(`60`/min), and `static_dir = "web"` so the server also serves the frontend
at `/`.

## Docker

```bash
docker build -t prismql-demo -f Dockerfile .
docker run --rm -p 8901:8901 prismql-demo
```

The `Dockerfile` honors `$PORT` (defaults to `8901`) for Railway compatibility.

## E2E check (container-level)

`demo/e2e_container.py` drives every example in `demo/web/examples.js`
against a running container — both dialects, both corpora — plus the
syntax-error path, unknown-corpus path, `GET /`, `GET /corpora`, and the
rate limiter (fires last; it poisons the per-IP window for a minute):

```bash
docker run --rm -d -p 8944:8901 --name prismql-demo-e2e prismql-demo
uv run python demo/e2e_container.py http://localhost:8944
docker stop prismql-demo-e2e
```

## Deploy (Railway)

```bash
railway login
railway init            # new project, e.g. "prismql-demo"
railway up               # builds the Dockerfile, deploys
railway domain            # generates a *.up.railway.app URL
```

For a custom domain: Railway dashboard → Settings → Domains → add the
domain, then at the DNS host add a CNAME record:
`<sub>.domain -> <target>.up.railway.app`.
