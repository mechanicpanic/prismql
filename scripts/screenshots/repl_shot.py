"""Render a faithful REPL session for the README screenshot.

Everything shown is real: the banner comes from PrismQLRepl, the query is
colorized with the same Pygments lexer the live REPL uses, and the results
are the engine's actual output formatted by the REPL's own formatter.
Only the interactivity is scripted (termframe needs a non-interactive
command to capture).
"""

import time
from pathlib import Path

from pygments import highlight
from pygments.formatters import Terminal256Formatter

from prismql.highlighting import PrismQLLexer
from prismql.repl import PrismQLRepl
from prismql.server.config import ServerConfig, build_engine, load_config

HERE = Path(__file__).parent

GREEN_BOLD = "\x1b[1;32m"
RESET = "\x1b[0m"

# A question, someone else's reply, and the asker's thanks — within 5 messages
LINES = [
    "SELECT from($u) AND is_question()",
    "FOLLOWED_BY from(!$u)",
    "FOLLOWED_BY from($u) AND contains(thanks) INWINDOW 5 LIMIT 3 OFFSET 3",
]
QUERY = " ".join(LINES)


def main() -> None:
    config: ServerConfig = load_config(HERE / "repl.toml")
    engine = build_engine(config)
    config.data = "demo/data/fcc.json"  # display the relative path in the banner
    repl = PrismQLRepl(engine=engine, server_config=config)

    print("PrismQL Interactive REPL")
    print("Type \\help for help, \\schema to inspect the corpus, \\quit to exit")
    print(repl.corpus_banner())
    print("Features: history, syntax highlighting")
    print()

    def colorize(text: str) -> str:
        return highlight(
            text, PrismQLLexer(), Terminal256Formatter(style="monokai")
        ).rstrip("\n")

    # Render the query as the wrapped input it is at this width
    prompt = f"{GREEN_BOLD}prismql[0]>{RESET} "
    print(f"{prompt}{colorize(LINES[0])}")
    for line in LINES[1:]:
        print(" " * 12 + colorize(line))

    start = time.time()
    result = repl.engine.execute(QUERY)
    elapsed = time.time() - start

    print()
    print(repl.format_result(result))
    print(f"\n(Query executed in {elapsed:.3f}s)")
    print()
    print(f"{GREEN_BOLD}prismql[1]>{RESET} ")


if __name__ == "__main__":
    main()
