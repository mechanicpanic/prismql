# PrismQL Matching Modes Design

## Overview

This document outlines a comprehensive matching system for PrismQL that supports:
1. **Word matching** (current - alphanumeric sequences)
2. **Token matching** (proper tokenization with punctuation)
3. **N-gram matching** (precomputed bigrams/trigrams for phrases)
4. **Substring matching** (efficient indexed substring search)
5. **Regex matching** (pattern-based search)

## 1. Matching Modes

### 1.1 Word Matching (Current)

**Definition**: Alphanumeric sequences separated by non-alphanumeric characters

**Current Implementation**:
```python
# Python
words = re.findall(r"\w+", text.lower())
# "Hello, world!" → ["hello", "world"]
# "user@example.com" → ["user", "example", "com"]
```

```rust
// Rust
text.split(|c: char| !c.is_alphanumeric())
```

**Pros**:
- Fast O(1) lookup via inverted index
- Simple and predictable
- Low memory overhead

**Cons**:
- Loses punctuation ("C++" becomes "c")
- Splits compound terms ("user@example.com" → 3 tokens)
- No phrase matching

**Use cases**:
- Simple keyword search
- Dictionary-based filtering
- General text search

---

### 1.2 Token Matching (Proposed)

**Definition**: Linguistic tokens preserving punctuation and compound terms

**Tokenization Strategy**:
```python
# Unicode-aware tokenization
tokens = tokenize_unicode_aware(text.lower())
# "Hello, world!" → ["hello", ",", "world", "!"]
# "user@example.com" → ["user@example.com"]
# "C++" → ["c++"]
# "don't" → ["don't"] or ["do", "n't"] (configurable)
```

**Implementation Options**:

**Option A: Simple Unicode Tokenizer (Recommended)**
```python
import regex  # or re with Unicode categories

def tokenize(text: str) -> list[str]:
    """
    Split on whitespace and Unicode punctuation, but keep:
    - Email patterns (user@domain)
    - URLs (http://...)
    - Programming terms (C++, C#)
    - Contractions (don't, isn't)
    """
    # Pattern: word characters + special cases
    pattern = r"""
        (?:https?://\S+)|              # URLs
        (?:\w+@\w+(?:\.\w+)+)|         # Emails
        (?:\w+[+#]\w*)|                # C++, C#
        (?:\w+(?:'\w+)*)|              # Contractions
        (?:\w+)                        # Regular words
    """
    return regex.findall(pattern, text, regex.VERBOSE | regex.IGNORECASE)
```

**Option B: spaCy Tokenizer (Heavy)**
```python
import spacy
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

def tokenize(text: str) -> list[str]:
    return [token.text.lower() for token in nlp(text)]
```

**Option C: NLTK Tokenizer (Medium)**
```python
from nltk.tokenize import word_tokenize

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in word_tokenize(text)]
```

**Recommendation**: **Option A** - lightweight, fast, covers 95% of use cases

**Index Structure**:
```python
# Separate token index
_token_index: dict[str, set[MessageId]] = {
    "hello": {1, 3, 5},
    "user@example.com": {7},
    "c++": {10, 12}
}
```

**Pros**:
- Preserves meaningful punctuation
- Better for technical text (code, emails, URLs)
- Still fast O(1) lookup

**Cons**:
- Slightly higher memory (more unique tokens)
- More complex tokenization logic

**Use cases**:
- Technical discussions (programming, emails)
- Exact term matching
- Named entity preservation

---

### 1.3 N-gram Matching (Proposed)

**Definition**: Precomputed sequences of N consecutive tokens for phrase matching

**N-gram Generation**:
```python
def generate_ngrams(tokens: list[str], n: int) -> list[str]:
    """Generate n-grams from token list."""
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

# Example:
tokens = ["hello", "world", "from", "alice"]
bigrams = generate_ngrams(tokens, 2)
# ["hello world", "world from", "from alice"]

trigrams = generate_ngrams(tokens, 3)
# ["hello world from", "world from alice"]
```

**Index Structure**:
```python
# Precomputed n-gram indexes (built at initialization)
_bigram_index: dict[str, set[MessageId]] = {
    "hello world": {1, 5},
    "world from": {1},
    "thank you": {2, 3, 7}
}

_trigram_index: dict[str, set[MessageId]] = {
    "hello world from": {1},
    "thank you very": {7}
}
```

**Configuration**:
```python
class BackendConfig:
    # Which n-grams to precompute
    ngram_sizes: list[int] = [2, 3]  # Bigrams and trigrams

    # Memory optimization: only index frequent n-grams
    ngram_min_frequency: int = 2  # Skip n-grams appearing once
    ngram_max_count: int = 10000  # Keep only top N n-grams
```

**Memory Considerations**:
- **Bigrams**: ~5-10x word index size
- **Trigrams**: ~10-20x word index size
- **Mitigation**: Frequency filtering, top-K selection

**Example Sizing**:
```python
# Dataset: 100K messages, avg 50 words each = 5M words
# Unique words: ~50K
# Unique bigrams: ~500K (10x)
# Unique trigrams: ~2M (40x)

# With filtering (min_freq=2):
# Unique bigrams: ~100K (2x) ← much better!
# Unique trigrams: ~200K (4x)
```

**Pros**:
- Fast phrase matching: O(1) lookup
- No runtime tokenization of phrases
- Captures multi-word expressions

**Cons**:
- Memory overhead (mitigated by filtering)
- Initialization time
- Fixed phrase boundaries

**Use cases**:
- Phrase detection ("thank you", "out of memory")
- Multi-word entity matching
- Fixed expression search

---

### 1.4 Substring Matching (Improved)

**Current Issue**: Linear scan through field values (O(n))

**Proposed Solution**: **Suffix Array + LCP Array** or **Trigram Index**

**Option A: Trigram Index (Recommended)**

**Concept**: Index all 3-character substrings, then verify candidates

```python
def generate_trigrams_substring(text: str) -> set[str]:
    """Generate all 3-char substrings."""
    text = text.lower()
    return {text[i:i+3] for i in range(len(text) - 2)}

# Example:
# "hello" → {"hel", "ell", "llo"}
# "world" → {"wor", "orl", "rld"}
```

**Index Structure**:
```python
_substring_trigram_index: dict[str, set[MessageId]] = {
    "hel": {1, 5, 10},  # All messages with "hel" substring
    "ell": {1, 5, 10},
    "wor": {2, 3, 7}
}
```

**Search Algorithm**:
```python
def search_substring(pattern: str) -> set[MessageId]:
    """Find messages containing pattern as substring."""
    if len(pattern) < 3:
        # Fallback to linear scan for short patterns
        return linear_search(pattern)

    # Extract trigrams from pattern
    pattern_trigrams = generate_trigrams_substring(pattern)

    # Candidate set: messages containing ALL trigrams
    candidates = None
    for trigram in pattern_trigrams:
        ids = _substring_trigram_index.get(trigram, set())
        if candidates is None:
            candidates = ids.copy()
        else:
            candidates &= ids  # Intersection

    # Verify: check actual substring in candidates
    result = set()
    for msg_id in candidates:
        doc = get_document(msg_id)
        if pattern in doc["text"].lower():
            result.add(msg_id)

    return result
```

**Example**:
```python
# Search for "ello wor" in "hello world"
pattern_trigrams = {"ell", "llo", "lo ", "o w", " wo", "wor"}
# All trigrams must be present in candidate messages
# Then verify exact substring
```

**Memory**: ~3x word index (each char position generates 1 trigram)

**Option B: Suffix Array (Lower Memory, More Complex)**

Build sorted suffix array at initialization, use binary search for lookup.

**Recommendation**: **Trigram index** - better balance of speed and simplicity

**Pros**:
- Much faster than linear scan
- Supports arbitrary substring patterns
- Predictable performance

**Cons**:
- Higher memory usage
- Still requires verification step

**Use cases**:
- Partial word matching ("temp" in "temperature")
- Fuzzy search preparation
- Pattern fragments

---

### 1.5 Regex Matching (Proposed)

**Implementation**: Compile regex once, scan all documents (with caching)

```python
import re
from functools import lru_cache

@lru_cache(maxsize=1000)
def compile_regex(pattern: str) -> re.Pattern:
    """Compile and cache regex patterns."""
    return re.compile(pattern, re.IGNORECASE)

def search_regex(pattern: str, field: str = "text") -> set[MessageId]:
    """Find messages matching regex pattern."""
    regex = compile_regex(pattern)
    result = set()

    for msg_id, doc in documents.items():
        text = doc.get(field, "")
        if regex.search(text):
            result.add(msg_id)

    return result
```

**Optimization**: Pre-filter candidates using trigram index if possible

```python
def search_regex_optimized(pattern: str) -> set[MessageId]:
    """Optimized regex search with pre-filtering."""

    # Try to extract literal prefixes/substrings from regex
    # Example: r"hello.*world" → contains "hello" AND "world"
    literal_parts = extract_literal_parts(pattern)

    if literal_parts:
        # Use word/token index to get candidates
        candidates = search_text(literal_parts, operator="AND")

        # Apply regex only to candidates
        regex = compile_regex(pattern)
        return {
            msg_id for msg_id in candidates
            if regex.search(get_document(msg_id)["text"])
        }
    else:
        # Full scan fallback
        return search_regex(pattern)
```

**Pros**:
- Maximum flexibility
- Supports complex patterns
- Standard regex syntax

**Cons**:
- Slower (O(n) in worst case)
- No indexing possible
- Regex compilation overhead (mitigated by caching)

**Use cases**:
- Complex pattern matching
- Email/phone validation
- Advanced text processing

---

## 2. Syntax Design

### 2.1 Explicit Match Mode Operators

**Proposal**: Add match mode specifiers to `contains()` and new operators

```sql
-- Word matching (current default)
SELECT contains(greetings)  -- Uses word index

-- Token matching
SELECT contains_tokens(greetings)  -- Uses token index
SELECT contains(greetings, mode=token)  -- Alternative syntax

-- N-gram matching (phrase)
SELECT contains_phrase("thank you")  -- Uses bigram index
SELECT contains_ngram("out of memory", n=3)  -- Explicit trigram

-- Substring matching
SELECT contains_substring("temp")  -- Partial word match
SELECT substring_match("@example.com")  -- Alternative

-- Regex matching
SELECT matches_regex(r"\d{3}-\d{3}-\d{4}")  -- Phone numbers
SELECT regex("\\w+@\\w+\\.com")  -- Email pattern
```

### 2.2 Grammar Additions

```antlr
// New condition types
condition
    : Contains '(' hdict ')'                                    // Word (current)
    | ContainsTokens '(' hdict ')'                             // Token
    | ContainsPhrase '(' String ')'                            // Phrase (bigram/trigram)
    | ContainsSubstring '(' String ')'                         // Substring
    | MatchesRegex '(' String ')'                              // Regex
    | Matches '(' String ',' String ')'                        // Generic: matches(text, pattern)
    ;

// New keywords
ContainsTokens     : 'CONTAINS_TOKENS'    | 'contains_tokens'    ;
ContainsPhrase     : 'CONTAINS_PHRASE'    | 'contains_phrase'    ;
ContainsSubstring  : 'CONTAINS_SUBSTRING' | 'contains_substring' ;
MatchesRegex       : 'MATCHES_REGEX'      | 'matches_regex'      ;
```

### 2.3 Unified API

**Backend Interface Extension**:

```python
class SearchBackend(ABC):
    """Base search backend interface."""

    # Current methods
    @abstractmethod
    def search_text(self, terms: Sequence[str], field: str = "text",
                    operator: str = "OR") -> set[MessageId]:
        """Word-based search."""
        ...

    # New methods
    def search_tokens(self, terms: Sequence[str], field: str = "text",
                     operator: str = "OR") -> set[MessageId]:
        """Token-based search (preserves punctuation)."""
        raise NotImplementedError("Token search not supported by this backend")

    def search_phrase(self, phrase: str, field: str = "text") -> set[MessageId]:
        """N-gram based phrase search."""
        raise NotImplementedError("Phrase search not supported by this backend")

    def search_substring(self, pattern: str, field: str = "text") -> set[MessageId]:
        """Substring search using trigram index."""
        raise NotImplementedError("Substring search not supported by this backend")

    def search_regex(self, pattern: str, field: str = "text") -> set[MessageId]:
        """Regex pattern search."""
        raise NotImplementedError("Regex search not supported by this backend")
```

**Configuration**:

```python
class BackendConfig:
    """Backend configuration."""

    # Tokenization
    tokenizer: str = "unicode"  # "unicode", "spacy", "nltk"
    preserve_case: bool = False  # Keep original case

    # N-grams
    enable_ngrams: bool = True
    ngram_sizes: list[int] = [2, 3]  # Bigrams and trigrams
    ngram_min_frequency: int = 2  # Filter rare n-grams
    ngram_max_count: int = 10000  # Keep top N

    # Substring
    enable_substring_index: bool = True
    substring_trigram_min_length: int = 3

    # Regex
    regex_cache_size: int = 1000
```

---

## 3. Implementation Strategy

### 3.1 Phase 1: Token Matching (High Priority)

**Why first**: Fixes current limitations with minimal complexity

**Tasks**:
1. Implement Unicode-aware tokenizer
2. Add `_token_index` alongside `_text_index`
3. Add `search_tokens()` method
4. Update grammar with `contains_tokens()`
5. Add tests

**Estimated Impact**:
- Memory: +20-30% (more unique tokens)
- Speed: Same (O(1) lookup)
- Coverage: Better for technical text

### 3.2 Phase 2: N-gram Matching (Medium Priority)

**Why second**: Big win for phrase search with controllable memory

**Tasks**:
1. Implement n-gram generator
2. Add frequency filtering
3. Build `_bigram_index`, `_trigram_index`
4. Add `search_phrase()` method
5. Add `contains_phrase()` to grammar
6. Configuration for n-gram sizes

**Estimated Impact**:
- Memory: +50-100% (with filtering) or +500-1000% (without)
- Speed: O(1) phrase lookup vs O(n) current
- Coverage: Native multi-word expression support

### 3.3 Phase 3: Substring Matching (Medium Priority)

**Why third**: Useful but less critical than tokens/phrases

**Tasks**:
1. Implement trigram index for substrings
2. Add verification step
3. Add `search_substring()` method
4. Add `contains_substring()` to grammar
5. Benchmark vs linear scan

**Estimated Impact**:
- Memory: +200-300% (many trigrams)
- Speed: 10-100x faster than linear for long texts
- Coverage: Partial word matching

### 3.4 Phase 4: Regex Matching (Low Priority)

**Why last**: Already supported via linear scan, optimization is bonus

**Tasks**:
1. Add regex compilation cache
2. Implement literal extraction for pre-filtering
3. Add `search_regex()` method
4. Add `matches_regex()` to grammar
5. Add regex pattern validation

**Estimated Impact**:
- Memory: Negligible (just cache)
- Speed: 2-10x with pre-filtering
- Coverage: Complex pattern matching

---

## 4. Rust Implementation

All matching modes should have Rust equivalents for performance:

```rust
// Token matching
pub fn tokenize_unicode(text: &str) -> Vec<String> {
    // Use regex crate with Unicode support
    // Or fancy-regex for complex patterns
}

// N-gram generation
pub fn generate_ngrams(tokens: &[String], n: usize) -> Vec<String> {
    tokens.windows(n)
        .map(|window| window.join(" "))
        .collect()
}

// Substring trigrams
pub fn generate_substring_trigrams(text: &str) -> HashSet<String> {
    text.chars()
        .collect::<Vec<_>>()
        .windows(3)
        .map(|w| w.iter().collect::<String>())
        .collect()
}

// Regex search with cache
use regex::Regex;
use lru::LruCache;

pub struct RegexCache {
    cache: LruCache<String, Regex>,
}

impl RegexCache {
    pub fn search(&mut self, pattern: &str, text: &str) -> bool {
        let re = self.cache.get_or_insert(pattern.to_string(), || {
            Regex::new(pattern).unwrap()
        });
        re.is_match(text)
    }
}
```

---

## 5. Migration Path

**Backward Compatibility**:

```python
# Current behavior (word-based) is preserved
SELECT contains(greetings)  # Still uses word index

# New explicit operators for other modes
SELECT contains_tokens(greetings)  # Opt-in to token matching
```

**Deprecation Timeline**:
- v0.x: All modes available, `contains()` defaults to word
- v1.0: Could add config to change default mode
- v2.0: Could make token matching default

---

## 6. Performance Comparison

| Mode | Lookup Speed | Memory Overhead | Use Case |
|------|-------------|-----------------|----------|
| Word | O(1) | Baseline | Simple keywords |
| Token | O(1) | +20-30% | Technical text, punctuation |
| Bigram | O(1) | +50-100% | 2-word phrases |
| Trigram | O(1) | +100-200% | 3-word phrases |
| Substring | O(k) verify | +200-300% | Partial matching |
| Regex | O(n) worst | Minimal | Complex patterns |

**Memory Example** (100K messages, 50 words avg):
```
Word index:     50K entries  → 2 MB
Token index:    70K entries  → 3 MB (+50%)
Bigram index:   100K entries → 4 MB (+100%)
Trigram index:  200K entries → 8 MB (+300%)
Substring index: 150K entries → 6 MB (+200%)

Total with all indexes: ~23 MB vs 2 MB baseline (11.5x)
```

**Recommendation**:
- Default: Word + Token (3x memory, covers 90% of use cases)
- Optional: N-grams (controllable via config)
- On-demand: Substring, Regex (enable when needed)

---

## 7. Configuration Example

```python
from prismql.backends import RustMemoryBackend, BackendConfig

config = BackendConfig(
    # Tokenization
    tokenizer="unicode",  # "unicode", "spacy", "nltk"

    # N-grams
    enable_ngrams=True,
    ngram_sizes=[2, 3],  # Bigrams and trigrams
    ngram_min_frequency=2,  # Filter rare n-grams

    # Substring
    enable_substring_index=True,

    # Regex
    regex_cache_size=1000
)

backend = RustMemoryBackend(messages, config=config)
```

---

## 8. Open Questions

1. **Default behavior**: Should `contains()` use word or token matching by default?
   - **Recommendation**: Keep word for backward compat, add `contains_tokens()` explicit

2. **N-gram memory**: What default frequency threshold?
   - **Recommendation**: `min_frequency=2` (skip unique n-grams)

3. **Substring vs Regex**: When to use which?
   - **Guideline**: Substring for literals, regex for patterns

4. **Token vs Word**: Should we deprecate word matching eventually?
   - **Recommendation**: No - word matching is simpler and faster for basic use cases

5. **Query optimizer**: Should we automatically choose best index?
   - **Example**: `contains("hello world")` → auto-detect phrase, use bigram index
   - **Recommendation**: Phase 2 feature after basic modes are stable

---

## 9. Example Queries

```sql
-- Word matching (current)
SELECT contains(greetings)
WHERE from(alice)

-- Token matching (preserve punctuation)
SELECT contains_tokens(email_addresses)
WHERE contains_tokens("C++")

-- Phrase matching (multi-word)
SELECT contains_phrase("thank you")
WHERE contains_phrase("out of memory")

-- Substring matching (partial words)
SELECT contains_substring("temp")  -- Matches "temperature", "temporary"
WHERE contains_substring("@gmail.com")

-- Regex matching (complex patterns)
SELECT matches_regex(r"\d{3}-\d{3}-\d{4}")  -- Phone numbers
WHERE matches_regex(r"\b[A-Z]{2,}\b")  -- Acronyms

-- Combining modes
SELECT
    contains_phrase("thank you") FOLLOWED_BY from(support) WITHIN 5
WHERE
    matches_regex(r"#\d+")  -- Contains issue number
```

---

## 10. Summary and Recommendations

### Immediate (Phase 1):
1. ✅ **Token matching** - fixes punctuation issues, minimal cost
   - Implement Unicode-aware tokenizer
   - Add `contains_tokens()` operator
   - Expected: +20-30% memory, same speed

### Near-term (Phase 2):
2. ✅ **N-gram matching** - huge win for phrases, controllable memory
   - Implement bigram/trigram indexes with frequency filtering
   - Add `contains_phrase()` operator
   - Expected: +50-100% memory (filtered), O(1) phrase search

### Future (Phase 3-4):
3. ⚠️ **Substring matching** - useful but expensive
   - Implement trigram index for substrings
   - Add `contains_substring()` operator
   - Expected: +200-300% memory, 10-100x faster than scan

4. ⚠️ **Regex matching** - nice-to-have optimization
   - Add regex cache and pre-filtering
   - Add `matches_regex()` operator
   - Expected: Minimal memory, 2-10x faster with pre-filtering

### Default Configuration:
```python
BackendConfig(
    tokenizer="unicode",
    enable_ngrams=True,
    ngram_sizes=[2, 3],
    ngram_min_frequency=2,
    enable_substring_index=False,  # Opt-in (expensive)
    regex_cache_size=1000
)
```

This provides:
- ✅ Fast word and token matching
- ✅ Efficient phrase search (2-3 word expressions)
- ✅ Reasonable memory overhead (~3-4x baseline)
- ✅ Backward compatible
- ✅ Extensible for future needs
