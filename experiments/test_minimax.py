#!/usr/bin/env python3
"""
Test MiniMax integration.

Verify that MiniMax provider is properly configured and can connect to the API.
"""

import os
import sys

from providers import MinimaxProvider


def test_minimax_connection():
    """Test basic MiniMax API connection."""
    api_key = os.getenv("MINIMAX_API_KEY")

    if not api_key:
        print("❌ MINIMAX_API_KEY environment variable not set")
        print("\nTo test MiniMax integration:")
        print("  1. Get your API key from https://platform.minimax.io")
        print("  2. Set environment variable: export MINIMAX_API_KEY='your_key'")
        print("  3. Run this script again")
        return False

    print("Testing MiniMax integration...")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    # Test MiniMax-M2
    print("[1/2] Testing MiniMax-M2...")
    try:
        provider = MinimaxProvider("MiniMax-M2", api_key)
        response, thinking = provider.generate(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'Hello' in exactly one word.",
            max_tokens=100,
        )
        print(f"✅ MiniMax-M2 connected successfully")
        print(f"   Response: {response[:50]}...")
        if thinking:
            print(f"   Thinking: {len(thinking)} chars")
    except Exception as e:
        print(f"❌ MiniMax-M2 failed: {e}")
        return False

    # Test MiniMax-M2-Stable
    print("\n[2/2] Testing MiniMax-M2-Stable...")
    try:
        provider = MinimaxProvider("MiniMax-M2-Stable", api_key)
        response, thinking = provider.generate(
            system_prompt="You are a helpful assistant.",
            user_message="Say 'Hello' in exactly one word.",
            max_tokens=100,
        )
        print(f"✅ MiniMax-M2-Stable connected successfully")
        print(f"   Response: {response[:50]}...")
        if thinking:
            print(f"   Thinking: {len(thinking)} chars")
    except Exception as e:
        print(f"❌ MiniMax-M2-Stable failed: {e}")
        return False

    # Test extended thinking
    print("\n[3/3] Testing extended thinking mode...")
    try:
        provider = MinimaxProvider("MiniMax-M2", api_key, extended_thinking=True)
        response, thinking = provider.generate(
            system_prompt="You are a helpful assistant.",
            user_message="Think carefully: What is 2+2?",
            max_tokens=2000,
        )
        print(f"✅ Extended thinking mode works")
        print(f"   Response: {response[:50]}...")
        if thinking:
            print(f"   Thinking blocks captured: {len(thinking)} chars")
        else:
            print(f"   Note: No thinking blocks in this response")
    except Exception as e:
        print(f"❌ Extended thinking failed: {e}")
        return False

    print("\n" + "=" * 80)
    print("✅ All MiniMax tests passed!")
    print("=" * 80)
    print("\nYou can now run experiments with MiniMax models:")
    print("  uv run python experiments/run_experiment.py --models minimax-m2 --strategies zero_shot --test-cases easy")
    return True


if __name__ == "__main__":
    success = test_minimax_connection()
    sys.exit(0 if success else 1)
