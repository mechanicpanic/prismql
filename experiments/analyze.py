"""
Analysis and reporting for experiment results.
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ModelMetrics:
    """Aggregate metrics for a model."""

    model: str
    strategy: str
    total_tests: int
    syntax_correct: int
    semantically_correct: int
    uses_fluent_syntax: int
    avg_edit_distance: float
    avg_attempts: float
    avg_time_ms: float
    by_difficulty: dict[str, dict[str, int]]
    by_category: dict[str, dict[str, int]]

    @property
    def syntax_accuracy(self) -> float:
        """Percentage of syntactically correct queries."""
        return (
            (self.syntax_correct / self.total_tests * 100)
            if self.total_tests > 0
            else 0.0
        )

    @property
    def semantic_accuracy(self) -> float:
        """Percentage of semantically correct queries (of those syntactically correct)."""
        return (
            (self.semantically_correct / self.syntax_correct * 100)
            if self.syntax_correct > 0
            else 0.0
        )

    @property
    def fluent_syntax_rate(self) -> float:
        """Percentage using fluent syntax (not deprecated)."""
        return (
            (self.uses_fluent_syntax / self.total_tests * 100)
            if self.total_tests > 0
            else 0.0
        )


def load_results(filename: str) -> dict[str, Any]:
    """Load experiment results from JSON file."""
    results_dir = Path(__file__).parent / "results"
    with open(results_dir / filename) as f:
        return json.load(f)


def analyze_results(
    results_data: dict[str, Any], test_cases_map: dict[str, Any]
) -> dict[str, ModelMetrics]:
    """
    Analyze experiment results and compute metrics.

    Args:
        results_data: Loaded JSON results
        test_cases_map: Map of test_case_id -> test_case info (difficulty, category)

    Returns:
        Dict mapping (model, strategy) -> ModelMetrics
    """
    # Group results by (model, strategy)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for result in results_data["results"]:
        key = (result["model"], result["prompt_strategy"])
        grouped[key].append(result)

    # Calculate metrics for each group
    metrics_map: dict[str, ModelMetrics] = {}

    for (model, strategy), results_list in grouped.items():
        total = len(results_list)
        syntax_correct = sum(1 for r in results_list if r["syntax_correct"])
        semantically_correct = sum(1 for r in results_list if r["semantically_correct"])
        fluent = sum(1 for r in results_list if r["uses_fluent_syntax"])

        edit_distances = [r["edit_distance_from_ground_truth"] for r in results_list]
        avg_edit = sum(edit_distances) / len(edit_distances) if edit_distances else 0

        attempts = [r["num_attempts"] for r in results_list]
        avg_attempts = sum(attempts) / len(attempts) if attempts else 0

        times = [r["time_taken_ms"] for r in results_list]
        avg_time = sum(times) / len(times) if times else 0

        # Break down by difficulty
        by_difficulty: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "correct": 0}
        )
        for r in results_list:
            tc = test_cases_map.get(r["test_case_id"])
            if tc:
                diff = tc["difficulty"]
                by_difficulty[diff]["total"] += 1
                if r["syntax_correct"]:
                    by_difficulty[diff]["correct"] += 1

        # Break down by category
        by_category: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "correct": 0}
        )
        for r in results_list:
            tc = test_cases_map.get(r["test_case_id"])
            if tc:
                cat = tc["category"]
                by_category[cat]["total"] += 1
                if r["syntax_correct"]:
                    by_category[cat]["correct"] += 1

        metrics = ModelMetrics(
            model=model,
            strategy=strategy,
            total_tests=total,
            syntax_correct=syntax_correct,
            semantically_correct=semantically_correct,
            uses_fluent_syntax=fluent,
            avg_edit_distance=avg_edit,
            avg_attempts=avg_attempts,
            avg_time_ms=avg_time,
            by_difficulty=dict(by_difficulty),
            by_category=dict(by_category),
        )

        metrics_map[f"{model}_{strategy}"] = metrics

    return metrics_map


def print_summary(metrics_map: dict[str, ModelMetrics]) -> None:
    """Print a summary table of results."""
    print("=" * 120)
    print("EXPERIMENT RESULTS SUMMARY")
    print("=" * 120)
    print()

    # Header
    print(
        f"{'Model':<30} {'Strategy':<20} {'Total':<8} {'Syntax':<10} {'Semantic':<10} {'Fluent%':<10} {'AvgEdit':<10} {'AvgTime(ms)':<12}"
    )
    print("-" * 120)

    # Sort by model then strategy
    sorted_metrics = sorted(metrics_map.values(), key=lambda m: (m.model, m.strategy))

    for m in sorted_metrics:
        print(
            f"{m.model:<30} {m.strategy:<20} {m.total_tests:<8} "
            f"{m.syntax_accuracy:>5.1f}%   {m.semantic_accuracy:>5.1f}%   "
            f"{m.fluent_syntax_rate:>5.1f}%    "
            f"{m.avg_edit_distance:>6.1f}    {m.avg_time_ms:>8.0f}"
        )

    print("=" * 120)
    print()


def print_detailed_analysis(metrics: ModelMetrics) -> None:
    """Print detailed analysis for a specific model/strategy."""
    print(f"\n{'=' * 80}")
    print(f"DETAILED ANALYSIS: {metrics.model} - {metrics.strategy}")
    print(f"{'=' * 80}\n")

    print("Overall Statistics:")
    print(f"  Total test cases: {metrics.total_tests}")
    print(
        f"  Syntax correct: {metrics.syntax_correct} ({metrics.syntax_accuracy:.1f}%)"
    )
    print(
        f"  Semantically correct: {metrics.semantically_correct} ({metrics.semantic_accuracy:.1f}%)"
    )
    print(
        f"  Using fluent syntax: {metrics.uses_fluent_syntax} ({metrics.fluent_syntax_rate:.1f}%)"
    )
    print(f"  Avg edit distance: {metrics.avg_edit_distance:.1f}")
    print(f"  Avg attempts: {metrics.avg_attempts:.1f}")
    print(f"  Avg time: {metrics.avg_time_ms:.0f}ms")

    print("\nBy Difficulty:")
    for diff in ["easy", "medium", "hard"]:
        stats = metrics.by_difficulty.get(diff, {"total": 0, "correct": 0})
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"] * 100
            print(
                f"  {diff:6s}: {stats['correct']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)"
            )

    print("\nBy Category:")
    for cat, stats in sorted(metrics.by_category.items()):
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"] * 100
            print(
                f"  {cat:25s}: {stats['correct']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)"
            )


def compare_models(
    metrics_map: dict[str, ModelMetrics], strategy: str = "zero_shot"
) -> None:
    """Compare different models using the same strategy."""
    print(f"\n{'=' * 80}")
    print(f"MODEL COMPARISON (Strategy: {strategy})")
    print(f"{'=' * 80}\n")

    # Filter to specific strategy
    filtered = {k: v for k, v in metrics_map.items() if v.strategy == strategy}

    if not filtered:
        print(f"No results found for strategy: {strategy}")
        return

    # Sort by syntax accuracy
    sorted_models = sorted(
        filtered.values(), key=lambda m: m.syntax_accuracy, reverse=True
    )

    print(f"{'Rank':<6} {'Model':<35} {'Syntax':<12} {'Semantic':<12} {'Fluent%':<10}")
    print("-" * 80)

    for rank, m in enumerate(sorted_models, 1):
        print(
            f"{rank:<6} {m.model:<35} {m.syntax_accuracy:>6.1f}%     "
            f"{m.semantic_accuracy:>6.1f}%     {m.fluent_syntax_rate:>6.1f}%"
        )


def compare_strategies(metrics_map: dict[str, ModelMetrics], model: str) -> None:
    """Compare different strategies for the same model."""
    print(f"\n{'=' * 80}")
    print(f"STRATEGY COMPARISON (Model: {model})")
    print(f"{'=' * 80}\n")

    # Filter to specific model
    filtered = {k: v for k, v in metrics_map.items() if v.model == model}

    if not filtered:
        print(f"No results found for model: {model}")
        return

    # Sort by syntax accuracy
    sorted_strategies = sorted(
        filtered.values(), key=lambda m: m.syntax_accuracy, reverse=True
    )

    print(
        f"{'Rank':<6} {'Strategy':<25} {'Syntax':<12} {'Semantic':<12} {'AvgAttempts':<12}"
    )
    print("-" * 80)

    for rank, m in enumerate(sorted_strategies, 1):
        print(
            f"{rank:<6} {m.strategy:<25} {m.syntax_accuracy:>6.1f}%     "
            f"{m.semantic_accuracy:>6.1f}%     {m.avg_attempts:>8.1f}"
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m experiments.analyze <results_file.json>")
        sys.exit(1)

    results_file = sys.argv[1]
    data = load_results(results_file)

    # Build test case map
    from .test_cases import ALL_TEST_CASES

    tc_map = {
        tc.id: {"difficulty": tc.difficulty, "category": tc.category}
        for tc in ALL_TEST_CASES
    }

    # Analyze
    metrics = analyze_results(data, tc_map)

    # Print reports
    print_summary(metrics)

    # Detailed analysis for each model/strategy combo
    for m in metrics.values():
        print_detailed_analysis(m)

    # Comparisons
    compare_models(metrics, "zero_shot")
    compare_strategies(
        metrics,
        list(metrics.values())[0].model if metrics else "claude-sonnet-4-5-20250929",
    )
