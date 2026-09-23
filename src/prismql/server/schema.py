"""What a loaded corpus holds and can answer: fields, values, capabilities.

PrismQL is schema-on-read — documents are free-form dicts — so the schema is
read off the loaded events: every event when the backend holds them (memory),
a sample otherwise. The server computes it once per load (graph
@aleph/prismql, #86); ``GET /schema``, the board's corpus card and the REPL's
``\\schema`` read the same payload.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

SCHEMA_SAMPLE_CAP = 1000  # events read when the backend cannot hand over all
EXAMPLES_MAX_CARDINALITY = 20  # `examples` (sorted) only for small value sets
TOP_N = 10  # `top`: the most frequent values with their counts
DISTINCT_CAP = 1000  # past this many distinct values a field lists none


def _events(backend: Any) -> tuple[list[dict[str, Any]], bool]:
    docs = getattr(backend, "documents", None)
    if isinstance(docs, list):
        return docs, True
    ids = list(backend.get_all_document_ids(limit=SCHEMA_SAMPLE_CAP))
    return (backend.get_documents(ids) if ids else []), False


def _field_stats(docs: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """name -> [events holding the key, value type names, Counter or None]."""
    stats: dict[str, list[Any]] = {}
    for doc in docs:
        for key, value in doc.items():
            st = stats.get(key)
            if st is None:
                st = stats[key] = [0, set(), Counter()]
            st[0] += 1
            if value is None:
                continue
            st[1].add(type(value).__name__)
            counter = st[2]
            if counter is not None:
                text = str(value)
                if text in counter or len(counter) < DISTINCT_CAP:
                    counter[text] += 1
                else:
                    st[2] = None  # too many values to list honestly
    return stats


def _field_info(
    present: int, types: set[str], counter: Counter[str] | None, n: int
) -> dict[str, Any]:
    info: dict[str, Any] = {
        "coverage": round(present / n, 3) if n else 0.0,
        "type": next(iter(types)) if len(types) == 1 else "mixed",
    }
    if counter is None:
        info["distinct"] = None
        info["distinct_over"] = DISTINCT_CAP
        return info
    info["distinct"] = len(counter)
    # a value per event (an id, free text) is not a vocabulary worth listing
    if counter and not (len(counter) == present == n):
        info["top"] = [[v, c] for v, c in counter.most_common(TOP_N)]
        if len(counter) <= EXAMPLES_MAX_CARDINALITY:
            info["examples"] = sorted(counter)[:10]
    return info


def text_search(backend: Any) -> str:
    """Which index answers text predicates: a full-text one or Python's."""
    if getattr(backend, "text_index", None) is not None:
        return "tantivy"
    return "tantivy" if type(backend).__name__ == "TantivyBackend" else "memory"


def _capabilities(backend: Any) -> dict[str, Any]:
    index = getattr(backend, "semantic_index", None)
    model = getattr(getattr(index, "embedder", None), "model_name", None)
    try:
        import tantivy  # noqa: F401

        search = True
    except ImportError:
        search = text_search(backend) == "tantivy"
    return {
        "similar": {"available": index is not None, "model": model},
        "search": search,
    }


def _dictionary_terms(dictionaries: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for name, value in dictionaries.items():
        if isinstance(value, dict):
            out[name] = {"terms": list(value["terms"]), "match": value.get("match")}
        else:
            out[name] = {"terms": list(value), "match": None}
    return out


def compute_schema(engine: Any, config: Any) -> dict[str, Any]:
    """The corpus schema: fields with coverage, type, distinct count and the
    most frequent values; what the corpus can answer; its dictionaries."""
    backend = engine.search_backend
    docs, complete = _events(backend)
    n = len(docs)
    fields = {
        key: _field_info(present, types, counter, n)
        for key, (present, types, counter) in sorted(_field_stats(docs).items())
    }
    return {
        "backend": type(backend).__name__,
        "documents": backend.get_total_documents(),
        "sampled": n,
        "complete": complete,
        "id_field": config.id_field,
        "timestamp_field": config.timestamp_field,
        "text_match": config.text_match,
        "text_search": text_search(backend),
        "text_language": config.text_language,
        "quantifier_ceiling": config.quantifier_ceiling,
        "fields": fields,
        "dictionaries": {
            name: len(value["terms"] if isinstance(value, dict) else value)
            for name, value in config.dictionaries.items()
        },
        "dictionary_terms": _dictionary_terms(config.dictionaries),
        "capabilities": _capabilities(backend),
        "board": dict(getattr(config, "board_fields", {}) or {}),
    }
