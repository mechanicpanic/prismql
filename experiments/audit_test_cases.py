#!/usr/bin/env python3
"""Audit test cases for ambiguous specifications and validation issues."""

from test_cases import ALL_TEST_CASES
import re

def audit_test_cases():
    """Audit test cases for issues that cause unfair scoring."""

    issues = []

    for tc in ALL_TEST_CASES:
        case_issues = []

        # Check 1: Description mentions windows/sequence but doesn't specify window size
        has_window_keywords = any(kw in tc.description.lower() for kw in [
            "followed by", "then", "after", "before", "preceded by", "within", "in sequence",
            "window", "windows", "appear", "together", "co-occur"
        ])

        # Also check if ground truth uses INWIN or WITHIN
        uses_window = "INWIN" in tc.ground_truth_query or "WITHIN" in tc.ground_truth_query

        if has_window_keywords or uses_window:
            # Check if window size is specified in description
            window_match = re.search(r'within (\d+)', tc.description.lower())
            inwin_match = re.search(r'inwin (\d+)', tc.description.lower())

            if not window_match and not inwin_match:
                # Extract window size from ground truth
                gt_windows = re.findall(r'(?:WITHIN|INWIN) (\d+)', tc.ground_truth_query)
                if gt_windows:
                    case_issues.append({
                        "type": "ambiguous_window",
                        "description": f"Description doesn't specify window size, but ground truth uses {set(gt_windows)}",
                        "severity": "high"
                    })

        # Check 2: Description says "asking" but ground truth doesn't enforce is_question()
        if "asking" in tc.description.lower() or "question" in tc.description.lower():
            # Check if ground truth uses is_question()
            if "is_question()" not in tc.ground_truth_query:
                # But description implies questions
                if any(word in tc.description.lower() for word in ["asking", "asks", "ask a question"]):
                    case_issues.append({
                        "type": "missing_is_question",
                        "description": "Description implies questions but ground truth doesn't use is_question()",
                        "severity": "medium"
                    })

        # Check 3: Specific user vs pattern variable ambiguity
        has_specific_user_desc = any(user in tc.description.lower() for user in [
            "alice", "bob", "charlie", "support", "customer", "manager", "user1", "user2"
        ])

        if has_specific_user_desc:
            # Check if ground truth uses pattern variable when description says specific user
            if "someone" in tc.description.lower() or "any user" in tc.description.lower() or "the same user" in tc.description.lower():
                # This is okay - pattern variable is correct
                pass
            else:
                # Description says specific user - check ground truth
                for user in ["alice", "bob", "charlie", "support", "customer", "manager", "user1", "user2", "user3"]:
                    if user in tc.description.lower() and f"from(${user})" in tc.ground_truth_query:
                        case_issues.append({
                            "type": "pattern_var_for_literal",
                            "description": f"Description says '{user}' (literal) but ground truth uses ${user} (pattern var)",
                            "severity": "high"
                        })

        # Check 4: Vague quantifiers
        if any(word in tc.description.lower() for word in ["twice", "three times", "multiple"]):
            if "twice" in tc.description.lower() and "{2}" not in tc.ground_truth_query and not tc.ground_truth_query.count("from(") >= 2:
                case_issues.append({
                    "type": "quantifier_ambiguous",
                    "description": "Description says 'twice' but implementation unclear",
                    "severity": "low"
                })

        # Check 5: Window vs sequence confusion
        if "together" in tc.description.lower() or "appear" in tc.description.lower():
            if "FOLLOWED_BY" in tc.ground_truth_query:
                # Description suggests unordered but ground truth uses sequence
                case_issues.append({
                    "type": "inwin_vs_followedby",
                    "description": "Description suggests unordered ('together'/'appear') but ground truth uses FOLLOWED_BY",
                    "severity": "medium"
                })

        if case_issues:
            issues.append({
                "test_case": tc,
                "issues": case_issues
            })

    return issues


def print_audit_report(issues):
    """Print audit report."""
    print("=" * 80)
    print("TEST CASE AUDIT REPORT")
    print("=" * 80)
    print()

    # Count by severity
    high_severity = sum(1 for item in issues for issue in item["issues"] if issue["severity"] == "high")
    medium_severity = sum(1 for item in issues for issue in item["issues"] if issue["severity"] == "medium")
    low_severity = sum(1 for item in issues for issue in item["issues"] if issue["severity"] == "low")

    print(f"Total test cases with issues: {len(issues)}/49")
    print(f"  High severity: {high_severity}")
    print(f"  Medium severity: {medium_severity}")
    print(f"  Low severity: {low_severity}")
    print()

    # Group by issue type
    by_type = {}
    for item in issues:
        for issue in item["issues"]:
            issue_type = issue["type"]
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append((item["test_case"], issue))

    print("=" * 80)
    print("ISSUES BY TYPE")
    print("=" * 80)
    print()

    for issue_type, cases in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n### {issue_type.upper().replace('_', ' ')} ({len(cases)} cases)")
        print("-" * 80)

        for tc, issue in cases:
            print(f"\n{tc.id} ({tc.difficulty}/{tc.category})")
            print(f"  Description: {tc.description}")
            print(f"  Ground truth: {tc.ground_truth_query}")
            print(f"  Issue: {issue['description']}")
            print(f"  Severity: {issue['severity']}")


if __name__ == "__main__":
    issues = audit_test_cases()
    print_audit_report(issues)

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("1. AMBIGUOUS WINDOW: Add explicit window sizes to descriptions")
    print("2. MISSING IS_QUESTION: Either add is_question() to ground truth or remove 'asking' from description")
    print("3. PATTERN VAR FOR LITERAL: Decide if specific users should use literals or pattern vars")
    print("4. INWIN VS FOLLOWEDBY: Clarify whether order matters in description")
    print()
    print("For rescoring, we should accept variations where:")
    print("- Window sizes are reasonable (±2 from ground truth)")
    print("- is_question() is added when description implies questions")
    print("- Literals and pattern variables are semantically equivalent")
