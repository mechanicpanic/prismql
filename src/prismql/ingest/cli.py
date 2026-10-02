"""``prismql ingest …`` — the command-line face of the ingest core."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

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
    parser.add_argument(
        "src",
        nargs="+",
        help="table file or log folder; for table, several files (each "
        "optionally LABEL=PATH) unite into one stream with --source-col",
    )
    parser.add_argument("dst", help="output .parquet")
    parser.add_argument(
        "--source-col",
        metavar="NAME",
        help="table: a column naming each row's source (its LABEL, else the "
        "file's stem); with several sources ids become LABEL:id",
    )
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
        "(column has_link), mentions (column mentions: @ + an --actor name), "
        "entities (column entities, spaCy); the engine reads them as its "
        "indexes",
    )
    parser.add_argument(
        "--actor",
        default="user",
        help="the column naming each event's author, for --annotate mentions",
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
    parser.add_argument(
        "--judge",
        metavar="TOML",
        help="questions for a local decision model; each answer becomes a "
        "label column and a <name>_p column (graph #154)",
    )
    parser.add_argument(
        "--judge-url",
        default="http://127.0.0.1:8000",
        help="the decision model's server (strands-decider serve), default %(default)s",
    )
    return parser


def _read_table(args: argparse.Namespace) -> Any:
    """The canonical stream of ``table``, or a usage message."""
    if not (args.id and args.time):
        return "table: --id and --time are required"
    try:
        table = core.read_sources(args.src, args.source_col, args.id)
    except ValueError as e:
        return f"table: {e}"
    return core.normalize(
        table,
        id_col=args.id,
        time_col=args.time,
        sort=args.sort,
        time_unit=args.time_unit,
        keep=[c for c in (args.keep or "").split(",") if c] or None,
    )


def _judge(df: Any, args: argparse.Namespace) -> Any:
    """``(df, stamp)`` with the decision model's columns, or a usage message."""
    from . import judge as judge_module

    try:
        questions = judge_module.load_questions(args.judge)
        return judge_module.judge(
            df, questions, post=judge_module.http_post(args.judge_url)
        )
    except (ValueError, OSError) as e:
        return f"--judge: {e}"


def _read_source(args: argparse.Namespace) -> Any:
    """The canonical stream of SRC, or a usage message."""
    if args.source == "table":
        return _read_table(args)
    if len(args.src) > 1:
        return f"{args.source}: one log folder at a time"
    if args.source == "claude-code":
        from .sources.claude_code import read_claude_code

        return read_claude_code(Path(args.src[0]))
    from .sources.codex import read_codex

    return read_codex(Path(args.src[0]))


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    df = _read_source(args)
    if isinstance(df, str):
        print(df, file=sys.stderr)
        return 2

    if (args.doc_prompt or args.query_prompt) and not args.embed:
        # a stamp is written only beside vectors this run computes
        print("--doc-prompt/--query-prompt need --embed COL", file=sys.stderr)
        return 2
    kinds = [k for k in (args.annotate or "").split(",") if k]
    if kinds:
        from .annotate import annotate

        try:
            df = annotate(
                df,
                kinds,
                text=args.text,
                spacy_model=args.spacy_model,
                actor=args.actor,
            )
        except ValueError as e:
            print(f"--annotate: {e}", file=sys.stderr)
            return 2
    if args.embed:
        df = core.embed(df, text=args.embed, model=args.model, prompt=args.doc_prompt)
    stamp = None
    if args.judge:
        judged = _judge(df, args)
        if isinstance(judged, str):
            print(judged, file=sys.stderr)
            return 2
        df, stamp = judged
    path = core.write(
        df,
        args.dst,
        embed_model=args.model if args.embed else None,
        embed_text=args.embed,
        embed_doc_prompt=args.doc_prompt,
        embed_query_prompt=args.query_prompt,
        annotations=kinds,
        judge=stamp,
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
