# PrismQL - Pattern Recognition in Sequential Messages Query Language

PrismQL is a domain-specific language for pattern matching and retrieval in conversational data. It's designed to work with any search backend, making it perfect for analyzing chat logs, support conversations, or any sequential message data.

<p align="center">
  <img src="docs/assets/repl.svg" alt="PrismQL REPL running a cross-corpus lead-lag query: news mentioning sanctions FOLLOWED_BY panic on a retail feed DURING 4 hours" width="780">
</p>

## Features

- **Search Backend Agnostic**: Works with OpenSearch, Elasticsearch, or any custom search engine
- **Advanced Pattern Matching**: Find complex patterns across message sequences
- **Window-based Grouping**: Group related messages within time/distance windows
- **NLP Integration**: Optional NLP backend for entity recognition and linguistic analysis
- **User Dictionaries**: Define custom word lists for domain-specific searches
- **Boolean Logic**: Combine conditions with AND, OR, NOT operators

## Installation

```bash
pip install prismql

# With OpenSearch support
pip install prismql[opensearch]

# With Elasticsearch support
pip install prismql[elasticsearch]

# With NLP support (spaCy)
pip install prismql[nlp]

# All extras
pip install prismql[all]
```

## Server & agent integration

Run PrismQL as a local HTTP server (agents and tools query it instead of
embedding Python):

```bash
pip install prismql[server]
prismql-server --config prismql.toml    # POST /evaluate, GET /reference
```

MCP-native agents get a single `evaluate()` tool via the stdio shim:

```bash
pip install prismql[server,mcp]
prismql-mcp    # finds the server via PRISMQL_SERVER_URL (default :8901)
```

`prismql.toml` holds all state — backend type, data file, dictionaries,
timestamp field:

```toml
[server]
port = 8901

[backend]
type = "rust_memory"        # or: memory
data = "events.jsonl"       # .json / .jsonl / .csv / .parquet

[dictionaries]
spikes = ["spike", "surge"]
```

`POST /evaluate` returns hydrated event groups; query errors come back as
structured 422s with messages designed for agent self-correction. Requests
may carry a `dictionaries` overlay — term lists merged over the config
dictionaries for that query only — so agents can iterate on the semantic
layer without touching server state.

<p align="center">
  <img src="docs/assets/server.svg" alt="prismql-server answering POST /evaluate with hydrated event groups" width="780">
</p>

## Quick Start

```python
from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Sample conversation data
messages = [
    {"id": 1, "text": "Hello, I need help with my order", "user": "customer1"},
    {"id": 2, "text": "Sure, what's your order number?", "user": "support"},
    {"id": 3, "text": "It's ORDER-12345", "user": "customer1"},
    {"id": 4, "text": "Let me check that for you", "user": "support"},
    {"id": 5, "text": "Can you tell me the status?", "user": "customer1"},
]

# Create in-memory backend for testing
backend = MemoryBackend(messages)

# Initialize PrismQL engine
engine = PrismQLEngine(search_backend=backend)

# Find all questions in the conversation (fluent syntax!)
results = engine.execute("SELECT is_question()")
print(results)  # [[2], [5]]

# Find messages from customer1 that contain questions
results = engine.execute("SELECT from(customer1) AND is_question()")
print(results)  # [[5]]

# Find question-answer pairs within 2 messages of each other
results = engine.execute("SELECT is_question(), from(support) INWINDOW 2")
print(results)  # [[2, 4]]
```

## How fast is it?

The VLDB 2023 row-pattern-recognition flagship query (robbery → battery →
vehicle theft, co-located, within 30 minutes) over the full City of
Chicago crime corpus — 8.5M events, 25 years: **PrismQL answers in ~5
seconds**, in exact match-count agreement with the optimized SQL
formulation, while the naive SQL join does not finish in 90 minutes. The
full comparison against DuckDB, SQLite, Flink MATCH_RECOGNIZE, and
Elastic EQL is in [docs/CHICAGO_BENCHMARK.md](docs/CHICAGO_BENCHMARK.md).

## Query Language Syntax

### Basic Structure
```
SELECT <conditions> [INWINDOW <window_size>]
```

### Conditions

**New Fluent Syntax (Recommended):**
- **contains(dict_name)** - Messages containing words from a dictionary
- **from(username)** - Messages from specific user
- **mentions_user(username)** - Messages mentioning a user
- **is_question()** - Messages containing questions
- **mentions_date()** - Messages containing dates
- **mentions_time()** - Messages containing times
- **mentions_place()** - Messages containing locations
- **mentions_org()** - Messages containing organizations
- **contains_link()** - Messages containing URLs

**Note**: Legacy syntax (`byuser()`, `haswordofdict()`, `hasquestion()`) is deprecated. See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details.

### Boolean Operators

```prismql
-- AND operator (fluent syntax)
SELECT from(alice) AND is_question()

-- OR operator
SELECT from(alice) OR from(bob)

-- NOT operator
SELECT NOT from(bot)

-- Complex combinations
SELECT (from(alice) OR from(bob)) AND is_question()
```

### Window Constraints

The `INWINDOW` clause groups messages that appear within N positions of each other:

```prismql
-- Find questions followed by answers within 5 messages (fluent syntax)
SELECT is_question(), contains(answers) INWINDOW 5
```

### Multiple Restrictions

Comma-separated restrictions find combinations:

```prismql
-- Find customer question + support response + resolution (fluent syntax)
SELECT from(customer) AND is_question(),
       from(support),
       contains(resolved)
       INWINDOW 10
```

### Subqueries

Parentheses create subqueries that are evaluated independently:

```prismql
-- Complex multi-stage pattern (fluent syntax)
SELECT
  (SELECT from(customer), contains(problem) INWINDOW 3);
  (SELECT from(support), contains(solution) INWINDOW 5)
  INWINDOW 20
```

## Using Custom Backends

### OpenSearch Backend

```python
from opensearchpy import OpenSearch
from prismql import PrismQLEngine
from prismql.backends.opensearch import OpenSearchBackend

# Connect to OpenSearch
client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,
)

# Create backend
backend = OpenSearchBackend(client, index_name="chat-logs")

# Create engine
engine = PrismQLEngine(search_backend=backend)

# Execute queries
results = engine.execute("SELECT contains(errors) INWINDOW 50")
```

### Creating Custom Backends

Implement the `SearchBackend` interface:

```python
from prismql.backends.base import SearchBackend
from typing import Set

class MyCustomBackend(SearchBackend):
    def search_text(self, terms, field="text", operator="OR") -> Set[int]:
        # Your implementation
        pass

    def search_by_field(self, field, value, exact=True) -> Set[int]:
        # Your implementation
        pass

    def get_total_documents(self) -> int:
        # Your implementation
        pass

    def get_all_document_ids(self, limit=None) -> Set[int]:
        # Your implementation
        pass
```

## User Dictionaries

Define custom word lists for domain-specific searches:

```python
# Add dictionaries
engine.add_dictionary("tech_terms", ["API", "backend", "frontend", "database"])
engine.add_dictionary("problems", ["error", "broken", "failed", "issue"])

# Use in queries
results = engine.execute("""
    SELECT contains(problems), contains(tech_terms) INWINDOW 10
""")

# List all dictionaries
all_dicts = engine.get_dictionaries()
```

## NLP Integration

For advanced linguistic analysis, add an NLP backend:

```python
from prismql.backends.spacy import SpacyNLPBackend

# Initialize spaCy backend
nlp_backend = SpacyNLPBackend(model="en_core_web_sm")

# Create engine with NLP support
engine = PrismQLEngine(
    search_backend=backend,
    nlp_backend=nlp_backend
)

# Now you can use NER-based conditions
results = engine.execute("""
    SELECT hasdate(), hasorganization() INWINDOW 5
""")
```

## Precomputed Indexes

For better performance on large datasets, precompute NLP features:

```python
from prismql.backends.base import PrecomputedIndexes

# Create indexes during data ingestion
indexes = PrecomputedIndexes(
    entities={
        "DATE": {1, 5, 12},      # Message IDs containing dates
        "ORG": {3, 7, 15},       # Message IDs containing organizations
    },
    questions={2, 5, 9, 14},     # Message IDs containing questions
)

# Use precomputed indexes
engine = PrismQLEngine(
    search_backend=backend,
    precomputed_indexes=indexes
)
```

## Advanced Examples

### Customer Support Analysis
```python
# Find escalation patterns
escalation_query = """
SELECT
  (SELECT from(customer) AND contains(complaint_words) INWINDOW 3);
  (SELECT from(customer) AND contains(frustration_words));
  (SELECT from(support) AND contains(escalation_words))
  INWINDOW 20
"""

# Find successful resolutions
resolution_query = """
SELECT
  contains(problem_words),
  from(support) AND contains(solution_words),
  from(customer) AND contains(satisfaction_words)
  INWINDOW 30
"""
```

### Security Analysis
```python
# Find potential security discussions
security_query = """
SELECT
  contains(security_terms) AND (contains_link() OR contains(credentials)),
  is_question()
  INWINDOW 10
"""
```

## Development

### Setup
```bash
# Install with uv (recommended)
uv sync --dev

# Or with pip
pip install -e .[dev]
```

### Running Tests
```bash
# With uv
uv run pytest

# With pip
pytest

# Run with coverage
uv run pytest --cov=prismql
```

### Code Formatting and Linting
```bash
# Format code with ruff
uv run ruff format .

# Check and fix linting issues
uv run ruff check . --fix

# Run both before committing
uv run ruff format . && uv run ruff check . --fix
```

### Building Documentation
```bash
# Install docs dependencies
pip install -e .[docs]

# Build docs
cd docs && make html
```

## Related Repositories

- **[prismql-research](../prismql-research)** - Research, experiments, and benchmarks for PrismQL
  - LLM query generation experiments
  - Performance benchmarks
  - Training data for LoRA fine-tuning
  - Research applications and use cases
  - Academic papers and implementation notes

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

PrismQL is inspired by the query language from the Chat Corpora Annotator project and uses ANTLR4 for parsing.
