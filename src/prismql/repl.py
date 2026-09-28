"""Interactive REPL for PrismQL queries."""

import sys
import time
from pathlib import Path
from typing import Any

from .aggregators.types import AggregateResult, GroupedResult
from .backends.base import PrecomputedIndexes, SearchBackend
from .engine import PrismQLEngine
from .exceptions import PrismQLRuntimeError, PrismQLSyntaxError
from .server.config import ServerConfig, compute_schema
from .types import NamedQueryResult

# Try to import prompt_toolkit for rich REPL experience
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.lexers import PygmentsLexer
    from prompt_toolkit.styles import Style

    try:
        from .highlighting import PrismQLLexer

        HAS_SYNTAX_HIGHLIGHTING = True
    except ImportError:
        HAS_SYNTAX_HIGHLIGHTING = False

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False
    HAS_SYNTAX_HIGHLIGHTING = False


class PrismQLRepl:
    """Interactive REPL for PrismQL queries."""

    def __init__(
        self,
        search_backend: SearchBackend | None = None,
        precomputed_indexes: PrecomputedIndexes | None = None,
        user_dictionaries: dict[str, list[str]] | None = None,
        *,
        engine: PrismQLEngine | None = None,
        server_config: ServerConfig | None = None,
    ) -> None:
        """
        Initialize the REPL.

        Args:
            search_backend: Search backend to use (ignored if engine is given)
            precomputed_indexes: Optional precomputed indexes
            user_dictionaries: Optional user dictionaries
            engine: Pre-built engine (e.g. from a prismql.toml via build_engine)
            server_config: The ServerConfig the engine was built from; used by
                \\schema and the startup banner. Synthesized from the engine's
                own settings when absent.
        """
        if engine is not None:
            self.engine = engine
        elif search_backend is not None:
            self.engine = PrismQLEngine(
                search_backend=search_backend,
                precomputed_indexes=precomputed_indexes,
                user_dictionaries=user_dictionaries or {},
            )
        else:
            raise ValueError("Provide either search_backend or engine")

        # The same config object the server uses — so \schema reports
        # exactly what GET /schema would for the same corpus.
        if server_config is None:
            server_config = ServerConfig(
                id_field=getattr(self.engine.search_backend, "id_field", "id"),
                timestamp_field=self.engine.timestamp_field,
                text_match=self.engine.text_match,
                dictionaries=dict(self.engine.user_dictionaries),
            )
        self.server_config = server_config
        self.query_count = 0
        self.history_file = Path.home() / ".prismql_history"

        # Setup prompt session if available
        if HAS_PROMPT_TOOLKIT:
            self.session: PromptSession[str] | None = PromptSession(
                history=FileHistory(str(self.history_file))
            )
            self.lexer: PygmentsLexer | None
            self.style: Style | None
            if HAS_SYNTAX_HIGHLIGHTING:
                self.lexer = PygmentsLexer(PrismQLLexer)
                self.style = Style.from_dict(
                    {
                        "prompt": "#00aa00 bold",
                    }
                )
            else:
                self.lexer = None
                self.style = None
        else:
            self.session = None
            self.lexer = None
            self.style = None

    def _fetch_message(self, msg_id: Any) -> dict[str, Any] | None:
        """Fetch a single message by ID from the backend."""
        try:
            # Get the document from backend
            docs = self.engine.search_backend.get_documents([msg_id])
            return docs[0] if docs else None
        except Exception:
            return None

    def _format_message(self, msg_id: Any, doc: dict[str, Any] | None) -> str:
        """Format a single message for display."""
        if not doc:
            return f"[{msg_id}]"

        # Extract key fields
        user = doc.get("user", "?")
        text = doc.get("text", doc.get("content", ""))

        # Truncate long text
        if len(text) > 60:
            text = text[:57] + "..."

        return f"[{msg_id}] {user}: {text}"

    def format_result(self, result: Any) -> str:
        """Format query result for display."""
        if isinstance(result, list):
            if not result:
                return "No results found."

            # Check if it's a QueryResult (list of message groups)
            if all(isinstance(item, list) for item in result):
                output = [f"Found {len(result)} result(s):\n"]
                for i, group in enumerate(result, 1):
                    output.append(f"  Group {i}:")
                    for msg_id in group:
                        doc = self._fetch_message(msg_id)
                        output.append(f"    {self._format_message(msg_id, doc)}")
                return "\n".join(output)

            # Plain list
            return f"Results: {result}"

        if isinstance(result, NamedQueryResult):
            output = [f"Found {len(result.results)} result(s):\n"]
            for i, group in enumerate(result.results, 1):
                output.append(f"  Group {i}:")
                names = result.pattern_names
                for j, msg_id in enumerate(group):
                    doc = self._fetch_message(msg_id)
                    msg_str = self._format_message(msg_id, doc)
                    # Add pattern name if available
                    if j < len(names) and names[j]:
                        output.append(f"    {names[j]}: {msg_str}")
                    else:
                        output.append(f"    {msg_str}")
            return "\n".join(output)

        if isinstance(result, AggregateResult):
            if result.is_grouped():
                output = ["Aggregated results (grouped):\n"]
                for group_key, value in result.grouped_values.items():
                    output.append(f"  {group_key}: {value}")
            else:
                output = [f"Aggregated result: {result.value}"]
            return "\n".join(output)

        if isinstance(result, GroupedResult):
            output = [f"Grouped results ({len(result.groups)} groups):\n"]
            for group_key, messages in result.groups.items():
                output.append(f"  {group_key}: {len(messages)} messages")
            return "\n".join(output)

        return str(result)

    def execute_command(self, command: str) -> bool:
        """
        Execute a special command.

        Returns True if should continue REPL, False to exit.
        """
        command = command.strip().lower()

        if command in ("\\q", "\\quit", "\\exit"):
            return False

        if command in ("\\h", "\\help", "\\?"):
            self.show_help()
            return True

        if command == "\\stats":
            self.show_stats()
            return True

        if command == "\\schema":
            self.show_schema()
            return True

        if command == "\\clear":
            # Clear screen
            print("\033[2J\033[H", end="")
            return True

        print(f"Unknown command: {command}")
        print("Type \\help for available commands.")
        return True

    def show_help(self) -> None:
        """Display help message."""
        help_text = """
PrismQL REPL - Interactive Query Interface

Commands:
  \\help, \\h, \\?     Show this help message
  \\quit, \\q, \\exit  Exit the REPL
  \\schema            Show loaded corpus: fields, types, dictionaries
  \\stats             Show query statistics
  \\clear             Clear screen

Query Syntax:
  SELECT <conditions>                    Basic query
  SELECT <cond1>, <cond2> INWINDOW N     Window query (unordered, positional)
  SELECT <cond1> FOLLOWED_BY <cond2>     Sequential query (ordered)
  SELECT ... DURING 1 hour               Temporal window (time-based)
  SELECT ... AGGREGATE count()           Aggregation
  SELECT ... GROUP BY field              Grouping

Examples:
  SELECT from(alice)
  SELECT from(alice) AND is_question()
  SELECT from(alice), from(bob) INWINDOW 5
  SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3
  SELECT from(alice) FOLLOWED_BY from(bob) DURING 2 hours
  SELECT from($user){3} INWINDOW 10
  SELECT RUN(from($user)){3,} DURING 5 minutes

Press Ctrl+C to cancel current query.
Press Ctrl+D or type \\quit to exit.
"""
        print(help_text)

    def show_stats(self) -> None:
        """Show REPL statistics."""
        print("\nQuery Statistics:")
        print(f"  Total queries executed: {self.query_count}")
        print(f"  Backend type: {type(self.engine.search_backend).__name__}")
        print(f"  Documents loaded: {self.engine.search_backend.get_total_documents()}")
        print(f"  User dictionaries: {len(self.engine.user_dictionaries)}")
        print()

    def show_schema(self) -> None:
        """Show the loaded corpus schema (same data as the server's GET /schema)."""
        schema = compute_schema(self.engine, self.server_config)
        print(
            f"\nCorpus: {schema['documents']} documents "
            f"(sampled {schema['sampled']}) · backend {schema['backend']}"
        )
        if self.server_config.data:
            print(f"  data: {self.server_config.data}")
        print(
            f"  id_field: {schema['id_field']} · "
            f"timestamp_field: {schema['timestamp_field']} · "
            f"text_match: {schema['text_match']}"
        )
        if schema["fields"]:
            print("\nFields:")
            width = max(len(name) for name in schema["fields"])
            for name, info in schema["fields"].items():
                line = (
                    f"  {name:<{width}}  {info['type']:<8}"
                    f"{info['coverage'] * 100:5.1f}%"
                )
                if "examples" in info:
                    line += "  e.g. " + ", ".join(info["examples"][:6])
                print(line)
        if schema["dictionaries"]:
            print("\nDictionaries:")
            for name, count in schema["dictionaries"].items():
                print(f"  {name} ({count} term{'s' if count != 1 else ''})")
        print()

    def corpus_banner(self) -> str:
        """One-line summary of what is loaded, shown at startup."""
        backend = self.engine.search_backend
        banner = (
            f"Loaded: {backend.get_total_documents()} documents "
            f"via {type(backend).__name__}"
        )
        if self.server_config.data:
            banner += f" from {self.server_config.data}"
        if self.engine.user_dictionaries:
            n = len(self.engine.user_dictionaries)
            banner += f" · {n} dictionar{'ies' if n != 1 else 'y'}"
        return banner

    def get_prompt(self) -> str:
        """Get the prompt string."""
        return f"prismql[{self.query_count}]> "

    def read_query(self) -> str | None:
        """Read a query from user input."""
        try:
            query: str
            if self.session and self.lexer and self.style:
                # Rich prompt with syntax highlighting
                query = self.session.prompt(
                    self.get_prompt(), lexer=self.lexer, style=self.style
                )
            elif self.session:
                # Basic prompt with history
                query = self.session.prompt(self.get_prompt())
            else:
                # Fallback to basic input
                query = input(self.get_prompt())

            return query.strip()
        except EOFError:
            # Ctrl+D pressed
            return None
        except KeyboardInterrupt:
            # Ctrl+C pressed
            print("\nQuery cancelled.")
            return ""

    def run(self) -> None:
        """Run the REPL loop."""
        print("PrismQL Interactive REPL")
        print("Type \\help for help, \\schema to inspect the corpus, \\quit to exit")
        print(self.corpus_banner())

        # Show enabled features
        features = []
        if HAS_PROMPT_TOOLKIT:
            features.append("history")
        if HAS_SYNTAX_HIGHLIGHTING:
            features.append("syntax highlighting")
        if features:
            print(f"Features: {', '.join(features)}")
        else:
            print("Tip: Install extras for enhanced experience:")
            print("  uv pip install '.[repl,highlighting]'")
        print()

        while True:
            query = self.read_query()

            # None means EOF (exit)
            if query is None:
                print("\nGoodbye!")
                break

            # Empty string means cancelled or empty input
            if not query:
                continue

            # Check for special commands
            if query.startswith("\\"):
                should_continue = self.execute_command(query)
                if not should_continue:
                    print("\nGoodbye!")
                    break
                continue

            # Execute PrismQL query
            try:
                start_time = time.time()
                result = self.engine.execute(query)
                elapsed = time.time() - start_time

                print()
                print(self.format_result(result))
                print(f"\n(Query executed in {elapsed:.3f}s)")
                print()

                self.query_count += 1

            except PrismQLSyntaxError as e:
                print(f"\nSyntax Error: {e}")
                if hasattr(e, "line") and hasattr(e, "column"):
                    print(f"  at line {e.line}, column {e.column}")
                print()

            except PrismQLRuntimeError as e:
                print(f"\nRuntime Error: {e}")
                print()

            except KeyboardInterrupt:
                print("\nQuery cancelled.")
                print()

            except Exception as e:
                print(f"\nUnexpected Error: {e}")
                print(f"  Type: {type(e).__name__}")
                print()


def main() -> None:
    """Main entry point for REPL (and ``prismql ingest …``)."""
    import argparse

    if sys.argv[1:2] == ["ingest"]:
        from .ingest.cli import run

        sys.exit(run(sys.argv[2:]))

    from .backends.factory import BackendFactory

    parser = argparse.ArgumentParser(description="PrismQL Interactive REPL")
    parser.add_argument(
        "--config",
        type=str,
        help=(
            "Path to configuration file: prismql.toml (same file the server "
            "takes) or a legacy backend JSON config"
        ),
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="memory",
        choices=["memory", "tantivy"],
        help="Backend type (default: memory)",
    )
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Load sample conversation data",
    )

    args = parser.parse_args()

    # Load configuration
    if args.config and args.config.endswith(".toml"):
        # The server's prismql.toml: one config, two frontends.
        from .server.config import build_engine, load_config

        server_config = load_config(args.config)
        repl = PrismQLRepl(
            engine=build_engine(server_config), server_config=server_config
        )
    elif args.config:
        import json

        with open(args.config) as f:
            config = json.load(f)
        (
            search_backend,
            precomputed,
            user_dicts,
        ) = BackendFactory.create_backends(config)
        repl = PrismQLRepl(
            search_backend=search_backend,
            precomputed_indexes=precomputed,
            user_dictionaries=user_dicts,
        )
    else:
        # Create default memory backend
        if args.sample_data:
            # Sample conversation data
            documents = [
                {"id": 1, "user": "alice", "text": "Hello everyone!"},
                {"id": 2, "user": "bob", "text": "Hi alice, how are you?"},
                {"id": 3, "user": "alice", "text": "I'm good thanks! How about you?"},
                {"id": 4, "user": "bob", "text": "Doing well!"},
                {
                    "id": 5,
                    "user": "alice",
                    "text": "I have a question about the project",
                },
                {"id": 6, "user": "charlie", "text": "What's your question?"},
                {"id": 7, "user": "alice", "text": "When is the deadline?"},
                {"id": 8, "user": "charlie", "text": "Next Friday"},
                {"id": 9, "user": "alice", "text": "Thanks!"},
                {"id": 10, "user": "bob", "text": "Good to know"},
            ]
        else:
            documents = []

        from .backends.memory import MemoryBackend

        repl = PrismQLRepl(search_backend=MemoryBackend(documents=documents))

    try:
        repl.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
