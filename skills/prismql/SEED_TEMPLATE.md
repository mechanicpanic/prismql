<!--
Template for application-specific PrismQL skills.
Fill every {{placeholder}}, delete instructional comments, save as
.claude/skills/prismql-{{dataset_slug}}/SKILL.md in the target project,
and copy LANGUAGE_REFERENCE.md into the same directory. Use cp -L: in the
source repo it is a symlink pointing above the skill folder, and a copy
that keeps the link (macOS cp -R, GNU cp -r and -R alike) points at
nothing from the new location.
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
| `id` | {{col}} | {{unique label; strings fine. Stream order is load order, not id order}} |
| `text` | {{col(s)}} | {{e.g. headline + body concatenated; only this field is text-indexed}} |
| `user` | {{col}} | {{what from() means here: ticker? author? service?}} |
| `timestamp` | {{col}} | {{unit; what DURING means here}} |

Data lives at: `{{path_or_table}}` ({{format}}, ~{{N}} records).

## How to run a query

<!-- Keep ONE of the two blocks below — whichever this project actually
uses — and delete the other. If the project runs a server, that is the
better default: warm engine, no per-query load cost, hydrated results. -->

**Server** (preferred), on port {{port}} — say the port here explicitly,
it is the one thing a fresh agent cannot find out for itself.
`curl -s localhost:{{port}}/health` to check it is up, `GET /schema` for
the live field list, then:

```bash
curl -s -X POST localhost:{{port}}/evaluate -H 'Content-Type: application/json' \
  -d '{"query": "{{example_query}}"}'
```

Body fields besides `query`: `max_results`, `hydrate` (`false` → ids only),
`dictionaries`, `output`, `corpus`, `label`.

```toml
# {{path}}/prismql.toml — the server's whole state
[server]
port = {{port}}

[backend]
type = "{{backend}}"
data = "{{data_path}}"
timestamp_fields = ["{{ts_col}}"]     # parsed on load

[engine]
timestamp_field = "{{ts_col}}"        # the axis DURING measures on
{{quantifier_ceiling = N — only if this dataset needs open ranges; see quirks}}

[dictionaries]
{{name}} = [{{terms}}]
```

Both timestamp keys are needed: without `[engine].timestamp_field` a
`DURING` query returns an empty result rather than an error. `GET /schema`
is the check — its `timestamp_field` must name a field listed in the same
response's `fields` block (the unset default is `timestamp`). Iterate on
term lists in-band with `"dictionaries": {"{{name}}": ["term", …]}` in the
request body (that query only), then persist the stable ones here.
`max_results` caps the groups in a response — use `AGGREGATE count()` for a
total.

**Inline Python** (no server):

```python
{{Complete, runnable loader: read files → docs list → backend → engine,
including the full user_dictionaries dict inline. Must run as-is with
`uv run python`. Backend choice: {{backend}} because {{reason}}.}}
```

## Dictionaries

<!-- The semantic layer. Keep definitions IN the config/loader above; list meanings here. -->

| Dictionary | Meaning | Sample terms |
|---|---|---|
| `{{name}}` | {{what it captures}} | {{3 terms}} |

## Verified example queries

<!-- Paste REAL output from smoke tests. At least: one filter, one INWINDOW,
     one FOLLOWED_BY. Add the dataset's signature pattern if it has one —
     a same-entity pattern is usually the one worth showing, and a variable
     binds the value slot of field() as well as from():
     field(kind, delete) AND field(page, $p) FOLLOWED_BY
     field(kind, save) AND field(page, $p) DURING 10 minutes. -->

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
- {{If any useful query needs an open range like `{2,}`: it is rejected
  (OPEN_QUANTIFIER) unless quantifier_ceiling is set — say what it is set
  to and why, or write bounded `{2,m}` in the examples.}}
- {{anything that surprised you during smoke-testing}}
