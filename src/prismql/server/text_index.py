"""The full-text index a memory corpus answers its text predicates from.

One tantivy index per corpus, built in load order (graph @aleph/prismql,
#91): ``contains``, phrases and ``/search`` read it; the memory backend
keeps fields, the order axis and ``substring`` mode. With
``text_index_path`` the index lives on disk next to a fingerprint of the
data it was built from, and is rebuilt — never reopened — for other data.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from ..config import DEFAULT_CONFIG

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


def _fingerprint(config: Any, docs: list[dict[str, Any]]) -> dict[str, Any]:
    stat = Path(config.data).stat()
    return {
        "data": str(Path(config.data).resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "rows": len(docs),
        "id_field": config.id_field,
        "text_language": config.text_language,
        "text_fields": list(DEFAULT_CONFIG.text_fields),
    }


def _reopen(path: Path, source: dict[str, Any]) -> Any | None:
    """The index at ``path`` if it was built from ``source``; else clear the
    folder (only if it is one of ours) and return None."""
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
    if index is not None and index.source == source:
        return index
    print(f"[prismql] text index at {path} rebuilt: built from other data")
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
    }
    if config.text_index_path is None:
        return TantivyBackend(docs, **kwargs)
    path = Path(config.text_index_path)
    source = _fingerprint(config, docs)
    index = _reopen(path, source)
    if index is not None:
        return index
    return TantivyBackend(docs, index_path=str(path), source=source, **kwargs)
