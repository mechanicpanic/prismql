#!/usr/bin/env python3
"""
Interactive test case review tool.

Helps validate that ground truth queries in test_cases.py are correct.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError, PrismQLSyntaxError

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
    get_all_required_dictionaries,
)


def validate_test_case(test_case, engine):
    """Validate a single test case.

    Returns:
        dict with validation results
    """
    result = {
        "id": test_case.id,
        "description": test_case.description,
        "query": test_case.ground_truth_query,
        "category": test_case.category,
        "difficulty": test_case.difficulty,
        "syntax_valid": False,
        "execution_result": None,
        "error": None,
        "warnings": [],
    }

    # 1. Check syntax
    try:
        query_result = engine.execute(test_case.ground_truth_query)
        result["syntax_valid"] = True
        result["execution_result"] = f"{len(query_result)} result groups"
    except PrismQLSyntaxError as e:
        result["error"] = f"SYNTAX ERROR: {e}"
    except PrismQLRuntimeError as e:
        result["error"] = f"RUNTIME ERROR: {e}"
    except Exception as e:
        result["error"] = f"UNEXPECTED ERROR: {type(e).__name__}: {e}"

    # 2. Check for known issues
    query = test_case.ground_truth_query

    # Known grammar limitations
    if "FOLLOWED_BY" in query and "{" in query:
        if query.index("{") < query.index("FOLLOWED_BY"):
            # Quantifier before FOLLOWED_BY is ok
            pass
        else:
            # Quantifier after FOLLOWED_BY is not supported
            result["warnings"].append(
                "⚠️  Grammar doesn't support quantifiers on FOLLOWED_BY"
            )

    # Operator compatibility issues
    if ("FOLLOWED_BY" in query or "PRECEDED_BY" in query) and (
        " AND " in query or " OR " in query
    ):
        # Check if AND/OR is at same level as sequential operator
        result["warnings"].append(
            "⚠️  Sequential operators can't be combined with AND/OR at same level"
        )

    # Deprecated syntax
    if "byuser(" in query:
        result["warnings"].append("💡 Uses deprecated byuser() - should use from()")
    if "haswordofdict(" in query:
        result["warnings"].append(
            "💡 Uses deprecated haswordofdict() - should use contains()"
        )

    return result


def print_test_case_review(result, verbose=False):
    """Pretty print a test case review."""
    status = (
        "✅"
        if result["syntax_valid"] and not result["warnings"]
        else "⚠️"
        if result["syntax_valid"]
        else "❌"
    )

    print(f"\n{status} [{result['id']}] {result['difficulty'].upper()}")
    print(f"   Category: {result['category']}")
    print(f"   Description: {result['description']}")
    print(f"   Query: {result['query']}")

    if result["syntax_valid"]:
        print(f"   ✓ Syntax valid - {result['execution_result']}")
    else:
        print(f"   ✗ {result['error']}")

    for warning in result["warnings"]:
        print(f"   {warning}")

    if verbose and result.get("notes"):
        print(f"   Notes: {result['notes']}")


def review_all_test_cases(verbose=False, filter_category=None, filter_difficulty=None):  # noqa: C901
    """Review all test cases and generate report."""

    # Setup engine with sample data
    sample_messages = [
        {
            "id": 1,
            "user": "alice",
            "text": "hello everyone",
            "timestamp": "2024-01-01T10:00:00Z",
        },
        {
            "id": 2,
            "user": "bob",
            "text": "hi alice",
            "timestamp": "2024-01-01T10:01:00Z",
        },
        {
            "id": 3,
            "user": "alice",
            "text": "how are you?",
            "timestamp": "2024-01-01T10:02:00Z",
        },
        {
            "id": 4,
            "user": "support",
            "text": "I can help with that issue",
            "timestamp": "2024-01-01T10:03:00Z",
        },
        {
            "id": 5,
            "user": "charlie",
            "text": "thanks for the solution",
            "timestamp": "2024-01-01T10:04:00Z",
        },
    ]

    backend = MemoryBackend(documents=sample_messages)
    all_dicts = get_all_required_dictionaries()
    engine = PrismQLEngine(search_backend=backend, user_dictionaries=all_dicts)

    # Collect all test cases
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

    # Statistics
    total = 0
    syntax_valid = 0
    has_warnings = 0
    has_errors = 0

    print("=" * 80)
    print("TEST CASE VALIDATION REPORT")
    print("=" * 80)

    for suite_name, test_cases in all_test_suites:
        suite_results = []

        for test_case in test_cases:
            # Apply filters
            if filter_category and test_case.category != filter_category:
                continue
            if filter_difficulty and test_case.difficulty != filter_difficulty:
                continue

            result = validate_test_case(test_case, engine)
            suite_results.append(result)

            total += 1
            if result["syntax_valid"]:
                syntax_valid += 1
            if result["warnings"]:
                has_warnings += 1
            if result["error"]:
                has_errors += 1

        if suite_results:
            print(f"\n{'=' * 80}")
            print(f"{suite_name.upper()}")
            print(f"{'=' * 80}")

            for result in suite_results:
                print_test_case_review(result, verbose=verbose)

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total test cases: {total}")
    print(f"Syntax valid: {syntax_valid}/{total} ({100*syntax_valid/total:.1f}%)")
    print(f"With warnings: {has_warnings}/{total} ({100*has_warnings/total:.1f}%)")
    print(f"With errors: {has_errors}/{total} ({100*has_errors/total:.1f}%)")

    if has_errors > 0:
        print(f"\n⚠️  {has_errors} test cases have syntax or runtime errors!")
        print("These need to be fixed before using as ground truth.")

    if has_warnings > 0:
        print(f"\n💡 {has_warnings} test cases have warnings")
        print("Review these to ensure they match current PrismQL capabilities.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Review PrismQL test cases")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument(
        "--difficulty",
        "-d",
        choices=["easy", "medium", "hard"],
        help="Filter by difficulty",
    )

    args = parser.parse_args()

    review_all_test_cases(
        verbose=args.verbose,
        filter_category=args.category,
        filter_difficulty=args.difficulty,
    )
