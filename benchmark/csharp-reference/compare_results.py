#!/usr/bin/env python3
"""Compare results from C# and Rust benchmarks to verify correctness."""

import json
from pathlib import Path


def load_results(rust_file, csharp_file):
    """Load results from both JSON files."""
    with open(rust_file) as f:
        rust_data = json.load(f)
    with open(csharp_file) as f:
        csharp_data = json.load(f)
    return rust_data, csharp_data


def compare_algorithm(algo_name, rust_data, csharp_data):
    """Compare results for a specific algorithm."""
    rust_algo = rust_data.get(algo_name, {})
    cs_algo = csharp_data.get(algo_name, {})

    if not rust_algo or not cs_algo:
        print(
            f"  ⚠️  {algo_name}: Missing data (Rust: {bool(rust_algo)}, C#: {bool(cs_algo)})"
        )
        return False

    # Handle different field names between Rust and C#
    rust_count = rust_algo.get("count", 0)
    cs_count = cs_algo.get("Count", cs_algo.get("count", 0))

    rust_time = rust_algo.get("time_ms", 0)
    cs_time = cs_algo.get("Time", cs_algo.get("time_ms", 0))

    rust_results = rust_algo.get("results", [])
    cs_results = cs_algo.get("Results", cs_algo.get("results", []))

    # Check if counts match
    count_match = rust_count == cs_count

    # Check if first 100 results match (sorting to handle order differences)
    rust_sorted = sorted([sorted(r) for r in rust_results])
    cs_sorted = sorted([sorted(r) for r in cs_results])
    results_match = rust_sorted == cs_sorted

    # Calculate speedup
    speedup = cs_time / rust_time if rust_time > 0 else 0

    # Print results
    status = "✅" if count_match and results_match else "❌"
    print(
        f"  {status} {algo_name:6} | Count: {rust_count:6} vs {cs_count:6} | "
        f"Time: {rust_time:8.1f}ms vs {cs_time:8.1f}ms | Speedup: {speedup:.2f}x"
    )

    if not count_match:
        print(f"      ❌ Count mismatch: Rust={rust_count}, C#={cs_count}")

    if not results_match and count_match:
        # Find differences in results
        rust_set = set(tuple(sorted(r)) for r in rust_results)
        cs_set = set(tuple(sorted(r)) for r in cs_results)

        missing_in_rust = cs_set - rust_set
        extra_in_rust = rust_set - cs_set

        if missing_in_rust:
            print(f"      ❌ Missing in Rust: {list(missing_in_rust)[:3]}...")
        if extra_in_rust:
            print(f"      ❌ Extra in Rust: {list(extra_in_rust)[:3]}...")

    return count_match and results_match


def main():
    queries = ["q1", "q2", "q3"]

    import os

    base_dir = "/tmp/csharp-benchmark/standalone"
    if not os.getcwd().endswith("standalone"):
        os.chdir(base_dir)

    print("=" * 80)
    print("BENCHMARK RESULTS COMPARISON - C# vs Rust")
    print("=" * 80)
    print()

    for query in queries:
        rust_file = f"rust_results_{query}.json"
        csharp_file = f"csharp_results_{query}.json"

        if not Path(rust_file).exists() or not Path(csharp_file).exists():
            print(f"⚠️  Skipping {query.upper()}: Missing files")
            print(
                f"   Rust: {Path(rust_file).exists()}, C#: {Path(csharp_file).exists()}"
            )
            print()
            continue

        rust_data, csharp_data = load_results(rust_file, csharp_file)

        print(f"{query.upper()} COMPARISON:")
        print("-" * 40)

        algorithms = ["N+NS", "N+S", "P+NS", "P+S"]
        all_match = True

        for algo in algorithms:
            if not compare_algorithm(algo, rust_data, csharp_data):
                all_match = False

        # Check H+P if present in Rust (not in C#)
        if "H+P" in rust_data:
            hp_data = rust_data["H+P"]
            print(
                f"  ℹ️  H+P    | Count: {hp_data['count']:6}    | "
                f"Time: {hp_data['time_ms']:8.1f}ms (Rust only)"
            )

        if all_match:
            print(f"  ✅ All algorithms match for {query.upper()}!")
        else:
            print(f"  ❌ Some algorithms don't match for {query.upper()}")

        print()

    print("=" * 80)
    print("SUMMARY:")
    print("✅ = Results match exactly")
    print("❌ = Results differ")
    print("ℹ️ = Information only")
    print("=" * 80)


if __name__ == "__main__":
    main()
