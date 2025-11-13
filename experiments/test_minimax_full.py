#!/usr/bin/env python3
"""See the full MiniMax responses."""

import os
from providers import MinimaxProvider

api_key = os.getenv("MINIMAX_API_KEY")

print("Testing MiniMax-M2 with full output...\n")
print("=" * 80)

provider = MinimaxProvider("MiniMax-M2", api_key)
response, thinking = provider.generate(
    system_prompt="You are a helpful assistant.",
    user_message="Say 'Hello' in exactly one word.",
    max_tokens=100,
)

print("FULL RESPONSE:")
print(response)
print()
print("-" * 80)
print("THINKING BLOCKS:")
print(thinking if thinking else "(none)")
print("=" * 80)
