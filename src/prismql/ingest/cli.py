"""``prismql ingest …`` — the command-line face of the ingest core."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import core

SOURCES = ("table", "claude-code", "codex")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prismql ingest",
        description=(
            "Turn a table or a harness log folder into a Parquet stream "
            "(position, id, time, fields[, emb]) the engine loads as-is."
        ),
    )
    parser.add_argument("source", choices=SOURCES, help="what SRC is")
    parser.add_argument("src", help="table file or log folder")
    parser.add_argument("dst", help="output .parquet")
    parser.add_argument("--id", help="id column (table)")
    parser.add_argument("--time", help="timestamp column (table)")
    parser.add_argument("--sort", help="column to order the stream by (table)")
    parser.add_argument(
        "--time-unit",
        choices=("s", "ms", "us", "ns"),
        help="unit of a numeric time column (default: guessed per value)",
    )
    parser.add_argument("--keep", help="comma-separated extra columns to keep (table)")
    parser.add_argument("--embed", metavar="COL", help="text column to embed into emb")
    parser.add_argument(
        "--annotate",
        metavar="KINDS",
        help="comma-separated: questions (column is_question), links "
        "(column has_link), entities (column entities, spaCy); the engine "
        "reads them as its indexes",
    )
    parser.add_argument(
        "--text",
        help="the one text column --annotate reads (default: every text field "
        "present — text, content, message — as the server does at load)",
    )
    parser.add_argument(
        "--spacy-model", default="en_core_web_sm", help="spaCy model for entities"
    )
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="sentence-transformers model for --embed",
    )
    parser.add_argument(
        "--doc-prompt",
        help="prefix for each embedded text (asymmetric models, e.g. "
        "embeddinggemma 'title: none | text: '); stamped into the file",
    )
    parser.add_argument(
        "--query-prompt",
        help="prefix the server puts on query text (e.g. embeddinggemma "
        "'task: search result | query: '); stamped into the file",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.source == "table":
        if not (args.id and args.time):
            print("table: --id and --time are required", file=sys.stderr)
            return 2
        df = core.normalize(
            core.read_source(args.src),
            id_col=args.id,
            time_col=args.time,
            sort=args.sort,
            time_unit=args.time_unit,
            keep=[c for c in (args.keep or "").split(",") if c] or None,
        )
    elif args.source == "claude-code":
        from .sources.claude_code import read_claude_code

        df = read_claude_code(Path(args.src))
    else:
        from .sources.codex import read_codex

        df = read_codex(Path(args.src))

    if (args.doc_prompt or args.query_prompt) and not args.embed:
        # a stamp is written only beside vectors this run computes
        print("--doc-prompt/--query-prompt need --embed COL", file=sys.stderr)
        return 2
    kinds = [k for k in (args.annotate or "").split(",") if k]
    if kinds:
        from .annotate import annotate

        try:
            df = annotate(df, kinds, text=args.text, spacy_model=args.spacy_model)
        except ValueError as e:
            print(f"--annotate: {e}", file=sys.stderr)
            return 2
    if args.embed:
        df = core.embed(df, text=args.embed, model=args.model, prompt=args.doc_prompt)
    path = core.write(
        df,
        args.dst,
        embed_model=args.model if args.embed else None,
        embed_text=args.embed,
        embed_doc_prompt=args.doc_prompt,
        embed_query_prompt=args.query_prompt,
        annotations=kinds,
    )
    info = core.describe(df)
    print(f"{path}: {info['rows']} rows, {info['first']} … {info['last']}")
    if info["null_time"]:
        print(f"  {info['null_time']} rows with unparseable time (kept, time=null)")
    print(f"  columns: {', '.join(info['columns'])}")
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
