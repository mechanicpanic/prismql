# Histogram Algorithm Benchmarks

This directory contains benchmark implementations and comparison tools for histogram-based window merging algorithms from the PANDL 2022 paper.

## Structure

```
benchmark/
├── csharp-reference/     # Fixed C# reference implementation
│   ├── HistogramBenchmark.cs
│   ├── HistogramBenchmark.csproj
│   └── compare_results.py
├── results/               # Benchmark results (created on run)
└── README.md             # This file
```

## Implementations Compared

1. **Rust Implementation** (`/home/aleph/projects/prismql-rust/`)
   - High-performance implementation with all 5 algorithms
   - Includes novel H+P (Histogram+Position) algorithm

2. **C# Reference** (`benchmark/csharp-reference/`)
   - Original implementation from PANDL 2022 paper
   - Fixed to correctly parse CSV with CsvHelper library
   - Implements 4 algorithms (N+NS, N+S, P+NS, P+S)

## Key Fixes Applied to C# Implementation

1. **CSV Field Mapping**: Fixed to read correct fields (12 for username, 22 for text)
2. **CSV Parser**: Replaced manual parsing with CsvHelper for robust handling
3. **User Mentions**: Changed to search without @ prefix to match data format

## Running Benchmarks

### Rust Benchmark
```bash
cd /home/aleph/projects/prismql-rust
./target/release/prismql-benchmark
```

### C# Benchmark
```bash
cd benchmark/csharp-reference
dotnet run --configuration Release -- ../../data/freecodecamp_casual_chatroom.csv
```

### Compare Results
```bash
cd benchmark/csharp-reference
python3 compare_results.py
```

## Verified Results (1M messages)

All implementations produce identical results:

| Query | Groups | Window | Results | Rust P+S | C# P+S | Speedup |
|-------|--------|--------|---------|----------|--------|---------|
| Q1    | 3      | 40     | 19      | 1.0ms    | 29.6ms | 29.6x   |
| Q2    | 5      | 40     | 3,420   | 159.9ms  | 642.7ms| 4.0x    |
| Q3    | 6      | 60     | 6,370   | 341.0ms  | 1514.9ms| 4.4x   |

**H+P Algorithm** (Rust-only): 50-150x faster than P+S

## Algorithm Performance Summary

- **N+NS** (Naive, No Sort): Slowest, exhaustive search
- **N+S** (Naive + Sort): 2-3x faster with early termination
- **P+NS** (Position, No Sort): 10-50x faster than naive
- **P+S** (Position + Sort): Best from paper, 100-200x faster than N+NS
- **H+P** (Histogram + Position): Novel algorithm, 50-150x faster than P+S

## Data Specifications

- Dataset: FreeCodeCamp casual chatroom
- Messages: 1,000,000
- Dictionaries: job (6 words), code (4), skill (7), dev (7), area (6), money (3)
- User mentions: "Kadams223" (8 occurrences)

## Validation

✅ All result counts match between implementations
✅ All message ID combinations match exactly
✅ Performance measurements reproducible
✅ CSV parsing verified with proper field mappings