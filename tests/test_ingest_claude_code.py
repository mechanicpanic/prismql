"""Claude Code transcripts → stream (graph #54, format #56)."""

from pathlib import Path

import pytest

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.ingest.sources.claude_code import read_claude_code

FIXTURE = Path(__file__).parent / "fixtures" / "claude_code"


def test_one_row_per_block_in_time_order():
    df = read_claude_code(FIXTURE)
    kinds = df.get_column("kind").to_list()
    assert kinds == [
        "prompt",
        "thinking",
        "text",
        "tool_use",
        "tool_result",
        "tool_use",
        "tool_result",
        "tool_use",
        "tool_result",
        "text",
    ]
    assert df.get_column("position").to_list() == list(range(10))
    assert df.get_column("project").unique().to_list() == ["claude_code"]
    assert df.get_column("session").unique().to_list() == ["s1"]


def test_tool_result_carries_the_tool_name_and_error_flag():
    df = read_claude_code(FIXTURE / "session.jsonl")
    results = df.filter(df.get_column("kind") == "tool_result")
    assert results.get_column("tool").to_list() == ["Read", "Bash", "Bash"]
    assert results.get_column("error").to_list() == [False, True, False]
    assert results.get_column("text").to_list()[1] == "FAILED tests/test_x.py::test_x"


def test_unknown_block_raises(tmp_path):
    bad = tmp_path / "s.jsonl"
    bad.write_text(
        '{"type":"assistant","uuid":"a","sessionId":"s","timestamp":"2026-01-01T00:00:00Z",'
        '"message":{"content":[{"type":"hologram"}]}}\n'
    )
    with pytest.raises(ValueError, match="unknown content block type 'hologram'"):
        read_claude_code(bad)


@pytest.mark.parametrize("use_ir", [True, False])
def test_the_stream_answers_a_question(use_ir):
    docs = read_claude_code(FIXTURE).to_dicts()
    engine = PrismQLEngine(MemoryBackend(docs), use_ir=use_ir, timestamp_field="time")
    # A tool failed, then the same tool was retried within 3 events.
    q = (
        "SELECT field(kind, tool_result) AND field(error, true) AND field(tool, $t)"
        " FOLLOWED_BY field(kind, tool_use) AND field(tool, $t) INWINDOW 3"
    )
    groups = engine.execute(q)
    assert len(groups) == 1
    ids = df_ids(docs, groups[0])
    assert ids == ["u3:0", "a3:0"]


def df_ids(docs, group):
    by_id = {d["id"]: d for d in docs}
    return [by_id[i]["id"] for i in group]
