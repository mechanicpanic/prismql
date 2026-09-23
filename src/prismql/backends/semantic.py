"""Semantic similarity index backing the similar_to() predicate.

The engine is deliberately commodity: any embedder behind the ``Embedder``
protocol works (sentence-transformers, a hosted API, a test fake). The
index is exact cosine over unit-normalized vectors: one matrix product
when numpy is installed (the ``semantic`` / ``ingest`` extras bring it —
381k×384 answers in milliseconds), a pure-Python loop otherwise (fine for
a few thousand rows). An ANN index is a later ``VectorIndex`` behind the
same two calls, ``search`` and ``rank``, built from the same ``emb`` column.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Protocol

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


def _matrix(vectors: Sequence[Sequence[float]]) -> Any | None:
    """An (n, d) float32 array when numpy is installed, else None."""
    try:
        import numpy as np
    except ImportError:
        return None
    if not vectors:
        return np.zeros((0, 0), dtype=np.float32)
    return np.asarray(vectors, dtype=np.float32)


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
        self.model_name = model_name
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
        self._matrix = _matrix(self._vectors)

    @classmethod
    def from_vectors(
        cls,
        embedder: Embedder,
        ids: Sequence[MessageId],
        vectors: Sequence[Sequence[float] | None],
        text_field: str = "text",
    ) -> SemanticIndex:
        """An index over precomputed vectors (an ``emb`` column written by
        ``prismql ingest --embed``); ``embedder`` only encodes query text.
        A null or all-zero vector means "no text": that id is not indexed."""
        index = cls.__new__(cls)
        index.embedder = embedder
        index.text_field = text_field
        index._ids = []
        index._vectors = []
        index._matrix = None
        try:
            import numpy as np

            have_numpy = True
        except ImportError:
            have_numpy = False
        if have_numpy:
            # Vectorized: 381k rows normalize in well under a second, where
            # the per-row Python loop below takes tens of seconds.
            arr: Any
            if isinstance(vectors, np.ndarray):
                arr = vectors.astype(np.float32, copy=False)
            else:
                width = next((len(v) for v in vectors if v is not None), 0)
                rows = [v if v is not None else [0.0] * width for v in vectors]
                arr = np.asarray(rows, dtype=np.float32) if rows else np.zeros((0, 0))
            norms = np.linalg.norm(arr, axis=1) if len(arr) else np.zeros(0)
            keep = norms > 0
            index._ids = [i for i, k in zip(ids, keep, strict=True) if k]
            # one writable copy of the kept rows, normalized in place: the
            # caller's matrix may be a read-only view of an Arrow buffer
            matrix = arr[keep] if not keep.all() else arr.copy()
            matrix /= norms[keep, None].astype(np.float32)
            index._matrix = matrix
            return index
        for doc_id, vector in zip(ids, vectors, strict=True):
            if vector is None or not any(vector):
                continue
            index._ids.append(doc_id)
            index._vectors.append(_normalize(vector))
        return index

    def __len__(self) -> int:
        return len(self._ids)

    def _scores(self, text: str) -> Any:
        query = _normalize(self.embedder.encode([text])[0])
        if self._matrix is not None:
            import numpy as np

            return self._matrix @ np.asarray(query, dtype=np.float32)
        return [
            sum(q * v for q, v in zip(query, vector, strict=False))
            for vector in self._vectors
        ]

    def search(self, text: str, *, threshold: float) -> set[MessageId]:
        """Embed ``text`` and return ids scoring >= threshold (cosine)."""
        if not self._ids:
            return set()
        scores = self._scores(text)
        return {
            doc_id
            for doc_id, score in zip(self._ids, scores, strict=True)
            if score >= threshold
        }

    def rank(
        self, text: str, *, limit: int, threshold: float | None = None
    ) -> list[tuple[MessageId, float]]:
        """The ``limit`` best ids with their cosine, best first — scouting,
        never the algebra: predicates return sets (graph #58)."""
        return self.rank_counted(text, limit=limit, threshold=threshold)[0]

    def rank_counted(
        self, text: str, *, limit: int, threshold: float | None = None
    ) -> tuple[list[tuple[MessageId, float]], int]:
        """Like :meth:`rank`, plus the true count of matches: rows scoring
        >= ``threshold``, or every indexed row when no threshold is given
        (scouting keeps only a depth, graph #65)."""
        if not self._ids or limit <= 0:
            return [], 0
        scores = self._scores(text)
        if self._matrix is not None:
            import numpy as np

            arr = np.asarray(scores)
            k = min(limit, len(arr))
            # every row scoring at least the k-th best, ties included, then
            # best first and ties by position — as the pure-Python path does
            kth = np.partition(-arr, k - 1)[k - 1]
            cand = np.flatnonzero(-arr <= kth)
            order = cand[np.lexsort((cand, -arr[cand]))][:k]
            pairs = [(self._ids[i], float(arr[i])) for i in order]
            total = int((arr >= threshold).sum()) if threshold is not None else len(arr)
        else:
            order_list = sorted(range(len(scores)), key=lambda i: (-scores[i], i))[
                :limit
            ]
            pairs = [(self._ids[i], float(scores[i])) for i in order_list]
            total = (
                sum(1 for s in scores if s >= threshold)
                if threshold is not None
                else len(scores)
            )
        if threshold is not None:
            pairs = [(i, s) for i, s in pairs if s >= threshold]
        return pairs, total
