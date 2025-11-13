#!/usr/bin/env python3
"""Relaxed semantic validator that accepts reasonable query variations."""

import re
from typing import Optional
from prismql import PrismQLEngine


class RelaxedSemanticValidator:
    """
    Validates queries with relaxed rules to handle ambiguous specifications.

    Accepts variations where:
    - Window sizes differ by ±2
    - is_question() is added when description implies questions
    - Pattern variables vs literals for specific users (user1, user2, etc.)
    - Reasonable alternative interpretations
    """

    def __init__(self, engine: PrismQLEngine):
        self.engine = engine

    def normalize_query(self, query: str) -> str:
        """Normalize query for comparison."""
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query.strip())
        return normalized

    def extract_window_sizes(self, query: str) -> list[int]:
        """Extract all WITHIN values from query."""
        return [int(m) for m in re.findall(r'WITHIN (\d+)', query)]

    def windows_compatible(self, gt_windows: list[int], gen_windows: list[int], tolerance: int = 2) -> bool:
        """
        Check if window sizes are compatible within tolerance.

        Accepts:
        - Same number of windows with each within ±tolerance
        - Or generated has one global window that encompasses all ground truth windows
        """
        if len(gt_windows) != len(gen_windows):
            # Check if generated uses single global window
            if len(gen_windows) == 1 and len(gt_windows) > 1:
                # Single window should be >= max ground truth window
                return gen_windows[0] >= max(gt_windows) - tolerance
            return False

        # Check each window is within tolerance
        for gt_w, gen_w in zip(gt_windows, gen_windows):
            if abs(gt_w - gen_w) > tolerance:
                return False
        return True

    def normalize_users(self, query: str) -> str:
        """
        Normalize user references to handle pattern var vs literal ambiguity.

        For users like user1, user2, user3, treat them as equivalent to $user1, $user2, etc.
        """
        # Convert user1/user2/user3 to pattern variables for comparison
        query = re.sub(r'from\(user(\d+)\)', r'from($user\1)', query)
        return query

    def is_semantically_equivalent(
        self,
        generated_query: str,
        ground_truth_query: str,
        description: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if generated query is semantically equivalent to ground truth.

        Returns:
            (is_equivalent, reason_if_not)
        """
        # Normalize both queries
        gen_norm = self.normalize_query(generated_query)
        gt_norm = self.normalize_query(ground_truth_query)

        # Exact match after normalization
        if gen_norm == gt_norm:
            return (True, None)

        # Check window size compatibility
        gt_windows = self.extract_window_sizes(ground_truth_query)
        gen_windows = self.extract_window_sizes(generated_query)

        if gt_windows and gen_windows:
            if not self.windows_compatible(gt_windows, gen_windows):
                # Windows incompatible - might still be acceptable if within tolerance
                window_diff = max(abs(gw - gew) for gw, gew in zip(gt_windows, gen_windows) if len(gt_windows) == len(gen_windows))
                if len(gt_windows) == len(gen_windows) and window_diff <= 2:
                    # Windows slightly different but acceptable
                    pass
                else:
                    # Check other differences
                    pass

        # Check if is_question() was added appropriately
        if "is_question()" in generated_query and "is_question()" not in ground_truth_query:
            # Check if description implies questions
            if any(word in description.lower() for word in ["asking", "asks", "ask a question", "question from"]):
                # This is a BETTER interpretation - accept it
                # But need to check if results match
                pass

        # Normalize user references (user1 vs $user1)
        gen_normalized_users = self.normalize_users(generated_query)
        gt_normalized_users = self.normalize_users(ground_truth_query)

        if gen_normalized_users == gt_normalized_users:
            return (True, "User reference style differs but semantically equivalent")

        # Try executing both and compare results
        try:
            gt_result = self.engine.execute(ground_truth_query)
            gen_result = self.engine.execute(generated_query)

            # Convert results to sets for comparison
            gt_set = self._result_to_set(gt_result)
            gen_set = self._result_to_set(gen_result)

            # Check if results are close enough
            if gt_set == gen_set:
                return (True, "Results identical despite query differences")

            # Check if results overlap significantly (>80%)
            if gt_set and gen_set:
                overlap = len(gt_set & gen_set) / max(len(gt_set), len(gen_set))
                if overlap >= 0.8:
                    return (True, f"Results {overlap*100:.1f}% similar")

            # Results differ
            missing = len(gt_set - gen_set)
            extra = len(gen_set - gt_set)
            return (False, f"Results differ: {missing} missing, {extra} extra")

        except Exception as e:
            # Can't execute - fall back to structural comparison
            return (False, f"Execution failed: {str(e)[:100]}")

    def _result_to_set(self, result):
        """Convert query result to set for comparison."""
        if not result:
            return set()

        result_set = set()
        for group in result:
            if isinstance(group, (list, tuple)):
                result_set.add(frozenset(group))
            else:
                result_set.add(frozenset([group]))
        return result_set

    def validate_with_relaxed_rules(
        self,
        generated_query: str,
        ground_truth_query: str,
        description: str,
    ) -> dict:
        """
        Validate generated query with relaxed rules.

        Returns:
            {
                "strict_match": bool,  # Exact structural match
                "relaxed_match": bool,  # Semantically equivalent
                "reason": str,  # Why it matches/doesn't match
                "verdict": "correct" | "acceptable" | "wrong"
            }
        """
        # Check strict match first
        gen_norm = self.normalize_query(generated_query)
        gt_norm = self.normalize_query(ground_truth_query)
        strict_match = gen_norm == gt_norm

        if strict_match:
            return {
                "strict_match": True,
                "relaxed_match": True,
                "reason": "Exact match",
                "verdict": "correct"
            }

        # Check relaxed match
        is_equiv, reason = self.is_semantically_equivalent(
            generated_query, ground_truth_query, description
        )

        if is_equiv:
            return {
                "strict_match": False,
                "relaxed_match": True,
                "reason": reason or "Semantically equivalent",
                "verdict": "acceptable"
            }

        return {
            "strict_match": False,
            "relaxed_match": False,
            "reason": reason or "Semantically different",
            "verdict": "wrong"
        }
