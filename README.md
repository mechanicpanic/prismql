# PrismQL - Pattern Recognition in Sequential Messages Query Language

PrismQL is a domain-specific language for pattern matching and retrieval in conversational data. It's designed to work with any search backend, making it perfect for analyzing chat logs, support conversations, or any sequential message data.

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

# Find all questions in the conversation
results = engine.execute("SELECT hasquestion()")
print(results)  # [[2], [5]]

# Find messages from customer1 that contain questions
results = engine.execute("SELECT byuser(customer1) AND hasquestion()")
print(results)  # [[5]]

# Find question-answer pairs within 2 messages of each other
results = engine.execute("SELECT hasquestion(), byuser(support) INWIN 2")
print(results)  # [[2, 4]]
```

## Query Language Syntax

### Basic Structure
```
SELECT <conditions> [INWIN <window_size>]
```

### Conditions

- **haswordofdict(dict_name)** - Messages containing words from a dictionary
- **byuser(username)** - Messages from specific user
- **hasusermentioned(username)** - Messages mentioning a user
- **hasquestion()** - Messages containing questions
- **hasdate()** - Messages containing dates
- **hastime()** - Messages containing times
- **haslocation()** - Messages containing locations
- **hasorganization()** - Messages containing organizations
- **hasurl()** - Messages containing URLs

### Boolean Operators

```sql
-- AND operator
SELECT byuser(alice) AND hasquestion()

-- OR operator  
SELECT byuser(alice) OR byuser(bob)

-- NOT operator
SELECT NOT byuser(bot)

-- Complex combinations
SELECT (byuser(alice) OR byuser(bob)) AND hasquestion()
```

### Window Constraints

The `INWIN` clause groups messages that appear within N positions of each other:

```sql
-- Find questions followed by answers within 5 messages
SELECT hasquestion(), haswordofdict(answers) INWIN 5
```

### Multiple Restrictions

Comma-separated restrictions find combinations:

```sql
-- Find customer question + support response + resolution
SELECT byuser(customer) AND hasquestion(), 
       byuser(support),
       haswordofdict(resolved) 
       INWIN 10
```

### Unrelated Restrictions (UNR)

The `UNR` flag generates all permutations instead of sliding windows:

```sql
-- Find any combination of these conditions
SELECT hasquestion(), hasurl(), hasdate() UNR
```

### Subqueries

Parentheses create subqueries that are evaluated independently:

```sql
-- Complex multi-stage pattern
SELECT 
  (SELECT byuser(customer), haswordofdict(problem) INWIN 3);
  (SELECT byuser(support), haswordofdict(solution) INWIN 5)
  INWIN 20
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
results = engine.execute("SELECT haswordofdict(errors) INWIN 50")
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
    SELECT haswordofdict(problems), haswordofdict(tech_terms) INWIN 10
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
    SELECT hasdate(), hasorganization() INWIN 5
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
  (SELECT byuser(customer) AND haswordofdict(complaint_words) INWIN 3);
  (SELECT byuser(customer) AND haswordofdict(frustration_words));
  (SELECT byuser(support) AND haswordofdict(escalation_words))
  INWIN 20
"""

# Find successful resolutions
resolution_query = """
SELECT
  haswordofdict(problem_words),
  byuser(support) AND haswordofdict(solution_words),
  byuser(customer) AND haswordofdict(satisfaction_words)
  INWIN 30
"""
```

### Security Analysis
```python
# Find potential security discussions
security_query = """
SELECT 
  haswordofdict(security_terms) AND (hasurl() OR haswordofdict(credentials)),
  hasquestion()
  INWIN 10
"""
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=prismql
```

### Building Documentation
```bash
# Install docs dependencies
pip install -e .[docs]

# Build docs
cd docs && make html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

PrismQL is inspired by the query language from the Chat Corpora Annotator project and uses ANTLR4 for parsing.