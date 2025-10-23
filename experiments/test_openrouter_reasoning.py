"""
Test script to verify OpenRouter reasoning is working.

Usage:
    OPENROUTER_API_KEY=... python experiments/test_openrouter_reasoning.py
"""

import os
import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from experiments.providers import OpenRouterProvider


def test_openrouter_reasoning():
    """Test that OpenRouter reasoning captures reasoning tokens."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Test with Gemini 2.5 Pro (paid model with reasoning)
    print("Testing Gemini 2.5 Pro with reasoning enabled...")
    print("=" * 80)

    provider = OpenRouterProvider(
        model="google/gemini-2.5-pro",
        api_key=api_key,
        enable_reasoning=True,
    )

    system_prompt = """You are an expert at writing PrismQL queries.
Generate a PrismQL query for the following request.
Respond with ONLY the query, starting with SELECT."""

    user_message = """Generate a PrismQL query for:
"Find messages from alice that contain the word 'problem' within 5 messages"

Available operators: from(), contains()
"""

    print("\nCalling API with reasoning enabled...")
    # OpenRouter reasoning models may need more tokens
    content, reasoning = provider.generate(system_prompt, user_message, max_tokens=3000)

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\nHas reasoning: {reasoning is not None}")

    if reasoning:
        print(f"\nReasoning length: {len(reasoning)} characters")
        print("\n--- REASONING (first 500 chars) ---")
        print(reasoning[:500])
        print("...\n")
    else:
        print("\nWARNING: No reasoning blocks returned!")

    print("\n--- CONTENT ---")
    print(content)
    print()


if __name__ == "__main__":
    test_openrouter_reasoning()
