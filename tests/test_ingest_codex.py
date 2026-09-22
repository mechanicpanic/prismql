"""Codex rollouts → stream (graph #54, format #57)."""

import json
from pathlib import Path

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.ingest.sources.codex import read_codex

FIXTURE = Path(__file__).parent / "fixtures" / "codex"


def test_one_row_per_item_with_project_and_model():
    df = read_codex(FIXTURE)
    assert df.get_column("kind").to_list() == [
        "developer",
        "prompt",
        "thinking",
        "tool_use",
        "tool_result",
        "tool_use",
        "tool_result",
        "tool_use",
        "tool_result",
        "text",
    ]
    assert df.get_column("project").unique().to_list() == ["proj"]
    assert df.get_column("model").unique().to_list() == ["gpt-5.4"]
    assert df.get_column("session").unique().to_list() == ["abc"]


def test_tool_results_resolve_names_and_exit_codes():
    df = read_codex(FIXTURE)
    results = df.filter(df.get_column("kind") == "tool_result")
    assert results.get_column("tool").to_list() == [
        "exec_command",
        "apply_patch",
        "exec_command",
    ]
    assert results.get_column("error").to_list() == [True, False, False]


def test_exit_code_phrase_inside_a_successful_output_is_not_an_error(tmp_path):
    call = {
        "type": "function_call",
        "name": "exec_command",
        "arguments": "{}",
        "call_id": "c",
    }
    output = {
        "type": "function_call_output",
        "call_id": "c",
        "output": "Chunk ID: 1\nProcess exited with code 0\nOutput:\n"
        "log says: Process exited with code 1",
    }
    rows = [
        json.dumps({"type": "response_item", "timestamp": ts, "payload": payload})
        for ts, payload in (
            ("2026-01-01T00:00:00Z", call),
            ("2026-01-01T00:00:01Z", output),
        )
    ]
    (tmp_path / "rollout-a.jsonl").write_text("\n".join(rows) + "\n")
    df = read_codex(tmp_path)
    assert df.filter(df.get_column("kind") == "tool_result").get_column(
        "error"
    ).to_list() == [False]


def test_error_column_is_a_bool_on_both_harnesses():
    from prismql.ingest.sources.claude_code import read_claude_code

    for df in (read_codex(FIXTURE), read_claude_code(FIXTURE.parent / "claude_code")):
        results = df.filter(df.get_column("kind") == "tool_result")
        assert results.get_column("error").null_count() == 0


def test_unknown_item_raises(tmp_path):
    bad = tmp_path / "rollout-x.jsonl"
    bad.write_text(
        '{"type":"response_item","timestamp":"2026-01-01T00:00:00Z","payload":{"type":"teleport"}}\n'
    )
    with pytest.raises(ValueError, match="unknown response item type 'teleport'"):
        read_codex(bad)


@pytest.mark.parametrize("use_ir", [True, False])
def test_same_question_as_claude_code(use_ir):
    docs = read_codex(FIXTURE).to_dicts()
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir, timestamp_field="time")
    q = (
        "SELECT field(kind, tool_result) AND field(error, true) AND field(tool, $t)"
        " FOLLOWED_BY field(kind, tool_use) AND field(tool, $t) INWINDOW 3"
    )
    groups = engine.execute(q)
    assert groups == [
        ["rollout-2026-03-17T18-19-47-abc:8", "rollout-2026-03-17T18-19-47-abc:11"]
    ]
