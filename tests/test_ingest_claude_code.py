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
    assert groups == [["session:6:0", "session:7:0"]]


def test_records_may_repeat_their_uuid_within_and_across_files(tmp_path):
    line = FIXTURE.joinpath("session.jsonl").read_text().splitlines()[2]
    (tmp_path / "agent-x.jsonl").write_text(line + "\n" + line + "\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "agent-x.jsonl").write_text(line + "\n")
    df = read_claude_code(tmp_path)
    assert df.height == 9  # three blocks: twice in one file, once in a same-named file
    assert df.get_column("id").n_unique() == 9
    assert df.get_column("uuid").unique().to_list() == ["a1"]


def test_truncated_line_and_lone_surrogate_do_not_abort(tmp_path, capsys):
    good = FIXTURE.joinpath("session.jsonl").read_text().splitlines()[1]
    surrogate = good.replace("fix the failing test", "bad \\ud83d char")
    (tmp_path / "s.jsonl").write_text(good + "\n" + surrogate + "\n" + good[:40] + "\n")
    df = read_claude_code(tmp_path)
    assert df.height == 2
    assert "\ufffd" in df.get_column("text").to_list()[1]
    (tmp_path / "empty").mkdir()
    assert read_claude_code(tmp_path / "empty").height == 0
    assert "<truncated line>×1" in capsys.readouterr().out


def test_harness_injected_user_records_are_not_prompts(tmp_path):
    """Skill text (isMeta) and task notifications (origin.kind) ride as user
    records; a person's own message — pasted text included — is a prompt."""
    import json

    recs = [
        ({"origin": {"kind": "human"}}, "fix the parser"),
        ({"isMeta": True}, "Base directory for this skill: ..."),
        ({"origin": {"kind": "task-notification"}}, "<task-notification>..."),
        (
            {"origin": {"kind": "human"}},
            '<pasted_content id="x">a note</pasted_content>',
        ),
        ({}, "an older log without origin"),
        ({"isCompactSummary": True}, "This session is being continued ..."),
    ]
    log = tmp_path / "s.jsonl"
    log.write_text(
        "\n".join(
            json.dumps(
                {
                    "type": "user",
                    "uuid": f"u{i}",
                    "sessionId": "s",
                    "timestamp": f"2026-01-01T00:00:0{i}Z",
                    "message": {"content": text},
                    **extra,
                }
            )
            for i, (extra, text) in enumerate(recs)
        )
    )
    kinds = read_claude_code(log).get_column("kind").to_list()
    assert kinds == ["prompt", "injected", "injected", "prompt", "prompt", "injected"]
