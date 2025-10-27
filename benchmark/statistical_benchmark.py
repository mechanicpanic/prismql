#!/usr/bin/env python3
"""
Statistical Benchmark Runner for Algorithm Comparison
Runs multiple iterations and calculates confidence intervals
"""

import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
import psutil
from scipy import stats


def get_hardware_info():
    """Gather system hardware information."""
    info = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(logical=False),
        "cpu_threads": psutil.cpu_count(logical=True),
        "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "python_version": platform.python_version(),
    }

    # Get CPU model on Linux
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    info["cpu_model"] = line.split(":")[1].strip()
                    break
    except:
        info["cpu_model"] = platform.processor()

    return info


def run_rust_benchmark(iterations=10):
    """Run Rust benchmark multiple times and collect results."""
    rust_binary = "/home/aleph/projects/prismql-rust/target/release/prismql-benchmark"

    if not Path(rust_binary).exists():
        print(f"Error: Rust binary not found at {rust_binary}")
        print("Please build with: cargo build --release --features benchmark")
        return None

    all_results = {
        "Q1": {"N+NS": [], "N+S": [], "P+NS": [], "P+S": [], "H+P": []},
        "Q2": {"N+NS": [], "N+S": [], "P+NS": [], "P+S": [], "H+P": []},
        "Q3": {"N+NS": [], "N+S": [], "P+NS": [], "P+S": [], "H+P": []},
    }

    print(f"Running {iterations} iterations of Rust benchmark...")

    for i in range(iterations):
        print(f"  Iteration {i + 1}/{iterations}...", end="", flush=True)

        try:
            # Run benchmark
            result = subprocess.run(
                [rust_binary],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                print(f" ERROR: {result.stderr}")
                continue

            # Parse output for timings
            lines = result.stdout.split("\n")
            current_query = None

            for line in lines:
                if "Q1:" in line:
                    current_query = "Q1"
                elif "Q2:" in line:
                    current_query = "Q2"
                elif "Q3:" in line:
                    current_query = "Q3"
                elif current_query and any(
                    algo in line for algo in ["N+NS", "N+S", "P+NS", "P+S", "H+P"]
                ):
                    # Extract timing from line like: "P+S                  207.0             1.1       193.19x              18"
                    parts = line.split()
                    if len(parts) >= 3:
                        algo = parts[0]
                        rust_time = float(parts[2])
                        all_results[current_query][algo].append(rust_time)

            print(" ✓")

        except subprocess.TimeoutExpired:
            print(" TIMEOUT")
        except Exception as e:
            print(f" ERROR: {e}")

    return all_results


def run_csharp_benchmark(iterations=10):
    """Run C# benchmark multiple times and collect results."""
    csharp_project = "/home/aleph/projects/prismql/benchmark/csharp-reference"
    csv_file = "/home/aleph/projects/prismql/data/freecodecamp_casual_chatroom.csv"

    all_results = {
        "Q1": {"P+NS": [], "P+S": []},
        "Q2": {"P+NS": [], "P+S": []},
        "Q3": {"P+NS": [], "P+S": []},
    }

    print(f"Running {iterations} iterations of C# benchmark...")

    for i in range(iterations):
        print(f"  Iteration {i + 1}/{iterations}...", end="", flush=True)

        try:
            # Run benchmark
            result = subprocess.run(
                ["dotnet", "run", "--configuration", "Release", "--", csv_file],
                cwd=csharp_project,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f" ERROR: {result.stderr}")
                continue

            # Parse output for timings
            lines = result.stdout.split("\n")
            current_query = None

            for line in lines:
                if "Q1:" in line:
                    current_query = "Q1"
                elif "Q2:" in line:
                    current_query = "Q2"
                elif "Q3:" in line:
                    current_query = "Q3"
                elif current_query and any(algo in line for algo in ["P+NS", "P+S"]):
                    # Extract timing from line like: "P+S                   29.6              19"
                    parts = line.split()
                    if len(parts) >= 2:
                        algo = parts[0]
                        cs_time = float(parts[1])
                        all_results[current_query][algo].append(cs_time)

            print(" ✓")

        except subprocess.TimeoutExpired:
            print(" TIMEOUT")
        except Exception as e:
            print(f" ERROR: {e}")

    return all_results


def calculate_statistics(times):
    """Calculate mean, std dev, and 95% confidence interval."""
    if not times:
        return None

    times = np.array(times)
    mean = np.mean(times)
    std = np.std(times, ddof=1)  # Sample std dev
    sem = std / np.sqrt(len(times))  # Standard error of the mean

    # 95% confidence interval
    confidence = 0.95
    ci = stats.t.interval(confidence, len(times) - 1, loc=mean, scale=sem)

    return {
        "mean": mean,
        "std": std,
        "min": np.min(times),
        "max": np.max(times),
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "n": len(times),
        "raw_times": times.tolist(),
    }


def generate_report(rust_results, csharp_results, hardware_info):
    """Generate comprehensive benchmark report."""
    report = []
    report.append("=" * 80)
    report.append("STATISTICAL BENCHMARK REPORT")
    report.append("=" * 80)
    report.append("")

    # Hardware info
    report.append("## Hardware Specifications")
    report.append(f"- CPU: {hardware_info.get('cpu_model', 'Unknown')}")
    report.append(
        f"- Cores: {hardware_info['cpu_count']} physical, {hardware_info['cpu_threads']} threads"
    )
    report.append(f"- Memory: {hardware_info['memory_gb']} GB")
    report.append(f"- Platform: {hardware_info['platform']}")
    report.append(f"- Timestamp: {hardware_info['timestamp']}")
    report.append("")

    # Results for each query
    for query in ["Q1", "Q2", "Q3"]:
        report.append(f"## {query} Results")
        report.append("")

        # Table header
        report.append(
            "| Algorithm | Implementation | Mean (ms) | 95% CI | Std Dev | Speedup |"
        )
        report.append(
            "|-----------|---------------|-----------|--------|---------|---------|"
        )

        # Get P+S baseline for speedup calculation
        rust_ps = None
        if rust_results and query in rust_results and "P+S" in rust_results[query]:
            rust_ps = calculate_statistics(rust_results[query]["P+S"])

        # Rust results
        if rust_results and query in rust_results:
            for algo in ["N+NS", "N+S", "P+NS", "P+S", "H+P"]:
                if algo in rust_results[query]:
                    stats = calculate_statistics(rust_results[query][algo])
                    if stats:
                        speedup = ""
                        if rust_ps and algo != "P+S":
                            speedup = f"{rust_ps['mean'] / stats['mean']:.2f}x"
                        elif algo == "P+S":
                            speedup = "baseline"

                        report.append(
                            f"| {algo:9} | Rust          | {stats['mean']:9.2f} | "
                            f"[{stats['ci_lower']:.2f}, {stats['ci_upper']:.2f}] | "
                            f"{stats['std']:7.2f} | {speedup:7} |"
                        )

        # C# results
        if csharp_results and query in csharp_results:
            for algo in ["P+NS", "P+S"]:
                if algo in csharp_results[query]:
                    stats = calculate_statistics(csharp_results[query][algo])
                    if stats:
                        speedup = ""
                        if rust_ps:
                            speedup = f"{rust_ps['mean'] / stats['mean']:.2f}x"

                        report.append(
                            f"| {algo:9} | C#            | {stats['mean']:9.2f} | "
                            f"[{stats['ci_lower']:.2f}, {stats['ci_upper']:.2f}] | "
                            f"{stats['std']:7.2f} | {speedup:7} |"
                        )

        report.append("")

        # H+P vs P+S comparison
        if rust_results and query in rust_results:
            if "H+P" in rust_results[query] and "P+S" in rust_results[query]:
                hp_stats = calculate_statistics(rust_results[query]["H+P"])
                ps_stats = calculate_statistics(rust_results[query]["P+S"])
                if hp_stats and ps_stats:
                    speedup = ps_stats["mean"] / hp_stats["mean"]
                    report.append(f"**H+P vs P+S speedup: {speedup:.2f}x**")
                    report.append("")

    return "\n".join(report)


def save_results(rust_results, csharp_results, hardware_info):
    """Save detailed results to JSON."""
    output = {"hardware": hardware_info, "rust": {}, "csharp": {}}

    # Process Rust results
    if rust_results:
        for query in rust_results:
            output["rust"][query] = {}
            for algo in rust_results[query]:
                stats = calculate_statistics(rust_results[query][algo])
                if stats:
                    output["rust"][query][algo] = stats

    # Process C# results
    if csharp_results:
        for query in csharp_results:
            output["csharp"][query] = {}
            for algo in csharp_results[query]:
                stats = calculate_statistics(csharp_results[query][algo])
                if stats:
                    output["csharp"][query][algo] = stats

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_results_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDetailed results saved to: {filename}")
    return filename


def main():
    """Run statistical benchmarks."""
    print("Statistical Benchmark Runner")
    print("=" * 40)

    # Get hardware info
    hardware_info = get_hardware_info()

    # Number of iterations
    iterations = 10

    # Run benchmarks
    rust_results = run_rust_benchmark(iterations)
    csharp_results = run_csharp_benchmark(iterations)

    # Generate report
    report = generate_report(rust_results, csharp_results, hardware_info)
    print("\n" + report)

    # Save results
    save_results(rust_results, csharp_results, hardware_info)

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"benchmark_report_{timestamp}.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()
