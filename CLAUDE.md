# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PrismQL is a domain-specific language (DSL) for pattern matching in conversational data. It uses ANTLR4 for parsing and implements a visitor pattern for query execution. The language is backend-agnostic, supporting any search engine (OpenSearch, Elasticsearch, in-memory) and optional NLP backends (spaCy).

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (recommended)
uv sync --dev

# Activate virtual environment
source .venv/bin/activate
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_basic.py

# Run with coverage
uv run pytest --cov=prismql --cov-report=html

# Run specific test markers
uv run pytest -m "not slow"           # Exclude slow tests
uv run pytest -m integration          # Only integration tests
```

### Linting and Formatting
```bash
# Format code with ruff
uv run ruff format .

# Check linting issues
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Run both formatting and linting (recommended before commits)
uv run ruff format . && uv run ruff check . --fix
```

### Type Checking
```bash
# Run mypy type checker
uv run mypy src/prismql
```

### Parser Generation
When the grammar file (`src/prismql/grammar/PrismQL.g4`) is modified, regenerate the parser:

```bash
./scripts/generate_parser.sh
```

This script:
- Downloads ANTLR 4.13.1 jar if not present
- Generates Python3 lexer, parser, and visitor classes
- Outputs to `src/prismql/grammar/generated/`

Note: Generated files in `src/prismql/grammar/generated/` are excluded from linting/type checking.

## Architecture Overview

### 1. Query Parsing (ANTLR-based)

**Grammar**: `src/prismql/grammar/PrismQL.g4`
- Defines PrismQL syntax using ANTLR4 grammar
- Supports both legacy operators (`haswordofdict`) and fluent syntax (`contains`)
- Key constructs: restrictions, boolean operators (AND/OR/NOT), window constraints (INWIN), subqueries

**Generated Parser**: `src/prismql/grammar/generated/`
- `PrismQLLexer.py`: Tokenizes input
- `PrismQLParser.py`: Builds parse tree
- `PrismQLVisitor.py`: Base visitor class (extended by query_visitor.py)

### 2. Query Execution (Visitor Pattern)

**Engine**: `src/prismql/engine.py`
- `PrismQLEngine`: Main entry point for query execution
- Parses query string → creates parse tree → visits tree with PrismQLVisitor
- Handles syntax/runtime errors with custom exceptions
- Factory method `from_config()` for configuration-based initialization

**Visitor**: `src/prismql/visitors/query_visitor.py`
- `PrismQLVisitor`: Traverses parse tree and executes query logic
- Delegates to backends for search/NLP operations
- Implements boolean operations on message ID sets (AND=intersection, OR=union, NOT=difference)
- Key methods:
  - `visitCondition()`: Evaluates individual conditions (e.g., `from(alice)`, `is_question()`)
  - `visitRestriction()`: Handles boolean logic between conditions
  - `visitRestrictions()`: Processes comma-separated restrictions
  - `_merge_restrictions()`: Applies window-based merging

### 3. Backend Abstraction

**Base Interfaces**: `src/prismql/backends/base.py`

- `SearchBackend` (ABC): Interface for any search engine
  - `search_text()`: Find messages containing terms
  - `search_by_field()`: Find messages by field value (e.g., user)
  - `get_all_document_ids()`: Retrieve all message IDs
  - Must return `set[MessageId]` for set operations

- `NLPBackend` (ABC): Interface for NLP operations
  - `extract_entities()`: Named entity recognition (DATE, TIME, ORG, etc.)
  - `has_question()`: Question detection
  - Optional: `extract_noun_phrases()`

- `PrecomputedIndexes`: Container for precomputed NLP features
  - For large datasets, compute NLP features once during ingestion
  - Store entity/question indexes as `dict[label, set[MessageId]]`

**Implementations**:
- `memory.py`: In-memory backend for testing/small datasets
- `opensearch.py`: OpenSearch/Elasticsearch integration
- `spacy.py`: spaCy-based NLP backend

**Factory**: `src/prismql/backends/factory.py`
- `BackendFactory`: Creates backends from configuration dictionaries
- `validate_config()`: Validates configuration structure
- `create_backends()`: Instantiates backends based on type
- `get_example_configs()`: Provides example configurations

### 4. Window Processing

**Window Processor**: `src/prismql/processors/window.py`
- `WindowProcessor.merge_restrictions()`: Core algorithm for INWIN clause
  - Given multiple restriction results (message ID sets), finds combinations where messages appear within window_size of each other
  - Example: `SELECT from(alice), from(bob) INWIN 5` finds pairs of messages (one from alice, one from bob) within 5 positions
  - Uses histogram-based approach with sorted message IDs

- `WindowProcessor.merge_queries()`: Merges results from subqueries
  - Groups messages from different subqueries that appear within window_size

**Window Semantics**:
- For numeric IDs: distance = `abs(id1 - id2)`
- For string IDs: distance = position difference in sorted list

### 5. Type System

**Types**: `src/prismql/types.py`
- `MessageId`: Union[int, str] - flexible ID type
- `MessageGroup`: list[MessageId] - result of single restriction
- `QueryResult`: list[MessageGroup] - final query result
- `Document`: dict[str, Any] - message/document from backend
- `NERLabel`: str - entity type label

### 6. Exception Hierarchy

**Exceptions**: `src/prismql/exceptions.py`
- `PrismQLSyntaxError`: Query parsing errors (line/column info)
- `PrismQLRuntimeError`: Query execution errors (includes query context)

## Key Design Patterns

1. **Visitor Pattern**: Query execution via tree traversal (visitor.py)
2. **Factory Pattern**: Backend creation from config (factory.py)
3. **Strategy Pattern**: Pluggable backends (SearchBackend/NLPBackend interfaces)
4. **Abstract Base Classes**: Interface contracts for backends

## Testing Strategy

- `tests/test_basic.py`: Core query functionality with MemoryBackend
- `tests/test_fluent_syntax.py`: New fluent operator syntax
- `tests/test_opensearch_backend.py`: OpenSearch integration (requires running instance)
- `tests/test_spacy_backend.py`: spaCy NLP backend
- `tests/test_integration.py`: End-to-end integration tests
- `tests/test_backend_factory.py`: Configuration factory tests

## Important Implementation Notes

### Message ID Sets
All backend search methods return `set[MessageId]` to enable efficient set operations:
- AND = intersection (`&`)
- OR = union (`|`)
- NOT = difference (`-`)

### Precomputed Indexes
For production use with large datasets:
1. Compute NLP features during data ingestion
2. Store in PrecomputedIndexes
3. Pass to engine on initialization
4. Visitor checks precomputed indexes first, falls back to NLP backend

### Field Mappings
When integrating with existing search infrastructure, use field_mappings in backend config:
```python
field_mappings = {
    "text": "message_content",  # Map PrismQL's "text" to your field
    "user": "author_username",  # Map PrismQL's "user" to your field
    "id": "message_id"          # Map PrismQL's "id" to your field
}
```

### Window Algorithm
The window merge algorithm (WindowProcessor) is critical for performance:
- Sorts all message IDs first
- Uses position-based indexing
- Finds valid combinations efficiently
- Avoids cartesian product of all possibilities

## Code Quality Settings

### Ruff Configuration (pyproject.toml)
- Line length: 88
- Target: Python 3.9+
- Ignores: ANN101 (self annotations), S101 (asserts in tests)
- Per-file ignores: visitors (N802, C901), grammar/generated (ALL)

### MyPy Configuration
- Strict mode enabled
- Disallows untyped defs
- Ignores: antlr4, grammar/generated modules

## Publishing

See `PUBLISHING.md` for release workflow details.
