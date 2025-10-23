# PrismQL Interactive REPL

The PrismQL REPL (Read-Eval-Print Loop) provides an interactive environment for writing and testing PrismQL queries in real-time.

## Installation

### Basic Installation

```bash
# Install PrismQL (basic functionality)
uv pip install .
```

### Enhanced REPL Experience

For the best interactive experience with syntax highlighting and advanced features:

```bash
# Install with REPL and highlighting support
uv pip install '.[repl,highlighting]'

# Or use uv's native syntax
uv sync --extra repl --extra highlighting
```

**Note**: In zsh, you must quote the brackets: `'.[repl,highlighting]'`

## Features

### Core Features (Always Available)

- **Interactive Query Execution**: Execute PrismQL queries and see results immediately
- **Query History**: Saved to `~/.prismql_history` (persists across sessions)
- **Error Handling**: Clear syntax and runtime error messages with context
- **Special Commands**: Built-in commands for help, stats, and control
- **Result Formatting**: Automatic formatting for different result types
- **Execution Timing**: See how long each query takes to execute

### Enhanced Features (Requires Optional Dependencies)

With `prompt_toolkit` installed (`[repl]` extra):
- **Line Editing**: Arrow keys, Ctrl+A/E for line navigation
- **History Navigation**: Up/Down arrows to browse query history
- **Multiline Editing**: Edit complex queries across multiple lines
- **Keyboard Shortcuts**: Emacs-style editing shortcuts

With `pygments` installed (`[highlighting]` extra):
- **Syntax Highlighting**: Color-coded query syntax in the prompt
- **Real-time Coloring**: Keywords, strings, and operators highlighted as you type

## Usage

### Starting the REPL

```bash
# Quick start with sample data (10 sample messages)
uv run prismql --sample-data

# Start with empty memory backend
uv run prismql

# Use with custom configuration file
uv run prismql --config config.json

# Specify backend type
uv run prismql --backend memory
```

### Sample Data Mode

The `--sample-data` flag loads 10 sample conversation messages:

```
ID  User      Text
--  --------  ----------------------------------
1   alice     Hello everyone!
2   bob       Hi alice, how are you?
3   alice     I'm good thanks! How about you?
4   bob       Doing well!
5   alice     I have a question about the project
6   charlie   What's your question?
7   alice     When is the deadline?
8   charlie   Next Friday
9   alice     Thanks!
10  bob       Good to know
```

Perfect for testing queries without setting up a backend.

## Special Commands

All special commands start with a backslash (`\`):

| Command | Aliases | Description |
|---------|---------|-------------|
| `\help` | `\h`, `\?` | Show help message with syntax examples |
| `\quit` | `\q`, `\exit` | Exit the REPL |
| `\stats` | - | Show query execution statistics |
| `\clear` | - | Clear the screen |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+D` | Exit the REPL (same as `\quit`) |
| `Ctrl+C` | Cancel current query input |
| `Up/Down` | Navigate query history (with prompt_toolkit) |
| `Ctrl+R` | Reverse search history (with prompt_toolkit) |

## Configuration

### Using a Configuration File

Create a JSON configuration file to customize the REPL backend:

```json
{
  "search_backend": {
    "type": "memory",
    "documents": [
      {"id": 1, "user": "alice", "text": "Hello world"},
      {"id": 2, "user": "bob", "text": "Hi alice!"}
    ]
  },
  "user_dictionaries": {
    "greetings": ["hello", "hi", "hey"],
    "questions": ["what", "when", "where", "how", "why"]
  }
}
```

Then run:

```bash
uv run prismql --config myconfig.json
```

### Backend Configuration Options

#### Memory Backend (Default)

```json
{
  "search_backend": {
    "type": "memory",
    "documents": [
      {"id": 1, "user": "alice", "text": "message text"}
    ],
    "field_mappings": {
      "text": "content",
      "user": "author"
    }
  }
}
```

#### OpenSearch Backend

```json
{
  "search_backend": {
    "type": "opensearch",
    "client": "<opensearch_client_object>",
    "index_name": "conversations",
    "field_mappings": {
      "text": "message_text",
      "user": "username",
      "id": "message_id"
    }
  }
}
```

**Note**: OpenSearch backend requires the client to be instantiated in Python code.

#### User Dictionaries

Define custom word lists for the `contains()` operator:

```json
{
  "user_dictionaries": {
    "greetings": ["hello", "hi", "hey", "good morning"],
    "thanks": ["thank", "thanks", "appreciate"],
    "problems": ["error", "issue", "bug", "problem"]
  }
}
```

Use in queries:

```prismql
SELECT contains(greetings)
SELECT contains(problems) FOLLOWED_BY contains(thanks) WITHIN 5
```

## Query Examples

### Basic Queries

```prismql
-- Find all messages from alice
SELECT from(alice)

-- Find all questions
SELECT is_question()

-- Find messages containing greeting words
SELECT contains(greetings)
```

### Boolean Operations

```prismql
-- Messages from alice OR bob
SELECT from(alice) OR from(bob)

-- Questions from alice
SELECT from(alice) AND is_question()

-- Messages NOT from alice
SELECT NOT from(alice)
```

### Window Queries (Unordered Co-occurrence)

```prismql
-- Alice and bob appearing within 5 messages (any order)
SELECT from(alice), from(bob) INWIN 5

-- Greetings and questions together within 3 messages
SELECT contains(greetings), is_question() INWIN 3
```

### Sequential Queries (Ordered)

```prismql
-- Alice followed by bob within 3 messages
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3

-- Question followed by support response
SELECT is_question() FOLLOWED_BY from(support) WITHIN 5

-- Customer NOT followed by support (unanswered)
SELECT from(customer) NOT_FOLLOWED_BY from(support) WITHIN 10
```

### Pattern Variables

```prismql
-- Same user posting twice
SELECT from($user), from($user) INWIN 3

-- User asking, then bob responding, then same user following up
SELECT from($user) FOLLOWED_BY from(bob) WITHIN 5 FOLLOWED_BY from($user) WITHIN 5
```

### Quantifiers

```prismql
-- Alice posting exactly 3 times within 10 messages
SELECT from(alice){3} INWIN 10

-- User posting 3+ times consecutively
SELECT from($user){3} FOLLOWED_BY NOT from($user) WITHIN 1
```

### Aggregation

```prismql
-- Count total results
SELECT from(alice) AGGREGATE count()

-- Count by user
SELECT from($user) GROUP BY user AGGREGATE count()
```

### Subqueries

```prismql
-- Sequential subqueries
SELECT (SELECT from(customer), contains(problems) INWIN 3) FOLLOWED_BY (SELECT from(support), contains(solutions) INWIN 3) WITHIN 10

-- Unordered subqueries
SELECT (SELECT from(alice), from(bob) INWIN 3) ; (SELECT from(charlie)) INWIN 8
```

## Result Format

### Query Results

```
prismql[0]> SELECT from(alice), from(bob) INWIN 5

Found 2 result(s):

  1. [1, 2]
  2. [3, 4]

(Query executed in 0.003s)
```

### Named Results

```
prismql[1]> SELECT from(alice) AS asker, from(bob) AS responder INWIN 3

Found 1 result(s):

  1. [asker=1, responder=2]

(Query executed in 0.002s)
```

### Aggregated Results

```
prismql[2]> SELECT from($user) GROUP BY user AGGREGATE count()

Aggregated results (grouped):

  alice: 4
  bob: 3
  charlie: 3

(Query executed in 0.005s)
```

### No Results

```
prismql[3]> SELECT from(dave)

No results found.

(Query executed in 0.001s)
```

## Error Messages

### Syntax Errors

```
prismql[4]> SELECT from(

Syntax Error: mismatched input '<EOF>' expecting ')'
  at line 1, column 13
```

### Runtime Errors

```
prismql[5]> SELECT contains(unknown_dict)

Runtime Error: Dictionary 'unknown_dict' not found
```

## Advanced Usage

### Programmatic REPL

You can also use the REPL programmatically in Python:

```python
from prismql.repl import PrismQLRepl
from prismql.backends.memory import MemoryBackend

# Create backend with your data
backend = MemoryBackend(documents=[
    {"id": 1, "user": "alice", "text": "Hello"},
    {"id": 2, "user": "bob", "text": "Hi there"}
])

# Create and run REPL
repl = PrismQLRepl(
    search_backend=backend,
    user_dictionaries={
        "greetings": ["hello", "hi", "hey"]
    }
)
repl.run()
```

### Custom Backend in REPL

For custom backends, create a config file with backend initialization:

```python
# custom_backend.py
from prismql.backends.memory import MemoryBackend

def get_backend():
    # Your custom data loading logic
    data = load_my_data()
    return MemoryBackend(documents=data)
```

Then use in config:

```json
{
  "search_backend": {
    "type": "memory",
    "documents": []
  }
}
```

## Troubleshooting

### History Not Saving

Check that `~/.prismql_history` is writable:

```bash
ls -la ~/.prismql_history
chmod 644 ~/.prismql_history
```

### No Syntax Highlighting

Install the highlighting extra:

```bash
uv pip install '.[highlighting]'
```

### Prompt Not Working

Install the REPL extra for enhanced prompts:

```bash
uv pip install '.[repl]'
```

The REPL will work without these extras but with reduced functionality.

## Tips and Best Practices

1. **Use `\stats`** to monitor query performance
2. **Save complex queries** to files and paste them into the REPL
3. **Start with `--sample-data`** to learn the syntax
4. **Use pattern variables** (`$user`) for flexible matching
5. **Test incrementally**: Start with simple queries and build up complexity
6. **Use `\clear`** to clean up the screen during long sessions
7. **Press Ctrl+C** to cancel long-running or incorrect queries
8. **Use history** (Up arrow) to modify previous queries

## See Also

- [PrismQL Grammar Reference](GRAMMAR.md)
- [Backend Configuration](BACKENDS.md)
- [Query Examples](EXAMPLES.md)
