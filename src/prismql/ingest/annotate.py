"""Text annotation — a step of layer 1, not of a backend (graph
@aleph/prismql, #106).

A corpus is annotated once: at ingest (``prismql ingest … --annotate``
writes the columns ``is_question`` and ``entities``) or, for questions only,
once at load when the column is missing. The engine reads the result as
``PrecomputedIndexes``, so every backend answers ``is_question()`` and the
entity predicates the same way.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from ..backends.base import PrecomputedIndexes
from ..types import MessageId

# '?' followed by the end, whitespace or closing punctuation: '?id=7' in a URL
# or query string is not a question (graph @aleph/prismql, #94).
_QUESTION_MARK = re.compile(r"\?(?=$|[\s)\]}\"'»”’.,;:!?])")
_QUESTION_WORDS = (
    "what", "who", "when", "where", "why", "how", "which", "can", "could",
    "would", "should", "do", "does", "did", "is", "are", "was", "were", "will",
)  # fmt: skip


def is_question(text: str) -> bool:
    """A clause-ending '?', or a question word opening the text."""
    if _QUESTION_MARK.search(text):
        return True
    lowered = text.lower().strip()
    return any(lowered.startswith(w + " ") for w in _QUESTION_WORDS)


def question_ids(
    docs: Iterable[dict[str, Any]], *, id_field: str, text_fields: Sequence[str]
) -> set[MessageId]:
    """Ids of the documents any of whose text fields is a question."""
    return {
        doc[id_field]
        for doc in docs
        if any(doc.get(f) is not None and is_question(str(doc[f])) for f in text_fields)
    }


def indexes_from_columns(
    docs: Sequence[dict[str, Any]], *, id_field: str
) -> PrecomputedIndexes | None:
    """The annotation columns an ingest wrote, as the engine's indexes; None
    when the documents carry neither ``is_question`` nor ``entities``."""
    has_questions = any("is_question" in d for d in docs[:1])
    has_entities = any("entities" in d for d in docs[:1])
    if not (has_questions or has_entities):
        return None
    entities: dict[str, set[MessageId]] = {}
    if has_entities:
        for doc in docs:
            for label in doc.get("entities") or ():
                entities.setdefault(str(label), set()).add(doc[id_field])
    questions = (
        {d[id_field] for d in docs if d.get("is_question")} if has_questions else None
    )
    return PrecomputedIndexes(entities=entities, questions=questions)
