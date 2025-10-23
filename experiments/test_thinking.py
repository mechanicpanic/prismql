"""
Test script to verify Anthropic extended thinking is working.

Usage:
    ANTHROPIC_API_KEY=sk-... python experiments/test_thinking.py
"""

import os
import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from experiments.providers import AnthropicProvider


def test_extended_thinking():
    """Test that extended thinking captures reasoning."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Test with extended thinking enabled
    print("Testing Opus 4.1 with extended thinking enabled...")
    print("=" * 80)

    provider = AnthropicProvider(
        model="claude-opus-4-1-20250805", api_key=api_key, extended_thinking=True
    )

    system_prompt = """You are an expert at writing PrismQL queries.
Generate a PrismQL query for the following request.
Respond with ONLY the query, starting with SELECT."""

    user_message = """Generate a PrismQL query for:
"Find messages from alice that contain the word 'problem' within 5 messages"

Available operators: from(), contains()
"""

    print("\nCalling API with extended thinking...")
    # Extended thinking requires budget_tokens >= 1024, and max_tokens > budget_tokens
    content, thinking = provider.generate(system_prompt, user_message, max_tokens=3000)

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\nHas thinking: {thinking is not None}")

    if thinking:
        print(f"\nThinking length: {len(thinking)} characters")
        print("\n--- THINKING (first 500 chars) ---")
        print(thinking[:500])
        print("...\n")
    else:
        print("\nWARNING: No thinking blocks returned!")

    print("\n--- CONTENT ---")
    print(content)
    print()


if __name__ == "__main__":
    test_extended_thinking()
