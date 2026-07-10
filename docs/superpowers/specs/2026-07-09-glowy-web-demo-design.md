# PrismQL live web demo ("the glowy demo") — design

**Date:** 2026-07-09
**Status:** approved (brainstorm with Aleph)
**Replaces:** the Streamlit demo as the public-facing showcase (Streamlit
demo stays in-repo for local use until explicitly retired).

## Purpose & audience

A live, hosted demo at Aleph's domain, primarily for **paper reviewers and
DB researchers**. A visitor should leave thinking: *the language is real,
runs live over real data, and the two surface syntaxes are provably
equivalent.* Cute but credible: one restrained spectral-glow visual
language, no toy vibes.

Hosting: **Railway** (Aleph has an account), custom domain via Railway's
domain flow + CNAME. Deployed with `railway up` from the laptop — the
GitHub repo stays private.

## Approach (decided)

**One FastAPI deployable, hand-rolled static frontend.** No React, no
build step, no Node. The existing `prismql.server` app serves both the
API and the page. Rejected: React/Vite SPA (build pipeline for one page),
Streamlit restyle (cannot fix its per-interaction rerun latency).

## Components

### 1. Backend (src/prismql/server/) — small, real product value

- **Named corpora.** `ServerConfig` grows `[corpora.<name>]` sections —
  each with its own data file, dictionaries, `field_mappings`, and
  timestamp field; `ServerState` holds one warm engine per corpus.
  `/evaluate` and `/schema` take an optional `corpus` parameter.
  **Backwards compatible:** existing single-corpus configs keep working
  (they define an implicit default corpus).
- **Static mount.** When the config names a demo directory, mount it with
  `StaticFiles` at `/` (API routes take precedence).
- **Guardrails:** server-side ceiling on `max_results`; per-IP rate
  limit; corpora sized so the worst legal query stays under ~1 s
  (bounded compute by construction — no thread-killing).

### 2. Frontend (demo/web/: index.html, style.css, app.js)

Visual language: near-black background, one spectral accent gradient
(violet→cyan), soft glows on focus/results. Prism motif: a thin white
beam enters the header prism and refracts into the gradient; the same
gradient lights result groups.

Layout, top to bottom:

1. **Header** — animated prism + one-line tagline.
2. **Corpus tabs** — "freeCodeCamp chat" / "Chicago crime events".
3. **Editor** — live token highlighting for both dialects (hand-rolled
   JS highlighter reusing the pipe tokenizer's token classes), plus the
   **classic ⇄ pipe toggle**: for curated examples both forms are
   pre-authored (and IR-equal by the pipe_gold proof method); flipping
   the toggle rewrites the query in place and reruns — the dual-surface
   claim as a UI gesture. Free-form queries run under dialect auto-detect
   (toggle disabled with a hint when the text no longer matches a known
   example).
4. **Example chips** grouped by concept: sequences, temporal, pattern
   variables, negative patterns, aggregation.
5. **Results pane** — FCC: glowing chat bubbles, matched messages lit,
   group boundaries visible; Chicago: timeline event cards. Latency
   badge per run. Syntax errors render the validator's teachable
   messages verbatim.

Not in v1 (easy later): "show IR" nerd toggle, shareable query URLs.

### 3. Data (demo/data/)

One export script produces two JSON corpora, both publishable:

- **FCC situations subset** (Aleph's own annotated freeCodeCamp Gitter
  data): ~5k messages — id, user, text, timestamp.
- **Chicago slice** (public domain): ~50k events — id, primary type,
  timestamp, location fields; `field_mappings` make `from()`/`field()`
  sensible for events.

### 4. Deploy

Root `Dockerfile` (uv-based: install `prismql[server]`, copy demo config
+ web + data; CMD runs uvicorn). Railway service → generated URL →
custom domain + CNAME. **Ship gate:** nothing deploys until Aleph says
ship; DNS changes are Aleph's.

## Testing

- Unit tests: multi-corpus config parsing, `corpus` param on
  /evaluate + /schema, backwards compat of single-corpus configs,
  static mount, guardrail caps.
- Local end-to-end before any deploy: server + page + real queries on
  both corpora, both dialects, error paths.

## Decisions log

- Audience: paper reviewers / DB researchers (over general playground).
- Corpora: FCC subset + Chicago slice (over synthetic support chat).
- Approach A (vanilla static + FastAPI) over React SPA and Streamlit
  restyle.
- Domain name: provided by Aleph at deploy time.
