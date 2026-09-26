"""Shell command text → the programs it runs (graph @aleph/prismql, #129).

What a shell command *says* is not what it *runs*: quoted strings, heredoc
bodies, comments and command substitutions are words or text, never
programs. They are removed or kept inside one word before a segment's
first word is read, so ``git commit -m 'stop using rm -rf'`` runs ``git``
and deletes nothing.
"""

from __future__ import annotations

import re
import shlex
from pathlib import PurePosixPath

# Wrappers run the program after their own options; the set names the
# options that take a value.
_WRAPPERS: dict[str, set[str]] = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U"},
    "env": {"-u", "-C", "-S"},
    "time": set(),
    "nohup": set(),
    "exec": {"-a"},
    "command": set(),
    "nice": {"-n"},
}
# A condition keyword leads the program it tests; a body keyword leads the
# program it introduces; a closing keyword ends nothing new.
_LEADS = {"if", "elif", "while", "until", "do", "then", "else", "!", "{", "}"}
_LEADS |= {"done", "fi", "esac"}
# A loop, case or function header runs no program of its own.
_HEADERS = {"for", "select", "case", "function"}
# Builtins that set the stage for the next segment.
_SETUP = {"cd", "export", "source", ".", "set", "unset", "pushd", "popd"}
_SEPARATOR_CHARS = set(";&|()\n")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC = re.compile(
    r"(<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2[^\n]*)\n"
    r".*?(?:\n[ \t]*\3[ \t]*(?=\n|$)|\Z)",
    re.DOTALL,
)
_SUBSTITUTION = re.compile(r"\$\([^()]*\)|`[^`]*`")
_SQL_CLIENTS = {"psql", "mysql", "sqlite3", "duckdb", "clickhouse-client"}
_SQL_DESTRUCTIVE = re.compile(
    r"\bdrop\s+(?:table|database|schema)\b|\btruncate\b", re.I
)


def segments(command: str) -> list[list[str]]:
    """The simple commands of a script, each as its words."""
    text = _HEREDOC.sub(lambda m: m.group(1), command)
    while _SUBSTITUTION.search(text):
        text = _SUBSTITUTION.sub("SUBST", text)
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        parts = list(lexer)
    except ValueError:  # an unbalanced quote: fall back to plain words
        parts = text.replace("\n", " ; ").split()
    out: list[list[str]] = []
    words: list[str] = []
    in_comment = False
    for part in parts:
        if in_comment and part != "\n":
            continue
        in_comment = False
        if part and set(part) <= _SEPARATOR_CHARS:
            if words:
                out.append(words)
            words = []
        elif part.startswith("#"):
            in_comment = True
        else:
            words.append(part)
    if words:
        out.append(words)
    return out


def program(words: list[str]) -> tuple[str | None, list[str]]:
    """The program a simple command runs and its arguments."""
    i = 0
    while i < len(words):
        word = words[i]
        if word in _LEADS or _ASSIGNMENT.match(word):
            i += 1
        elif word in _WRAPPERS:
            takes = _WRAPPERS[word]
            i += 1
            while i < len(words) and words[i].startswith("-"):
                i += 2 if words[i] in takes else 1
        else:
            break
    if i >= len(words) or words[i] in _SETUP | _HEADERS:
        return None, []
    return PurePosixPath(words[i]).name or None, words[i + 1 :]


def destructive(name: str | None, args: list[str]) -> bool:
    """Whether the program deletes or overwrites what cannot be taken back."""
    if name == "rm":
        return any(_is_recursive_flag(a) for a in _options(args))
    if name == "git":
        return _git_destructive(args)
    if name == "find":
        return "-delete" in args
    if name == "dd":
        return any(a.startswith("of=") for a in args)
    if name and name.startswith("mkfs"):
        return True
    if name in _SQL_CLIENTS:
        return any(_SQL_DESTRUCTIVE.search(a) for a in args)
    return False


def _options(args: list[str]) -> list[str]:
    out = []
    for a in args:
        if a == "--":
            break
        if a.startswith("-"):
            out.append(a)
    return out


def _is_recursive_flag(arg: str) -> bool:
    if arg.startswith("--"):
        return arg == "--recursive"
    return "r" in arg.lower()


def _git_destructive(args: list[str]) -> bool:
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c") else 1
    if i >= len(args):
        return False
    sub, rest = args[i], args[i + 1 :]
    options = _options(rest)
    if sub == "push":
        forced = any(o == "--force" or _short_has(o, "f") for o in options)
        return forced or any(a.startswith("+") for a in rest if a not in options)
    if sub == "reset":
        return "--hard" in options
    if sub == "clean":
        return any(o == "--force" or _short_has(o, "f") for o in options)
    return False


def _short_has(option: str, letter: str) -> bool:
    return not option.startswith("--") and letter in option[1:]
