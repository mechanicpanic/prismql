import json
import re
from pathlib import Path

from antlr4 import CommonTokenStream, InputStream

from prismql.dialects.pipe import parse_pipe
from prismql.engine import PrismQLEngine  # noqa: F401 (engines via config)
from prismql.grammar.generated.PrismQLLexer import PrismQLLexer
from prismql.grammar.generated.PrismQLParser import PrismQLParser
from prismql.ir.lower import lower_query
from prismql.server.config import build_engine, load_config

HERE = Path(__file__).parent
raw = (HERE / "web/examples.js").read_text(encoding="utf-8")
examples = json.loads(re.search(r"=\s*(\{.*\});", raw, re.DOTALL).group(1))
config = load_config(HERE / "prismql.toml")

failures = []
for corpus, entries in examples.items():
    engine = build_engine(config.corpus(corpus))
    for ex in entries:
        parser = PrismQLParser(
            CommonTokenStream(PrismQLLexer(InputStream(ex["classic"])))
        )
        if lower_query(parser.parse().query()) != parse_pipe(ex["pipe"]):
            failures.append((corpus, ex["label"], "IR mismatch"))
            continue
        result = engine.execute(ex["pipe"])
        # Aggregate/grouped results define no __len__, so the old len()
        # check silently passed them as "1 results" even when empty —
        # inspect their actual contents instead.
        if hasattr(result, "__len__"):
            n = len(result)
        else:
            d = result.to_dict()
            if "grouped_values" in d or "group_counts" in d:
                n = len(d.get("grouped_values") or d.get("group_counts") or {})
            else:
                n = 1 if d.get("value") else 0
        print(f"  [{corpus}] {ex['label']}: {n} results")
        if n == 0:
            failures.append((corpus, ex["label"], "empty result"))

print(f"failures: {len(failures)}")
for f in failures:
    print(" ", f)
raise SystemExit(1 if failures else 0)
