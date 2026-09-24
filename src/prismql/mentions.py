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
    """Every event's mentions, and the events mentioning each name."""

    def __init__(self, docs: Sequence[dict[str, Any]], id_field: str) -> None:
        self.by_name: dict[str, set[MessageId]] = {}
        self.any: set[MessageId] = set()
        for doc in docs:
            names = doc.get(MENTIONS_FIELD) or []
            for name in names:
                self.by_name.setdefault(str(name).lower(), set()).add(doc[id_field])
            if names:
                self.any.add(doc[id_field])

    def ids(self, name: str) -> set[MessageId]:
        return self.by_name.get(name.lower(), set())


def mentions_of(backend: Any, actor_field: str, text_fields: Sequence[str]) -> Mentions:
    """The corpus's mentions, found once and kept on the backend: events
    that already carry a ``mentions`` list are taken as they are."""
    with _lock:
        cached = getattr(backend, "_prismql_mentions", None)
        if cached is not None and cached[0] == actor_field:
            known: Mentions = cached[1]
            return known
        docs = getattr(backend, "documents", None)
        if not isinstance(docs, list):
            raise PrismQLRuntimeError(
                "mentions_user() has no backing here: this index keeps no events "
                "to read mentions from. Annotate at ingest (prismql ingest … "
                "--annotate mentions --actor <author column>)."
            )
        id_field = getattr(backend, "id_field", "id")
        if not any(isinstance(d.get(MENTIONS_FIELD), list) for d in docs):
            pattern = mention_pattern(
                str(d[actor_field]) for d in docs if d.get(actor_field) is not None
            )
            for d in docs:
                found: list[str] = []
                for f in text_fields:
                    if d.get(f) is not None:
                        found += [
                            n
                            for n in find_mentions(str(d[f]), pattern)
                            if n not in found
                        ]
                d[MENTIONS_FIELD] = found
        result = Mentions(docs, id_field)
        backend._prismql_mentions = (actor_field, result)
        return result
