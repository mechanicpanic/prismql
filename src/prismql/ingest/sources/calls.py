"""A tool call as structure (graph @aleph/prismql, #129).

Both harness adapters write a call's arguments as text; here they become
fields a query can name — ``cmd`` (the first program a shell command
runs), ``path``, ``host``, ``action`` — and the result's outcome, duration
and size move onto the call itself, so one event answers "what was run and
how did it end". A field is ``None`` when the call does not say it.
"""

from __future__ import annotations

import json
import re
import shlex
from typing import Any

from .shell import destructive, program, segments

SHELL_TOOLS = {"Bash", "exec_command", "shell", "local_shell"}
READ_TOOLS = {"Read", "Grep", "Glob", "LS", "NotebookRead", "view_image"}
WRITE_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit", "apply_patch"}
NETWORK_TOOLS = {"WebFetch", "WebSearch", "web_search"}
NETWORK_CMDS = {"curl", "wget", "ssh", "scp", "rsync", "nc", "http", "gh"}

_URL_HOST = re.compile(r"https?://(?:[^@/\s]+@)?([^/\s:'\"?#@]+)")
_PATCH_FILE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", re.MULTILINE)


def describe_call(tool: str | None, args: Any) -> dict[str, str | None]:
    """``cmd``, ``path``, ``host`` and ``action`` of one call."""
    args = _parsed(args)
    command = _command(tool, args)
    if command is None:
        url = args.get("url") if isinstance(args, dict) else None
        return {
            "cmd": None,
            "path": _path(tool, args),
            "host": _host(url),
            "action": _tool_action(tool),
        }
    programs = [program(words) for words in segments(command)]
    programs = [(name, rest) for name, rest in programs if name]
    names = {name for name, _ in programs}
    host = next(
        (
            h
            for name, rest in programs
            if name in NETWORK_CMDS
            for h in map(_host, rest)
            if h
        ),
        None,
    )
    if any(destructive(name, rest) for name, rest in programs):
        action = "destructive"
    elif names & NETWORK_CMDS:
        action = "network"
    elif "apply_patch" in names:
        action = "write"
    else:
        action = "exec"
    return {
        "cmd": programs[0][0] if programs else None,
        "path": _patch_path(command) if "apply_patch" in names else None,
        "host": host,
        "action": action,
    }


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


def _path(tool: str | None, args: Any) -> str | None:
    if tool == "apply_patch":
        if isinstance(args, dict):
            args = args.get("input", args.get("patch"))
        return _patch_path(args) if isinstance(args, str) else None
    if tool in READ_TOOLS | WRITE_TOOLS and isinstance(args, dict):
        for key in ("file_path", "notebook_path", "path"):
            if isinstance(args.get(key), str):
                return str(args[key])
    return None


def _patch_path(text: str) -> str | None:
    found = _PATCH_FILE.search(text)
    return found.group(1).strip() if found else None


def _host(text: Any) -> str | None:
    found = _URL_HOST.search(text) if isinstance(text, str) else None
    return found.group(1).lower() if found else None


def _tool_action(tool: str | None) -> str | None:
    if tool in NETWORK_TOOLS:
        return "network"
    if tool in WRITE_TOOLS:
        return "write"
    if tool in READ_TOOLS:
        return "read"
    return "exec" if tool in SHELL_TOOLS else None
