#!/usr/bin/env python3
"""Test Rust backend integration with PrismQL."""

import time
from prismql.engine import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Create sample dataset
messages = [
    {"id": 0, "text": "Hello world", "user": "alice"},
    {"id": 1, "text": "Hi alice", "user": "bob"},
    {"id": 2, "text": "How are you?", "user": "alice"},
    {"id": 3, "text": "I'm good thanks", "user": "bob"},
    {"id": 4, "text": "What about you?", "user": "bob"},
    {"id": 5, "text": "Great!", "user": "alice"},
]

# Add more messages for performance testing
for i in range(6, 1000):
    messages.append({
        "id": i,
        "text": f"Test message {i}",
        "user": "charlie" if i % 2 == 0 else "dave"
    })

print("Testing Rust backend integration with PrismQL")
print("=" * 60)

# Create backend and engine
backend = MemoryBackend(messages)
engine = PrismQLEngine(backend)

# Test 1: Simple INWIN query
print("\nTest 1: Simple INWIN query")
query = "SELECT from(alice), from(bob) INWIN 3"
print(f"Query: {query}")

start = time.time()
result = engine.execute(query)
elapsed = time.time() - start

print(f"Results: {result}")
print(f"Count: {len(result)}")
print(f"Time: {elapsed*1000:.2f}ms")

# Test 2: More complex query with 3 groups
print("\nTest 2: Three-way INWIN query")
query = "SELECT from(alice), from(bob), from(charlie) INWIN 10"
print(f"Query: {query}")

start = time.time()
result = engine.execute(query)
elapsed = time.time() - start

print(f"Count: {len(result)}")
print(f"Time: {elapsed*1000:.2f}ms")

# Test 3: Larger window
print("\nTest 3: Larger window (should find more results)")
query = "SELECT from(alice), from(bob) INWIN 100"
print(f"Query: {query}")

start = time.time()
result = engine.execute(query)
elapsed = time.time() - start

print(f"Count: {len(result)}")
print(f"Time: {elapsed*1000:.2f}ms")

# Test 4: Check if Rust backend is actually being used
print("\nTest 4: Verifying Rust backend is loaded")
try:
    from prismql_rust import merge_histogram_pruned
    print("✓ Rust backend available!")

    # Direct test
    groups = [[0, 2, 5], [1, 3, 4]]
    result = merge_histogram_pruned(groups, 3)
    print(f"Direct Rust call result: {result}")
except ImportError:
    print("✗ Rust backend not available - using Python fallback")

print("\n" + "=" * 60)
print("All tests completed!")
