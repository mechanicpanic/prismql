<!--
Template for application-specific PrismQL skills.
Fill every {{placeholder}}, delete instructional comments, save as
.claude/skills/prismql-{{dataset_slug}}/SKILL.md in the target project,
and copy LANGUAGE_REFERENCE.md into the same directory.
-->
---
name: prismql-{{dataset_slug}}
description: Query the {{dataset_name}} dataset with PrismQL pattern matching. Use when the user asks about patterns, sequences, or co-occurrences in {{dataset_name}} ({{one_line_domain_description}}).
---

# PrismQL × {{dataset_name}}

{{Two sentences: what the dataset contains, what one record represents, and
what ordering means (chronological? per-conversation? per-ticker?).}}

Read `LANGUAGE_REFERENCE.md` in this directory before writing queries.
Chains take one trailing window (`a FOLLOWED_BY b FOLLOWED_BY c INWINDOW 5`)
or per-link windows; the final link must always have one.

## Data location & field mapping

| PrismQL field | Source column | Notes |
|---|---|---|
| `id` | {{col}} | {{sequential int? assigned via enumerate()?}} |
| `text` | {{col(s)}} | {{e.g. headline + body concatenated}} |
| `user` | {{col}} | {{what from() means here: ticker? author? service?}} |
| `timestamp` | {{col}} | {{unit; what DURING means here}} |

Data lives at: `{{path_or_table}}` ({{format}}, ~{{N}} records).

## Loader (verified)

```python
{{Complete, runnable loader: read files → docs list → backend → engine,
including the full user_dictionaries dict inline. Must run as-is with
`uv run python`. Backend choice: {{backend}} because {{reason}}.}}
```

<!-- Alternative to the inline loader: if this project runs prismql-server,
replace the loader with a prismql.toml (backend, data path, dictionaries)
and query via `curl -X POST localhost:{{port}}/evaluate`. Same dictionaries,
warm engine, no per-query load cost. Iterate on dictionaries via the
request-scoped overlay — `"dictionaries": {"name": ["term", …]}` in the
request body (that query only; persist stable ones into prismql.toml).
For batch/mining queries add `"output": "file"` — all groups go to a JSONL
file server-side, the response is just {count, path, preview}.
NOTE: `GET /schema` self-describes the corpus (fields, coverage, example
values, dictionaries) — the field-mapping table below can be generated
from it rather than hand-written, and agents should prefer /schema as the
live source of truth. -->

## Dictionaries

<!-- The semantic layer. Keep definitions IN the loader above; list meanings here. -->

| Dictionary | Meaning | Sample terms |
|---|---|---|
| `{{name}}` | {{what it captures}} | {{3 terms}} |

## Verified example queries

<!-- Paste REAL output from smoke tests. At least: one filter, one INWINDOW,
     one FOLLOWED_BY. Add the dataset's signature pattern if it has one. -->

```python
engine.execute('{{filter_query}}')
# → {{actual output}}

engine.execute('{{inwindow_query}}')
# → {{actual output}}

engine.execute('{{followed_by_query}}')
# → {{actual output}}
```

## Dataset-specific quirks

- {{e.g. "ids restart per conversation — INWINDOW never crosses conversations"}}
- {{e.g. "timestamps are seconds; DURING 1 hour ≈ 40 records at peak volume"}}
- {{anything that surprised you during smoke-testing}}
