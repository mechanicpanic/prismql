FROM python:3.12-slim

# Pinned (was :latest): a breaking uv release must not change build
# behavior between two otherwise-identical deploys.
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv pip install --system ".[server]"

COPY demo/prismql.toml demo/
COPY demo/web demo/web
COPY demo/data demo/data

# Drop privileges: the service handles anonymous internet traffic and
# must not run as root inside the container.
RUN useradd --create-home --uid 1001 prismql && chown -R prismql /app
USER prismql

ENV PORT=8901
CMD ["sh", "-c", "prismql-server --config demo/prismql.toml --port ${PORT}"]
