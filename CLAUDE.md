# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PrismQL is a domain-specific language (DSL) for pattern matching in conversational data. It uses ANTLR4 for parsing and implements a visitor pattern for query execution. The language is backend-agnostic, supporting any search engine (OpenSearch, Elasticsearch, in-memory) and optional NLP backends (spaCy).

## Important: INWINDOW Operator (Nov 2025 Update)

**PrismQL now uses `INWINDOW` as the unified positional window operator!**

```prismql
# ✅ Current (recommended):
SELECT from(alice), from(bob) INWINDOW 5
SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 3

# ⚠️ Deprecated (still works for backward compatibility):
SELECT from(alice), from(bob) INWIN 5
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
```

**Why the change?**
- **INWIN** and **WITHIN** were confusing - same concept, different names
- **INWINDOW** clearly indicates **positional** distance (not temporal)
- Frees up **WITHIN** for future temporal filtering: `SELECT from(alice) DURING 5 days`

**Key Point:** `INWINDOW` measures distance in **message positions**, not time!
- Numeric IDs: `distance = abs(id1 - id2)`
- String IDs: Position difference in sorted list

See `INWINDOW_UNIFICATION.md` for full details.

## Project History

PrismQL is a complete redevelopment of the **Chat-Corpora-Annotator** project (2020 undergrad thesis at SPbU). The original project was a C# desktop application with a query language called "Macther" for Boolean retrieval and pattern matching in chat datasets.

**Original Repository:** https://github.com/yakovypg/Chat-Corpora-Annotator

**Key improvements in PrismQL:**
- Python-based library (vs C# desktop app)
- Backend-agnostic architecture (vs tied to Lucene/CoreNLP)
- Advanced pattern matching (FOLLOWED_BY, variables, quantifiers)
- Comprehensive test coverage (331+ tests)
- Publishable as library

**Where to consult original implementation:**

1. **Histogram-based window merging algorithm:**
   - File: `Chat-Corpora-Annotator/Infrastructure/Helpers/WindowIndexer.cs`
   - Method: `GetIndexesInWindow()`
   - This is the original algorithm for finding message combinations within windows
   - Used as reference for `src/prismql/processors/window.py`

2. **Operator implementations:**
   - Directory: `Chat-Corpora-Annotator/Model/Parsers/Macther/QueryExecutorComponents/`
   - `IRestriction.cs` - Base restriction interface
   - `AndRestriction.cs`, `OrRestriction.cs`, `NotRestriction.cs` - Boolean operators
   - `InwinRestriction.cs` - Window constraint operator
   - Original semantics for INWIN and Boolean operations

3. **ANTLR4 grammar:**
   - File: `Chat-Corpora-Annotator/Model/Parsers/Macther/Macther.g4`
   - Original grammar for Boolean retrieval language
   - Reference for operator precedence and syntax design

**Note:** When implementing new features or debugging algorithms, the C# codebase can be consulted for original semantics and algorithm details.

## Development Commands

### Environment Setup
```bash
# Install dependencies with uv (recommended)
uv sync --dev

# Activate virtual environment
source .venv/bin/activate
```

### Rust Backend (Optional but Recommended)

PrismQL includes an optional high-performance Rust backend that provides **50-100x speedup** for window merge operations and FOLLOWED_BY queries.

**Building and Installing:**
```bash
# Install maturin (Python build tool for Rust extensions)
uv pip install maturin

# Build and install the Rust module (from prismql-rust directory)
uv run python -m maturin develop --release --manifest-path ../prismql-rust/Cargo.toml
```

**What gets accelerated:**
- Window merge operations (`INWIN` clause): Uses `merge_histogram_pruned()` algorithm
- FOLLOWED_BY queries: Uses `merge_followed_by()` algorithm
- Both algorithms use Rust only for numeric message IDs, falling back to Python for strings

**Verification:**
```bash
# Test that Rust backend is installed
uv run python -c "import prismql_rust; print('Rust backend available!')"

# Run tests with Rust backend
uv run pytest tests/
```

**Note:** The Python implementation serves as a reference and fallback. The Rust backend is automatically used when available and when message IDs are numeric.

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
  - `visitRestriction()`: Returns `Union[set[MessageId], list[MessageGroup]]` - handles both normal restrictions (sets) and sequential operators (lists of pairs)
  - `visitRestrictions()`: Returns `tuple[list[MessageGroup], bool]` - processes comma-separated restrictions and tracks if result is sequential
  - `_merge_restrictions()`: Applies window-based merging
  - `_create_sequential_pairs()`: Creates message pairs for FOLLOWED_BY/PRECEDED_BY
  - `_extend_sequences_followed_by()`: Extends sequences for chained FOLLOWED_BY
  - `_extend_sequences_preceded_by()`: Extends sequences for chained PRECEDED_BY

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

### 5. Rust Backend (Performance Layer)

**Location**: `/Users/asmirnov/Projects/vibes/prismql-rust/`

The Rust backend provides high-performance implementations of computationally expensive algorithms:

**Implemented Functions** (`src/prismql_rust/src/lib.rs`):
- `merge_histogram_pruned()`: Optimized window merge using histogram with progressive pruning (50-100x faster than Python)
- `merge_followed_by()`: Optimized sequential pattern matching for FOLLOWED_BY operator (10-100x faster)
- `merge_p_s()`, `merge_p_ns()`, `merge_n_s()`, `merge_n_ns()`: Reference implementations from PANDL 2022 paper

**Integration Points**:
- `src/prismql/processors/window.py:59`: Uses `merge_histogram_pruned()` when available
- `src/prismql/visitors/query_visitor.py:944`: Uses `merge_followed_by()` when available
- Both locations check `RUST_AVAILABLE` and fall back to Python if:
  - Rust module not installed
  - Message IDs are strings (Rust only handles numeric IDs)
  - Any runtime error occurs

**Building**:
- Uses PyO3 0.23+ for Python bindings
- Uses Maturin for building Python wheels
- Requires Rust toolchain (cargo)

**Algorithm Details**:
- **Greedy matching**: FOLLOWED_BY returns only the closest match for each LHS message, not all possible matches
- **Histogram approach**: Deduplicates and sorts message IDs before processing
- **Progressive pruning**: Builds results iteratively, pruning invalid combinations early

### 6. Type System

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

### FOLLOWED_BY and PRECEDED_BY Return Complete Sequences

**IMPORTANT**: As of commit `3a00cd6`, FOLLOWED_BY and PRECEDED_BY now return complete message sequences (pairs/triples/etc), not just the LHS messages.

```python
# Query: SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
# OLD behavior: [[1], [3]]  # Just alice messages
# NEW behavior: [[1, 2], [3, 4]]  # Complete pairs [alice, bob]

# Chained sequences also work:
# Query: SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3 FOLLOWED_BY from(charlie) WITHIN 3
# Returns: [[1, 2, 3], [4, 5, 6]]  # Complete triples
```

**Why this matters**:
- Tests in `test_lookahead_lookbehind.py` expect pairs, not individual messages
- `flatten()` helper is used in tests to get all IDs from result groups
- PRECEDED_BY returns pairs in chronological order: `[earlier_msg, later_msg]`

**Implementation details**:
- `visitRestriction()` returns `list[MessageGroup]` for sequential operators
- `visitRestrictions()` checks if result is sequential and skips window merging
- `_create_sequential_pairs()` builds the actual pairs
- Chained operators use `_extend_sequences_*()` to append/prepend to existing sequences

### INWIN is Unordered (Critical Understanding!)

**INWIN finds ANY combination of messages within the window**, even if they satisfy different restrictions.

```python
# This query is often misunderstood:
# SELECT from(alice){2}, contains(solutions) INWIN 10

# What it means:
# - 2 messages from alice
# - 1 message containing "solutions"
# - The "solutions" message can be from ANYONE (alice, bob, support, etc.)

# Example result: [27:bob, 35:alice, 37:alice]
# - 27 is bob with "password" (in solutions dictionary)
# - 35 and 37 are both alice

# To filter properly, use AND:
# SELECT from(alice) AND contains(solutions)  # Only alice's messages with solutions
```

**Common patterns**:
```sql
-- ❌ WRONG: Finds alice messages + any solution message
SELECT from(alice){2}, contains(solutions) INWIN 10

-- ✅ RIGHT: Finds only alice's messages that contain solutions
SELECT from(alice) AND contains(solutions)

-- ✅ RIGHT: Finds 2 alice messages, both containing solutions
SELECT (from(alice) AND contains(solutions)){2} INWIN 10

-- ✅ RIGHT: Finds 2 alice messages, at least one with solutions
SELECT (from(alice) AND contains(solutions)), from(alice) INWIN 10
```

### Variable Constraints with Quantifiers

Pattern variables with quantifiers now correctly enforce same-value constraints:

```python
# Query: SELECT from($user){2} INWIN 10
# OLD behavior: Could return [alice, bob] (mixed users)
# NEW behavior: Only returns [alice, alice] or [bob, bob] (same user)
```

**How it works**:
- Variable constraints are tracked during `visitCondition()` (e.g., `from($user)`)
- Quantifier expansion in `visitRestrictions()` duplicates constraints for each position
- `VariableValidator` filters results where variables don't match

**Known limitation**: Window processor's greedy algorithm may miss some valid combinations. For more reliable results, use specific users: `SELECT from(alice){2} INWIN 10`

### Operator Compatibility

**Sequential operators (FOLLOWED_BY, PRECEDED_BY) cannot be combined with AND/OR**:
```python
# ❌ ERROR: AND operator cannot be used with sequential operators
SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3 AND contains(greetings)

# ✅ CORRECT: Put conditions inside the sequence
SELECT (from(alice) AND contains(greetings)) FOLLOWED_BY from(bob) WITHIN 3
```

**Reason**: Sequential operators return `list[MessageGroup]` while AND/OR require `set[MessageId]`

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

## Demo Application

The Streamlit demo (`demo/app.py`) provides an interactive interface for testing PrismQL queries.

### Running the Demo
```bash
streamlit run demo/app.py
```

### Demo Features
- **Interactive query editor** with monospace font
- **Syntax highlighting** using Pygments
- **Example queries** organized by category:
  - Basic Queries
  - Boolean Operations
  - Window Patterns
  - Sequential Patterns (FOLLOWED_BY)
  - Pattern Variables
  - Quantifiers
  - Advanced
  - **Understanding INWIN (Important!)** - explains common pitfalls
- **Dataset viewer** (`pages/01_📊_View_Dataset.py`)
- **Result formatting** with message details

### Understanding INWIN Section

Added in commit `3a00cd6` to help users understand a common pitfall:

The demo includes a dedicated section showing:
- ❌ Common mistake: `SELECT from(alice){2}, contains(solutions) INWIN 10`
- ✅ Correct alternatives using AND
- Info box explaining INWIN is unordered

This section was added because users often expect `from(alice){2}, contains(solutions) INWIN 10` to only return alice's messages, but it actually finds ANY 3 messages within window (2 from alice + 1 with solutions from anyone).

## Recent Changes (Commit 3a00cd6)

### Bug Fixes
1. **FOLLOWED_BY returns complete sequences** ✅
   - Previously returned only LHS messages `[[1], [3]]`
   - Now returns complete pairs `[[1, 2], [3, 4]]`
   - Chained sequences work: `[[1, 2, 3], [4, 5, 6]]`

2. **Variable constraints with quantifiers** ✅
   - `SELECT from($user){2}` now enforces same user
   - Invalid combinations (mixed users) filtered out
   - Known limitation: May miss some valid combinations due to window processor

3. **Grammar support for quantifiers on FOLLOWED_BY** ❌
   - Not fixed (requires grammar restructure)
   - Workaround: Use INWIN or explicit chaining

### Implementation Changes
- `visitRestriction()`: Return type changed to `Union[set[MessageId], list[MessageGroup]]`
- `visitRestrictions()`: Return type changed to `tuple[list[MessageGroup], bool]`
- Added `_extend_sequences_followed_by()` and `_extend_sequences_preceded_by()`
- Variable constraints duplicated for each quantifier position

### Test Updates
- 7 tests in `test_lookahead_lookbehind.py` updated to expect pairs
- All 331 tests passing

## Publishing

See `PUBLISHING.md` for release workflow details.
