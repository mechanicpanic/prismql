"""Text annotation — a step of layer 1, not of a backend (graph
@aleph/prismql, #106).

A corpus is annotated once: at ingest (``prismql ingest … --annotate``
writes the columns ``is_question``, ``has_link`` and ``entities``) or, for
questions and links, once at load when the column is missing. The engine
reads the result as ``PrecomputedIndexes``, so every backend answers
``is_question()``, ``contains_link()`` and the entity predicates the same way.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from ..backends.base import PrecomputedIndexes
from ..config import DEFAULT_CONFIG
from ..tokenizers import URL_SHAPE
from ..types import MessageId

# The text fields every annotation reads — at ingest and at load, on every
# backend — so one corpus gets one answer (graph @aleph/prismql, #106).
TEXT_FIELDS: tuple[str, ...] = tuple(DEFAULT_CONFIG.text_fields)
# Schema metadata an ingest stamps: which annotation columns it wrote. Only a
# stamped file's columns are annotations; a field that merely shares the name
# stays an ordinary field.
ANNOTATIONS_KEY = b"prismql.annotations"

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


_LINK = re.compile(URL_SHAPE, re.IGNORECASE)


def has_link(text: str) -> bool:
    """A link as the tokenizer cuts one: a scheme and what follows up to
    whitespace (graph @aleph/prismql, #115)."""
    return _LINK.search(text) is not None


def _matching_ids(
    docs: Iterable[dict[str, Any]],
    rule: Any,
    *,
    id_field: str,
    text_fields: Sequence[str],
) -> set[MessageId]:
    return {
        doc[id_field]
        for doc in docs
        if any(doc.get(f) is not None and rule(str(doc[f])) for f in text_fields)
    }


def link_ids(
    docs: Iterable[dict[str, Any]],
    *,
    id_field: str,
    text_fields: Sequence[str] = TEXT_FIELDS,
) -> set[MessageId]:
    """Ids of the documents any of whose text fields has a link."""
    return _matching_ids(docs, has_link, id_field=id_field, text_fields=text_fields)


def question_ids(
    docs: Iterable[dict[str, Any]],
    *,
    id_field: str,
    text_fields: Sequence[str] = TEXT_FIELDS,
) -> set[MessageId]:
    """Ids of the documents any of whose text fields is a question."""
    return _matching_ids(docs, is_question, id_field=id_field, text_fields=text_fields)


def indexes_from_columns(
    docs: Sequence[dict[str, Any]], *, id_field: str, kinds: Sequence[str]
) -> PrecomputedIndexes | None:
    """The columns an ingest stamped as annotations (``kinds``), as the
    engine's indexes; None when it stamped none. Only a real ``True`` is a
    question; ``entities`` must be a list of labels."""
    if not kinds:
        return None
    questions = None
    if "questions" in kinds:
        questions = {d[id_field] for d in docs if d.get("is_question") is True}
    links = None
    if "links" in kinds:
        links = {d[id_field] for d in docs if d.get("has_link") is True}
    entities: dict[str, set[MessageId]] | None = None
    if "entities" in kinds:
        entities = {}
        for doc in docs:
            labels = doc.get("entities")
            if isinstance(labels, list | tuple):
                for label in labels:
                    entities.setdefault(str(label), set()).add(doc[id_field])
    return PrecomputedIndexes(entities=entities, questions=questions, links=links)


def stamped_kinds(path: str) -> tuple[str, ...]:
    """The annotations an ingest stamped into a Parquet file; () otherwise."""
    if not str(path).endswith(".parquet"):
        return ()
    import pyarrow.parquet as pq

    raw = (pq.read_schema(path).metadata or {}).get(ANNOTATIONS_KEY, b"")
    return tuple(k for k in raw.decode().split(",") if k)


ANNOTATIONS = ("questions", "links", "mentions", "entities")


def annotate(
    df: Any,
    kinds: Sequence[str],
    *,
    text: str | None,
    spacy_model: str,
    actor: str = "user",
) -> Any:
    """Add the annotation columns ``kinds`` name to a Polars frame: bool
    ``is_question`` and ``has_link`` (the rules above) and/or ``entities``
    (spaCy NER labels present in the text, a sorted list). ``text`` names one
    column; without it every column of ``TEXT_FIELDS`` present is read, as at
    load."""
    import polars as pl

    unknown = [k for k in kinds if k not in ANNOTATIONS]
    if unknown:
        raise ValueError(f"unknown annotation {unknown[0]!r}; known: {ANNOTATIONS}")
    fields = [text] if text else [f for f in TEXT_FIELDS if f in df.columns]
    missing = [f for f in fields if f not in df.columns]
    if missing or not fields:
        raise ValueError(
            f"text column {(missing or ['text'])[0]!r} not in {df.columns}"
        )
    rows = df.select(fields).to_dicts()
    if "questions" in kinds:
        flags = [
            any(r[f] is not None and is_question(str(r[f])) for f in fields)
            for r in rows
        ]
        df = df.with_columns(pl.Series("is_question", flags, dtype=pl.Boolean))
    if "links" in kinds:
        flags = [
            any(r[f] is not None and has_link(str(r[f])) for f in fields) for r in rows
        ]
        df = df.with_columns(pl.Series("has_link", flags, dtype=pl.Boolean))
    texts = [
        "\n".join(str(r[f]) for f in fields if r[f] is not None) or None for r in rows
    ]
    if "mentions" in kinds:
        # @ and a name some event's author has (graph @aleph/prismql, #121)
        from ..mentions import find_mentions, mention_pattern

        if actor not in df.columns:
            raise ValueError(f"--actor column {actor!r} not in {df.columns}")
        names = mention_pattern(str(v) for v in df.get_column(actor).drop_nulls())
        found = [
            list(
                dict.fromkeys(
                    n
                    for f in fields
                    if r[f] is not None
                    for n in find_mentions(str(r[f]), names)
                )
            )
            for r in rows
        ]
        df = df.with_columns(pl.Series("mentions", found, dtype=pl.List(pl.Utf8)))
    if "entities" in kinds:
        labels = _entity_labels(texts, spacy_model)
        df = df.with_columns(pl.Series("entities", labels, dtype=pl.List(pl.Utf8)))
    return df


def _entity_labels(texts: Sequence[str | None], model: str) -> list[list[str]]:
    try:
        import spacy
    except ImportError as e:
        raise ImportError(
            "--annotate entities needs spaCy: uv pip install 'prismql[nlp]' "
            f"and python -m spacy download {model}"
        ) from e
    nlp = spacy.load(model, disable=["parser", "lemmatizer"])
    out: list[list[str]] = []
    for doc in nlp.pipe((t or "" for t in texts), batch_size=256):
        out.append(sorted({ent.label_ for ent in doc.ents}))
    return out
