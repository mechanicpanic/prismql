# Actual Benchmark Results - Hardware & Performance

**Date**: 2025-10-24
**Hardware**: Intel Core i7-1260P (12 cores, 16 threads) @ 4.7GHz, 16GB RAM
**OS**: Linux 6.17.4-arch2-1 x86_64

## Executive Summary

The optimized H+P (Histogram+Position) algorithm achieves:
- **53.3x speedup** over P+S on Q3 (6,370 results)
- **32.2x speedup** over P+S on Q2 (3,420 results)
- **2.4x slower** than P+S on Q1 (18 results) due to overhead

## Full Benchmark Results (1M messages)

### Q1: Job + Code + User Mention (3 groups, 18 results)

| Algorithm | Rust (ms) | C# (ms) | Rust vs C# | vs Rust P+S |
|-----------|-----------|---------|------------|-------------|
| N+NS      | 7,802.1   | -       | -          | 0.0001x     |
| N+S       | 1,549.6   | -       | -          | 0.0007x     |
| P+NS      | 4.0       | 17.6    | 4.4x       | 0.28x       |
| **P+S**   | **1.1**   | 29.6    | **26.9x**  | baseline    |
| **H+P**   | **2.6**   | -       | -          | **0.42x**   |

**Key Finding**: H+P has overhead that makes it 2.4x slower than P+S on small result sets.

### Q2: Job + Skill×2 + Area + Money (5 groups, 3,420 results)

| Algorithm | Rust (ms) | C# (ms) | Rust vs C# | vs Rust P+S |
|-----------|-----------|---------|------------|-------------|
| N+NS      | 12,144.8  | -       | -          | 0.013x      |
| N+S       | 3,286.6   | -       | -          | 0.048x      |
| P+NS      | 488.9     | 1,139.6 | 2.3x       | 0.32x       |
| **P+S**   | **157.7** | 642.7   | **4.1x**   | baseline    |
| **H+P**   | **4.9**   | -       | -          | **32.2x**   |

**Key Finding**: H+P is 32x faster than P+S on medium-sized result sets.

### Q3: Job + Dev + Skill×2 + Area + Money (6 groups, 6,370 results)

| Algorithm | Rust (ms) | C# (ms)  | Rust vs C# | vs Rust P+S |
|-----------|-----------|----------|------------|-------------|
| N+NS      | 17,383.4  | -        | -          | 0.025x      |
| N+S       | 4,623.0   | -        | -          | 0.096x      |
| P+NS      | 1,136.7   | 2,429.9  | 2.1x       | 0.39x       |
| **P+S**   | **442.8** | 1,514.9  | **3.4x**   | baseline    |
| **H+P**   | **8.3**   | -        | -          | **53.3x**   |

**Key Finding**: H+P is 53x faster than P+S on large result sets!

## Algorithm Comparison

### H+P Performance Characteristics

| Query | Results | P+S (ms) | H+P (ms) | Speedup | Analysis |
|-------|---------|----------|----------|---------|----------|
| Q1    | 18      | 1.1      | 2.6      | 0.42x   | Overhead dominates on small sets |
| Q2    | 3,420   | 157.7    | 4.9      | 32.2x   | Excellent performance on medium sets |
| Q3    | 6,370   | 442.8    | 8.3      | 53.3x   | Exceptional performance on large sets |

### Cross-Language Performance

| Query | Rust P+S | C# P+S | Speedup | Rust H+P | vs C# P+S |
|-------|----------|--------|---------|----------|-----------|
| Q1    | 1.1ms    | 29.6ms | 26.9x   | 2.6ms    | 11.4x     |
| Q2    | 157.7ms  | 642.7ms| 4.1x    | 4.9ms    | **131x**  |
| Q3    | 442.8ms  | 1514.9ms| 3.4x   | 8.3ms    | **182x**  |

## Key Optimizations in H+P

1. **Binary Search with partition_point**
   - Skips positions that violate order constraints in O(log n)
   - Directly jumps to valid candidates

2. **Early Termination**
   - Stops processing when positions exceed window bounds
   - Sorted histograms enable this optimization

3. **Pre-collected Constraints**
   - Existing messages collected once per partial result
   - Fast uniqueness checking with single containment test

4. **Window Bound Pre-calculation**
   - `window_lo` and `window_hi` calculated once
   - Simple range checks instead of repeated calculations

## Performance Analysis

### Complexity

| Algorithm | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| N+NS      | O(n · m²)      | O(n)             |
| N+S       | O(n · m²)      | O(n + m log m)   |
| P+NS      | ~O(n · m)      | O(n)             |
| P+S       | ~O(n · m)      | O(n + m log m)   |
| **H+P**   | **O(k·n·log m)**| **O(n)**        |

Where:
- n = size of smallest group
- m = average group size
- k = number of groups

### Scalability

H+P scales exceptionally well with:
- ✅ Large result sets (32-53x speedup)
- ✅ Many groups (6 groups still fast)
- ✅ Large windows (maintains performance)
- ❌ Small result sets (overhead makes it slower)

## Recommendations

1. **Use H+P for production queries** with >100 expected results
2. **Use P+S for small queries** with <100 expected results
3. **Adaptive selection**: Choose algorithm based on group sizes

## Notes

- Single-run benchmark (not statistical average)
- C# runs with CsvHelper for proper CSV parsing
- Rust compiled with `--release` and optimizations
- Both implementations verified to produce identical results
- Group sizes: job=50,110, code=135,860, skill=54,744, dev=23,747, area=17,045, money=2,368, mentions=7-8