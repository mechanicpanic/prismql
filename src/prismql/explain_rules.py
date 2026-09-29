"""Which conditions of a query can explain an event, and how each is
matched (graph @aleph/prismql, #119) — the IR side of ``explain``."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any

from .ir.nodes import (
    Contains,
    ContainsPhrase,
    ContainsTokens,
    FieldMatch,
    Literal,
    Not,
    SequenceLink,
    SimilarTo,
    SubqueryChain,
)


@dataclass(frozen=True)
class TextRule:
    label: str
    terms: tuple[str, ...]
    mode: str  # "stem" | "token" | "substring"
    phrase: bool = False  # contains_phrase: always a phrase


def rule_for(engine: Any, leaf: Any) -> tuple[str, Any] | None:
    if isinstance(leaf, Contains | ContainsTokens) and isinstance(
        leaf.dict_name, Literal
    ):
        name = leaf.dict_name.text
        terms = tuple(engine.user_dictionaries.get(name, ()))
        if isinstance(leaf, ContainsTokens):
            return "text", TextRule(f"contains_tokens({name})", terms, "token")
        mode = engine.dictionary_modes.get(name, engine.text_match)
        return "text", TextRule(f"contains({name})", terms, mode)
    if isinstance(leaf, ContainsPhrase):
        label = f'contains_phrase("{leaf.phrase}")'
        return "text", TextRule(label, (leaf.phrase,), "token", phrase=True)
    if isinstance(leaf, FieldMatch) and isinstance(leaf.value, Literal):
        return "field", (f"field({leaf.field_name}, {leaf.value.text})", leaf)
    if isinstance(leaf, SimilarTo):
        return "similar", (f'similar_to("{leaf.text}", {leaf.threshold})', leaf)
    return None


def field_holds(fm: FieldMatch, doc: dict[str, Any]) -> bool:
    value = doc.get(fm.field_name)
    if value is None or not isinstance(fm.value, Literal):
        return False
    want = fm.value.text.lower()
    haves = (
        [str(v).lower() for v in value]
        if isinstance(value, list | tuple)
        else [str(value).lower()]
    )
    return any(h == want if fm.exact else want in h for h in haves)


def leaves(node: Any) -> list[Any]:
    """Condition leaves in query order, none from an excluded side."""
    if isinstance(node, Not):
        return []
    if isinstance(node, SequenceLink) and node.op.startswith("NOT"):
        return leaves(node.lhs)
    if isinstance(node, SubqueryChain):
        kept = [
            c.query for c in node.continuations if not (c.op or "").startswith("NOT")
        ]
        return leaves(node.head) + leaves(kept)
    if isinstance(
        node, Contains | ContainsTokens | ContainsPhrase | FieldMatch | SimilarTo
    ):
        return [node]
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        out: list[Any] = []
        for f in dataclasses.fields(node):
            out.extend(leaves(getattr(node, f.name)))
        return out
    if isinstance(node, tuple | list):
        return [leaf for x in node for leaf in leaves(x)]
    return []
