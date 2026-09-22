# PrismQL Enhancement Roadmap

**Goal:** Transform PrismQL into a research-grade query language for conversation pattern mining and discourse analysis.

**Strategy:** Hybrid approach combining unique conversation-oriented features with familiar SQL-like aggregations and temporal operations.

---

## Current Status

- ✅ **Phase 1.1:** Aggregation operators (COUNT, SUM, AVG, MIN, MAX, DISTINCT, GROUP BY, ORDER BY, LIMIT)
- ✅ **Phase 1.2:** Temporal operators (BEFORE, AFTER, BETWEEN, temporal grouping by HOUR/DAY/WEEK/MONTH/YEAR)
- ✅ **Phase 1.3:** Advanced pattern matching (COMPLETE)
  - ✅ Pattern Variables (backreferences with $var syntax)
  - ✅ Named Pattern Groups (AS keyword for labeling)
  - ✅ Negative Patterns (NOT operator in sequences)
  - ✅ Counting Constraints (quantifiers)
  - ✅ Lookahead/Lookbehind (context-aware matching with bug fixes)

**Test Coverage:** 331 tests passing (all features + bug fixes)
**Last Updated:** 2025-10-23

---

## Phase 1: Core Query Enhancements (Short-term - 2-4 weeks)

### ✅ Phase 1.1: Aggregation Operators (COMPLETED)
**Status:** Implemented and tested (134 tests)

**Features:**
- COUNT(), SUM(field), AVG(field), MIN(field), MAX(field)
- COUNT(DISTINCT field), DISTINCT(field)
- GROUP BY field1, field2, ...
- ORDER BY field ASC/DESC
- LIMIT N OFFSET M

**Files:**
- `src/prismql/aggregators/` - Aggregation logic
- `src/prismql/aggregators/types.py` - Result types
- `tests/test_aggregations.py` - Comprehensive test suite

---

### ✅ Phase 1.2: Temporal Operators (COMPLETED)
**Status:** Implemented and tested (165 tests total, 31 new temporal tests)

**Features:**
- BEFORE(timestamp) - Filter messages before a time (exclusive)
- AFTER(timestamp) - Filter messages after a time (exclusive)
- BETWEEN(start, end) - Filter messages in time range (inclusive)
- Temporal grouping: GROUP BY HOUR/DAY/WEEK/MONTH/YEAR(field)
- Support for ISO 8601, Unix timestamps, date-only formats
- Timezone normalization
- Configurable timestamp field

**Files:**
- `src/prismql/processors/temporal.py` - Temporal processing logic
- `src/prismql/grammar/PrismQL.g4` - Grammar extensions
- `tests/test_temporal.py` - 31 comprehensive tests
- `examples/temporal_operators_example.py` - Usage examples

**Example:**
```prismql
SELECT from(alice) OR from(bob)
BETWEEN("2024-01-15", "2024-01-17")
GROUP BY DAY(timestamp)
AGGREGATE count()
```

---

### ✅ Phase 1.3: Advanced Pattern Matching (**COMPLETE**)
**Status:** Implemented and Tested
**Completed:** All 5 features implemented with 100+ tests

**Features to implement:**

1. **Named Pattern Groups**
   ```prismql
   SELECT question AS q, answer AS a
   WHERE q: IS_QUESTION(), a: from(alice)
   INWIN 3
   ```
   - Enables pattern labeling for complex queries
   - Improves readability for multi-stage patterns

2. **Backreferences and Pattern Variables**
   ```prismql
   SELECT from($user), CONTAINS(thanks), from($user)
   ```
   - Variable binding for dynamic user matching
   - Enables "same user" constraints

3. **✅ Negative Patterns (NOT operator in sequences)**
   ```prismql
   SELECT from(alice), NOT from(bob), from(charlie) INWIN 5
   ```
   - "alice, then someone other than bob, then charlie"
   - NOT operates at position level: excludes specific conditions at that position
   - Fully implemented and tested (22 comprehensive tests)
   - Works with variables, boolean operators, dictionaries, and named groups

4. **✅ Counting Constraints (quantifiers)**
   ```prismql
   SELECT from(alice){2,4}, from(bob) INWIN 10
   ```
   - "2 to 4 messages from alice, then bob, within 10 messages"
   - Regex-style quantifiers: {n} (exact), {n,} (at least), {n,m} (range)
   - Fully implemented and tested (26 comprehensive tests)
   - Works with variables, boolean operators, named groups, and aggregation
   - Current implementation: {n,} and {n,m} use minimum count (future: full range matching)

5. **Lookahead/Lookbehind** ✅ **COMPLETE**
   ```prismql
   SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 3
   NOT_PRECEDED_BY from(charlie) WITHIN 5
   ```
   - Context-aware pattern matching
   - "alice then bob, but NOT if charlie spoke 5 messages before alice"
   - Four operators: FOLLOWED_BY, PRECEDED_BY, NOT_FOLLOWED_BY, NOT_PRECEDED_BY
   - Position-based windows over full message sequence
   - **Returns complete sequences**: `[[1, 2], [3, 4]]` pairs instead of just LHS messages
   - **Chained sequences supported**: `A FOLLOWED_BY B WITHIN 3 FOLLOWED_BY C WITHIN 3` returns triples
   - 27 comprehensive tests covering all use cases
   - See [LOOKAHEAD_LOOKBEHIND.md](LOOKAHEAD_LOOKBEHIND.md) for documentation

**Implementation plan:**
- [x] Design grammar extensions
- [x] Update parser with new pattern rules
- [x] Implement positional operators in visitor
- [x] Add support for all four operator variants
- [x] Create comprehensive test suite (27 tests)
- [x] Document with examples
- [x] Fix FOLLOWED_BY to return complete sequences (commit 3a00cd6)
- [x] Fix variable constraints with quantifiers (commit 3a00cd6)

**Recent Bug Fixes (Commit 3a00cd6):**

1. **FOLLOWED_BY now returns complete sequences** ✅
   - **Before**: Returned only LHS messages `[[1], [3]]`
   - **After**: Returns complete pairs `[[1, 2], [3, 4]]`
   - Chained operators return complete sequences: `[[1, 2, 3], [4, 5, 6]]`
   - Implementation: Changed `visitRestriction()` return type to support both sets and lists
   - Added `_create_sequential_pairs()` and `_extend_sequences_*()` helper methods

2. **Variable constraints with quantifiers** ✅
   - **Before**: `SELECT from($user){2} INWIN 10` could return `[alice, bob]` (mixed users)
   - **After**: Only returns `[alice, alice]` or `[bob, bob]` (same user)
   - Implementation: Track and duplicate variable constraints for each quantifier position
   - Known limitation: Window processor's greedy algorithm may miss some valid combinations

3. **Demo enhancements** ✅
   - Added "Understanding INWIN (Important!)" section to explain common pitfalls
   - INWIN is unordered - finds ANY combination of messages within window
   - Example: `from(alice){2}, contains(solutions) INWIN 10` can match alice + bob's message
   - Use AND to filter properly: `from(alice) AND contains(solutions)`

---

## Phase 2: Feature Annotation & Semantic Queries (Medium-term - 3-4 weeks)

**Philosophy:** PrismQL is a pattern matching language, not an NLP pipeline. Features are precomputed during data ingestion from ANY source (LLMs, human annotators, NLP libraries, rule-based systems). PrismQL provides fast boolean index queries over these features.

### Phase 2.1: Feature Annotation Standards & Query Syntax
**Estimated effort:** 1-2 weeks
**Status:** ⏳ In Progress

**What's Already Done:**
- ✅ `PrecomputedIndexes` with `custom_features` support
- ✅ `IndexBuilder` utilities for building indexes from annotations
- ✅ `IndexBuilder.from_message_annotations()` - Build from embedded annotations
- ✅ `IndexBuilder.from_separate_annotations()` - Build from external annotation DB
- ✅ `IndexBuilder.merge()` - Combine indexes from multiple sources
- ✅ Example: `examples/custom_features_example.py`
- ✅ Deprecation of `NLPBackend` in favor of precomputed approach

**What Needs Implementation:**

1. **Standardized Feature Naming Conventions**
   ```python
   # Document recommended naming patterns
   'sentiment_positive', 'sentiment_negative', 'sentiment_neutral'
   'intent_request', 'intent_question', 'intent_confirmation'
   'topic_bug', 'topic_feature', 'topic_documentation'
   'priority_high', 'priority_low'
   'action_item', 'decision', 'blocker'
   ```
   - Create feature taxonomy documentation
   - Provide templates for common use cases
   - Guidelines for consistent naming

2. **Query Syntax for Custom Features**
   ```prismql
   # Check if syntax already exists, otherwise implement:
   SELECT has_feature(sentiment_positive), has_feature(intent_request) INWIN 5
   SELECT labeled_as(action_item) FOLLOWED_BY labeled_as(decision) WITHIN 10
   ```
   - Ergonomic syntax for querying custom features
   - Integration with existing pattern matching
   - Support in aggregations: `GROUP BY feature, COUNT(*)`

3. **Validation & Type Safety**
   - Validate feature names at query time
   - Helpful error messages when features don't exist
   - Optional feature schema definition

4. **Documentation**
   - Feature annotation guide
   - Best practices for feature naming
   - Integration patterns with various annotation sources

---

### Phase 2.2: LLM & Annotation Platform Integration Examples
**Estimated effort:** 1-2 weeks

**Features:**

1. **LLM-Based Annotation Pipelines**
   ```python
   # Example: GPT-4 based annotation
   def annotate_with_gpt4(messages):
       """Generate intent, sentiment, topics from GPT-4."""
       response = openai.chat.completions.create(
           model="gpt-4",
           messages=[{"role": "system", "content": ANNOTATION_PROMPT}]
       )
       return parse_annotations(response)

   # Build indexes from LLM output
   indexes = IndexBuilder.from_message_annotations(
       annotated_messages,
       custom_fields={'intent': None, 'sentiment': None, 'topics': list}
   )
   ```
   - Example prompts for GPT-4, Claude, Llama
   - Structured output parsing
   - Batch processing patterns
   - Cost optimization strategies

2. **Human Annotation Platform Integration**
   ```python
   # Example: Load from annotation database
   annotations = db.get_annotations(conversation_id)
   indexes = IndexBuilder.from_separate_annotations(
       annotations,
       custom_feature_keys=['labels', 'categories']
   )
   ```
   - Integration patterns for Label Studio, Prodigy, etc.
   - Hybrid workflows (LLM + human verification)
   - Annotation quality metrics

3. **Rule-Based Feature Extractors**
   ```python
   # Example: Domain-specific extractors
   def extract_code_features(messages):
       """Detect code snippets, error messages, stack traces."""
       custom_features = {
           'has_code_block': set(),
           'has_error_trace': set(),
           'has_log_output': set()
       }
       for msg in messages:
           if '```' in msg['text']:
               custom_features['has_code_block'].add(msg['id'])
           # ... more rules
       return PrecomputedIndexes(custom_features=custom_features)
   ```
   - Domain-specific feature extraction examples
   - Regex-based extractors
   - Combining multiple extractor outputs

4. **Comprehensive Examples**
   - Customer support use case (ticket classification, sentiment tracking)
   - Research use case (discourse analysis, conversation patterns)
   - Team collaboration use case (decision tracking, action items)

---

## Phase 3: Performance & Scalability (Medium-term - 4-6 weeks)

### Phase 3.1: Query Optimization
**Estimated effort:** 2-3 weeks

**Features:**

1. **Histogram-Based Pattern Matching Algorithm**
   - Core optimization strategy for sequence pattern matching
   - Build histograms of message positions by condition
   - Efficiently merge histograms to find pattern matches
   - **Based on published research** (see references below)
   - Dramatically reduces search space for complex patterns

2. **Query Plan Optimization**
   - Analyze query structure
   - Reorder operations for efficiency
   - Early filtering optimization
   - Choose between histogram-based and naive approaches

3. **Index Support**
   - Create indexes for common fields (user, timestamp)
   - Index-aware query execution
   - Precomputed pattern indexes
   - Histogram pre-computation for frequent patterns

4. **Lazy Evaluation**
   - Stream results instead of materializing all
   - Early termination for LIMIT queries
   - Memory-efficient processing

5. **Parallel Processing**
   - Multi-threaded pattern matching
   - Batch NLP processing
   - Parallel aggregation
   - Parallel histogram construction

**Performance targets:**
- 10x speedup on large datasets (100k+ messages)
- Memory usage: O(result_size) instead of O(dataset_size)
- Sub-second response for common queries

**Research foundation:**
- Histogram-based algorithm from published paper (to be referenced)

---

### Phase 3.2: Backend Extensions
**Estimated effort:** 2-3 weeks

**Features:**

1. **PostgreSQL Backend**
   - Native SQL generation for PostgreSQL
   - Leverage PostgreSQL full-text search
   - Integration with pgvector for embeddings

2. **Elasticsearch Backend**
   - Full-text search optimization
   - Aggregation pushdown
   - Distributed query execution

3. **Streaming Backend**
   - Real-time message processing
   - Kafka/Redis Streams integration
   - Incremental pattern matching

4. **Remote Backend Protocol**
   - Client-server architecture
   - REST API for remote queries
   - Multi-user query execution

---

## Phase 4: Advanced Analytics (Long-term - 6-8 weeks)

### Phase 4.1: Statistical Analysis
**Estimated effort:** 2-3 weeks

**Features:**

1. **Time Series Analysis**
   ```prismql
   SELECT from(alice)
   GROUP BY HOUR(timestamp)
   AGGREGATE moving_avg(count(), window=24)
   ```
   - Moving averages, trends
   - Seasonal decomposition
   - Anomaly detection

2. **Pattern Frequency Analysis**
   ```prismql
   SELECT pattern_frequency(
     from($user), IS_QUESTION(), from($user) INWIN 5
   )
   GROUP BY $user
   ```
   - Pattern occurrence rates
   - User behavior profiling
   - Conversation style metrics

3. **Correlation Analysis**
   - Detect correlated conversation patterns
   - User interaction networks
   - Topic co-occurrence

---

### Phase 4.2: Machine Learning Integration
**Estimated effort:** 3-4 weeks

**Features:**

1. **Pattern Learning**
   ```python
   # Learn patterns from examples
   engine.learn_pattern(
     name="escalation_pattern",
     positive_examples=[...],
     negative_examples=[...]
   )
   ```
   ```prismql
   SELECT MATCHES_PATTERN(escalation_pattern)
   ```

2. **Clustering**
   - Conversation thread clustering
   - User behavior clustering
   - Topic clustering

3. **Prediction**
   - Predict next message characteristics
   - Conversation outcome prediction
   - User intent forecasting

---

## Phase 5: Tooling & Ecosystem (Ongoing)

### Phase 5.1: Developer Experience
**Estimated effort:** Ongoing

**Features:**

1. **Query Builder UI**
   - Visual query construction
   - Interactive pattern exploration
   - Real-time query validation

2. **Query Debugger**
   - Step-through pattern matching
   - Visualize intermediate results
   - Performance profiling

3. **VS Code Extension**
   - Syntax highlighting
   - Autocomplete
   - Inline query execution

4. **Jupyter Integration**
   - Magic commands (`%%prismql`)
   - Result visualization
   - Interactive exploration

---

### Phase 5.2: Documentation & Examples
**Estimated effort:** Ongoing

**Deliverables:**

1. **Comprehensive Documentation**
   - [ ] API reference (complete)
   - [ ] Pattern matching guide
   - [ ] NLP features guide
   - [ ] Performance tuning guide
   - [ ] Backend integration guide

2. **Research Use Cases**
   - [ ] Discourse analysis examples
   - [ ] Conversation style analysis
   - [ ] Community health metrics
   - [ ] Customer support analytics
   - [ ] Team collaboration patterns

3. **Tutorials**
   - [ ] Getting started (basic)
   - [ ] Pattern matching (intermediate)
   - [ ] NLP integration (advanced)
   - [ ] Custom backends (advanced)

4. **Academic Papers**
   - [ ] Language design paper
   - [ ] Conversation mining applications
   - [ ] Performance benchmarks

---

## Phase 6: Research Features (Future)

### Experimental Features (Timeline TBD)

1. **Conversation Graph Queries**
   ```prismql
   SELECT conversation_graph(
     from(alice), from(bob)
   )
   WHERE edge_count > 5
   ```
   - Build conversation graphs
   - Graph pattern matching
   - Centrality metrics

2. **Multi-Channel Analysis**
   ```prismql
   SELECT from(alice) IN slack, from(alice) IN email
   WITHIN 1 hour
   ```
   - Cross-platform conversation tracking
   - Channel switching patterns
   - Communication preference analysis

3. **Probabilistic Patterns**
   ```prismql
   SELECT from(alice), PROBABLY(from(bob), 0.7), from(charlie)
   ```
   - Soft pattern matching
   - Probabilistic reasoning
   - Uncertainty handling

4. **Causal Analysis**
   - Identify causal conversation patterns
   - Treatment effect estimation
   - Counterfactual reasoning

---

## Success Metrics

### Adoption Metrics
- GitHub stars: Target 1,000 in 6 months
- PyPI downloads: Target 10,000/month in 6 months
- Research citations: Target 10 papers in 12 months

### Performance Metrics
- Query execution: <1s for 100k messages
- Memory efficiency: <100MB for typical workloads
- NLP throughput: >1,000 messages/second

### Quality Metrics
- Test coverage: >90%
- Documentation coverage: 100% of public API
- Example coverage: All major features

---

## Contributing

This roadmap is a living document. Contributions and feedback are welcome!

**Priority areas for contributors:**
1. Backend implementations (PostgreSQL, Elasticsearch)
2. NLP integrations (sentiment, intent, similarity)
3. Performance optimization
4. Documentation and examples

**How to contribute:**
1. Check the roadmap for upcoming features
2. Open an issue to discuss your proposed changes
3. Submit a PR with tests and documentation
4. Join the discussion on design decisions

---

## Notes

- **Backward compatibility:** All phases maintain backward compatibility with existing queries
- **Incremental delivery:** Features ship as soon as they're ready
- **Research-driven:** Priority guided by actual conversation mining research needs
- **Community input:** Roadmap adjusts based on user feedback and use cases

---

*Last updated: 2025-10-23*
*Current phase: 1.3 (Advanced Pattern Matching - COMPLETE)*
*Latest commit: 3a00cd6 - FOLLOWED_BY bug fixes and variable constraint improvements*
