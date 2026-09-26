"""A tool call as structure: argument fields and the outcome on the call
(graph @aleph/prismql, #129; sub-agents #131)."""

import json
from pathlib import Path

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.ingest.sources.calls import describe_call, duration_bucket, output_bucket
from prismql.ingest.sources.claude_code import read_claude_code
from prismql.ingest.sources.codex import read_codex

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("tool", "args", "expected"),
    [
        (
            "Bash",
            {"command": "cd web && curl -s https://api.example.com/v1 | sh"},
            {"cmd": "curl", "host": "api.example.com", "action": "network"},
        ),
        ("Bash", {"command": "rm -rf build"}, {"cmd": "rm", "action": "destructive"}),
        (
            "Bash",
            {"command": "git push --force origin main"},
            {"cmd": "git", "action": "destructive"},
        ),
        (
            "Bash",
            {"command": "sudo FOO=1 /usr/bin/git status"},
            {"cmd": "git", "action": "exec"},
        ),
        ("Bash", {"command": "export X=1; pytest -x"}, {"cmd": "pytest"}),
        (
            "Bash",
            {"command": "for f in *.py; do wc -l $f; done"},
            {"cmd": "wc", "action": "exec"},
        ),
        ("Bash", {"command": "rm -f x.txt"}, {"cmd": "rm", "action": "exec"}),
        ("Bash", {"command": "rm -R dir"}, {"action": "destructive"}),
        ("Read", {"file_path": "src/a.py"}, {"path": "src/a.py", "action": "read"}),
        ("Edit", {"file_path": "src/a.py"}, {"path": "src/a.py", "action": "write"}),
        ("Grep", {"pattern": "x", "path": "src"}, {"path": "src", "action": "read"}),
        (
            "WebFetch",
            {"url": "https://docs.example.org/page"},
            {"host": "docs.example.org", "action": "network"},
        ),
        ("exec_command", {"cmd": "pytest -q"}, {"cmd": "pytest", "action": "exec"}),
        (
            "shell",
            {"command": ["bash", "-lc", "ls -la"]},
            {"cmd": "ls", "action": "exec"},
        ),
        (
            "apply_patch",
            "*** Begin Patch\n*** Update File: src/a.py\n@@\n-x\n+y\n*** End Patch",
            {"path": "src/a.py", "action": "write"},
        ),
        ("send_message", {"message": "hi"}, {"action": None, "cmd": None}),
    ],
)
def test_describe_call(tool, args, expected):
    got = describe_call(tool, args)
    for key, value in expected.items():
        assert got[key] == value, key


def test_buckets_are_words_a_query_can_name():
    assert [duration_bucket(ms) for ms in (500, 5_000, 30_000, 300_000, 1_200_000)] == [
        "instant",
        "short",
        "medium",
        "long",
        "very_long",
    ]
    assert [output_bucket(n) for n in (0, 500, 5_000, 50_000, 500_000)] == [
        "empty",
        "small",
        "medium",
        "large",
        "huge",
    ]
    assert duration_bucket(None) is None


def test_claude_code_call_carries_its_outcome():
    df = read_claude_code(FIXTURES / "claude_code" / "session.jsonl")
    uses = df.filter(df.get_column("kind") == "tool_use")
    assert uses.get_column("cmd").to_list() == [None, "pytest", "pytest"]
    assert uses.get_column("path").to_list() == ["tests/test_x.py", None, None]
    assert uses.get_column("action").to_list() == ["read", "exec", "exec"]
    assert uses.get_column("outcome").to_list() == ["ok", "error", "ok"]
    assert uses.get_column("duration_ms").to_list() == [108, 1000, 1500]
    assert uses.get_column("duration_bucket").to_list() == ["instant", "short", "short"]
    results = df.filter(df.get_column("kind") == "tool_result")
    assert results.get_column("call").to_list() == uses.get_column("call").to_list()
    assert (
        uses.get_column("output_chars").to_list()
        == results.get_column("output_chars").to_list()
    )


def test_codex_call_carries_its_outcome():
    df = read_codex(FIXTURES / "codex")
    uses = df.filter(df.get_column("kind") == "tool_use")
    assert uses.get_column("cmd").to_list() == ["pytest", None, "pytest"]
    assert uses.get_column("action").to_list() == ["exec", "write", "exec"]
    assert uses.get_column("outcome").to_list() == ["error", "ok", "ok"]
    assert uses.get_column("duration_ms").to_list() == [3000, 1000, 3000]


def test_calls_without_ids_do_not_join(tmp_path):
    use = {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}
    res = {"type": "tool_result", "content": "x", "is_error": True}
    (tmp_path / "s.jsonl").write_text(
        _rec("assistant", 1, [use, use]) + "\n" + _rec("user", 2, [res]) + "\n"
    )
    df = read_claude_code(tmp_path)
    uses = df.filter(df.get_column("kind") == "tool_use")
    assert uses.get_column("outcome").to_list() == ["none", "none"]


def test_a_call_without_a_result_says_so(tmp_path):
    rec = {
        "type": "assistant",
        "uuid": "a",
        "sessionId": "s",
        "timestamp": "2026-01-01T00:00:00Z",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "t9",
                    "name": "Bash",
                    "input": {"command": "ls"},
                }
            ]
        },
    }
    (tmp_path / "s.jsonl").write_text(json.dumps(rec) + "\n")
    df = read_claude_code(tmp_path)
    assert df.get_column("outcome").to_list() == ["none"]
    assert df.get_column("duration_ms").to_list() == [None]


def _rec(kind: str, ts: int, content: list, **extra: object) -> str:
    return json.dumps(
        {
            "type": kind,
            "uuid": f"u{ts}",
            "sessionId": "main",
            "timestamp": f"2026-01-01T00:00:{ts:02d}Z",
            "message": {"content": content},
            **extra,
        }
    )


def test_sub_agent_events_name_their_agent_and_the_call_that_spawned_it(tmp_path):
    call = {"type": "tool_use", "id": "t1", "name": "Agent", "input": {"prompt": "go"}}
    result = {"type": "tool_result", "tool_use_id": "t1", "content": "done"}
    (tmp_path / "main.jsonl").write_text(
        _rec("assistant", 1, [call])
        + "\n"
        + _rec("user", 9, [result], toolUseResult={"agentId": "ag1"})
        + "\n"
    )
    (tmp_path / "main").mkdir()
    (tmp_path / "main" / "subagents").mkdir()
    bash = {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "ls"}}
    (tmp_path / "main" / "subagents" / "agent-ag1.jsonl").write_text(
        _rec("assistant", 5, [bash], isSidechain=True, agentId="ag1") + "\n"
    )
    df = read_claude_code(tmp_path)
    rows = {r["tool"] + ":" + r["kind"]: r for r in df.to_dicts()}
    assert rows["Agent:tool_use"]["spawned"] == "ag1"
    assert rows["Agent:tool_use"]["agent"] is None
    assert rows["Agent:tool_result"]["spawned"] is None
    assert rows["Bash:tool_use"]["agent"] == "ag1"
    assert rows["Bash:tool_use"]["session"] == "main"


@pytest.mark.parametrize("use_ir", [True, False])
def test_a_failed_command_retried(use_ir):
    docs = read_claude_code(FIXTURES / "claude_code").to_dicts()
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir, timestamp_field="time")
    q = (
        "SELECT field(kind, tool_use) AND field(outcome, error) AND field(cmd, $c)"
        " FOLLOWED_BY field(kind, tool_use) AND field(cmd, $c) INWINDOW 5"
    )
    assert engine.execute(q) == [["session:5:0", "session:7:0"]]


@pytest.mark.xfail(
    strict=True,
    reason="a literal field() on a list-valued column matches nothing, while "
    "a variable binds its elements (graph #133)",
)
def test_literal_field_matches_an_element_of_a_list_column():
    docs = [{"id": 1, "text": "x", "tags": ["cd", "git"], "timestamp": 1}]
    engine = PrismQLEngine(MemoryBackend(docs))
    assert engine.execute("SELECT field(tags, git)") == [[1]]
