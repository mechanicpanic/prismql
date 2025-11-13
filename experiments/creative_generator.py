#!/usr/bin/env python3
"""
Creative PrismQL Query Generator

Generates novel training examples by:
1. Loading seed examples from existing data
2. Sending batches to LLM (Sonnet 4.5 with extended thinking)
3. Validating generated queries (syntax + semantic)
4. Saving high-quality examples for LoRA training
"""

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic

from prismql import QueryValidator
from test_cases import get_all_required_dictionaries


@dataclass
class GeneratedExample:
    """A generated training example with validation results."""

    id: str
    description: str
    query: str
    category: str
    difficulty: str
    operators_used: list[str]
    notes: str
    dictionaries: dict[str, list[str]]
    # Validation results
    syntax_valid: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    # Metadata
    generated_at: str
    thinking: str | None = None  # Extended thinking from model


class CreativeQueryGenerator:
    """Generate creative PrismQL queries using LLM."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        use_extended_thinking: bool = True,
    ):
        """
        Initialize generator.

        Args:
            api_key: Anthropic API key
            model: Model to use (default: Sonnet 4.5)
            use_extended_thinking: Enable extended thinking mode
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.use_extended_thinking = use_extended_thinking

        # Initialize validator with all test dictionaries
        all_dicts = get_all_required_dictionaries()
        self.validator = QueryValidator(
            user_dictionaries=all_dicts, check_deprecated=True, check_performance=False
        )

        # Load language reference
        lang_ref_path = Path(__file__).parent.parent / "LANGUAGE_REFERENCE.md"
        with open(lang_ref_path) as f:
            self.language_reference = f.read()

    def _create_system_prompt(self) -> str:
        """Create system prompt for creative query generation."""
        return f"""Generate creative PrismQL training examples for fine-tuning.

{self.language_reference}

TASK: Generate diverse, realistic query examples covering all operators.

OUTPUT FORMAT (JSON array):
[
  {{
    "id": "creative_001",
    "description": "Natural language request",
    "query": "SELECT ...",
    "category": "support_analytics|moderation|conversation_analysis|etc",
    "difficulty": "easy|medium|hard",
    "operators_used": ["from", "contains", "INWINDOW", "etc"],
    "notes": "What makes this interesting/tricky",
    "dictionaries": {{"dict_name": ["word1", "word2"]}}
  }}
]

REQUIREMENTS:
- Use INWINDOW for positional windows, DURING for temporal
- Wrap subqueries: (SELECT ...) even for single restrictions
- Be creative: realistic scenarios, not obvious patterns
- Ensure syntactic correctness
- Include diverse use cases and difficulty levels"""

    def _create_user_prompt(
        self, seed_examples: list[dict[str, Any]], num_to_generate: int
    ) -> str:
        """
        Create user prompt with seed examples.

        Args:
            seed_examples: Existing examples to inspire from
            num_to_generate: Number of new examples to generate

        Returns:
            User prompt string
        """
        # Sample a few seed examples for inspiration
        import random

        sample_size = min(5, len(seed_examples))
        samples = random.sample(seed_examples, sample_size)

        prompt = f"""Generate {num_to_generate} NEW, creative PrismQL examples.

INSPIRATION (do NOT copy these - generate NOVEL examples):
{json.dumps(samples, indent=2)}

Generate {num_to_generate} completely NEW examples with:
- Different use cases and scenarios
- Creative operator combinations
- Realistic business logic
- Varied difficulty levels

Return ONLY the JSON array, no explanations."""

        return prompt

    def generate_batch(
        self,
        seed_examples: list[dict[str, Any]],
        batch_size: int = 10,
        max_tokens: int = 4000,
    ) -> list[GeneratedExample]:
        """
        Generate a batch of creative examples.

        Args:
            seed_examples: Existing examples for inspiration
            batch_size: Number of examples to generate
            max_tokens: Max tokens for response

        Returns:
            List of validated GeneratedExample objects
        """
        print(f"Generating batch of {batch_size} examples...")

        # Create prompts
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(seed_examples, batch_size)

        # Configure extended thinking if enabled
        if self.use_extended_thinking:
            thinking_config = {"type": "enabled", "budget_tokens": 2000}
        else:
            thinking_config = {"type": "disabled"}

        # Call Claude
        print(f"Calling {self.model} with extended thinking...")
        start_time = time.time()

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            thinking=thinking_config,
        )

        elapsed = time.time() - start_time
        print(f"Response received in {elapsed:.1f}s")

        # Extract content and thinking
        content_text = ""
        thinking_text = ""

        for block in response.content:
            if block.type == "thinking":
                thinking_text += block.thinking + "\n"
            elif block.type == "text":
                content_text += block.text

        # Parse JSON response
        try:
            # Extract JSON from potential markdown code blocks
            json_text = content_text.strip()
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()

            generated_data = json.loads(json_text)
            print(f"Parsed {len(generated_data)} examples from response")

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            print(f"Response: {content_text[:500]}")
            return []

        # Validate each generated example
        validated_examples = []
        for i, data in enumerate(generated_data, 1):
            print(f"  Validating {i}/{len(generated_data)}: {data.get('id', 'unknown')}")

            # Validate query syntax
            query = data.get("query", "")
            validation_result = self.validator.validate(query)

            example = GeneratedExample(
                id=data.get("id", f"creative_{i:03d}"),
                description=data.get("description", ""),
                query=query,
                category=data.get("category", "uncategorized"),
                difficulty=data.get("difficulty", "medium"),
                operators_used=data.get("operators_used", []),
                notes=data.get("notes", ""),
                dictionaries=data.get("dictionaries", {}),
                syntax_valid=validation_result.valid,
                validation_errors=[str(e) for e in validation_result.errors],
                validation_warnings=[str(w) for w in validation_result.warnings],
                generated_at=datetime.now().isoformat(),
                thinking=thinking_text if thinking_text else None,
            )

            validated_examples.append(example)

            # Print validation status
            if validation_result.valid:
                print(f"    ✅ Valid")
            else:
                print(f"    ❌ Invalid: {validation_result.errors[0]}")

        return validated_examples

    def generate_dataset(
        self,
        seed_file: str | Path,
        total_examples: int = 100,
        batch_size: int = 10,
        output_file: str | Path | None = None,
        rate_limit_delay: float = 5.0,
    ) -> list[GeneratedExample]:
        """
        Generate full dataset of creative examples.

        Args:
            seed_file: Path to seed examples JSON
            total_examples: Total number of examples to generate
            batch_size: Examples per API call
            output_file: Where to save results (optional)
            rate_limit_delay: Seconds to wait between batches

        Returns:
            List of all generated examples
        """
        # Load seed examples
        print(f"Loading seed examples from {seed_file}")
        with open(seed_file) as f:
            seed_data = json.load(f)

        # Handle different JSON formats
        if isinstance(seed_data, dict):
            seed_examples = seed_data.get("examples", [])
        else:
            seed_examples = seed_data

        print(f"Loaded {len(seed_examples)} seed examples")

        # Generate in batches
        all_examples = []
        num_batches = (total_examples + batch_size - 1) // batch_size

        for batch_num in range(num_batches):
            remaining = total_examples - len(all_examples)
            current_batch_size = min(batch_size, remaining)

            print(f"\n{'='*80}")
            print(f"BATCH {batch_num + 1}/{num_batches} ({current_batch_size} examples)")
            print(f"{'='*80}")

            batch = self.generate_batch(seed_examples, current_batch_size)
            all_examples.extend(batch)

            # Save incrementally
            if output_file:
                self.save_dataset(all_examples, output_file)
                print(f"Saved {len(all_examples)} examples to {output_file}")

            # Rate limiting
            if batch_num < num_batches - 1:
                print(f"Waiting {rate_limit_delay}s before next batch...")
                time.sleep(rate_limit_delay)

        return all_examples

    def save_dataset(
        self, examples: list[GeneratedExample], output_file: str | Path
    ) -> None:
        """
        Save generated examples to JSON file.

        Args:
            examples: Generated examples to save
            output_file: Output file path
        """
        # Calculate statistics
        valid_examples = [ex for ex in examples if ex.syntax_valid]
        invalid_examples = [ex for ex in examples if not ex.syntax_valid]

        data = {
            "metadata": {
                "total_examples": len(examples),
                "valid_examples": len(valid_examples),
                "invalid_examples": len(invalid_examples),
                "success_rate": len(valid_examples) / len(examples) if examples else 0,
                "generated_at": datetime.now().isoformat(),
                "model": self.model,
                "extended_thinking": self.use_extended_thinking,
            },
            "examples": [asdict(ex) for ex in examples],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)


def main():
    """Main entry point for creative query generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate creative PrismQL examples")
    parser.add_argument(
        "--seed-file",
        type=str,
        required=True,
        help="Path to seed examples JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/training/creative_generated.json",
        help="Output file path",
    )
    parser.add_argument(
        "--total",
        type=int,
        default=100,
        help="Total examples to generate",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Examples per API call",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-5-20250929",
        help="Model to use",
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Disable extended thinking",
    )

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return 1

    # Create generator
    generator = CreativeQueryGenerator(
        api_key=api_key,
        model=args.model,
        use_extended_thinking=not args.no_thinking,
    )

    # Generate dataset
    print(f"Generating {args.total} creative examples...")
    print(f"Model: {args.model}")
    print(f"Extended thinking: {not args.no_thinking}")
    print()

    examples = generator.generate_dataset(
        seed_file=args.seed_file,
        total_examples=args.total,
        batch_size=args.batch_size,
        output_file=args.output,
    )

    # Print summary
    valid = [ex for ex in examples if ex.syntax_valid]
    invalid = [ex for ex in examples if not ex.syntax_valid]

    print(f"\n{'='*80}")
    print("GENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total generated: {len(examples)}")
    print(f"✅ Valid: {len(valid)} ({len(valid)/len(examples)*100:.1f}%)")
    print(f"❌ Invalid: {len(invalid)} ({len(invalid)/len(examples)*100:.1f}%)")
    print(f"\nSaved to: {args.output}")

    if invalid:
        print(f"\nInvalid examples:")
        for ex in invalid[:5]:  # Show first 5
            print(f"  - {ex.id}: {ex.validation_errors[0]}")

    return 0


if __name__ == "__main__":
    exit(main())
