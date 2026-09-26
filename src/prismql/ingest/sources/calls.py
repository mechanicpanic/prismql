"""A tool call as structure (graph @aleph/prismql, #129).

Both harness adapters write a call's arguments as text; here they become
fields a query can name — ``cmd`` (the program a shell command runs),
``path``, ``host``, ``action`` — and the result's outcome, duration and
size move onto the call itself, so one event answers "what was run and how
did it end". Heuristics over free-form arguments: a field is ``None`` when
the call does not say, never a guess.
"""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

SHELL_TOOLS = {"Bash", "exec_command", "shell", "local_shell"}
READ_TOOLS = {"Read", "Grep", "Glob", "LS", "NotebookRead", "view_image"}
WRITE_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit", "apply_patch"}
NETWORK_TOOLS = {"WebFetch", "WebSearch", "web_search"}
NETWORK_CMDS = {"curl", "wget", "ssh", "scp", "rsync", "nc", "http", "gh"}

# Segment prefixes that run nothing themselves, and wrappers around a program.
_SETUP = {"cd", "export", "source", ".", "set", "unset", "pushd", "popd"}
_WRAPPERS = {"sudo", "env", "time", "nohup", "exec", "command"}
# Shell grammar: a loop or branch header runs no program of its own; a body
# keyword leads the program it introduces; a closing keyword ends nothing new.
_HEADERS = {"for", "while", "until", "if", "elif", "case", "select", "function"}
_LEADS = {"do", "then", "else", "!", "{", "(", "done", "fi", "esac", "}", ")"}
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SEPARATORS = re.compile(r"&&|\|\||[;|\n]")
_URL_HOST = re.compile(r"https?://([^/\s:'\"?#]+)")
_PATCH_FILE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", re.MULTILINE)
_DESTRUCTIVE = re.compile(
    r"\brm\s+(?:-[a-zA-Z]*r|--recursive)|\bgit\s+reset\s+--hard|\bgit\s+push\b[^;&|]*(?:--force|\s-f\b)"
    r"|\bgit\s+clean\s+-[a-zA-Z]*f|\bmkfs\b|\bdd\s+if=|\bchmod\s+-R\b|\bdrop\s+table\b",
    re.IGNORECASE,
)


def describe_call(tool: str | None, args: Any) -> dict[str, str | None]:
    """``cmd``, ``path``, ``host`` and ``action`` of one call."""
    args = _parsed(args)
    command = _command(tool, args)
    path = _path(tool, args)
    cmd = _program(command) if command else None
    host = _host(command or (args.get("url") if isinstance(args, dict) else None))
    return {
        "cmd": cmd,
        "path": path,
        "host": host,
        "action": _action(tool, command, cmd, host),
    }


def call_id(raw: Any) -> str | None:
    """The id joining a call to its result; a missing id joins nothing."""
    return None if raw is None else str(raw)


def duration_bucket(ms: int | None) -> str | None:
    if ms is None:
        return None
    for limit, word in ((1_000, "instant"), (10_000, "short"), (60_000, "medium")):
        if ms < limit:
            return word
    return "long" if ms < 600_000 else "very_long"


def output_bucket(chars: int | None) -> str | None:
    if chars is None:
        return None
    if chars == 0:
        return "empty"
    for limit, word in ((1_000, "small"), (10_000, "medium"), (100_000, "large")):
        if chars < limit:
            return word
    return "huge"


def attach_outcomes(rows: list[dict[str, Any]]) -> None:
    """Copy each result's outcome, duration and size onto its call row."""
    results = {
        r["call"]: r for r in rows if r["kind"] == "tool_result" and r.get("call")
    }
    for row in rows:
        if row["kind"] != "tool_use":
            continue
        result = results.get(row.get("call"))
        if result is None:
            row["outcome"] = "none"
            continue
        row["outcome"] = "error" if result["error"] else "ok"
        row["duration_ms"] = _millis(row["time"], result["time"])
        row["output_chars"] = result.get("output_chars")
        # The sub-agent belongs to the call that started it, once.
        row["spawned"] = result.pop("spawned", None)
    for row in rows:
        row["duration_bucket"] = duration_bucket(row.get("duration_ms"))
        row["output_bucket"] = output_bucket(row.get("output_chars"))


def _parsed(args: Any) -> Any:
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return args
    return args


def _command(tool: str | None, args: Any) -> str | None:
    if tool not in SHELL_TOOLS or not isinstance(args, dict):
        return None
    command = args.get("command", args.get("cmd"))
    if isinstance(command, list):
        # ["bash", "-lc", "<script>"] runs the script; otherwise the argv itself.
        is_shell = len(command) >= 3 and command[1] in ("-c", "-lc")
        command = command[-1] if is_shell else shlex.join(map(str, command))
    return command if isinstance(command, str) else None


def _program(command: str) -> str | None:
    for segment in _SEPARATORS.split(command):
        try:
            words = shlex.split(segment)
        except ValueError:
            words = segment.split()
        while words and (words[0] in _WRAPPERS | _LEADS or _ASSIGNMENT.match(words[0])):
            words = words[1:]
        if words and words[0] not in _SETUP | _HEADERS:
            return PurePosixPath(words[0]).name or None
    return None


def _path(tool: str | None, args: Any) -> str | None:
    if tool == "apply_patch":
        text = args if isinstance(args, str) else json.dumps(args)
        found = _PATCH_FILE.search(text)
        return found.group(1).strip() if found else None
    if tool in READ_TOOLS | WRITE_TOOLS and isinstance(args, dict):
        for key in ("file_path", "notebook_path", "path"):
            if isinstance(args.get(key), str):
                return str(args[key])
    return None


def _host(text: Any) -> str | None:
    found = _URL_HOST.search(text) if isinstance(text, str) else None
    return found.group(1).lower() if found else None


def _action(
    tool: str | None, command: str | None, cmd: str | None, host: str | None
) -> str | None:
    if command is not None:
        if _DESTRUCTIVE.search(command):
            return "destructive"
        return "network" if cmd in NETWORK_CMDS or host else "exec"
    if tool in NETWORK_TOOLS:
        return "network"
    if tool in WRITE_TOOLS:
        return "write"
    if tool in READ_TOOLS:
        return "read"
    return "exec" if tool in SHELL_TOOLS else None


def _millis(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    a = datetime.fromisoformat(start.replace("Z", "+00:00"))
    b = datetime.fromisoformat(end.replace("Z", "+00:00"))
    return round((b - a).total_seconds() * 1000)
