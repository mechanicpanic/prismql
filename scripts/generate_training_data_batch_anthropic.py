#!/usr/bin/env python3
"""
Generate training data using Anthropic Message Batches API (50% cheaper!).

Workflow:
1. Create batch requests
2. Submit to Anthropic Message Batches API
3. Poll for completion (24hr max)
4. Download and validate results

Usage:
    python scripts/generate_training_data_batch_anthropic.py --total 5000 --output data/training_5k.json
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import anthropic
from prismql import QueryValidator

# Import config from sync script
import importlib.util
spec = importlib.util.spec_from_file_location("sync_script", Path(__file__).parent / "generate_training_data.py")
sync_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_module)

TEST_DICTIONARIES = sync_module.TEST_DICTIONARIES
PRECOMPUTED_INDEXES = sync_module.PRECOMPUTED_INDEXES
IMAGINARY_DATASETS = sync_module.IMAGINARY_DATASETS
DIFFICULTY_LEVELS = sync_module.DIFFICULTY_LEVELS


def create_batch_requests(
    language_reference: str,
    available_dicts: list[str],
    available_features: list[str],
    total_examples: int,
    model: str = "claude-sonnet-4-5-20250929"
) -> list[dict]:
    """Create Message Batch requests - ONE REQUEST PER EXAMPLE for individual thinking."""

    # Format datasets
    datasets_text = "\n\n".join([
        f"### {ds['name']}\n{ds['description']}\n\n"
        f"Schema: {json.dumps(ds['schema'], indent=2)}\n\n"
        f"Example rows:\n{json.dumps(ds['example_rows'], indent=2)}\n\n"
        f"Common use cases:\n" + "\n".join(f"- {uc}" for uc in ds['use_cases'])
        for ds in IMAGINARY_DATASETS
    ])

    # Format difficulty levels
    difficulty_text = "\n\n".join([
        f"### {level.upper()}\n{info['description']}\n\n"
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

Generate ONE realistic training example in the following format:

```json
{{
  "dataset": "Customer Support Chat",
  "difficulty": "medium",
  "description": "Find customers who asked urgent questions that weren't answered by support within 5 messages",
  "query": "SELECT from(customer) AND is_question() AND has_feature(is_urgent) NOT_FOLLOWED_BY from(support) INWINDOW 5"
}}
```

## REQUIREMENTS

1. **Realism**: Generate a request that would actually be asked by a data analyst, moderator, or support manager
2. **Variety**: Choose a random dataset and difficulty level
3. **Natural language**: Write description as a natural request, not technical specification
4. **Correctness**: Ensure query is syntactically valid according to the language reference
5. **Diversity**: Use different operators, patterns, and combinations
6. **Grounded scenario**: Base example on the provided dataset schema and use cases

Return ONLY the JSON object (not an array), no explanations."""

    # Create difficulty distribution (programmatic!)
    difficulty_distribution = {
        "easy": int(total_examples * 0.25),      # 25%
        "medium": int(total_examples * 0.35),    # 35%
        "hard": int(total_examples * 0.30),      # 30%
        "expert": int(total_examples * 0.10)     # 10%
    }

    # Adjust for rounding
    total_allocated = sum(difficulty_distribution.values())
    if total_allocated < total_examples:
        difficulty_distribution["medium"] += (total_examples - total_allocated)

    # Create list of difficulties
    difficulties = []
    for diff, count in difficulty_distribution.items():
        difficulties.extend([diff] * count)

    # Create uniform dataset distribution
    dataset_names = [ds["name"] for ds in IMAGINARY_DATASETS]
    num_datasets = len(dataset_names)
    examples_per_dataset = total_examples // num_datasets
    remainder = total_examples % num_datasets

    datasets = []
    for i, dataset_name in enumerate(dataset_names):
        count = examples_per_dataset + (1 if i < remainder else 0)
        datasets.extend([dataset_name] * count)

    # Shuffle both for variety
    import random
    random.shuffle(difficulties)
    random.shuffle(datasets)

    # Create ONE request per example with assigned difficulty AND dataset
    requests = []

    for example_num in range(total_examples):
        difficulty = difficulties[example_num]
        dataset = datasets[example_num]

        user_prompt = f"Generate ONE realistic PrismQL training example for the '{dataset}' dataset with difficulty level: {difficulty}. Return ONLY the JSON object."

        # Update system prompt to use assigned difficulty and dataset
        system_prompt_with_constraints = system_prompt.replace(
            '"dataset": "Customer Support Chat",',
            f'"dataset": "{dataset}",'
        ).replace(
            '"difficulty": "medium"',
            f'"difficulty": "{difficulty}"'
        )

        request = {
            "custom_id": f"example_{example_num:04d}_{difficulty}_{dataset[:10]}",
            "params": {
                "model": model,
                "max_tokens": 2500,  # Enough for thinking (2000) + output (500)
                "messages": [
                    {"role": "user", "content": user_prompt}
                ],
                "system": system_prompt_with_constraints,
                # Enable extended thinking for per-example reasoning
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 2000  # Must be < max_tokens
                }
            }
        }

        requests.append(request)

    return requests


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate training data using Anthropic Batch API (50% cheaper + per-example thinking!)")
    parser.add_argument("--total", type=int, default=5000, help="Total examples to generate")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-5-20250929", help="Model to use")
    parser.add_argument("--poll-interval", type=int, default=60, help="Seconds between status checks")

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

    available_dicts = list(TEST_DICTIONARIES.keys())
    available_features = list(PRECOMPUTED_INDEXES.keys())

    print(f"{'='*60}")
    print("ANTHROPIC MESSAGE BATCHES API")
    print("ONE REQUEST PER EXAMPLE (individual thinking!)")
    print(f"{'='*60}")
    print(f"Model: {args.model}")
    print(f"Total examples: {args.total}")
    print(f"Strategy: 1 API call per example = unique CoT reasoning")
    print(f"Output: {args.output}\n")

    # Step 1: Create batch requests
    print("[1/3] Creating batch requests...")
    requests = create_batch_requests(
        language_reference,
        available_dicts,
        available_features,
        args.total,
        args.model
    )
    print(f"  Created {len(requests)} batch requests (1 per example)")
    print(f"  Each request includes extended thinking (2000 tokens budget)")

    # Show distribution
    from collections import Counter
    difficulties_in_batch = [req["custom_id"].split("_")[2] for req in requests]
    datasets_in_batch = [req["custom_id"].split("_")[3] for req in requests]

    print(f"\n  Difficulty distribution:")
    for diff, count in sorted(Counter(difficulties_in_batch).items()):
        print(f"    {diff}: {count}")

    print(f"\n  Dataset distribution:")
    for ds, count in sorted(Counter(datasets_in_batch).items()):
        print(f"    {ds}: {count}")

    print(f"\n  Note: Anthropic allows up to 100,000 requests per batch\n")

    # Step 2: Submit batch
    print("[2/3] Submitting to Anthropic Message Batches API...")
    message_batch = client.messages.batches.create(
        requests=requests
    )

    print(f"  Batch ID: {message_batch.id}")
    print(f"  Status: {message_batch.processing_status}")
    print(f"  Request counts: {message_batch.request_counts}")
    print(f"  Estimated completion: within 24 hours\n")

    # Step 3: Poll for completion
    print("[3/3] Waiting for completion...")
    print(f"  (Polling every {args.poll_interval}s, Ctrl+C to stop and check later)\n")

    try:
        while message_batch.processing_status in ["in_progress", "starting"]:
            time.sleep(args.poll_interval)
            message_batch = client.messages.batches.retrieve(message_batch.id)

            if message_batch.processing_status == "in_progress":
                counts = message_batch.request_counts
                total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
                completed = counts.succeeded + counts.errored
                print(f"  Progress: {completed}/{total} requests completed")

        print(f"\n  Final status: {message_batch.processing_status}")
        print(f"  Request counts:")
        print(f"    Succeeded: {message_batch.request_counts.succeeded}")
        print(f"    Errored: {message_batch.request_counts.errored}")
        print(f"    Canceled: {message_batch.request_counts.canceled}")
        print(f"    Expired: {message_batch.request_counts.expired}\n")

        if message_batch.processing_status == "ended":
            # Check if we have any errors to debug
            if message_batch.request_counts.errored > 0:
                print(f"\n⚠️  WARNING: {message_batch.request_counts.errored} requests failed!")
                print(f"Attempting to fetch error details...\n")

            # Download results
            print("Downloading results...")

            # Use Anthropic client to fetch results (handles auth properly)
            try:
                results_response = client.messages.batches.results(message_batch.id)

                # The results come as a generator of result objects
                results_data = []
                for result in results_response:
                    results_data.append(result)

                print(f"Fetched {len(results_data)} result objects from batch")
            except Exception as e:
                print(f"Error fetching results: {e}")
                print(f"\nBatch details:")
                print(f"  ID: {message_batch.id}")
                print(f"  Results URL: {message_batch.results_url if hasattr(message_batch, 'results_url') else 'N/A'}")
                return 1

            # Parse and validate
            print(f"Processing {len(results_data)} results...")
            all_examples = []
            valid_count = 0
            error_count = 0

            for result in results_data:
                # Check result type
                if result.result.type == "error":
                    error_count += 1
                    error_detail = result.result.error
                    # Print first 10 errors to debug
                    if error_count <= 10:
                        print(f"  ❌ Error #{error_count} in {result.custom_id}:")
                        print(f"     Type: {error_detail.type}")
                        print(f"     Message: {error_detail.message}")
                    continue

                if result.result.type != "succeeded":
                    continue

                # Extract message content
                message = result.result.message
                response_content = ""
                thinking_content = ""

                for block in message.content:
                    if block.type == "text":
                        response_content += block.text
                    elif block.type == "thinking":
                        thinking_content += block.thinking

                # Parse JSON
                json_text = response_content.strip()
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1].split("```")[0].strip()
                elif "```" in json_text:
                    json_text = json_text.split("```")[1].split("```")[0].strip()

                try:
                    # Parse single example (not array since we generate 1 per request)
                    ex = json.loads(json_text)

                    query = ex.get("query", "").strip()
                    query = " ".join(query.split())  # Normalize whitespace

                    validation_result = validator.validate(query)

                    all_examples.append({
                        "dataset": ex.get("dataset", "").strip(),
                        "difficulty": ex.get("difficulty", "medium").strip(),
                        "description": ex.get("description", "").strip(),
                        "query": query,
                        "syntax_valid": validation_result.valid,
                        "syntax_errors": [str(e) for e in validation_result.errors] if not validation_result.valid else [],
                        "warnings": [str(w) for w in validation_result.warnings] if validation_result.warnings else [],
                        "thinking": thinking_content if thinking_content else None
                    })

                    if validation_result.valid:
                        valid_count += 1

                except json.JSONDecodeError as e:
                    print(f"  JSON parse error in {result.custom_id}: {e}")
                    continue

            if error_count > 10:
                print(f"  ... and {error_count - 10} more errors")

            print(f"\nValidation complete: {len(all_examples)} examples extracted, {error_count} errors")

            # Save results
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            difficulty_dist = {}
            for ex in all_examples:
                diff = ex["difficulty"]
                difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1

            with open(output_path, "w") as f:
                json.dump({
                    "metadata": {
                        "total": len(all_examples),
                        "syntax_valid": valid_count,
                        "syntax_invalid": len(all_examples) - valid_count,
                        "success_rate": f"{valid_count/len(all_examples)*100:.1f}%" if all_examples else "0%",
                        "batch_id": message_batch.id,
                        "model": args.model,
                        "difficulty_distribution": difficulty_dist
                    },
                    "examples": all_examples
                }, f, indent=2, ensure_ascii=False)

            # Note: Anthropic doesn't return token usage in batch results yet
            # Estimate based on standard pricing
            INPUT_COST_PER_1M = 1.5  # Sonnet 4.5 batch pricing
            OUTPUT_COST_PER_1M = 7.5

            print(f"\n{'='*60}")
            print("GENERATION COMPLETE")
            print(f"{'='*60}")
            print(f"Total examples: {len(all_examples)}")
            print(f"Total errors: {error_count}")
            if all_examples:
                print(f"✓ Syntax valid: {valid_count} ({valid_count/len(all_examples)*100:.1f}%)")
                print(f"✗ Syntax invalid: {len(all_examples) - valid_count}")
            else:
                print(f"⚠️  No examples generated - all requests failed!")
            print(f"\nCost estimate (with 50% batch discount):")
            print(f"  Claude Sonnet 4.5: $1.50/$7.50 per M tokens (vs $3/$15 standard)")
            print(f"  💡 Tip: Add prompt caching for up to 93% total discount!")
            print(f"\nSaved to: {args.output}")
            print(f"{'='*60}")

        else:
            print(f"\n❌ Batch ended with status: {message_batch.processing_status}")
            return 1

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Batch is still running.")
        print(f"Batch ID: {message_batch.id}")
        print(f"Check status later with: client.messages.batches.retrieve('{message_batch.id}')")
        print(f"\nTo cancel: client.messages.batches.cancel('{message_batch.id}')")
        return 0

    return 0


if __name__ == "__main__":
    exit(main())
