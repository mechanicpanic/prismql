"""Export the demo corpora from the research repo's benchmark data.

Run once on Aleph's machine; the outputs are committed. Both sources are
publishable: the FCC subset is Aleph's own annotated dataset, the Chicago
data is public domain (City of Chicago open data).
"""

import csv
import json
from pathlib import Path

RESEARCH = Path.home() / "Projects/research/prismql-research/benchmarks"
OUT = Path(__file__).parent / "data"
CHICAGO_ROWS = 50_000


def export_fcc() -> int:
    src = RESEARCH / "fcc-situations/messages.jsonl"
    docs = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        docs.append(
            {
                "id": m["id"],
                "user": m["user"],
                "text": m["text"],
                "timestamp": m["timestamp"],
                "topic": m["topic"],
            }
        )
    (OUT / "fcc.json").write_text(json.dumps(docs, ensure_ascii=False))
    return len(docs)


def export_chicago() -> int:
    src = RESEARCH / "chicago-crime/data/tier_100k.flink.csv"
    docs = []
    with src.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            docs.append(
                {
                    "id": int(row[0]),
                    "type": row[1],
                    "key": row[2],
                    "timestamp": int(row[3]),
                }
            )
            if len(docs) >= CHICAGO_ROWS:
                break
    (OUT / "chicago.json").write_text(json.dumps(docs))
    return len(docs)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print(f"fcc: {export_fcc()} messages")
    print(f"chicago: {export_chicago()} events")
