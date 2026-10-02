"""``prismql ingest … --judge questions.toml``: a local decision model
answers typed questions about each event; the answers become columns a
query reads with ``field()`` (graph @aleph/prismql, #154)."""

import json
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import pytest

from prismql.ingest.judge import JUDGE_KEY, judge, load_questions

QUESTIONS = """
[questions.phase]
type = "choice"
instructions = "What is the agent doing?"
where = { role = "assistant" }
min_confidence = 0.6
[questions.phase.criteria]
progressing = "moving the task forward"
giving_up = "abandoning the task"

[questions.claims_done]
type = "noul"
instructions = "Does the agent claim the task is done?"
where = { role = "assistant" }
min_confidence = 0.5

[questions.mood]
type = "score"
instructions = "How frustrated is the person?"
where = { role = "user" }
criteria = ["calm", "frustrated", "angry"]
"""

EVENTS = pl.DataFrame(
    {
        "id": ["1", "2", "3", "4"],
        "role": ["user", "assistant", "assistant", "assistant"],
        "text": ["fix it!", "I give up.", "Done, tests pass.", "Hmm."],
    }
)


def _fake(state: str | dict, questions: dict) -> dict:
    """Answers keyed on the text, as the server would shape them."""
    text = state if isinstance(state, str) else state["text"]
    answers: dict = {}
    for name, q in questions.items():
        if q["type"] == "noul":
            answers[name] = {"type": "noul", "noul": 0.95 if "Done" in text else 0.4}
        elif q["type"] == "choice":
            pick = "giving_up" if "give up" in text else "progressing"
            conf = 0.3 if text == "Hmm." else 0.9
            answers[name] = {
                "type": "choice",
                "choice": pick,
                "probabilities": dict.fromkeys(q["criteria"], 0.5),
                "confidence": conf,
            }
        else:
            answers[name] = {
                "type": "score",
                "score": 1.2,
                "legend": {"0": "calm", "1": "frustrated", "2": "angry"},
                "probabilities": {"0": 0.1, "1": 0.8, "2": 0.1},
                "confidence": 0.7,
            }
    return {"model": "fake-decider", "answers": answers}


@pytest.fixture
def questions(tmp_path: Path) -> dict:
    p = tmp_path / "q.toml"
    p.write_text(QUESTIONS)
    return load_questions(p)


def test_each_question_is_asked_only_where_it_applies(questions):
    asked: list[tuple[str, list[str]]] = []

    def post(state: str, qs: dict) -> dict:
        asked.append((state, sorted(qs)))
        return _fake(state, qs)

    judge(EVENTS, questions, post=post)
    assert asked == [
        ("fix it!", ["mood"]),
        ("I give up.", ["claims_done", "phase"]),
        ("Done, tests pass.", ["claims_done", "phase"]),
        ("Hmm.", ["claims_done", "phase"]),
    ]


def test_answers_become_labels_and_probabilities(questions):
    df, _stamp = judge(EVENTS, questions, post=_fake)
    assert df["phase"].to_list() == [None, "giving_up", "progressing", "unsure"]
    assert df["phase_p"].to_list() == [None, 0.9, 0.9, 0.3]
    # p(true)=0.4 is |2p-1|=0.2 sure, under 0.5: unsure, not "no"
    assert df["claims_done"].to_list() == [None, "unsure", "yes", "unsure"]
    assert df["claims_done_p"].to_list() == [None, 0.4, 0.95, 0.4]
    # a score's label is its most likely level
    assert df["mood"].to_list() == ["frustrated", None, None, None]


def test_the_stamp_names_the_model_and_the_exact_questions(questions):
    _df, stamp = judge(EVENTS, questions, post=_fake)
    assert stamp["model"] == "fake-decider"
    assert stamp["questions"] == questions
    assert len(stamp["sha256"]) == 64


def test_a_bad_question_file_is_refused(tmp_path):
    p = tmp_path / "q.toml"
    p.write_text('[questions.x]\ntype = "choice"\ninstructions = "?"\n')
    with pytest.raises(ValueError, match="criteria"):
        load_questions(p)
    p.write_text('[questions.text]\ntype = "noul"\ninstructions = "?"\n')
    with pytest.raises(ValueError, match="column"):
        judge(EVENTS, load_questions(p), post=_fake)


def test_the_cli_writes_the_columns_and_the_stamp(tmp_path, monkeypatch):
    from prismql.ingest import cli
    from prismql.ingest import judge as judge_module

    src = tmp_path / "events.jsonl"
    rows = [
        {"id": r["id"], "time": f"2026-10-02T10:0{i}:00Z", **r}
        for i, r in enumerate(EVENTS.to_dicts())
    ]
    src.write_text("\n".join(json.dumps(r) for r in rows))
    qfile = tmp_path / "q.toml"
    qfile.write_text(QUESTIONS)
    monkeypatch.setattr(judge_module, "http_post", lambda _url: _fake)
    dst = tmp_path / "out.parquet"
    assert (
        cli.run(
            [
                "table",
                str(src),
                str(dst),
                "--id",
                "id",
                "--time",
                "time",
                "--keep",
                "role,text",
                "--judge",
                str(qfile),
            ]
        )
        == 0
    )
    table = pq.read_table(dst)
    assert "phase" in table.column_names and "claims_done_p" in table.column_names
    stamp = json.loads(table.schema.metadata[JUDGE_KEY])
    assert stamp["model"] == "fake-decider"


def test_max_chars_sends_only_the_start_of_a_long_text(tmp_path):
    p = tmp_path / "q.toml"
    p.write_text(
        '[questions.done]\ntype = "noul"\ninstructions = "Done?"\nmax_chars = 5\n'
    )
    seen: list = []

    def post(state: str, _qs: dict) -> dict:
        seen.append(state)
        return {"model": "m", "answers": {"done": {"type": "noul", "noul": 0.9}}}

    judge(
        pl.DataFrame({"id": ["1"], "text": ["Done. And then a long list"]}),
        load_questions(p),
        post=post,
    )
    assert seen == ["Done."]
