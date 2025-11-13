#!/usr/bin/env python3
"""Analyze model syntax errors to identify patterns."""

import json
import sys
from collections import Counter

def analyze_errors(result_file, model_filter=None):
    """Analyze syntax errors from experiment results."""
    with open(result_file) as f:
        data = json.load(f)

    # Find results for the specified model (or auto-detect if not specified)
    if model_filter:
        model_tests = [
            result for result in data["results"]
            if model_filter in result["model"] and result["prompt_strategy"] == "zero_shot"
        ]
        model_name = model_filter
    else:
        # Auto-detect: use first model in results
        if not data["results"]:
            print("No results found!")
            return
        model_name = data["results"][0]["model"]
        model_tests = [
            result for result in data["results"]
            if result["model"] == model_name and result["prompt_strategy"] == "zero_shot"
        ]

    if not model_tests:
        print(f"No results found for model: {model_name}")
        return

    print("=" * 80)
    print(f"{model_name.upper()} ERROR ANALYSIS")
    print("=" * 80)
    print()

    # Categorize errors
    syntax_errors = []
    semantic_errors = []
    both_correct = []

    for test in model_tests:
        if test["syntax_correct"] and test["semantically_correct"]:
            both_correct.append(test)
        elif not test["syntax_correct"]:
            syntax_errors.append(test)
        elif not test["semantically_correct"]:
            semantic_errors.append(test)

    print(f"✅ Both correct: {len(both_correct)}/49 ({len(both_correct)/49*100:.1f}%)")
    print(f"⚠️  Syntax errors: {len(syntax_errors)}/49 ({len(syntax_errors)/49*100:.1f}%)")
    print(f"❌ Semantic errors (but syntax OK): {len(semantic_errors)}/49 ({len(semantic_errors)/49*100:.1f}%)")
    print()

    # Analyze syntax errors by category
    print("=" * 80)
    print("SYNTAX ERRORS BY CATEGORY")
    print("=" * 80)
    print()

    # Need to load test cases to get categories
    from test_cases import ALL_TEST_CASES
    test_case_map = {tc.id: tc for tc in ALL_TEST_CASES}

    category_counts = Counter(
        test_case_map[test["test_case_id"]].category for test in syntax_errors
    )
    for category, count in category_counts.most_common():
        print(f"{category}: {count} errors")

    print()
    print("=" * 80)
    print("SYNTAX ERROR DETAILS")
    print("=" * 80)
    print()

    for i, test in enumerate(syntax_errors[:15], 1):  # Show first 15
        tc = test_case_map[test["test_case_id"]]
        print(f"{i}. {tc.id} ({tc.difficulty}/{tc.category})")
        print(f"   Description: {tc.description}")
        print(f"   Expected: {tc.ground_truth_query}")
        print(f"   Got:      {test['final_query']}")

        # Show parse error if available
        if test["syntax_errors"]:
            error_msg = test["syntax_errors"][0] if test["syntax_errors"] else ""
            # Truncate long error messages
            if len(error_msg) > 150:
                error_msg = error_msg[:150] + "..."
            print(f"   Error:    {error_msg}")

        # Check if semantically correct
        if test["semantically_correct"]:
            print(f"   ✅ Semantically CORRECT despite syntax error (fluent)")

        print()

    if len(syntax_errors) > 15:
        print(f"... and {len(syntax_errors) - 15} more syntax errors")
        print()

    # Analyze semantic errors
    if semantic_errors:
        print("=" * 80)
        print("SEMANTIC ERRORS (syntax correct but wrong result)")
        print("=" * 80)
        print()

        for i, test in enumerate(semantic_errors, 1):
            tc = test_case_map[test["test_case_id"]]
            print(f"{i}. {tc.id} - {tc.description}")
            print(f"   Expected: {tc.ground_truth_query}")
            print(f"   Got:      {test['final_query']}")
            if test["semantic_errors"]:
                print(f"   Issue:    {test['semantic_errors'][0][:150]}")
            print()

if __name__ == "__main__":
    result_file = sys.argv[1] if len(sys.argv) > 1 else "results/custom_experiment_20251113_102102.json"
    model_filter = sys.argv[2] if len(sys.argv) > 2 else None
    analyze_errors(result_file, model_filter)
