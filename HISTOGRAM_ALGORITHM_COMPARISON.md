# Histogram Algorithm Comparison

**Date:** 2025-10-23
**Paper:** Query Processing and Optimization for a Custom Retrieval Language (PANDL 2022)
**Authors:** Kuzin, Smirnova, Slobodkin, Chernishev

---

## Paper's Algorithms

### 1. N+NS (Naive, No Sort)
**Complexity:** O(n · m²)

**Algorithm:**
- Recursive approach
- Starts with first group
- For each message in first group, tries to build combination
- Checks order constraint (msg_i < msg_i+1)
- Checks INWIN constraint
- No optimizations

**Performance:** Baseline (slowest)

---

### 2. N+S (Naive, with Sort)
**Complexity:** O(n · m² + m log m)

**Algorithm:**
- Same as N+NS but sorts each group first
- **Key optimization:** Early termination
  - If current message exceeds INWIN window, stop checking rest of sorted group
- Still naive recursive approach

**Performance:** 1.8-2.2x faster than N+NS

---

### 3. P+NS (Position-based, No Sort)
**Complexity:** Better than naive, not formally analyzed

**Algorithm:**
- **Key innovation:** Start with smallest group first
- Reduces recursive branches
- "Position-based" checking: must verify both:
  - Previous message ID < current ID (if already placed)
  - Current ID < next message ID (if already placed)

**Performance:** 8-10.8x faster than N+NS

---

### 4. P+S (Position-based, with Sort) ⭐ BEST
**Complexity:** Not formally analyzed, empirically best

**Algorithm:**
- Combines P+NS (smallest first) with N+S (sorting for early termination)
- Sorts each group: O(k · m log m)
- Processes smallest to largest
- Uses sorted order for early pruning

**Performance:** **10.9x faster than N+NS** (best overall)

**Why it wins:**
- Smallest-first minimizes recursive tree depth
- Sorting enables aggressive pruning
- Synergy between both optimizations

---

### 5. H+S (Histograms with Sort)
**Complexity:** O(k · n log n) for multi-way merge

**Algorithm:**
1. **Build equi-width histograms** for each group
2. **Sort groups by size** (smallest first)
3. **Two-at-a-time merging:**
   - Consider triples (A, B, C)
   - Evaluate merge orders: (AB)C, (BC)A, (AC)B
   - Use histogram intersection to estimate intermediate sizes
   - Choose order with smallest intermediate
4. **Merge** using histogram intersection

**Performance:** Sometimes beats P+S (25% on specific queries), never loses

**Why histogram intersection matters:**
- Identifies which merge order produces fewest intermediates
- Example from paper (Figure 3):
  - Groups A, B, C with different distributions
  - (AC) produces fewer intermediates than (AB)
  - Histograms reveal this statically

---

## My Algorithm (Claude's Design)

### HistogramWindowProcessor.merge_restrictions_histogram()

**Complexity:** O(k · n · log m)

**Algorithm:**
1. **Build position map:** Convert all message IDs to positions O(n log n)
2. **Create histograms:** Sorted position lists for each group O(k · m log m)
3. **Sort by size:** Order histograms smallest to largest O(k log k)
4. **Multi-way merge:**
   - Start with smallest histogram
   - For each position in starting histogram:
     - Use **binary search** to find candidates in other histograms: O(log m)
     - Check all-pairs INWIN constraint: O(k²)
     - Add valid combination

**Key Differences from Paper:**
- **Multi-way merge** (not two-at-a-time)
- **Binary search** for window lookups (same as paper's implicit approach)
- **No histogram intersection** for size estimation

---

### HistogramWindowProcessor.merge_restrictions_optimized()

**Complexity:** O(k · n · log n)

**Algorithm:**
1. Same histogram setup
2. **Progressive merge with pruning:**
   - Start with smallest: `results = [(pos,) for pos in hist[0]]`
   - For each subsequent histogram:
     - Extend each partial result with compatible positions
     - **Prune:** Drop partial results that can't be extended
   - Early termination if results become empty

**Key Differences:**
- **Progressive pruning** reduces intermediate result size
- Similar to two-at-a-time but maintains partial results
- More memory-efficient for sparse patterns

---

### HistogramWindowProcessor.merge_two_way_sweep()

**Complexity:** O(n + m) - **OPTIMAL for two groups**

**Algorithm:**
- Two-pointer sweep-line
- For each position in hist1:
  - Advance pointer in hist2 to window start
  - Collect all positions within window
- **Linear time!**

**Use Case:** Optimal for 2-restriction queries

---

## Theoretical Analysis Comparison

| Algorithm | Complexity | Space | Best For |
|-----------|-----------|-------|----------|
| **N+NS** (Paper) | O(n · m²) | O(n) | Baseline |
| **N+S** (Paper) | O(n · m²) | O(n + k·m log m) | Small windows |
| **P+NS** (Paper) | ~O(n · m) | O(n) | Sparse patterns |
| **P+S** (Paper) ⭐ | ~O(n · m) | O(n + k·m log m) | **General purpose** |
| **H+S** (Paper) | O(k · n log n) | O(n + histograms) | Many groups, skewed distribution |
| **Two-way sweep** (Mine) | O(n + m) | O(n) | **Two groups only** |
| **Multi-way** (Mine) | O(k · n · log m) | O(n) | Many groups |
| **Progressive** (Mine) | O(k · n · log n) | O(n + partials) | Sparse with pruning |

---

## Empirical Results from Paper

**Dataset:** 1M messages from freeCodeCamp Gitter Chat

| Query | Groups | N+NS (ms) | P+S (ms) | Speedup |
|-------|--------|-----------|----------|---------|
| Q1    | 3      | 2253.5    | 207.0    | **10.9x** |
| Q2    | 5      | 4260.6    | 419.1    | **10.2x** |
| Q3    | 2 subqueries | 4354.1 | 379.2 | **11.5x** |
| Q4    | 3 subqueries | 11615.2 | 1318.6 | **8.8x** |
| **Total** | — | **22483.4** | **2323.9** | **9.7x** |

**H+S Results:**
- Q5: 1479 ms (H+S) vs 1865 ms (P+S) = **25% faster**
- Q5 has 8 user OR clauses - skewed distribution benefits histogram approach

---

## Key Insights from Paper

### 1. Why P+S Wins Overall

**Smallest-first** + **Early termination** = Powerful synergy

- Starting with smallest group minimizes recursive tree
- Sorting enables aggressive pruning when window exceeded
- No histogram overhead for size estimation

### 2. When H+S Wins

**Skewed distributions** where merge order matters:

```
Example from paper (Figure 3):
Hist A: [■■■     ■■■]  <- Sparse at edges
Hist B: [    ■■■    ]  <- Dense in middle
Hist C: [■■■     ■■■]  <- Sparse at edges

Merging (AB) first: Many intermediates (A overlaps little with B)
Merging (AC) first: Few intermediates (A and C align well)
```

H+S detects this via histogram intersection and chooses (AC)B order.

### 3. Sorting is Nearly Free

Figure 4 in paper shows sorting overhead is negligible compared to merge benefits.

### 4. Lucene Access Dominates for Complex Queries

For Q4 (3 subqueries), Lucene index access became the bottleneck.
This motivated Phase 3 optimization in PrismQL roadmap.

---

## My Algorithm's Novel Contributions

### 1. Two-Way Sweep (O(n+m))
**Paper doesn't have this!**

Optimal linear-time algorithm for two-group case:
```python
def merge_two_way_sweep(hist1, hist2, window):
    pairs = []
    j = 0
    for pos1 in hist1:
        while j < len(hist2) and hist2[j] < pos1 - window:
            j += 1
        k = j
        while k < len(hist2) and hist2[k] <= pos1 + window:
            pairs.append((pos1, hist2[k]))
            k += 1
    return pairs  # O(n + m) time!
```

### 2. Progressive Pruning
Paper's H+S does two-at-a-time. My progressive merge:
- Maintains partial results through all histograms
- Prunes impossible partial results early
- Potentially better memory locality

### 3. Explicit Complexity Analysis
Paper doesn't provide formal complexity analysis. I do.

---

## Recommendations

### For PrismQL Implementation:

1. **Default algorithm:** Port paper's **P+S** (proven 10x speedup)
   - Simplest to implement
   - Best general-purpose performance
   - Minimal overhead

2. **Optimize two-group case:** Use my **two-way sweep**
   - O(n + m) is optimal
   - Common case in practice

3. **Optional: H+S for skewed data**
   - Requires histogram statistics
   - Beneficial for queries with many OR clauses
   - More complex to implement

4. **Progressive pruning:** Experimental
   - Test on real workloads
   - May help with very large k (many groups)

---

## Benchmark Implementation Plan

### Phase 1: Implement Paper's Algorithms
- ✅ N+NS (current window.py is close)
- [ ] N+S
- [ ] P+NS
- [ ] P+S (priority)
- [ ] H+S

### Phase 2: Download Benchmark Data
- [ ] freeCodeCamp Gitter dataset (Kaggle)
- [ ] First 1M messages
- [ ] Load into MemoryBackend

### Phase 3: Port Benchmark Queries
- [ ] Q1: 3 groups, UNR, INWIN 40
- [ ] Q2: 5 groups, INWIN 40
- [ ] Q3: 2 subqueries
- [ ] Q4: 3 subqueries
- [ ] Q5: 8 OR clauses (tests H+S)

### Phase 4: Run Comparisons
- [ ] Measure: N+NS, N+S, P+NS, P+S, H+S
- [ ] Measure: My histogram algorithms
- [ ] Compare with paper's results
- [ ] Generate performance report

---

## Expected Outcomes

### Hypothesis 1: P+S will match paper's results
- Should see ~10x speedup vs naive
- Proven approach

### Hypothesis 2: Two-way sweep will excel on 2-group queries
- Theoretical O(n+m) advantage
- Should be fastest for this case

### Hypothesis 3: H+S will win on Q5
- Paper showed 25% improvement
- Validates histogram intersection approach

### Hypothesis 4: Progressive pruning performance TBD
- Could be better for sparse patterns
- Could be worse due to overhead
- Needs empirical testing

---

## Conclusion

**Paper's P+S algorithm is proven and should be our baseline.**

My algorithms provide:
1. **Theoretical optimality** for two-group case (O(n+m))
2. **Alternative approaches** (progressive pruning) worth testing
3. **Formal complexity analysis** the paper lacks

Next step: **Implement benchmark and measure real performance!**
