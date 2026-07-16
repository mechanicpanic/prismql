"""Semantic similarity index backing the similar_to() predicate.

The engine is deliberately commodity: any embedder behind the ``Embedder``
protocol works (sentence-transformers, a hosted API, a test fake). The
index is exact brute-force cosine over unit-normalized vectors in pure
Python — no numpy in the core install; at MemoryBackend scale this is
plenty, and heavier backends can implement ``search_semantic`` natively.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol

from ..types import Document, MessageId


class Embedder(Protocol):
    """Anything that turns texts into fixed-width float vectors."""

    def encode(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return one vector per input text, all the same dimension."""
        ...


def _normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0:
        return [0.0] * len(vector)
    return [x / norm for x in vector]


class SentenceTransformerEmbedder:
    """Embedder backed by a local sentence-transformers model.

    Requires the ``semantic`` extra: ``pip install 'prismql[semantic]'``.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "sentence-transformers is required for SentenceTransformerEmbedder. "
                "Install it with: pip install 'prismql[semantic]' "
                "(or supply any other Embedder implementation)"
            ) from e
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        # ndarray rows -> lists at the boundary (also pins the Any away)
        return [[float(x) for x in row] for row in self.model.encode(list(texts))]


class SemanticIndex:
    """Per-message embedding index with threshold-to-set search.

    Built once over the same ``documents``/``id_field`` inputs the backend
    constructor receives; ``search`` embeds the query and returns the set of
    message ids whose cosine similarity is >= threshold.
    """

    def __init__(
        self,
        embedder: Embedder,
        documents: Sequence[Document],
        id_field: str = "id",
        text_field: str = "text",
    ) -> None:
        self.embedder = embedder
        self.text_field = text_field

        ids: list[MessageId] = []
        texts: list[str] = []
        for doc in documents:
            doc_id = doc.get(id_field)
            if doc_id is None:
                raise ValueError(f"Document missing required '{id_field}' field")
            text = doc.get(text_field)
            if text is None or str(text) == "":
                continue
            ids.append(doc_id)
            texts.append(str(text))

        self._ids = ids
        self._vectors = [_normalize(v) for v in embedder.encode(texts)] if texts else []

    def search(self, text: str, *, threshold: float) -> set[MessageId]:
        """Embed ``text`` and return ids scoring >= threshold (cosine)."""
        if not self._ids:
            return set()
        query = _normalize(self.embedder.encode([text])[0])
        return {
            doc_id
            for doc_id, vector in zip(self._ids, self._vectors)
            if sum(q * v for q, v in zip(query, vector)) >= threshold
        }
