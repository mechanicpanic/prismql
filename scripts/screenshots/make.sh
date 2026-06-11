#!/bin/bash
# Regenerate the README terminal screenshots (docs/assets/*.svg).
# Requires termframe (https://github.com/pamburus/termframe) and jq.
# Everything in the frames is real output: repl_shot.py runs the engine,
# server_shot.sh starts an actual prismql-server and curls it.
set -euo pipefail
cd "$(dirname "$0")"
OUT=../../docs/assets

termframe \
  --title "prismql" \
  --mode dark \
  --embed-fonts true \
  -W 84 -H auto \
  -o "$OUT/repl.svg" \
  -- uv run --project ../.. python repl_shot.py

termframe \
  --title "prismql-server" \
  --mode dark \
  --embed-fonts true \
  -W 84 -H auto \
  -o "$OUT/server.svg" \
  -- ./server_shot.sh

echo "Wrote $OUT/repl.svg and $OUT/server.svg"
