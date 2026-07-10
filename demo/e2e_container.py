"""Container-level E2E check for the PrismQL web demo API surface.

Runs against a *running* `prismql-demo` docker container (see demo/README.md
"E2E check" section for how to launch it). Not part of the pytest suite —
run standalone with `uv run python demo/e2e_container.py [base_url]`.

Order matters: the rate-limit probe fires 65 rapid requests and poisons the
per-IP window for a minute, so it always runs last.
"""

from __future__ import annotations

import json as jsonlib
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8944"
EXAMPLES_JS = Path(__file__).parent / "web" / "examples.js"


def post(path: str, body: dict) -> tuple[int, dict]:
    data = jsonlib.dumps(body).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 (fixed http(s) BASE)
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 (fixed http(s) BASE)
            return resp.status, jsonlib.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, jsonlib.loads(e.read())


def get(path: str) -> tuple[int, bytes]:
    req = urllib.request.Request(BASE + path, method="GET")  # noqa: S310
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 (fixed http(s) BASE)
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def load_examples() -> dict:
    """Parse the `window.EXAMPLES = {...};` JS literal as JSON."""
    text = EXAMPLES_JS.read_text()
    m = re.search(r"window\.EXAMPLES\s*=\s*(\{.*\});", text, re.DOTALL)
    if not m:
        raise RuntimeError("could not locate window.EXAMPLES in examples.js")
    return jsonlib.loads(m.group(1))


failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {msg}")
    if not cond:
        failures.append(msg)


def main() -> int:
    print(f"== E2E against {BASE} ==\n")

    # -- GET / serves index.html --
    status, body = get("/")
    check(
        status == 200 and b"<html" in body.lower(),
        "GET / serves index.html (200, <html>)",
    )

    # -- GET /corpora --
    status, raw = get("/corpora")
    corpora_payload = jsonlib.loads(raw)
    check(
        status == 200 and set(corpora_payload.get("corpora", [])) == {"fcc", "chicago"},
        f"GET /corpora returns fcc+chicago (got {corpora_payload})",
    )

    # -- Examples: both dialects, both corpora --
    examples = load_examples()
    for corpus, items in examples.items():
        print(f"\n-- corpus: {corpus} ({len(items)} examples) --")
        for ex in items:
            label = ex["label"]
            s_classic, r_classic = post(
                "/evaluate", {"query": ex["classic"], "corpus": corpus}
            )
            s_pipe, r_pipe = post("/evaluate", {"query": ex["pipe"], "corpus": corpus})

            check(
                s_classic == 200 and r_classic.get("ok") is True,
                f"[{corpus}] classic ok: {label}",
            )
            check(
                s_pipe == 200 and r_pipe.get("ok") is True,
                f"[{corpus}] pipe ok: {label}",
            )

            def ids_of(payload: dict) -> list:
                return [r["ids"] for r in payload.get("results", [])]

            if r_classic.get("kind") in ("aggregate", "grouped"):
                # Validate classic based on kind
                if r_classic.get("kind") == "aggregate":
                    check(
                        r_classic.get("value") is not None
                        or r_classic.get("grouped_values"),
                        f"[{corpus}] classic non-empty (aggregate): {label}",
                    )
                else:  # grouped
                    check(
                        bool(r_classic.get("groups")),
                        f"[{corpus}] classic non-empty (grouped): {label}",
                    )
                # Validate pipe based on kind
                if r_pipe.get("kind") == "aggregate":
                    check(
                        r_pipe.get("value") is not None or r_pipe.get("grouped_values"),
                        f"[{corpus}] pipe non-empty (aggregate): {label}",
                    )
                else:  # grouped (kind equality checked below)
                    check(
                        bool(r_pipe.get("groups")),
                        f"[{corpus}] pipe non-empty (grouped): {label}",
                    )
                check(
                    r_classic.get("kind") == r_pipe.get("kind"),
                    f"[{corpus}] classic/pipe same result kind: {label}",
                )
            else:
                classic_ids = ids_of(r_classic)
                pipe_ids = ids_of(r_pipe)
                check(
                    bool(classic_ids), f"[{corpus}] classic non-empty results: {label}"
                )
                check(
                    classic_ids == pipe_ids,
                    f"[{corpus}] classic/pipe identical result ids: {label}"
                    + (
                        ""
                        if classic_ids == pipe_ids
                        else f" ({classic_ids} != {pipe_ids})"
                    ),
                )

    # -- Syntax error path --
    status, r = post("/evaluate", {"query": "SELECT from(", "corpus": "fcc"})
    check(status == 422, f"syntax error -> 422 (got {status})")
    check(
        r.get("ok") is False
        and r.get("error", {}).get("type") == "syntax"
        and r.get("error", {}).get("message"),
        f"syntax error has teachable message (got {r.get('error')})",
    )

    # -- Unknown corpus --
    status, r = post(
        "/evaluate", {"query": "SELECT from(alice)", "corpus": "nonexistent"}
    )
    check(status == 422, f"unknown corpus -> 422 (got {status})")

    # -- Rate limit (LAST: poisons the per-IP window for a minute) --
    print("\n-- rate limit probe (65 rapid requests) --")
    saw_429 = False
    for _i in range(65):
        status, r = post("/evaluate", {"query": "SELECT from(alice)", "corpus": "fcc"})
        if status == 429:
            saw_429 = True
            break
    check(saw_429, "rate limit: saw a 429 within 65 rapid requests")

    print(f"\n== {len(failures)} failure(s) ==")
    for f in failures:
        print(f" - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
