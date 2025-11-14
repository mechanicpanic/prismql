#!/usr/bin/env python3
"""
Generate large-scale training dataset using Claude API.

Usage:
    python scripts/generate_training_data.py --total 5000 --output data/training_5k.json
"""

import json
import os
import sys
from pathlib import Path

# Add src to path so we can import prismql
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import anthropic
from prismql import QueryValidator

# Rich dictionaries for realistic examples
TEST_DICTIONARIES = {
    # Greetings & social
    "greetings": ["hello", "hi", "hey", "good morning", "good afternoon", "welcome", "greetings"],
    "thanks": ["thanks", "thank you", "appreciate", "grateful", "thx", "ty"],
    "apologies": ["sorry", "apologize", "apologies", "my bad", "excuse me"],
    "goodbyes": ["bye", "goodbye", "see you", "take care", "later", "farewell"],

    # Support & issues
    "problems": ["error", "issue", "bug", "problem", "broken", "not working", "crash", "fail"],
    "solutions": ["fix", "solved", "resolved", "solution", "workaround", "patch", "update"],
    "escalation": ["urgent", "escalate", "manager", "supervisor", "critical", "emergency"],
    "confirmation": ["confirmed", "verified", "checked", "validated", "reproduced"],

    # Technical terms
    "technical": ["database", "server", "api", "endpoint", "configuration", "deployment", "authentication"],
    "programming": ["function", "class", "variable", "method", "syntax", "compile", "debug"],
    "errors": ["exception", "null", "undefined", "timeout", "permission denied", "404", "500"],

    # Business & analytics
    "metrics": ["revenue", "conversion", "engagement", "retention", "churn", "growth"],
    "features": ["feature", "functionality", "capability", "enhancement", "improvement"],
    "feedback": ["feedback", "suggestion", "complaint", "review", "rating", "comment"],

    # Moderation
    "spam": ["spam", "advertisement", "promotion", "buy now", "click here", "limited offer"],
    "toxic": ["rude", "offensive", "inappropriate", "harass", "abuse", "insult"],
    "policy": ["violation", "terms of service", "community guidelines", "banned", "warning"],

    # Customer service
    "requests": ["request", "need", "want", "could you", "please", "help", "assist"],
    "status": ["pending", "in progress", "completed", "cancelled", "waiting", "processing"],
    "billing": ["invoice", "payment", "charge", "refund", "subscription", "pricing", "cost"],

    # Additional common terms (added after seeing Claude use them)
    "answers": ["answer", "response", "reply", "explanation", "clarification", "info"],
    "banned": ["banned", "suspended", "blocked", "restricted", "removed"],
}

# Precomputed feature indexes for has_feature() examples
PRECOMPUTED_INDEXES = {
    "is_greeting": set(),  # Messages starting conversations
    "is_farewell": set(),  # Messages ending conversations
    "is_urgent": set(),    # High-priority messages
    "is_technical": set(), # Technical discussion
    "is_spam": set(),      # Spam messages
    "is_toxic": set(),     # Toxic/inappropriate content
    "needs_escalation": set(),  # Requires supervisor attention
    "is_resolved": set(),  # Problem resolution confirmations
    "has_code": set(),     # Contains code snippets
    "has_link": set(),     # Contains URLs
}

# Imaginary datasets with schemas and examples
IMAGINARY_DATASETS = [
    {
        "name": "Customer Support Chat",
        "description": "Customer support conversations between customers and support agents",
        "schema": {
            "id": "integer (sequential message ID)",
            "user": "string (customer_123, support_alice, support_bob, manager_charlie)",
            "text": "string (message content)",
            "timestamp": "datetime",
            "role": "string (customer, support, manager)",
        },
        "example_rows": [
            {"id": 1, "user": "customer_123", "text": "Hi, my payment failed", "role": "customer"},
            {"id": 2, "user": "support_alice", "text": "Let me check that for you", "role": "support"},
            {"id": 3, "user": "support_alice", "text": "I see the issue, updating now", "role": "support"},
            {"id": 4, "user": "customer_123", "text": "Thank you!", "role": "customer"},
        ],
        "use_cases": [
            "Find unanswered customer questions",
            "Detect escalation patterns",
            "Measure response time patterns",
            "Identify problem-solution pairs",
            "Track customer satisfaction"
        ]
    },
    {
        "name": "Team Collaboration Chat",
        "description": "Internal team communication in Slack/Discord style",
        "schema": {
            "id": "integer",
            "user": "string (alice, bob, charlie, diana)",
            "text": "string",
            "timestamp": "datetime",
            "channel": "string (engineering, design, general)",
        },
        "example_rows": [
            {"id": 1, "user": "alice", "text": "Anyone know why the build is failing?", "channel": "engineering"},
            {"id": 2, "user": "bob", "text": "Checking now", "channel": "engineering"},
            {"id": 3, "user": "bob", "text": "Found it - missing dependency", "channel": "engineering"},
        ],
        "use_cases": [
            "Find questions and their answers",
            "Detect blockers and solutions",
            "Identify same person asking multiple times",
            "Track discussion patterns",
            "Find announcements without responses"
        ]
    },
    {
        "name": "Content Moderation Queue",
        "description": "Messages flagged for moderation review",
        "schema": {
            "id": "integer",
            "user": "string",
            "text": "string",
            "timestamp": "datetime",
            "reported_by": "string (user who reported)",
        },
        "example_rows": [
            {"id": 1, "user": "user_456", "text": "Buy cheap products now!!!", "reported_by": "user_789"},
            {"id": 2, "user": "moderator_alice", "text": "Removed - spam", "reported_by": None},
        ],
        "use_cases": [
            "Find spam followed by moderator action",
            "Detect toxic patterns",
            "Track false positives",
            "Identify repeat offenders",
            "Measure moderation response time"
        ]
    },
    {
        "name": "Community Forum",
        "description": "Q&A forum like Stack Overflow or Reddit",
        "schema": {
            "id": "integer",
            "user": "string",
            "text": "string",
            "timestamp": "datetime",
            "post_type": "string (question, answer, comment)",
        },
        "example_rows": [
            {"id": 1, "user": "alice", "text": "How do I fix this error?", "post_type": "question"},
            {"id": 2, "user": "bob", "text": "Try updating your dependencies", "post_type": "answer"},
            {"id": 3, "user": "alice", "text": "That worked, thanks!", "post_type": "comment"},
        ],
        "use_cases": [
            "Find unanswered questions",
            "Identify helpful users",
            "Detect question-answer-thanks patterns",
            "Track topic clusters",
            "Find duplicate questions"
        ]
    },
    {
        "name": "Live Streaming Chat",
        "description": "Fast-paced chat during live streams (Twitch/YouTube style)",
        "schema": {
            "id": "integer",
            "user": "string",
            "text": "string",
            "timestamp": "datetime",
            "is_subscriber": "boolean",
        },
        "example_rows": [
            {"id": 1, "user": "viewer_123", "text": "First!", "is_subscriber": False},
            {"id": 2, "user": "viewer_456", "text": "Hello everyone!", "is_subscriber": True},
            {"id": 3, "user": "streamer", "text": "Welcome!", "is_subscriber": None},
        ],
        "use_cases": [
            "Detect spam bursts",
            "Find streamer interactions",
            "Identify conversation starters",
            "Track emote patterns",
            "Measure engagement spikes"
        ]
    }
]

# Difficulty level definitions
DIFFICULTY_LEVELS = {
    "easy": {
        "description": "Single condition or simple boolean combinations",
        "examples": [
            "from(user) - single user filter",
            "contains(dict) - dictionary matching",
            "from(alice) AND is_question() - two conditions",
            "from(alice) OR from(bob) - simple OR"
        ],
        "characteristics": [
            "1-2 operators",
            "No window constraints",
            "No sequential patterns",
            "Basic boolean logic"
        ]
    },
    "medium": {
        "description": "Window patterns, multiple conditions, basic temporal/positional constraints",
        "examples": [
            "from(alice), from(bob) INWINDOW 5 - co-occurrence",
            "is_question(), contains(answers) INWINDOW 10",
            "(from(alice) OR from(bob)) AND is_question(), contains(answers) INWINDOW 5",
            "from(alice), from(bob) DURING 1 hour - temporal"
        ],
        "characteristics": [
            "3-5 operators",
            "INWINDOW or DURING clauses",
            "Multiple boolean conditions",
            "No sequential patterns"
        ]
    },
    "hard": {
        "description": "Sequential patterns, pattern variables, quantifiers, complex logic",
        "examples": [
            "from(customer) FOLLOWED_BY from(support) INWINDOW 5 - sequence",
            "from($user), from($user) INWINDOW 3 - pattern variables",
            "from(alice){3,} INWINDOW 10 - quantifiers",
            "is_question() NOT_FOLLOWED_BY contains(answers) INWINDOW 5 - negative patterns"
        ],
        "characteristics": [
            "5-8 operators",
            "FOLLOWED_BY/PRECEDED_BY",
            "Pattern variables ($user)",
            "Quantifiers {N}, {N,}",
            "Negative patterns"
        ]
    },
    "expert": {
        "description": "Subqueries, complex multi-stage patterns, edge cases, advanced combinations",
        "examples": [
            "SELECT (SELECT from(alice), from(bob) INWINDOW 3) ; (SELECT from(charlie)) INWINDOW 10 - subqueries",
            "SELECT from($user) AND is_question() FOLLOWED_BY from($user) AND contains(thanks) INWINDOW 5 - variables + sequence",
            "Complex moderation workflows with multiple stages"
        ],
        "characteristics": [
            "8+ operators",
            "Subqueries with grouping",
            "Multi-stage patterns",
            "Complex variable usage",
            "Edge cases and advanced logic"
        ]
    }
}


def generate_batch(
    client,
    validator: QueryValidator,
    language_reference: str,
    available_dicts: list[str],
    available_features: list[str],
    batch_size: int = 10,
    use_openrouter: bool = False,
    model: str = "claude-sonnet-4-5-20250929"
) -> tuple[list[dict], dict]:
    """Generate a batch of training examples using Claude or OpenRouter API.

    Returns:
        (validated_examples, usage_stats)
    """

    # Format datasets for prompt
    datasets_text = "\n\n".join([
        f"### {ds['name']}\n"
        f"{ds['description']}\n\n"
        f"Schema: {json.dumps(ds['schema'], indent=2)}\n\n"
        f"Example rows:\n{json.dumps(ds['example_rows'], indent=2)}\n\n"
        f"Common use cases:\n" + "\n".join(f"- {uc}" for uc in ds['use_cases'])
        for ds in IMAGINARY_DATASETS
    ])

    # Format difficulty levels
    difficulty_text = "\n\n".join([
        f"### {level.upper()}\n"
        f"{info['description']}\n\n"
        f"Characteristics:\n" + "\n".join(f"- {c}" for c in info['characteristics']) + "\n\n"
        f"Examples:\n" + "\n".join(f"- {e}" for e in info['examples'])
        for level, info in DIFFICULTY_LEVELS.items()
    ])

    system_prompt = f"""{language_reference}

---

# TRAINING DATA GENERATION TASK

You are generating training data for fine-tuning a language model to translate natural language requests into PrismQL queries (similar to text-to-SQL).

## IMAGINARY DATASETS

{datasets_text}

## DIFFICULTY LEVELS

{difficulty_text}

## AVAILABLE DICTIONARIES
{', '.join(available_dicts)}

## AVAILABLE FEATURES (for has_feature())
{', '.join(available_features)}

## YOUR TASK

Generate {batch_size} realistic training examples in the following format:

```json
[
  {{
    "dataset": "Customer Support Chat",
    "difficulty": "medium",
    "description": "Find customers who asked urgent questions that weren't answered by support within 5 messages",
    "query": "SELECT from(customer) AND is_question() AND has_feature(is_urgent) NOT_FOLLOWED_BY from(support) INWINDOW 5"
  }}
]
```

## REQUIREMENTS

1. **Realism**: Generate requests that would actually be asked by data analysts, moderators, or support managers
2. **Variety**: Mix datasets, difficulty levels, and use cases
3. **Natural language**: Write descriptions as natural requests, not technical specifications
4. **Correctness**: Ensure queries are syntactically valid according to the language reference
5. **Diversity**: Use different operators, patterns, and combinations
6. **Difficulty distribution**: Include examples from all difficulty levels
7. **Grounded scenarios**: Base examples on the provided dataset schemas and use cases

Return ONLY the JSON array, no explanations."""

    user_prompt = f"Generate {batch_size} diverse, realistic PrismQL training examples. Return ONLY the JSON array."

    # Call API (Anthropic or OpenRouter)
    if use_openrouter:
        # OpenRouter API call (OpenAI-compatible)
        response = client.chat.completions.create(
            model=model,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
    else:
        # Anthropic API call with extended thinking
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            thinking={"type": "enabled", "budget_tokens": 2000},
        )

    # Extract content and thinking (handle multi-line properly)
    content_text = ""
    thinking_text = ""

    if use_openrouter:
        # OpenRouter response format (OpenAI-compatible)
        content_text = response.choices[0].message.content
        # OpenRouter doesn't support thinking tokens (yet)
    else:
        # Anthropic response format
        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "thinking":
                thinking_text += block.thinking

    # Parse JSON from response (may be wrapped in markdown)
    json_text = content_text.strip()
    if "```json" in json_text:
        json_text = json_text.split("```json")[1].split("```")[0].strip()
    elif "```" in json_text:
        json_text = json_text.split("```")[1].split("```")[0].strip()

    # Parse JSON (handles newlines in strings automatically)
    try:
        examples = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"\n  ERROR: Failed to parse JSON from Claude response: {e}")
        print(f"  Response preview: {json_text[:200]}")
        return []

    # Validate each example with QueryValidator
    validated = []
    for i, ex in enumerate(examples):
        query = ex.get("query", "").strip()

        # Normalize whitespace in multi-line queries
        query = " ".join(query.split())

        # Syntactic validation
        result = validator.validate(query)

        validated.append({
            "dataset": ex.get("dataset", "").strip(),
            "difficulty": ex.get("difficulty", "medium").strip(),
            "description": ex.get("description", "").strip(),
            "query": query,
            "syntax_valid": result.valid,
            "syntax_errors": [str(e) for e in result.errors] if not result.valid else [],
            "warnings": [str(w) for w in result.warnings] if result.warnings else [],
            # Capture CoT for potential use in LoRA training (reasoning format)
            "thinking": thinking_text if thinking_text else None
        })

    # Extract usage statistics
    usage_stats = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }

    return validated, usage_stats


def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Generate training data using Claude API")
    parser.add_argument("--total", type=int, default=5000, help="Total examples to generate")
    parser.add_argument("--batch-size", type=int, default=10, help="Examples per API call")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between batches (seconds)")

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return 1

    # Initialize
    client = anthropic.Anthropic(api_key=api_key)
    validator = QueryValidator(user_dictionaries=TEST_DICTIONARIES, custom_features=PRECOMPUTED_INDEXES)

    # Load LANGUAGE_REFERENCE.md
    lang_ref_path = Path(__file__).parent.parent / "LANGUAGE_REFERENCE.md"
    with open(lang_ref_path) as f:
        language_reference = f.read()

    # Get available dictionaries and features
    available_dicts = list(TEST_DICTIONARIES.keys())
    available_features = list(PRECOMPUTED_INDEXES.keys())

    print(f"Loaded {len(available_dicts)} dictionaries")
    print(f"Loaded {len(available_features)} features")
    print(f"Loaded {len(IMAGINARY_DATASETS)} imaginary datasets")
    print(f"Loaded {len(DIFFICULTY_LEVELS)} difficulty levels")

    # Generate in batches
    all_examples = []
    num_batches = (args.total + args.batch_size - 1) // args.batch_size

    # Cost tracking (Sonnet 4.5 pricing)
    total_input_tokens = 0
    total_output_tokens = 0
    INPUT_COST_PER_1M = 3.0  # $3 per million input tokens
    OUTPUT_COST_PER_1M = 15.0  # $15 per million output tokens

    print(f"\nGenerating {args.total} examples in {num_batches} batches...")
    print(f"Output: {args.output}\n")

    for batch_num in range(num_batches):
        remaining = args.total - len(all_examples)
        current_batch_size = min(args.batch_size, remaining)

        print(f"[{batch_num + 1}/{num_batches}] Generating {current_batch_size} examples...", end=" ", flush=True)

        try:
            batch, usage_stats = generate_batch(client, validator, language_reference, available_dicts, available_features, current_batch_size)

            if not batch:
                print("✗ No examples returned (JSON parse error)")
                continue

            # Track token usage
            total_input_tokens += usage_stats["input_tokens"]
            total_output_tokens += usage_stats["output_tokens"]

            valid_count = sum(1 for ex in batch if ex["syntax_valid"])
            all_examples.extend(batch)

            # Calculate cost for this batch
            batch_cost = (usage_stats["input_tokens"] / 1_000_000 * INPUT_COST_PER_1M +
                         usage_stats["output_tokens"] / 1_000_000 * OUTPUT_COST_PER_1M)

            print(f"✓ ({valid_count}/{len(batch)} valid, ${batch_cost:.3f})")

            # Save incrementally with validation statistics
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            valid_total = sum(1 for ex in all_examples if ex["syntax_valid"])
            invalid_total = len(all_examples) - valid_total

            # Calculate difficulty distribution
            difficulty_dist = {}
            for ex in all_examples:
                diff = ex["difficulty"]
                difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1

            # Calculate dataset distribution
            dataset_dist = {}
            for ex in all_examples:
                ds = ex["dataset"]
                dataset_dist[ds] = dataset_dist.get(ds, 0) + 1

            with open(output_path, "w") as f:
                json.dump({
                    "metadata": {
                        "total": len(all_examples),
                        "syntax_valid": valid_total,
                        "syntax_invalid": invalid_total,
                        "success_rate": f"{valid_total/len(all_examples)*100:.1f}%" if all_examples else "0%",
                        "target": args.total,
                        "progress": f"{len(all_examples)}/{args.total}",
                        "datasets": [ds["name"] for ds in IMAGINARY_DATASETS],
                        "difficulty_levels": list(DIFFICULTY_LEVELS.keys()),
                        "difficulty_distribution": difficulty_dist,
                        "dataset_distribution": dataset_dist
                    },
                    "examples": all_examples
                }, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            continue

        # Rate limiting
        if batch_num < num_batches - 1:
            time.sleep(args.delay)

    # Final summary
    valid = sum(1 for ex in all_examples if ex["syntax_valid"])
    invalid = len(all_examples) - valid

    # Calculate total cost
    total_cost = (total_input_tokens / 1_000_000 * INPUT_COST_PER_1M +
                  total_output_tokens / 1_000_000 * OUTPUT_COST_PER_1M)

    print(f"\n{'='*60}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total examples: {len(all_examples)}")
    print(f"✓ Syntax valid: {valid} ({valid/len(all_examples)*100:.1f}%)")
    print(f"✗ Syntax invalid: {invalid} ({invalid/len(all_examples)*100:.1f}%)")
    print(f"\nToken usage:")
    print(f"  Input tokens: {total_input_tokens:,}")
    print(f"  Output tokens: {total_output_tokens:,}")
    print(f"  Total tokens: {total_input_tokens + total_output_tokens:,}")
    print(f"\nCost estimate:")
    print(f"  Input: ${total_input_tokens / 1_000_000 * INPUT_COST_PER_1M:.2f}")
    print(f"  Output: ${total_output_tokens / 1_000_000 * OUTPUT_COST_PER_1M:.2f}")
    print(f"  Total: ${total_cost:.2f}")
    print(f"\nDifficulty distribution:")
    for diff, count in sorted(difficulty_dist.items()):
        print(f"  {diff}: {count}")
    print(f"\nSaved to: {args.output}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    exit(main())
