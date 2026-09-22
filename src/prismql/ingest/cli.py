"""``prismql ingest …`` — the command-line face of the ingest core."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import core

SOURCES = ("table", "claude-code")


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
    parser.add_argument("--keep", help="comma-separated extra columns to keep (table)")
    parser.add_argument("--embed", metavar="COL", help="text column to embed into emb")
    parser.add_argument(
        "--model",
        default="all-MiniLM-L6-v2",
        help="sentence-transformers model for --embed",
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
            keep=[c for c in (args.keep or "").split(",") if c] or None,
        )
    else:
        from .sources.claude_code import read_claude_code

        df = read_claude_code(Path(args.src))

    if args.embed:
        df = core.embed(df, text=args.embed, model=args.model)
    path = core.write(
        df,
        args.dst,
        embed_model=args.model if args.embed else None,
        embed_text=args.embed,
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
