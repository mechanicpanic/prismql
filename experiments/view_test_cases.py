#!/usr/bin/env python3
"""
Interactive test case viewer for manual review.

Navigate through test cases one by one and review them interactively.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.test_cases import (
    AGGREGATION_QUERIES,
    AMBIGUOUS_QUERIES,
    BASIC_QUERIES,
    COMPLEX_QUERIES,
    EDGE_CASE_QUERIES,
    NEGATIVE_PATTERN_QUERIES,
    PATTERN_VARIABLE_QUERIES,
    QUANTIFIER_QUERIES,
    SEQUENTIAL_QUERIES,
    SEQUENTIAL_SUBQUERY_QUERIES,
    SUBQUERY_QUERIES,
    WINDOW_QUERIES,
)


def collect_all_test_cases():
    """Collect all test cases into a single list with suite names."""
    all_test_suites = [
        ("Basic Queries", BASIC_QUERIES),
        ("Window Queries", WINDOW_QUERIES),
        ("Sequential Queries", SEQUENTIAL_QUERIES),
        ("Complex Queries", COMPLEX_QUERIES),
        ("Pattern Variables", PATTERN_VARIABLE_QUERIES),
        ("Quantifiers", QUANTIFIER_QUERIES),
        ("Negative Patterns", NEGATIVE_PATTERN_QUERIES),
        ("Aggregations", AGGREGATION_QUERIES),
        ("Subqueries", SUBQUERY_QUERIES),
        ("Sequential Subqueries", SEQUENTIAL_SUBQUERY_QUERIES),
        ("Edge Cases", EDGE_CASE_QUERIES),
        ("Ambiguous Cases", AMBIGUOUS_QUERIES),
    ]

    all_cases = []
    for suite_name, test_cases in all_test_suites:
        for test_case in test_cases:
            all_cases.append((suite_name, test_case))

    return all_cases


def display_test_case(suite_name, test_case, index, total):
    """Display a single test case with all details."""
    print("\n" + "=" * 80)
    print(f"TEST CASE {index + 1}/{total}")
    print("=" * 80)
    print(f"Suite: {suite_name}")
    print(f"ID: {test_case.id}")
    print(f"Category: {test_case.category}")
    print(f"Difficulty: {test_case.difficulty.upper()}")
    print()
    print("Description:")
    print(f"  {test_case.description}")
    print()
    print("Ground Truth Query:")
    print(f"  {test_case.ground_truth_query}")
    print()

    if test_case.required_dictionaries:
        print("Required Dictionaries:")
        for dict_name, words in test_case.required_dictionaries.items():
            print(f"  {dict_name}: {words}")
        print()

    if test_case.notes:
        print("Notes:")
        print(f"  {test_case.notes}")
        print()


def interactive_review():  # noqa: C901
    """Run interactive review session."""
    all_cases = collect_all_test_cases()
    total = len(all_cases)
    current_index = 0
    flagged = set()  # Track flagged test cases

    print("=" * 80)
    print("INTERACTIVE TEST CASE VIEWER")
    print("=" * 80)
    print(f"Total test cases: {total}")
    print()
    print("Commands:")
    print("  n/next     - Next test case")
    print("  p/prev     - Previous test case")
    print("  f/flag     - Flag this test case as needing review")
    print("  u/unflag   - Remove flag from this test case")
    print("  g/goto N   - Go to test case number N")
    print("  l/list     - List all flagged test cases")
    print("  q/quit     - Quit")
    print("  ?/help     - Show this help")
    print()

    while True:
        suite_name, test_case = all_cases[current_index]
        is_flagged = test_case.id in flagged
        flag_marker = " [FLAGGED]" if is_flagged else ""

        display_test_case(suite_name, test_case, current_index, total)

        print("=" * 80)
        print(f"[{current_index + 1}/{total}]{flag_marker} {test_case.id}")

        try:
            command = input("Command (? for help): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nQuitting...")
            break

        if command in ["n", "next", ""]:
            if current_index < total - 1:
                current_index += 1
            else:
                print("Already at last test case")

        elif command in ["p", "prev"]:
            if current_index > 0:
                current_index -= 1
            else:
                print("Already at first test case")

        elif command in ["f", "flag"]:
            flagged.add(test_case.id)
            print(f"✓ Flagged {test_case.id}")

        elif command in ["u", "unflag"]:
            if test_case.id in flagged:
                flagged.remove(test_case.id)
                print(f"✓ Removed flag from {test_case.id}")
            else:
                print(f"{test_case.id} was not flagged")

        elif command.startswith("g") or command.startswith("goto"):
            try:
                parts = command.split()
                if len(parts) >= 2:
                    target = int(parts[1]) - 1
                    if 0 <= target < total:
                        current_index = target
                    else:
                        print(f"Invalid test case number. Must be 1-{total}")
                else:
                    print("Usage: g/goto N")
            except ValueError:
                print("Invalid number")

        elif command in ["l", "list"]:
            if flagged:
                print("\nFlagged test cases:")
                for _, tc in all_cases:
                    if tc.id in flagged:
                        print(f"  - {tc.id}: {tc.description}")
                print(f"\nTotal flagged: {len(flagged)}")
            else:
                print("No test cases flagged")
            input("\nPress Enter to continue...")

        elif command in ["q", "quit", "exit"]:
            break

        elif command in ["?", "help", "h"]:
            print("\nCommands:")
            print("  n/next     - Next test case")
            print("  p/prev     - Previous test case")
            print("  f/flag     - Flag this test case as needing review")
            print("  u/unflag   - Remove flag from this test case")
            print("  g/goto N   - Go to test case number N")
            print("  l/list     - List all flagged test cases")
            print("  q/quit     - Quit")
            print("  ?/help     - Show this help")
            input("\nPress Enter to continue...")

        else:
            print(f"Unknown command: '{command}'. Type ? for help")

    # Show summary
    if flagged:
        print("\n" + "=" * 80)
        print("FLAGGED TEST CASES")
        print("=" * 80)
        for _, tc in all_cases:
            if tc.id in flagged:
                print(f"  {tc.id} ({tc.difficulty}): {tc.description}")
        print(f"\nTotal flagged: {len(flagged)}")
    else:
        print("\nNo test cases were flagged.")


if __name__ == "__main__":
    try:
        interactive_review()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
