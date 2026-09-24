"""Why an event is in a result (graph @aleph/prismql, #119).

An ``Explainer`` is built from a query's IR and the engine that ran it, and
kept beside the stored result, so a page asked for later can still say, for
each event, which of the query's conditions it satisfies: for text
conditions the terms, fields and character offsets that matched, for
``similar_to`` the cosine, for ``field`` the name. Conditions under ``NOT``
are skipped — an event is never in a result because of what it lacks.

Offsets come from the same cutting of text into words as the index
(``prismql.tokenizers``) and, in ``stem`` mode, the same Snowball stemmer;
a multi-word term, or a term the tokenizer splits (``sign-in``), is a run
of consecutive tokens. ``tests/test_explain.py`` holds the explanation to
the index: every event a ``contains`` finds is explained.
"""

from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from typing import Any

from .config import DEFAULT_CONFIG
from .ir.nodes import (
    Contains,
    ContainsPhrase,
    ContainsTokens,
    FieldMatch,
    Literal,
    Not,
    SequenceLink,
    SimilarTo,
)
from .tokenizers import _UNICODE_TOKEN_PATTERN


@dataclass(frozen=True)
class _TextRule:
    label: str
    terms: tuple[str, ...]
    mode: str  # "stem" | "token" | "substring"


@dataclass
class Explainer:
    text_rules: list[_TextRule] = field(default_factory=list)
    field_rules: list[tuple[str, FieldMatch]] = field(default_factory=list)
    similar_rules: list[tuple[str, SimilarTo]] = field(default_factory=list)
    text_fields: tuple[str, ...] = tuple(DEFAULT_CONFIG.text_fields)
    stemmer: Any = None
    semantic_index: Any = None
    # the rule order as the query reads, for the output
    order: list[tuple[str, int]] = field(default_factory=list)
    _query_vectors: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(cls, engine: Any, ir: Any) -> Explainer:
        backend = engine.search_backend
        ex = cls(
            text_fields=tuple(
                getattr(getattr(backend, "config", None), "text_fields", None)
                or DEFAULT_CONFIG.text_fields
            ),
            semantic_index=getattr(backend, "semantic_index", None),
        )
        language = getattr(backend, "text_language", "english")
        try:
            import snowballstemmer

            ex.stemmer = snowballstemmer.stemmer(language)
        except (ImportError, KeyError):
            ex.stemmer = None
        for leaf in _leaves(ir):
            ex._add(engine, leaf)
        return ex

    def _add(self, engine: Any, leaf: Any) -> None:
        if isinstance(leaf, Contains | ContainsTokens) and isinstance(
            leaf.dict_name, Literal
        ):
            name = leaf.dict_name.text
            terms = tuple(engine.user_dictionaries.get(name, ()))
            if isinstance(leaf, ContainsTokens):
                label, mode = f"contains_tokens({name})", "token"
            else:
                label = f"contains({name})"
                mode = engine.dictionary_modes.get(name, engine.text_match)
            self.order.append(("text", len(self.text_rules)))
            self.text_rules.append(_TextRule(label, terms, mode))
        elif isinstance(leaf, ContainsPhrase):
            self.order.append(("text", len(self.text_rules)))
            self.text_rules.append(
                _TextRule(f'contains_phrase("{leaf.phrase}")', (leaf.phrase,), "stem")
            )
        elif isinstance(leaf, FieldMatch) and isinstance(leaf.value, Literal):
            label = f"field({leaf.field_name}, {leaf.value.text})"
            self.order.append(("field", len(self.field_rules)))
            self.field_rules.append((label, leaf))
        elif isinstance(leaf, SimilarTo):
            label = f'similar_to("{leaf.text}", {leaf.threshold})'
            self.order.append(("similar", len(self.similar_rules)))
            self.similar_rules.append((label, leaf))

    def explain(
        self, doc: dict[str, Any], id_field: str = "id"
    ) -> list[dict[str, Any]]:
        """The query's conditions this event satisfies, in query order."""
        out: list[dict[str, Any]] = []
        for kind, i in self.order:
            if kind == "text":
                rule = self.text_rules[i]
                matches = self._text_matches(rule, doc)
                if matches:
                    out.append({"predicate": rule.label, "matches": matches})
            elif kind == "field":
                label, fm = self.field_rules[i]
                if _field_holds(fm, doc):
                    out.append({"predicate": label})
            else:
                label, st = self.similar_rules[i]
                score = self._score(st.text, doc.get(id_field))
                if score is not None:
                    out.append({"predicate": label, "score": round(score, 4)})
        return out

    def _norm(self, token: str, mode: str) -> str:
        token = token.lower()
        if mode == "stem" and self.stemmer is not None:
            return str(self.stemmer.stemWord(token))
        return token

    def _text_matches(
        self, rule: _TextRule, doc: dict[str, Any]
    ) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for fname in self.text_fields:
            value = doc.get(fname)
            if value is None:
                continue
            text = str(value)
            tokens = [
                (m.group(0), m.start(), m.end())
                for m in _UNICODE_TOKEN_PATTERN.finditer(text)
            ]
            for term in rule.terms:
                parts = [m.group(0) for m in _UNICODE_TOKEN_PATTERN.finditer(term)]
                if rule.mode == "substring" and len(parts) == 1:
                    for m in re.finditer(re.escape(term), text, re.IGNORECASE):
                        matches.append(_match(term, fname, m.start(), m.end()))
                    continue
                # a phrase or a split term matches in stem form, as the index does
                mode = rule.mode if len(parts) == 1 else "stem"
                want = [self._norm(p, mode) for p in parts]
                if not want:
                    continue
                normed = [self._norm(t, mode) for t, _, _ in tokens]
                n = len(want)
                for k in range(len(normed) - n + 1):
                    if normed[k : k + n] == want:
                        matches.append(
                            _match(term, fname, tokens[k][1], tokens[k + n - 1][2])
                        )
        matches.sort(key=lambda m: (m["field"], m["start"]))
        return matches

    def _score(self, text: str, doc_id: Any) -> float | None:
        index = self.semantic_index
        if index is None or doc_id is None:
            return None
        vector = self._query_vectors.get(text)
        if vector is None:
            vector = self._query_vectors[text] = index.query_vector(text)
        score: float | None = index.cosine(vector, doc_id)
        return score


def _match(term: str, fname: str, start: int, end: int) -> dict[str, Any]:
    return {"term": term, "field": fname, "start": start, "end": end}


def _field_holds(fm: FieldMatch, doc: dict[str, Any]) -> bool:
    value = doc.get(fm.field_name)
    if value is None or not isinstance(fm.value, Literal):
        return False
    have, want = str(value).lower(), fm.value.text.lower()
    return have == want if fm.exact else want in have


def _leaves(node: Any) -> list[Any]:
    """Condition leaves in query order, none from under a NOT (nor the
    right side of a NOT_FOLLOWED_BY / NOT_PRECEDED_BY link)."""
    if isinstance(node, Not):
        return []
    if isinstance(node, SequenceLink) and node.op.startswith("NOT"):
        return _leaves(node.lhs)
    if isinstance(
        node, Contains | ContainsTokens | ContainsPhrase | FieldMatch | SimilarTo
    ):
        return [node]
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        out: list[Any] = []
        for f in dataclasses.fields(node):
            out.extend(_leaves(getattr(node, f.name)))
        return out
    if isinstance(node, tuple | list):
        return [leaf for x in node for leaf in _leaves(x)]
    return []
