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
