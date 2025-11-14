#!/usr/bin/env python3
"""
Generate training data using OpenAI Batch API (50% cheaper!).

Workflow:
1. Create JSONL file with batch requests
2. Upload to OpenAI Batch API
3. Poll for completion (24hr max)
4. Download and validate results

Usage:
    python scripts/generate_training_data_batch.py --total 5000 --output data/training_5k.json
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from openai import OpenAI
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
    batch_size: int = 10,
    model: str = "gpt-5.1-20251113"
) -> list[dict]:
    """Create JSONL batch requests."""

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

    # Create batch requests
    num_batches = (total_examples + batch_size - 1) // batch_size
    requests = []

    for batch_num in range(num_batches):
        remaining = total_examples - (batch_num * batch_size)
        current_batch_size = min(batch_size, remaining)

        user_prompt = f"Generate {current_batch_size} diverse, realistic PrismQL training examples. Return ONLY the JSON array."

        request = {
            "custom_id": f"batch_{batch_num}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 4000
            }
        }

        requests.append(request)

    return requests


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate training data using OpenAI Batch API (50% cheaper!)")
    parser.add_argument("--total", type=int, default=5000, help="Total examples to generate")
    parser.add_argument("--batch-size", type=int, default=10, help="Examples per batch request")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file")
    parser.add_argument("--model", type=str, default="gpt-5.1-20251113", help="Model to use (gpt-5.1-20251113 or gpt-4o)")
    parser.add_argument("--poll-interval", type=int, default=60, help="Seconds between status checks")

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set")
        return 1

    # Initialize
    client = OpenAI(api_key=api_key)
    validator = QueryValidator(user_dictionaries=TEST_DICTIONARIES, custom_features=PRECOMPUTED_INDEXES)

    # Load LANGUAGE_REFERENCE.md
    lang_ref_path = Path(__file__).parent.parent / "LANGUAGE_REFERENCE.md"
    with open(lang_ref_path) as f:
        language_reference = f.read()

    available_dicts = list(TEST_DICTIONARIES.keys())
    available_features = list(PRECOMPUTED_INDEXES.keys())

    print(f"{'='*60}")
    print("OPENAI BATCH API GENERATION (50% discount!)")
    print(f"{'='*60}")
    print(f"Model: {args.model}")
    print(f"Total examples: {args.total}")
    print(f"Batch size: {args.batch_size}")
    print(f"Output: {args.output}\n")

    # Step 1: Create batch requests
    print("[1/4] Creating batch requests...")
    requests = create_batch_requests(
        language_reference,
        available_dicts,
        available_features,
        args.total,
        args.batch_size,
        args.model
    )
    print(f"  Created {len(requests)} batch requests\n")

    # Step 2: Write JSONL file
    print("[2/4] Writing batch input file...")
    batch_input_file = Path(args.output).with_suffix(".batch_input.jsonl")
    with open(batch_input_file, "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")
    print(f"  Wrote {batch_input_file}\n")

    # Step 3: Upload and create batch
    print("[3/4] Uploading to OpenAI Batch API...")
    with open(batch_input_file, "rb") as f:
        batch_input_file_obj = client.files.create(file=f, purpose="batch")

    batch = client.batches.create(
        input_file_id=batch_input_file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    print(f"  Batch ID: {batch.id}")
    print(f"  Status: {batch.status}")
    print(f"  Estimated completion: within 24 hours\n")

    # Step 4: Poll for completion
    print("[4/4] Waiting for completion...")
    print(f"  (Polling every {args.poll_interval}s, Ctrl+C to stop and check later)\n")

    try:
        while batch.status not in ["completed", "failed", "expired", "cancelled"]:
            time.sleep(args.poll_interval)
            batch = client.batches.retrieve(batch.id)

            if batch.status == "in_progress":
                progress = f"{batch.request_counts.completed}/{batch.request_counts.total}"
                print(f"  Progress: {progress} requests completed")

        print(f"\n  Final status: {batch.status}")

        if batch.status == "completed":
            print(f"  Completed: {batch.request_counts.completed}")
            print(f"  Failed: {batch.request_counts.failed}\n")

            # Download results
            print("Downloading results...")
            result_file_id = batch.output_file_id
            result_content = client.files.content(result_file_id)
            result_data = result_content.read().decode('utf-8')

            # Parse and validate
            print("Validating results...")
            all_examples = []
            valid_count = 0

            for line in result_data.strip().split('\n'):
                result = json.loads(line)

                if result.get("error"):
                    print(f"  Error in {result['custom_id']}: {result['error']}")
                    continue

                response_content = result["response"]["body"]["choices"][0]["message"]["content"]

                # Parse JSON
                json_text = response_content.strip()
                if "```json" in json_text:
                    json_text = json_text.split("```json")[1].split("```")[0].strip()
                elif "```" in json_text:
                    json_text = json_text.split("```")[1].split("```")[0].strip()

                try:
                    examples = json.loads(json_text)

                    for ex in examples:
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
                            "warnings": [str(w) for w in validation_result.warnings] if validation_result.warnings else []
                        })

                        if validation_result.valid:
                            valid_count += 1

                except json.JSONDecodeError as e:
                    print(f"  JSON parse error in {result['custom_id']}: {e}")
                    continue

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
                        "batch_id": batch.id,
                        "model": args.model,
                        "difficulty_distribution": difficulty_dist
                    },
                    "examples": all_examples
                }, f, indent=2, ensure_ascii=False)

            # Calculate cost (50% discount!)
            INPUT_COST_PER_1M = 0.625  # GPT-5.1 batch pricing
            OUTPUT_COST_PER_1M = 5.0
            total_cost = (batch.usage.prompt_tokens / 1_000_000 * INPUT_COST_PER_1M +
                         batch.usage.completion_tokens / 1_000_000 * OUTPUT_COST_PER_1M)

            print(f"\n{'='*60}")
            print("GENERATION COMPLETE")
            print(f"{'='*60}")
            print(f"Total examples: {len(all_examples)}")
            print(f"✓ Syntax valid: {valid_count} ({valid_count/len(all_examples)*100:.1f}%)")
            print(f"✗ Syntax invalid: {len(all_examples) - valid_count}")
            print(f"\nToken usage:")
            print(f"  Input: {batch.usage.prompt_tokens:,}")
            print(f"  Output: {batch.usage.completion_tokens:,}")
            print(f"\nCost (with 50% batch discount):")
            print(f"  Total: ${total_cost:.2f}")
            print(f"  (Would have been ${total_cost * 2:.2f} without batch API)")
            print(f"\nSaved to: {args.output}")
            print(f"{'='*60}")

        else:
            print(f"\n❌ Batch failed with status: {batch.status}")
            return 1

    except KeyboardInterrupt:
        print(f"\n\nInterrupted! Batch is still running.")
        print(f"Batch ID: {batch.id}")
        print(f"Check status later with: client.batches.retrieve('{batch.id}')")
        return 0

    return 0


if __name__ == "__main__":
    exit(main())
