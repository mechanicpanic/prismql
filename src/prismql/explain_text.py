"""Where a text condition matched inside an event, by the index's own rules
(graph @aleph/prismql, #60 for the rules, #119 for the explanation).

A deliberate second reading of the matching rule, not a second rule: the
backends answer "which events", never "where in the text", so the offsets
are found here, and tests hold them to what the engine returns. The rules,
as both backends apply them:

- a term with a space is a phrase: its plain (unstemmed, lower-case)
  tokens, adjacent and in order, in the ``text`` field only;
- a term without a space, in ``stem`` mode: its Snowball stems, in every
  text field; several tokens (``sign-in``) must be adjacent;
- the same in ``token`` mode, on plain tokens;
- in ``substring`` mode: a case-insensitive substring of ``text``, or the
  term as whole words in any text field.
"""

from __future__ import annotations

import re
import threading
from typing import Any

from .tokenizers import _UNICODE_TOKEN_PATTERN

PHRASE_FIELD = "text"
_local = threading.local()


def stemmer(language: str) -> Any:
    """A Snowball stemmer for this thread — the stemmer keeps state between
    calls, so one shared across request threads could mix words."""
    cache: dict[str, Any] = getattr(_local, "stemmers", None) or {}
    _local.stemmers = cache
    if language not in cache:
        try:
            import snowballstemmer

            cache[language] = snowballstemmer.stemmer(language)
        except (ImportError, KeyError):
            cache[language] = None
    return cache[language]


def _tokens(text: str) -> list[tuple[str, int, int]]:
    return [
        (m.group(0).lower(), m.start(), m.end())
        for m in _UNICODE_TOKEN_PATTERN.finditer(text)
    ]


class _Field:
    """One field's tokens, normalized once and indexed by value."""

    def __init__(self, text: str, language: str) -> None:
        self.text = text
        self.tokens = _tokens(text)
        self.language = language
        self._by: dict[str, dict[str, list[int]]] = {}

    def positions(self, norm: str) -> dict[str, list[int]]:
        if norm not in self._by:
            st = stemmer(self.language) if norm == "stem" else None
            index: dict[str, list[int]] = {}
            for k, (tok, _, _) in enumerate(self.tokens):
                key = st.stemWord(tok) if st is not None else tok
                index.setdefault(key, []).append(k)
            self._by[norm] = index
        return self._by[norm]


def _run(f: _Field, keys: list[str], norm: str) -> list[tuple[int, int]]:
    """Spans where ``keys`` occur as adjacent tokens."""
    index = f.positions(norm)
    starts = index.get(keys[0], [])
    if len(keys) == 1:
        return [(f.tokens[k][1], f.tokens[k][2]) for k in starts]
    later = [set(index.get(key, ())) for key in keys[1:]]
    out = []
    for k in starts:
        if all(k + j in s for j, s in enumerate(later, 1)):
            out.append((f.tokens[k][1], f.tokens[k + len(keys) - 1][2]))
    return out


def _keys(term: str, norm: str, language: str) -> list[str]:
    st = stemmer(language) if norm == "stem" else None
    return [st.stemWord(t) if st is not None else t for t, _, _ in _tokens(term)]


def term_spans(
    term: str,
    mode: str,
    fields: dict[str, _Field],
    language: str,
    *,
    phrase: bool = False,
) -> list[tuple[str, int, int]]:
    """(field, start, end) of each place ``term`` matched."""
    out: list[tuple[str, int, int]] = []
    if phrase or " " in term.strip():
        keys = _keys(term, "plain", language)
        if keys and PHRASE_FIELD in fields:
            out += [
                (PHRASE_FIELD, s, e)
                for s, e in _run(fields[PHRASE_FIELD], keys, "plain")
            ]
        return out
    if mode == "substring":
        text_field = fields.get(PHRASE_FIELD)
        if text_field is not None:
            for m in re.finditer(re.escape(term), text_field.text, re.IGNORECASE):
                out.append((PHRASE_FIELD, m.start(), m.end()))
        keys = _keys(term, "plain", language)
        for name, f in fields.items():
            if name != PHRASE_FIELD and keys:
                out += [(name, s, e) for s, e in _run(f, keys, "plain")]
        return out
    norm = "stem" if mode == "stem" else "plain"
    keys = _keys(term, norm, language)
    if keys:
        for name, f in fields.items():
            out += [(name, s, e) for s, e in _run(f, keys, norm)]
    return out


def fields_of(
    doc: dict[str, Any], names: tuple[str, ...], language: str
) -> dict[str, _Field]:
    return {n: _Field(str(doc[n]), language) for n in names if doc.get(n) is not None}
