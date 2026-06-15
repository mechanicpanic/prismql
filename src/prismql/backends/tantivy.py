"""Tantivy-backed search backend: an inverted index with stemming.

Unlike :class:`MemoryBackend` (which defaults to *substring* matching and
rebuilds a pure-Python index every run), this backend uses the tantivy search
engine and therefore has deliberately different — and, for real text, better —
semantics:

- **Text search is stemmed token matching.** ``contains("running")`` also
  matches "run"/"runs" (Lucene-style fulltext), *not* substring. This is the
  honest fulltext behaviour and gives stemming for free.
- **Phrase search is native** (tantivy phrase queries) — no n-gram precompute.
- **The index can be persisted on disk.** Pass ``index_path=`` and a later
  process opens it instead of rebuilding (the "no 40-second rebuild" win).

Because the semantics differ from ``MemoryBackend``, this backend is tested
against its *own* expectations (``tests/test_tantivy_backend.py``), not blind
parity with the substring backend.

Numeric ids round-trip as real ``int``s so the ``prismql-rust`` window/sequence
merge fast paths (gated on all-int ids) still fire on top of tantivy search.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..config import DEFAULT_CONFIG, BackendConfig
from ..types import Document, MessageId
from .base import SearchBackend

try:
    import tantivy

    _TANTIVY_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the extra
    tantivy = None
    _TANTIVY_AVAILABLE = False

_DOC_FIELD = "_doc"  # stored JSON of the original document (for get_documents)
_STEM_TOKENIZER = "en_stem"  # built-in: lowercase + English (Snowball) stemmer
_RAW_TOKENIZER = "raw"  # whole value as a single token (exact field match)
_META_NAME = "_prismql_meta.json"  # sidecar recording field roles for reopen
_REGEX_SPECIAL = re.compile(r"([.^$*+?()\[\]{}|\\])")


def _regex_escape(value: str) -> str:
    """Escape regex metacharacters (tantivy uses Rust regex syntax)."""
    return _REGEX_SPECIAL.sub(r"\\\1", value)


def _quote(term: str) -> str:
    """Wrap a term/phrase for parse_query so special characters are inert and
    the field analyzer (lowercase + stem) is applied to it."""
    escaped = term.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


class TantivyBackend(SearchBackend):
    """A :class:`SearchBackend` backed by the tantivy search engine."""

    def __init__(
        self,
        documents: Sequence[Document] | None = None,
        id_field: str = "id",
        config: BackendConfig | None = None,
        *,
        index_path: str | None = None,
        text_fields: Sequence[str] | None = None,
        heap_size: int = 50_000_000,
        num_threads: int = 1,
    ) -> None:
        if not _TANTIVY_AVAILABLE:
            raise ImportError(
                "TantivyBackend requires the 'tantivy' package. Install it with: "
                "uv pip install 'prismql[tantivy]'  (or: pip install tantivy)"
            )
        self.id_field = id_field
        self.config = config or DEFAULT_CONFIG

        if (
            index_path is not None
            and Path(index_path).exists()
            and tantivy.Index.exists(str(index_path))
        ):
            self._open_existing(index_path)
        else:
            self._build(
                list(documents or []), text_fields, index_path, heap_size, num_threads
            )

        self._index.reload()
        self._searcher = self._index.searcher()
        self._schema = self._index.schema

    # ------------------------------------------------------------------ build
    def _build(  # noqa: C901
        self,
        documents: list[Document],
        text_fields: Sequence[str] | None,
        index_path: str | None,
        heap_size: int,
        num_threads: int,
    ) -> None:
        # Discover fields and the id type from the documents.
        observed: set[str] = set()
        id_is_int = True
        for doc in documents:
            observed.update(doc.keys())
            raw_id = doc.get(self.id_field)
            if raw_id is not None and not isinstance(raw_id, int):
                id_is_int = False
        observed.discard(self.id_field)

        if text_fields is not None:
            text = list(text_fields)
        else:
            # configured text fields that actually appear, always incl. "text"
            text = [f for f in self.config.text_fields if f in observed]
            if "text" not in text:
                text.insert(0, "text")
        text_set = set(text)
        meta = sorted(observed - text_set)

        self._id_is_int = id_is_int
        self._text_fields = text_set
        self._meta_fields = set(meta)

        sb = tantivy.SchemaBuilder()
        if id_is_int:
            sb.add_integer_field(self.id_field, stored=True, indexed=True, fast=True)
        else:
            sb.add_text_field(self.id_field, stored=True, tokenizer_name=_RAW_TOKENIZER)
        for f in sorted(text_set):
            sb.add_text_field(f, stored=False, tokenizer_name=_STEM_TOKENIZER)
        for f in meta:
            sb.add_text_field(f, stored=False, tokenizer_name=_RAW_TOKENIZER)
        sb.add_json_field(_DOC_FIELD, stored=True)
        schema = sb.build()

        if index_path is not None:
            Path(index_path).mkdir(parents=True, exist_ok=True)
            self._index = tantivy.Index(schema, path=str(index_path))
        else:
            self._index = tantivy.Index(schema)

        writer = self._index.writer(heap_size=heap_size, num_threads=num_threads)
        for doc in documents:
            td = tantivy.Document()
            raw_id = doc.get(self.id_field)
            if raw_id is None:
                continue  # a document without an id cannot be addressed
            if id_is_int:
                td.add_integer(self.id_field, int(raw_id))
            else:
                td.add_text(self.id_field, str(raw_id))
            for f in text_set:
                if f in doc and doc[f] is not None:
                    td.add_text(f, str(doc[f]))
            for f in self._meta_fields:
                if f in doc and doc[f] is not None:
                    td.add_text(f, str(doc[f]).lower())
            td.add_json(_DOC_FIELD, json.dumps(doc, default=str))
            writer.add_document(td)
        writer.commit()

        if index_path is not None:
            (Path(index_path) / _META_NAME).write_text(
                json.dumps(
                    {
                        "id_field": self.id_field,
                        "id_is_int": self._id_is_int,
                        "text_fields": sorted(self._text_fields),
                        "meta_fields": sorted(self._meta_fields),
                    }
                ),
                encoding="utf-8",
            )

    def _open_existing(self, index_path: str) -> None:
        self._index = tantivy.Index.open(str(index_path))
        meta = json.loads((Path(index_path) / _META_NAME).read_text(encoding="utf-8"))
        self.id_field = meta["id_field"]
        self._id_is_int = meta["id_is_int"]
        self._text_fields = set(meta["text_fields"])
        self._meta_fields = set(meta["meta_fields"])

    # ------------------------------------------------------------- internals
    def _coerce_id(self, raw: Any) -> MessageId:
        return int(raw) if self._id_is_int else str(raw)

    def _ids_for(self, query: Any, limit: int | None = None) -> set[MessageId]:
        n = limit if limit is not None else max(self._searcher.num_docs, 1)
        result = self._searcher.search(query, n)
        out: set[MessageId] = set()
        for _score, addr in result.hits:
            out.add(self._coerce_id(self._searcher.doc(addr).get_first(self.id_field)))
        return out

    def _analyzed(self, field: str, term: str) -> Any | None:
        term = term.strip()
        if not term:
            return None
        return self._index.parse_query(_quote(term), [field])

    # --------------------------------------------------------- search methods
    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """Stemmed token search. NOTE: not substring — "run" matches "running",
        but "un" does not match "run"."""
        if not terms:
            return set()
        per_term: list[set[MessageId]] = []
        for term in terms:
            if field in self._text_fields:
                q = self._analyzed(field, term)
                per_term.append(self._ids_for(q) if q is not None else set())
            elif field in self._meta_fields or field == self.id_field:
                per_term.append(self.search_by_field(field, term, exact=True))
            else:
                per_term.append(set())
        if not per_term:
            return set()
        if operator.upper() == "AND":
            result = per_term[0]
            for s in per_term[1:]:
                result = result & s
            return result
        return set().union(*per_term)

    def search_tokens(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """On tantivy this coincides with :meth:`search_text` — both match
        analyzed (stemmed) tokens against the inverted index."""
        return self.search_text(terms, field, operator)

    def search_phrase(self, phrase: str, field: str = "text") -> set[MessageId]:
        """Native analyzed phrase search (terms must be adjacent, in order)."""
        if field not in self._text_fields:
            return set()
        q = self._analyzed(field, phrase)
        return self._ids_for(q) if q is not None else set()

    def search_by_field(
        self, field: str, value: str, exact: bool = True
    ) -> set[MessageId]:
        """Exact or partial match on a metadata (keyword) field.

        Metadata values are indexed lowercased, so matching is case-insensitive.
        Partial matching is a substring (regex ``.*value.*``) over the raw value.
        """
        if field in self._text_fields:
            # text fields are stemmed/tokenized; "exact field value" isn't a
            # natural fit, so treat it as an analyzed phrase match.
            q = self._analyzed(field, value)
            return self._ids_for(q) if q is not None else set()
        if field != self.id_field and field not in self._meta_fields:
            return set()

        if field == self.id_field and self._id_is_int:
            try:
                return self._ids_for(
                    tantivy.Query.term_query(self._schema, field, int(value))
                )
            except (ValueError, TypeError):
                return set()

        v = str(value).lower()
        if exact:
            return self._ids_for(tantivy.Query.term_query(self._schema, field, v))
        pattern = f".*{_regex_escape(v)}.*"
        return self._ids_for(tantivy.Query.regex_query(self._schema, field, pattern))

    # ----------------------------------------------------------- corpus stats
    def get_total_documents(self) -> int:
        return int(self._searcher.num_docs)

    def get_all_document_ids(self, limit: int | None = None) -> set[MessageId]:
        if self._searcher.num_docs == 0:
            return set()
        return self._ids_for(tantivy.Query.all_query(), limit)

    def get_documents(self, ids: Sequence[MessageId]) -> list[Document]:
        if not ids:
            return []
        if self._id_is_int:
            values: list[Any] = []
            for i in ids:
                try:
                    values.append(int(i))
                except (ValueError, TypeError):
                    continue
        else:
            values = [str(i) for i in ids]
        if not values:
            return []
        query = tantivy.Query.term_set_query(self._schema, self.id_field, values)
        result = self._searcher.search(query, len(values))
        by_id: dict[MessageId, Document] = {}
        for _score, addr in result.hits:
            stored = self._searcher.doc(addr)
            raw = stored.get_first(_DOC_FIELD)
            doc = raw if isinstance(raw, dict) else json.loads(raw)
            by_id[self._coerce_id(stored.get_first(self.id_field))] = doc
        # preserve requested order, drop misses, dedupe
        seen: set[MessageId] = set()
        ordered: list[Document] = []
        for i in ids:
            key = self._coerce_id(i) if not isinstance(i, (int, str)) else i
            if key in by_id and key not in seen:
                seen.add(key)
                ordered.append(by_id[key])
        return ordered
