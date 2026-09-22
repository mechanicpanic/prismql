"""Tantivy-backed search backend: an inverted index with stemming, on disk.

Text matching follows the corpus's ``text_match`` mode like every backend
(graph #59): ``stem`` (the default; Snowball in ``text_language``) and
``token`` are served from two indexed twins of every text field, phrases
are plain adjacent tokens, and ``substring`` is refused — an inverted index
has no backing for it. The memory backend gives the same sets in the modes
both support (``tests/test_text_mode_parity.py``).

- **Persisted on disk.** Pass ``index_path=`` and a later process opens the
  index instead of rebuilding; the order axis travels with it as the
  ``order.parquet`` sidecar (ids in load order, configured time fields as
  UTC micros), so sequence operators work on a reopened index (graph #39).
- **Ranked search for scouting** (``rank``): tantivy query syntax with BM25,
  outside the language's set algebra (graph #58).
- **``similar_to``** through the same ``SemanticIndex`` the memory backend
  takes (``semantic_index=``).

Numeric ids round-trip as real ``int``s.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, cast

from ..config import DEFAULT_CONFIG, BackendConfig
from ..tokenizers import UNICODE_WORD_SHAPES
from ..types import Document, MessageId
from .base import SearchBackend
from .order import OrderIndex, epoch_micros

try:
    import tantivy

    _TANTIVY_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without the extra
    tantivy = cast(Any, None)
    _TANTIVY_AVAILABLE = False

_DOC_FIELD = "_doc"  # stored JSON of the original document (for get_documents)
_STEM_TOKENIZER = "prismql_stem"  # simple + lowercase + Snowball(text_language)
_PLAIN_ANALYZER = "prismql_token"  # simple + lowercase, no stemming
_RAW_TOKENIZER = "raw"  # whole value as a single token (exact field match)
_PLAIN_SUFFIX = "__tok"  # twin of every text field, indexed without stemming


def _register_analyzers(index: Any, language: str) -> None:
    """Both analyzers a text field needs: stemmed (default contains()) and
    plain tokens (``match = "token"`` / phrases); same Snowball language
    name as the memory backend (graph #59)."""
    # The memory backend's token shapes (C++, e-mails, URLs, contractions):
    # the same regex, so both backends cut text identically.
    tokenizer = tantivy.Tokenizer.regex(UNICODE_WORD_SHAPES)
    base = tantivy.TextAnalyzerBuilder(tokenizer).filter(tantivy.Filter.lowercase())
    index.register_tokenizer(_PLAIN_ANALYZER, base.build())
    stem = (
        tantivy.TextAnalyzerBuilder(tokenizer)
        .filter(tantivy.Filter.lowercase())
        .filter(tantivy.Filter.stemmer(language))
    )
    index.register_tokenizer(_STEM_TOKENIZER, stem.build())


_ORDER_NAME = "order.parquet"  # the axis sidecar: id, <field>_us per position
_META_NAME = "_prismql_meta.json"  # sidecar recording field roles for reopen
# Bumped when the index layout changes; an index from an older layout is
# refused on open with rebuild instructions rather than failing mid-query.
_SCHEMA_VERSION = 2  # 2: stemmed + plain twins per text field, order sidecar
_REGEX_SPECIAL = re.compile(r"([.^$*+?()\[\]{}|\\])")


def _regex_escape(value: str) -> str:
    """Escape regex metacharacters (tantivy uses Rust regex syntax)."""
    return _REGEX_SPECIAL.sub(r"\\\1", value)


def _quote(term: str) -> str:
    """Wrap a term/phrase for parse_query so special characters are inert and
    the field analyzer (lowercase + stem) is applied to it."""
    escaped = term.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _write_order(index_path: Path, order: OrderIndex, fields: Sequence[str]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    n = order.size()
    positions = list(range(n))
    columns: dict[str, Any] = {"id": order.ids_at(positions)}
    for f in fields:
        columns[f"{f}_us"] = pa.array(
            order.timestamps_at(positions, f), type=pa.int64()
        )
    pq.write_table(pa.table(columns), index_path / _ORDER_NAME)


def _read_order(index_path: Path) -> tuple[OrderIndex, list[str]] | None:
    """The axis written by ``_write_order``; None for an index built before
    the sidecar existed (then the backend has no axis, as before)."""
    path = index_path / _ORDER_NAME
    if not path.exists():
        return None
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    fields = [c[: -len("_us")] for c in table.column_names if c.endswith("_us")]
    timestamps = {f: table.column(f"{f}_us").to_pylist() for f in fields}
    return OrderIndex(ids=table.column("id").to_pylist(), timestamps=timestamps), fields


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
        text_language: str = "english",
        semantic_index: Any | None = None,
        timestamp_fields: Sequence[str] | None = None,
    ) -> None:
        if not _TANTIVY_AVAILABLE:
            raise ImportError(
                "TantivyBackend requires the 'tantivy' package. Install it with: "
                "uv pip install 'prismql[tantivy]'  (or: pip install tantivy)"
            )
        self.id_field = id_field
        self.config = config or DEFAULT_CONFIG
        self.text_language = text_language
        # similar_to(): the vector index is independent of the text index
        # (built from documents or read from an ingested emb column).
        self.semantic_index = semantic_index
        self.timestamp_fields = list(
            dict.fromkeys([*(timestamp_fields or []), "timestamp"])
        )

        if (
            index_path is not None
            and Path(index_path).exists()
            and tantivy.Index.exists(str(index_path))
        ):
            self._open_existing(index_path)
        else:
            docs = list(documents or [])
            self._build(docs, text_fields, index_path, heap_size, num_threads)
            # The order axis (spec layer 2b): load order of the documents we
            # were given, with the configured time fields as UTC micros.
            with_id = [doc for doc in docs if self.id_field in doc]
            self.order = OrderIndex(
                ids=[doc[self.id_field] for doc in with_id],
                timestamps={
                    f: [epoch_micros(doc.get(f)) for doc in with_id]
                    for f in self.timestamp_fields
                },
            )
            if index_path is not None:
                # The axis travels with the index as a sidecar table, so an
                # index opened from disk keeps it (graph #39).
                _write_order(Path(index_path), self.order, self.timestamp_fields)

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
            sb.add_text_field(
                f + _PLAIN_SUFFIX, stored=False, tokenizer_name=_PLAIN_ANALYZER
            )
        for f in meta:
            sb.add_text_field(f, stored=False, tokenizer_name=_RAW_TOKENIZER)
        sb.add_json_field(_DOC_FIELD, stored=True)
        schema = sb.build()

        if index_path is not None:
            Path(index_path).mkdir(parents=True, exist_ok=True)
            self._index = tantivy.Index(schema, path=str(index_path))
        else:
            self._index = tantivy.Index(schema)
        _register_analyzers(self._index, self.text_language)

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
                    td.add_text(f + _PLAIN_SUFFIX, str(doc[f]))
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
                        "text_language": self.text_language,
                        "schema_version": _SCHEMA_VERSION,
                    }
                ),
                encoding="utf-8",
            )

    def _open_existing(self, index_path: str) -> None:
        meta = json.loads((Path(index_path) / _META_NAME).read_text(encoding="utf-8"))
        if meta.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError(
                f"{index_path}: tantivy index layout "
                f"{meta.get('schema_version', 1)} is older than this prismql "
                f"({_SCHEMA_VERSION}); rebuild it from the documents (delete the "
                "folder and start with [backend].data set)"
            )
        self._index = tantivy.Index.open(str(index_path))
        self.text_language = meta.get("text_language", self.text_language)
        _register_analyzers(self._index, self.text_language)
        order = _read_order(Path(index_path))
        if order is not None:
            self.order, self.timestamp_fields = order
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
    def _terms(
        self, terms: Sequence[str], field: str, operator: str, suffix: str
    ) -> set[MessageId]:
        if not terms:
            return set()
        per_term: list[set[MessageId]] = []
        for term in terms:
            if field in self._text_fields:
                q = self._analyzed(field + suffix, term)
                per_term.append(self._ids_for(q) if q is not None else set())
            elif field in self._meta_fields or field == self.id_field:
                per_term.append(self.search_by_field(field, term, exact=True))
            else:
                per_term.append(set())
        if operator.upper() == "AND":
            result = per_term[0]
            for s in per_term[1:]:
                result = result & s
            return result
        return set().union(*per_term)

    def search_text(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """Substring matching has no backing in an inverted index: refuse
        (the engine checks ``supports_match`` first; graph #59)."""
        raise NotImplementedError(
            "TantivyBackend cannot match substrings; use text_match 'stem' or 'token'"
        )

    def search_stems(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """Whole-word search on stemmed tokens ("run" matches "running")."""
        return self._terms(terms, field, operator, "")

    def search_tokens(
        self, terms: Sequence[str], field: str = "text", operator: str = "OR"
    ) -> set[MessageId]:
        """Whole-word search on plain lowercase tokens (no stemming)."""
        return self._terms(terms, field, operator, _PLAIN_SUFFIX)

    def supports_match(self, mode: str) -> bool:
        return mode in ("stem", "token")

    def rank(self, query: str, *, limit: int) -> list[tuple[MessageId, float]]:
        """Ranked hits for a query in tantivy's own syntax (AND/OR/NOT,
        "quoted phrases", field:term, prefix*) over the stemmed text fields —
        scouting, outside the algebra (graph #58). BM25 scores, best first."""
        if limit <= 0 or self._searcher.num_docs == 0:
            return []
        fields = sorted(self._text_fields)
        parsed = self._index.parse_query(query, fields)
        result = self._searcher.search(parsed, limit)
        return [
            (
                self._coerce_id(self._searcher.doc(addr).get_first(self.id_field)),
                float(score),
            )
            for score, addr in result.hits
        ]

    def search_semantic(self, text: str, *, threshold: float) -> set[MessageId]:
        if self.semantic_index is None:
            return super().search_semantic(text, threshold=threshold)
        return set(self.semantic_index.search(text, threshold=threshold))

    def search_phrase(self, phrase: str, field: str = "text") -> set[MessageId]:
        """Native phrase search on plain tokens (adjacent, in order, not
        stemmed — the same meaning as the memory backend's n-gram phrases)."""
        if field not in self._text_fields:
            return set()
        q = self._analyzed(field + _PLAIN_SUFFIX, phrase)
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

    # -- order contract (spec 2026-09-18) ---------------------------------
    def has_order_axis(self) -> bool:
        return getattr(self, "order", None) is not None

    def positions(self, ids: Iterable[MessageId]) -> list[int]:
        if not self.has_order_axis():
            raise self._no_axis()
        return self.order.positions(ids)

    def sorted_positions(self, ids: Iterable[MessageId]) -> list[int]:
        if not self.has_order_axis():
            raise self._no_axis()
        return self.order.sorted_positions(ids)

    def ids_at(self, positions: Iterable[int]) -> list[MessageId]:
        if not self.has_order_axis():
            raise self._no_axis()
        return self.order.ids_at(positions)

    def timestamps_at(self, positions: Iterable[int], field: str) -> list[int | None]:
        if not self.has_order_axis():
            raise self._no_axis()
        return self.order.timestamps_at(positions, field)

    def has_timestamp_field(self, field: str) -> bool:
        return self.has_order_axis() and self.order.has_timestamp_field(field)

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
            if raw is None:
                continue
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
