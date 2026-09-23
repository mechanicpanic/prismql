"""An ingested emb column reaches the semantic index as one numpy matrix,
not as Python lists of floats (graph @aleph/prismql, #95): the lists cost
about eight times the matrix, which on Village's next stream (569k x 768)
meant 10-15 GB at start for a 1.75 GB index."""

import tracemalloc

import pytest

np = pytest.importorskip("numpy")
pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from prismql.backends.semantic import SemanticIndex  # noqa: E402
from prismql.server.config import load_corpus  # noqa: E402

N, D = 20_000, 64


class _Embedder:
    def encode(self, texts: list) -> list:
        return [[1.0] + [0.0] * (D - 1) for _ in texts]


def _parquet(tmp_path) -> str:
    rng = np.random.default_rng(7)
    vectors = rng.standard_normal((N, D)).astype(np.float32)
    vectors[5] = 0.0  # a textless row: a zero vector, not indexed
    emb = pa.FixedSizeListArray.from_arrays(pa.array(vectors.ravel()), D)
    table = pa.table(
        {
            "position": pa.array(range(N), type=pa.int64()),
            "id": pa.array(range(N), type=pa.int64()),
            "text": pa.array([f"t{i}" for i in range(N)]),
            "emb": emb,
        }
    ).replace_schema_metadata({b"prismql.embed_model": b"fake"})
    path = tmp_path / "e.parquet"
    pq.write_table(table, path)
    return str(path)


def test_the_emb_column_becomes_one_float32_matrix(tmp_path):
    docs, vectors, stamp = load_corpus(_parquet(tmp_path))
    assert stamp is not None and stamp.model == "fake" and len(docs) == N
    assert isinstance(vectors, np.ndarray)
    assert vectors.shape == (N, D) and vectors.dtype == np.float32
    index = SemanticIndex.from_vectors(_Embedder(), [d["id"] for d in docs], vectors)
    assert len(index) == N - 1  # the zero row is skipped
    norms = np.linalg.norm(index._matrix, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_loading_peaks_near_the_matrix_size(tmp_path):
    path = _parquet(tmp_path)
    matrix_bytes = N * D * 4
    tracemalloc.start()
    try:
        docs, vectors, _ = load_corpus(path)
        SemanticIndex.from_vectors(_Embedder(), [d["id"] for d in docs], vectors)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    # documents (3 small fields x 20k) cost well under the matrix; the vectors
    # may be held about twice (the loaded matrix and the normalized index)
    assert peak < 4 * matrix_bytes + 12_000_000, peak
