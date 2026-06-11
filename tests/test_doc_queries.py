"""Every PrismQL example in the docs must actually parse.

Extracts all ```prismql fenced blocks from the shipped reference and the
repo docs and runs them through the real parser. Statements preceded by a
comment containing ❌ or WRONG are skipped (they document mistakes, some of
which are semantic and still parse) — everything else must be valid.

This exists because the docs accumulated fictional syntax for years
(INWINDOW 5 minutes, mentions_place(Paris), parenless AFTER, chained
negative lookarounds) that silently parsed before the grammar's entry rule
was EOF-anchored.
"""

import re
from pathlib import Path

import pytest

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLSyntaxError

REPO_ROOT = Path(__file__).resolve().parents[1]

DOC_FILES = [
    "src/prismql/LANGUAGE_REFERENCE.md",
    "QUICK_REFERENCE.md",
    "README.md",
    "WHY_NOT_SQL.md",
    "docs/REPL.md",
    "docs/SYNTAX_HIGHLIGHTING.md",
    "skills/prismql/LANGUAGE_REFERENCE.md",
]


def extract_statements(path: Path) -> list[tuple[str, bool]]:
    """Return (statement, expected_valid) pairs from ```prismql blocks."""
    text = path.read_text(encoding="utf-8")
    statements: list[tuple[str, bool]] = []
    for block in re.findall(r"```prismql\n(.*?)```", text, re.S):
        lines: list[tuple[str, bool]] = []  # (content, marked_wrong)
        marked_wrong = False
        for raw in block.splitlines():
            line = re.sub(r"\s--.*$", "", raw)
            if raw.strip().startswith("--") or not line.strip():
                marked_wrong = "❌" in raw or "WRONG" in raw.upper()
                lines.append(("", marked_wrong))
            else:
                lines.append((line, marked_wrong))
        current: list[str] = []
        current_wrong = False
        for content, wrong in lines:
            if not content:
                if current:
                    statements.append((" ".join(current), not current_wrong))
                    current = []
                current_wrong = wrong or current_wrong if current else wrong
            elif re.match(r"SELECT\b", content) and current:
                statements.append((" ".join(current), not current_wrong))
                current = [content]
                current_wrong = wrong
            else:
                if not current:
                    current_wrong = wrong
                current.append(content)
        if current:
            statements.append((" ".join(current), not current_wrong))
    # Only real, complete queries — skip syntax skeletons with placeholders
    return [
        (s, ok)
        for s, ok in statements
        if "SELECT" in s and "<" not in s and "restriction1" not in s
    ]


@pytest.fixture(scope="module")
def engine():
    return PrismQLEngine(MemoryBackend(documents=[{"id": 1, "user": "a", "text": "t"}]))


@pytest.mark.parametrize("doc", DOC_FILES)
def test_all_doc_queries_parse(engine, doc):
    path = REPO_ROOT / doc
    if not path.exists():
        pytest.skip(f"{doc} not present")
    failures = []
    checked = 0
    for statement, expected_valid in extract_statements(path):
        if not expected_valid:
            continue  # documented mistakes; some are semantic and parse fine
        checked += 1
        try:
            engine.validate(statement)
        except PrismQLSyntaxError as e:
            failures.append(f"  {statement[:110]}\n    -> {str(e)[:90]}")
    assert checked > 0, f"no queries extracted from {doc} — extractor broken?"
    assert not failures, f"{doc}:\n" + "\n".join(failures)
