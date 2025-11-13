#!/usr/bin/env python3
"""Verify that the fixed subquery test cases have valid syntax."""

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend
from prismql.exceptions import PrismQLSyntaxError
from experiments.test_cases import SUBQUERY_QUERIES, SEQUENTIAL_SUBQUERY_QUERIES

# Create minimal engine for syntax validation
backend = MemoryBackend([])
engine = PrismQLEngine(backend)

print("Verifying fixed subquery syntax...\n")

failed = []
for tc in SUBQUERY_QUERIES + SEQUENTIAL_SUBQUERY_QUERIES:
    try:
        # Execute with empty data - will validate syntax
        engine.execute(tc.ground_truth_query)
        print(f"✓ {tc.id}: {tc.ground_truth_query[:60]}...")
    except PrismQLSyntaxError as e:
        print(f"✗ {tc.id}: SYNTAX ERROR - {str(e)}")
        failed.append((tc.id, str(e)))
    except Exception:
        # Runtime errors are OK - we just want to validate syntax
        print(f"✓ {tc.id}: {tc.ground_truth_query[:60]}...")

print(f"\n{'='*80}")
if failed:
    print(f"FAILED: {len(failed)} queries have syntax errors:")
    for tc_id, error in failed:
        print(f"  - {tc_id}: {error}")
else:
    print(f"SUCCESS: All {len(SUBQUERY_QUERIES) + len(SEQUENTIAL_SUBQUERY_QUERIES)} subquery test cases are syntactically valid!")
