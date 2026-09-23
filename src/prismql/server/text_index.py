"""The full-text index a memory corpus answers its text predicates from.

One tantivy index per corpus, built in load order (graph @aleph/prismql,
#91): ``contains``, phrases and ``/search`` read it; the memory backend
keeps the documents, the order axis and ``substring`` mode. With
``text_index_path`` the index lives on disk next to a fingerprint of the
text it was built from and of the code that cut it into words; any other
text or code gets a rebuild, never the old index.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from ..config import DEFAULT_CONFIG
from ..tokenizers import UNICODE_WORD_SHAPES

MODES = ("tantivy", "memory")
_META_NAME = "_prismql_meta.json"  # written by TantivyBackend into its folder


def _tantivy_installed() -> bool:
    try:
        import tantivy  # noqa: F401
    except ImportError:
        return False
    return True


def _mode(config: Any) -> str:
    mode: str | None = config.text_index
    if mode is not None and mode not in MODES:
        raise ValueError(f"text_index must be one of {MODES}; got {mode!r}")
    if mode == "tantivy" and config.text_match == "substring":
        raise ValueError(
            "text_index = 'tantivy' cannot answer text_match = 'substring' "
            "(tantivy matches whole tokens); use text_index = 'memory'"
        )
    if mode is None:
        substring = config.text_match == "substring"
        return "memory" if substring or not _tantivy_installed() else "tantivy"
    return mode


def _version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "unknown"


def _fingerprint(config: Any, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """What the index answers for: the loaded text itself (not the file's
    size and mtime, which a copy keeps) and the code that tokenized it."""
    from ..backends.tantivy import _SCHEMA_VERSION

    fields = [config.id_field, *DEFAULT_CONFIG.text_fields]
    content = hashlib.blake2b(digest_size=16)
    for doc in docs:
        for f in fields:
            content.update(repr(doc.get(f)).encode("utf-8", "surrogatepass"))
            content.update(b"\x00")
        content.update(b"\x01")
    return {
        "content": content.hexdigest(),
        "rows": len(docs),
        "id_field": config.id_field,
        "text_language": config.text_language,
        "text_fields": list(DEFAULT_CONFIG.text_fields),
        "tokenizer": hashlib.sha256(UNICODE_WORD_SHAPES.encode()).hexdigest()[:16],
        "tantivy": _version("tantivy"),
        "snowballstemmer": _version("snowballstemmer"),
        "layout": _SCHEMA_VERSION,
    }


def _reopen(path: Path, source: dict[str, Any]) -> Any | None:
    """The index at ``path`` if it was built from ``source``; otherwise clear
    the folder when it is one of our text indexes and return None."""
    from ..backends.tantivy import TantivyBackend

    if not path.exists():
        return None
    if not (path / _META_NAME).exists():
        if any(path.iterdir()):
            raise ValueError(
                f"{path} exists and is not a prismql text index; "
                "refusing to overwrite it"
            )
        return None
    try:
        index = TantivyBackend(index_path=str(path))
    except ValueError:  # an older layout
        index = None
    if index is not None and index.stores_documents:
        raise ValueError(
            f"{path} holds a tantivy backend's own index, not a text index; "
            "give text_index_path a folder of its own"
        )
    if index is not None and index.source == source and index.has_order_axis():
        return index
    print(f"[prismql] text index at {path} rebuilt: built from other data or code")
    shutil.rmtree(path)
    return None


def build_text_index(config: Any, docs: list[dict[str, Any]]) -> Any | None:
    """The corpus's text index, or None when Python's answers (``memory``)."""
    if _mode(config) == "memory":
        return None
    from ..backends.tantivy import TantivyBackend

    threads = max(1, min(4, os.cpu_count() or 1))
    kwargs: dict[str, Any] = {
        "id_field": config.id_field,
        "text_fields": list(DEFAULT_CONFIG.text_fields),
        "text_language": config.text_language,
        "timestamp_fields": config.timestamp_fields,
        "num_threads": threads,
        "heap_size": 128_000_000 * threads,
        "store_documents": False,
    }
    if config.text_index_path is None:
        return TantivyBackend(docs, **kwargs)
    if len({type(d.get(config.id_field)) for d in docs}) > 1:
        # the order sidecar is one Arrow column; mixed id types cannot round-trip
        print(
            f"[prismql] text index kept in memory, not at {config.text_index_path}: "
            "ids mix types"
        )
        return TantivyBackend(docs, **kwargs)
    path = Path(config.text_index_path)
    source = _fingerprint(config, docs)
    index = _reopen(path, source)
    if index is not None:
        return index
    return TantivyBackend(docs, index_path=str(path), source=source, **kwargs)
