# PrismQL Quickstart Guide

Get started with PrismQL in 5 minutes for your experiment prototype.

## Installation

### Option 1: Install from local development (editable mode)
```bash
cd /Users/asmirnov/Projects/vibes/prismql
uv pip install -e .
```

### Option 2: Install with Rust backend (recommended for performance)
```bash
# Install base package
uv pip install -e .

# Install Rust backend (50-100x faster for complex queries)
uv pip install maturin
uv run python -m maturin develop --release --manifest-path ../prismql-rust/Cargo.toml
```

## Basic Usage

### 1. Import and Setup

```python
from prismql import PrismQLEngine
from prismql.backends import MemoryBackend

# Prepare your messages
messages = [
    {'id': 1, 'user': 'alice', 'text': 'Hello everyone'},
    {'id': 2, 'user': 'bob', 'text': 'Hi alice, how are you?'},
    {'id': 3, 'user': 'charlie', 'text': 'Hey there'},
    {'id': 4, 'user': 'alice', 'text': 'I need help with the project'},
]

# Create backend and engine
backend = MemoryBackend(messages)
engine = PrismQLEngine(backend)
```

### 2. Run Queries

```python
# Find messages from a specific user
result = engine.execute("SELECT from(alice)")
print(f"Found {len(result)} messages from alice")

# Find messages containing specific words
user_dicts = {"greetings": ["hello", "hi", "hey"]}
engine = PrismQLEngine(backend, user_dictionaries=user_dicts)
result = engine.execute("SELECT contains(greetings)")

# Boolean operations
result = engine.execute("SELECT from(alice) AND contains(greetings)")

# Window constraints - find alice and bob messages within 3 positions
result = engine.execute("SELECT from(alice), from(bob) INWIN 3")

# Sequential patterns - alice followed by bob within 5 positions
result = engine.execute("SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 5")
```

### 3. Use Rust Backend (High Performance)

```python
from prismql.backends import RustMemoryBackend

# Drop-in replacement for MemoryBackend
backend = RustMemoryBackend(messages)
engine = PrismQLEngine(backend)

# Same API, 50-100x faster for complex queries!
result = engine.execute("SELECT from(alice), from(bob) INWIN 10")
```

## For Your Experiment

### Load Your Data

```python
# Example: Load from CSV
import csv

messages = []
with open('your_chat_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        messages.append({
            'id': int(row['id']),
            'user': row['user'],
            'text': row['text'],
            # Add any other fields you need
        })

backend = MemoryBackend(messages)
engine = PrismQLEngine(backend)
```

### Define Custom Dictionaries

```python
# Define your domain-specific word groups
user_dicts = {
    "questions": ["how", "what", "why", "when", "where"],
    "problems": ["error", "issue", "bug", "problem", "broken"],
    "solutions": ["fixed", "solved", "resolved", "working"],
    "greetings": ["hello", "hi", "hey", "greetings"],
}

engine = PrismQLEngine(backend, user_dictionaries=user_dicts)

# Now you can use them in queries
result = engine.execute("SELECT contains(problems)")
```

### Run Multiple Queries

```python
queries = [
    "SELECT from(alice)",
    "SELECT contains(problems)",
    "SELECT from(alice), contains(problems) INWIN 5",
    "SELECT from(support) FOLLOWED_BY contains(solutions) WITHIN 10",
]

for query in queries:
    result = engine.execute(query)
    print(f"Query: {query}")
    print(f"Results: {len(result)} groups found")
    print()
```

### Access Results

```python
result = engine.execute("SELECT from(alice)")

# Result is a list of message groups
for group in result:
    print(f"Group: {group}")

    # Get the actual messages
    messages = backend.get_documents(group)
    for msg in messages:
        print(f"  [{msg['id']}] {msg['user']}: {msg['text']}")
```

## Example Experiment Script

```python
from prismql import PrismQLEngine
from prismql.backends import RustMemoryBackend

# Load your data
messages = [
    {'id': 1, 'user': 'user1', 'text': 'I have an error in my code'},
    {'id': 2, 'user': 'support', 'text': 'What error are you seeing?'},
    {'id': 3, 'user': 'user1', 'text': 'TypeError: cannot concatenate'},
    {'id': 4, 'user': 'support', 'text': 'Try using str() to convert'},
    {'id': 5, 'user': 'user1', 'text': 'Thanks! That fixed it'},
]

# Setup
backend = RustMemoryBackend(messages)  # Use fast backend
user_dicts = {
    "problems": ["error", "issue", "bug"],
    "solutions": ["fixed", "solved", "try", "use"],
}
engine = PrismQLEngine(backend, user_dictionaries=user_dicts)

# Find support interactions where problem was resolved
query = """
    SELECT
        from(user1) AND contains(problems),
        from(support) AND contains(solutions)
    INWIN 5
"""

result = engine.execute(query)
print(f"Found {len(result)} support resolution patterns")

for group in result:
    docs = backend.get_documents(group)
    print("\nPattern found:")
    for doc in docs:
        print(f"  [{doc['id']}] {doc['user']}: {doc['text']}")
```

## Next Steps

1. **Explore Examples**: Check `examples/` directory for more patterns
2. **Read Documentation**: See `CLAUDE.md` for comprehensive guide
3. **Run Tests**: `uv run pytest tests/` to see all features in action
4. **Optimize**: Use `RustMemoryBackend` for large datasets

## Common Patterns for Experiments

### Pattern 1: Question-Answer Pairs
```python
result = engine.execute("""
    SELECT is_question() FOLLOWED_BY from(support) WITHIN 3
""")
```

### Pattern 2: Problem Resolution
```python
result = engine.execute("""
    SELECT
        contains(problems),
        contains(solutions)
    INWIN 10
""")
```

### Pattern 3: User Engagement Clusters
```python
result = engine.execute("""
    SELECT from(alice){3} INWIN 20
""")
```

### Pattern 4: Support Response Time
```python
result = engine.execute("""
    SELECT
        from(user) AND contains(questions)
        FOLLOWED_BY from(support)
    WITHIN 5
""")
```

## Tips

- **Start simple**: Test with `MemoryBackend` on small data first
- **Scale up**: Switch to `RustMemoryBackend` for large datasets
- **Use dictionaries**: Define domain-specific word groups upfront
- **Debug queries**: Run `uv run pytest tests/` to see query examples
- **Performance**: Rust backend is 50-100x faster for window operations

Happy experimenting! 🚀
