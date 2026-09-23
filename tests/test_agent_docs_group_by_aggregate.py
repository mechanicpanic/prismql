"""Agent-facing text (the MCP tool description, the skill and the agent-use
doc) must say what GROUP BY ... AGGREGATE actually does: inline in full AND
kept as a pageable "rows" result under result_id/total — not "no result_id,
not kept" (that claim describes a plain aggregate or a GROUP BY without
AGGREGATE only). Pinned after the answer went stale post-shipping (graph
@aleph/prismql, #90 fix round 1, #2)."""

from pathlib import Path

from prismql.server.mcp import _TOOL_DESCRIPTION

REPO_ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (REPO_ROOT / path).read_text()


def test_mcp_tool_description_says_group_by_aggregate_is_kept():
    assert "GROUP BY ... AGGREGATE" in _TOOL_DESCRIPTION
    assert "kept" in _TOOL_DESCRIPTION.split("GROUP BY ... AGGREGATE", 1)[1][:200]
    assert '"rows"' in _TOOL_DESCRIPTION


def test_skill_doc_says_group_by_aggregate_is_kept():
    text = _text("skills/prismql/SKILL.md")
    assert "GROUP BY" in text and "AGGREGATE" in text
    # the stale claim ("everything except an aggregate or GROUP BY answer")
    # must no longer describe GROUP BY ... AGGREGATE as carrying no id
    assert "GROUP BY ... AGGREGATE" in text


def test_agent_use_doc_says_group_by_aggregate_is_kept():
    text = _text("docs/AGENT-USE.md")
    assert "GROUP BY ... AGGREGATE" in text


# The exact stale sentences each text carried before #90; the positive
# checks above pass even if one of them comes back beside the new wording.
STALE = {
    "src/prismql/server/mcp.py": (
        "Aggregate and GROUP BY\nanswers are small and returned inline only"
    ),
    "skills/prismql/SKILL.md": (
        "except an aggregate or `GROUP BY` answer, which stay small and inline"
    ),
    "docs/AGENT-USE.md": "aggregate or `GROUP BY` answer — those carry no id",
}


def test_the_stale_claims_are_gone():
    for path, sentence in STALE.items():
        text = " ".join(_text(path).split())
        assert " ".join(sentence.split()) not in text, path
