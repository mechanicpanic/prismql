"""
Display experiment results (all models, with or without reasoning).

Usage:
    python experiments/show_results.py <results_file.json>
    python experiments/show_results.py <results_file.json> --test-case basic_001
    python experiments/show_results.py <results_file.json> --verbose
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.test_cases import ALL_TEST_CASES


def show_results(  # noqa: C901
    results_file: str, test_case_filter: str | None = None, verbose: bool = False
) -> None:
    """Display experiment results."""
    results_path = Path(results_file)

    if not results_path.exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)

    with open(results_path) as f:
        data = json.load(f)

    results = data.get("results", [])

    # Build test case lookup
    test_case_map = {tc.id: tc for tc in ALL_TEST_CASES}

    print("=" * 100)
    print("EXPERIMENT RESULTS")
    print(f"File: {results_file}")
    print(f"Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"Total Results: {len(results)}")
    print("=" * 100)
    print()

    # Group by model and strategy
    by_model_strategy = {}
    for result in results:
        key = (result["model"], result["prompt_strategy"])
        if key not in by_model_strategy:
            by_model_strategy[key] = []
        by_model_strategy[key].append(result)

    # Print summary by model/strategy
    print("SUMMARY BY MODEL & STRATEGY")
    print("-" * 100)
    print(
        f"{'Model':<40} {'Strategy':<20} {'Total':>6} {'Correct':>8} {'Accuracy':>10}"
    )
    print("-" * 100)

    for (model, strategy), model_results in sorted(by_model_strategy.items()):
        correct = sum(1 for r in model_results if r.get("semantically_correct"))
        total = len(model_results)
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"{model:<40} {strategy:<20} {total:>6} {correct:>8} {accuracy:>9.1f}%")

    print("-" * 100)
    print()

    # Detailed results
    if verbose or test_case_filter:
        print()
        print("=" * 100)
        print("DETAILED RESULTS")
        print("=" * 100)

        for result in results:
            test_case_id = result["test_case_id"]

            # Filter by test case if specified
            if test_case_filter and test_case_id != test_case_filter:
                continue

            print()
            print("-" * 100)
            print(f"Test Case: {test_case_id}")
            print(f"Model: {result['model']}")
            print(f"Strategy: {result['prompt_strategy']}")
            print("-" * 100)

            # Show test case details
            if test_case_id in test_case_map:
                tc = test_case_map[test_case_id]
                print()
                print(f"Description: {tc.description}")
                print()
                print(f"Ground Truth: {tc.ground_truth_query}")
                print()

            # Show generated query
            final_query = result.get("final_query", "")
            print(f"Generated:    {final_query}")
            print()

            # Show results
            syntax_correct = result.get("syntax_correct", False)
            semantic_correct = result.get("semantically_correct")
            edit_distance = result.get("edit_distance_from_ground_truth", 999)

            print(f"✓ Syntax Correct: {syntax_correct}")
            print(
                f"{'✓' if semantic_correct else '✗'} Semantically Correct: {semantic_correct}"
            )
            print(f"  Edit Distance: {edit_distance}")

            # Show errors if any
            errors = result.get("syntax_errors", []) + result.get("semantic_errors", [])
            if errors:
                print()
                print("Errors:")
                for err in errors:
                    print(f"  - {err}")

            # Show warnings if any
            warnings = result.get("warnings", [])
            if warnings:
                print()
                print("Warnings:")
                for warn in warnings:
                    print(f"  - {warn}")

            # Show attempts if verbose
            if verbose:
                attempts = result.get("attempts", [])
                if len(attempts) > 1:
                    print()
                    print(f"Attempts: {len(attempts)}")
                    for i, attempt in enumerate(attempts, 1):
                        print(f"  Attempt {i}: {attempt.get('query', 'N/A')}")

            # Show CoT status
            has_cot = result.get("has_chain_of_thought", False)
            if has_cot:
                print()
                print("💭 Has Chain-of-Thought (use show_cot.py to view)")

            print()

    # Error summary
    print()
    print("=" * 100)
    print("ERROR SUMMARY")
    print("=" * 100)

    failed_results = [r for r in results if not r.get("semantically_correct")]
    if failed_results:
        print(f"\n{len(failed_results)} failed test case(s):\n")
        for result in failed_results:
            tc_id = result["test_case_id"]
            model = result["model"]
            strategy = result["prompt_strategy"]
            query = result.get("final_query", "N/A")
            print(f"  {tc_id} | {model} | {strategy}")
            print(f"    Generated: {query}")
            if result.get("syntax_errors"):
                print(f"    Errors: {', '.join(result['syntax_errors'][:2])}")
            print()
    else:
        print("\n✓ All test cases passed!\n")

    print("=" * 100)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: python experiments/show_results.py <results_file.json> [--test-case <id>] [--verbose]"
        )
        sys.exit(1)

    results_file = sys.argv[1]
    test_case_filter = None
    verbose = False

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--test-case" and i + 1 < len(sys.argv):
            test_case_filter = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--verbose":
            verbose = True
            i += 1
        else:
            print(f"Unknown argument: {sys.argv[i]}")
            sys.exit(1)

    show_results(results_file, test_case_filter, verbose)


if __name__ == "__main__":
    main()
