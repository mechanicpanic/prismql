"""Why an event is in a result (graph @aleph/prismql, #119).

An ``Explainer`` is built from a query's IR and the engine that ran it, and
kept beside the stored result, so a page asked for later can still say, for
each event, which of the query's conditions it satisfies: for text
conditions the terms, fields and character offsets that matched (found by
``explain_text`` under the index's own rules), for ``similar_to`` the cosine
when it clears the threshold, for ``field`` the name. Conditions on the
excluded side — under ``NOT``, right of a ``NOT_FOLLOWED_BY`` — are left
out: an event is never in a result because of what it lacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import DEFAULT_CONFIG
from .explain_rules import field_holds, leaves, rule_for
from .explain_text import fields_of, term_spans


@dataclass
class Explainer:
    rules: list[tuple[str, Any]] = field(default_factory=list)  # (kind, rule)
    text_fields: tuple[str, ...] = tuple(DEFAULT_CONFIG.text_fields)
    language: str = "english"
    semantic_index: Any = None
    _query_vectors: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(cls, engine: Any, ir: Any) -> Explainer:
        backend = engine.search_backend
        config = getattr(backend, "config", None)
        ex = cls(
            text_fields=tuple(
                getattr(config, "text_fields", None) or DEFAULT_CONFIG.text_fields
            ),
            language=getattr(backend, "text_language", "english"),
            semantic_index=getattr(backend, "semantic_index", None),
        )
        for leaf in leaves(ir):
            rule = rule_for(engine, leaf)
            if rule is not None:
                ex.rules.append(rule)
        return ex

    @property
    def nbytes(self) -> int:
        """A rough size for the result store's budget: the terms dominate."""
        size = 512
        for kind, rule in self.rules:
            if kind == "text":
                size += 64 * len(rule.terms) + sum(len(t) for t in rule.terms)
        return size

    def explain(
        self, doc: dict[str, Any], id_field: str = "id"
    ) -> list[dict[str, Any]]:
        """The query's conditions this event satisfies, in query order."""
        out: list[dict[str, Any]] = []
        fields = fields_of(doc, self.text_fields, self.language)
        for kind, rule in self.rules:
            if kind == "text":
                matches = [
                    {"term": term, "field": f, "start": s, "end": e}
                    for term in rule.terms
                    for f, s, e in term_spans(
                        term, rule.mode, fields, self.language, phrase=rule.phrase
                    )
                ]
                if matches:
                    matches.sort(key=lambda m: (m["field"], m["start"], m["end"]))
                    out.append({"predicate": rule.label, "matches": matches})
            elif kind == "field":
                label, fm = rule
                if field_holds(fm, doc):
                    out.append({"predicate": label})
            else:
                label, st = rule
                score = self._score(st.text, doc.get(id_field))
                if score is not None and score >= st.threshold:
                    out.append({"predicate": label, "score": round(score, 4)})
        return out

    def _score(self, text: str, doc_id: Any) -> float | None:
        index = self.semantic_index
        if index is None or doc_id is None:
            return None
        vector = self._query_vectors.get(text)
        if vector is None:
            vector = self._query_vectors[text] = index.query_vector(text)
        score: float | None = index.cosine(vector, doc_id)
        return score
