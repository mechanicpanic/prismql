"""
Display chain-of-thought reasoning from experiment results.

Usage:
    python experiments/show_cot.py <results_file.json>
    python experiments/show_cot.py <results_file.json> --test-case basic_001
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.test_cases import ALL_TEST_CASES


def show_chain_of_thought(  # noqa: C901
    results_file: str, test_case_filter: str | None = None
) -> None:
    """Display chain-of-thought from experiment results."""
    results_path = Path(results_file)

    if not results_path.exists():
        print(f"Error: File not found: {results_file}")
        sys.exit(1)

    with open(results_path) as f:
        data = json.load(f)

    results = data.get("results", [])

    # Build test case lookup
    test_case_map = {tc.id: tc for tc in ALL_TEST_CASES}

    print("=" * 80)
    print("CHAIN-OF-THOUGHT ANALYSIS")
    print(f"Results file: {results_file}")
    print("=" * 80)
    print()

    cot_count = 0
    total_count = 0

    for result in results:
        total_count += 1

        # Filter by test case if specified
        if test_case_filter and result["test_case_id"] != test_case_filter:
            continue

        # Check if this result has CoT
        if not result.get("has_chain_of_thought", False):
            continue

        cot_count += 1

        print(f"\n{'=' * 80}")
        print(f"Test Case: {result['test_case_id']}")
        print(f"Model: {result['model']}")
        print(f"Strategy: {result['prompt_strategy']}")
        print(f"{'=' * 80}\n")

        # Show test case details
        test_case_id = result["test_case_id"]
        if test_case_id in test_case_map:
            tc = test_case_map[test_case_id]
            print("--- Test Description ---")
            print(f"{tc.description}")
            print()
            print("--- Ground Truth Query ---")
            print(f"{tc.ground_truth_query}")
            print()

        # Show all attempts with CoT
        for i, attempt in enumerate(result.get("attempts", []), 1):
            cot = attempt.get("chain_of_thought")
            if cot:
                print(f"--- Attempt {i} Chain-of-Thought ---")
                print(cot)
                print()

                print(f"--- Attempt {i} Generated Query ---")
                print(attempt["query"])
                print()

        # Show final CoT if different from last attempt
        final_cot = result.get("final_chain_of_thought")
        if final_cot:
            print("--- Final Chain-of-Thought ---")
            print(final_cot)
            print()

        print("--- Results ---")
        print(f"Syntax Correct: {result['syntax_correct']}")
        print(f"Semantically Correct: {result['semantically_correct']}")
        print(
            f"Edit Distance from Ground Truth: {result['edit_distance_from_ground_truth']}"
        )

        # Show final query vs ground truth comparison
        final_query = result.get("final_query", "")
        if test_case_id in test_case_map:
            gt_query = test_case_map[test_case_id].ground_truth_query
            if final_query and final_query.strip().lower() == gt_query.strip().lower():
                print("Match: ✓ Generated query matches ground truth exactly")
            elif final_query:
                print("Match: ✗ Generated query differs from ground truth")
                print(f"  Expected: {gt_query}")
                print(f"  Got:      {final_query}")
        print()

    print("=" * 80)
    print(f"Summary: {cot_count}/{total_count} results have chain-of-thought")
    print("=" * 80)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(
            "Usage: python experiments/show_cot.py <results_file.json> [--test-case <id>]"
        )
        sys.exit(1)

    results_file = sys.argv[1]
    test_case_filter = None

    # Parse optional --test-case filter
    if len(sys.argv) >= 4 and sys.argv[2] == "--test-case":
        test_case_filter = sys.argv[3]

    show_chain_of_thought(results_file, test_case_filter)


if __name__ == "__main__":
    main()
