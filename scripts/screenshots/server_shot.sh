#!/bin/bash
# Render a real server interaction for the README screenshot.
# Starts an actual prismql-server, waits for it, runs the curls shown.
set -euo pipefail
cd "$(dirname "$0")"

PORT=8931
PROMPT=$'\e[1;32m\xe2\x9d\xaf\e[0m'
DIM=$'\e[2m'
RESET=$'\e[0m'

cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT

echo "$PROMPT prismql-server --config prismql.toml &"
uv run --project ../.. prismql-server --config prismql.toml >server.log 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 50); do
  curl -s "localhost:$PORT/health" >/dev/null 2>&1 && break
  sleep 0.1
done
grep -m1 "Uvicorn running" server.log | sed "s/^/${DIM}/;s/$/${RESET}/" || true
echo

echo "$PROMPT curl -s :$PORT/evaluate -d '{\"query\":"
echo "      \"SELECT contains(sanctions) FOLLOWED_BY contains(panic) DURING 4 hours\"}' | jq"
curl -s "localhost:$PORT/evaluate" \
  -H 'content-type: application/json' \
  -d '{"query": "SELECT contains(sanctions) FOLLOWED_BY contains(panic) DURING 4 hours"}' | jq .
rm -f server.log
