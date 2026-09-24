"""Who a message addresses (graph @aleph/prismql, #121): ``@`` followed by a
name one of the corpus's authors has — the longest that fits, any case —
marks a mention. An address like ``cy@bob.org`` is not one (a word character
or a dot right before ``@``), nor ``@bobby`` for ``bob`` (the name must end
there).

The engine reads mentions from a ``mentions`` column (``prismql ingest …
--annotate mentions``) or, without one, finds them once in the events'
text fields and keeps them on the events, so the operator layer reads them
by position like any field.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Iterable, Sequence
from typing import Any

from .exceptions import PrismQLRuntimeError
from .types import MessageId

MENTIONS_FIELD = "mentions"
_lock = threading.Lock()


class Names:
    """The corpus's author names as one pattern, longest first, and each
    name's own spelling by its lower-case form."""

    def __init__(self, names: Iterable[str]) -> None:
        unique = sorted({n for n in names if n}, key=len, reverse=True)
        self.canon = {n.lower(): n for n in unique}
        alts = "|".join(re.escape(n) for n in unique)
        self.rx = (
            re.compile(rf"(?<![\w.])@({alts})(?![\w-]|\.\w)", re.IGNORECASE)
            if unique
            else None
        )


def mention_pattern(names: Iterable[str]) -> Names:
    return Names(names)


def find_mentions(text: str, names: Names) -> list[str]:
    """The names ``text`` addresses, in order, each once, spelled as the
    author value, not as typed."""
    if names.rx is None or "@" not in text:
        return []
    out: list[str] = []
    for m in names.rx.finditer(text):
        name = names.canon.get(m.group(1).lower(), m.group(1))
        if name not in out:
            out.append(name)
    return out


class Mentions:
    """Every event's mentions, the column the operator layer reads them
    from, and the events mentioning each name."""

    def __init__(
        self, field: str, ids: Sequence[MessageId], lists: Sequence[Any]
    ) -> None:
        self.field = field
        self.by_name: dict[str, set[MessageId]] = {}
        self.any: set[MessageId] = set()
        for doc_id, names in zip(ids, lists, strict=True):
            for name in names or []:
                self.by_name.setdefault(str(name).lower(), set()).add(doc_id)
            if names:
                self.any.add(doc_id)

    def ids(self, name: str) -> set[MessageId]:
        return self.by_name.get(name.lower(), set())


def _refuse(why: str) -> PrismQLRuntimeError:
    return PrismQLRuntimeError(
        f"mentions_user() has no backing here: {why}. Annotate at ingest "
        "(prismql ingest … --annotate mentions --actor <author column>) and "
        "load that file."
    )


def mentions_of(
    backend: Any,
    actor_field: str,
    text_fields: Sequence[str],
    column: str | None = None,
) -> Mentions:
    """The corpus's mentions, kept on the backend. ``column`` names an
    ingest-stamped ``mentions`` column, read as it is; without one they are
    found once in the text and written onto the events under a field of
    their own (``_mentions:<actor field>``), never over the user's data —
    which only a backend that reads fields from its events can hold."""
    field = column or f"_mentions:{actor_field}"
    with _lock:
        cache: dict[str, Mentions] = backend.__dict__.setdefault(
            "_prismql_mentions", {}
        )
        if field in cache:
            return cache[field]
        positions = list(range(backend.get_total_documents()))
        ids = backend.ids_at(positions)
        values_at = getattr(backend, "values_at", None)
        if column is not None:
            lists = values_at(positions, column) if values_at is not None else None
            if lists is None:
                raise _refuse(
                    f"this backend cannot read the {column!r} column by position"
                )
        else:
            docs = getattr(backend, "documents", None)
            if not isinstance(docs, list) or values_at is None:
                raise _refuse("this index keeps no events to write mentions onto")
            names = mention_pattern(
                str(d[actor_field]) for d in docs if d.get(actor_field) is not None
            )
            for d in docs:
                found: list[str] = []
                for f in text_fields:
                    if d.get(f) is not None:
                        found += [
                            n for n in find_mentions(str(d[f]), names) if n not in found
                        ]
                d[field] = found
            lists = values_at(positions, field)
            if lists is None or (docs and lists[0] != docs[0][field]):
                raise _refuse("this backend does not read fields from its events")
        result = Mentions(field, ids, lists)
        cache[field] = result
        return result
