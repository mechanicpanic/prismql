"""
Generate training data for fine-tuning small models on PrismQL query generation.

This script creates synthetic training examples by:
1. Using test cases as templates
2. Generating variations with different users, dictionaries, time windows
3. Creating reasoning chains (CoT) for each example
4. Formatting for LoRA fine-tuning (Alpaca, ShareGPT, etc.)
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
import random

from test_cases import ALL_TEST_CASES, get_all_required_dictionaries


@dataclass
class TrainingExample:
    """A single training example for fine-tuning."""

    instruction: str  # System prompt + task description
    input: str  # Natural language request
    output: str  # PrismQL query
    reasoning: str | None = None  # Chain of thought (optional)
    metadata: dict[str, Any] | None = None  # Test case info, difficulty, etc.


class PrismQLTrainingDataGenerator:
    """Generate training data for PrismQL query generation."""

    def __init__(self, system_prompt: str | None = None):
        """
        Initialize generator.

        Args:
            system_prompt: Custom system prompt (uses default if None)
        """
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.dictionaries = get_all_required_dictionaries()

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for PrismQL generation."""
        return """You are a PrismQL expert. PrismQL is a query language for pattern matching in conversational data.

Key operators:
- FROM: from(user) - filter by user
- CONTAINS: contains(dict) - messages containing words from dictionary
- IS_QUESTION: is_question() - detect questions
- BOOLEAN: AND, OR, NOT - combine conditions
- INWINDOW N: messages within N positions of each other
- DURING TIME: messages within TIME of each other (e.g., DURING 1 hour)
- FOLLOWED_BY: sequential patterns (A FOLLOWED_BY B INWINDOW N)
- PATTERN VARIABLES: $user, $person - match same value across restrictions
- QUANTIFIERS: {N}, {N,}, {N,M} - repetition patterns

Convert natural language requests into valid PrismQL queries."""

    def generate_from_test_case(
        self, test_case: Any, include_reasoning: bool = True
    ) -> TrainingExample:
        """
        Generate training example from a test case.

        Args:
            test_case: TestCase object
            include_reasoning: Include chain-of-thought reasoning

        Returns:
            TrainingExample
        """
        instruction = self.system_prompt
        input_text = test_case.description
        output = test_case.ground_truth_query

        # Generate reasoning chain if requested
        reasoning = None
        if include_reasoning:
            reasoning = self._generate_reasoning(test_case)

        metadata = {
            "test_case_id": test_case.id,
            "category": test_case.category,
            "difficulty": test_case.difficulty,
            "required_dictionaries": list(test_case.required_dictionaries.keys()),
        }

        return TrainingExample(
            instruction=instruction,
            input=input_text,
            output=output,
            reasoning=reasoning,
            metadata=metadata,
        )

    def _generate_reasoning(self, test_case: Any) -> str:
        """
        Generate chain-of-thought reasoning for a test case.

        This explains the thought process behind the query.
        """
        reasoning_parts = []

        # Step 1: Identify intent
        if "find" in test_case.description.lower():
            reasoning_parts.append(
                f"1. Intent: User wants to find/search for specific patterns"
            )
        elif "count" in test_case.description.lower():
            reasoning_parts.append(f"1. Intent: User wants to count/aggregate results")

        # Step 2: Identify key components
        components = []
        query = test_case.ground_truth_query

        if "from(" in query.lower():
            components.append("user filtering")
        if "contains(" in query.lower():
            components.append("keyword/dictionary matching")
        if "is_question()" in query.lower():
            components.append("question detection")
        if "inwindow" in query.lower():
            components.append("positional window constraints")
        if "during" in query.lower():
            components.append("temporal window constraints")
        if "followed_by" in query.lower():
            components.append("sequential ordering")
        if "$" in query:
            components.append("pattern variables")
        if "{" in query:
            components.append("quantifiers")

        if components:
            reasoning_parts.append(f"2. Components needed: {', '.join(components)}")

        # Step 3: Operator selection
        if "inwindow" in query.lower() and "during" not in query.lower():
            reasoning_parts.append(
                "3. Window type: INWINDOW (positional) - measures message distance"
            )
        elif "during" in query.lower():
            reasoning_parts.append(
                "3. Window type: DURING (temporal) - uses actual timestamps"
            )

        if "followed_by" in query.lower():
            reasoning_parts.append("4. Ordering: FOLLOWED_BY creates sequential pairs")
        elif "," in query and "inwindow" in query.lower():
            reasoning_parts.append(
                "4. Ordering: Comma-separated restrictions are unordered within window"
            )

        # Step 4: Construction
        reasoning_parts.append(f"5. Final query: {query}")

        return "\n".join(reasoning_parts)

    def generate_variations(
        self, test_case: Any, num_variations: int = 3
    ) -> list[TrainingExample]:
        """
        Generate variations of a test case with different parameters.

        Args:
            test_case: Base test case
            num_variations: Number of variations to generate

        Returns:
            List of TrainingExample variations
        """
        variations = []

        # Variation strategies based on category
        if test_case.category in ["basic_filtering", "boolean_operations"]:
            variations.extend(self._vary_users(test_case, num_variations))
        elif test_case.category in ["window_patterns", "temporal_patterns"]:
            variations.extend(self._vary_windows(test_case, num_variations))
        elif test_case.category == "pattern_variables":
            variations.extend(self._vary_variable_names(test_case, num_variations))

        return variations[:num_variations]

    def _vary_users(self, test_case: Any, count: int) -> list[TrainingExample]:
        """Generate variations with different user names."""
        variations = []
        user_names = ["alice", "bob", "charlie", "david", "emma", "frank"]

        for i in range(count):
            # Replace user names in description and query
            new_desc = test_case.description
            new_query = test_case.ground_truth_query

            # Simple replacement (could be more sophisticated)
            for old_user in ["alice", "bob", "charlie"]:
                if old_user in new_query.lower():
                    new_user = random.choice(
                        [u for u in user_names if u != old_user]
                    )
                    new_desc = new_desc.replace(old_user, new_user)
                    new_query = new_query.replace(f"from({old_user})", f"from({new_user})")
                    break

            example = TrainingExample(
                instruction=self.system_prompt,
                input=new_desc,
                output=new_query,
                reasoning=self._generate_reasoning(test_case),
                metadata={
                    "base_test_case": test_case.id,
                    "variation_type": "user_substitution",
                    "variation_index": i,
                },
            )
            variations.append(example)

        return variations

    def _vary_windows(self, test_case: Any, count: int) -> list[TrainingExample]:
        """Generate variations with different window sizes."""
        variations = []
        window_sizes = [3, 5, 10, 15, 20]

        for i, window_size in enumerate(window_sizes[:count]):
            new_desc = test_case.description
            new_query = test_case.ground_truth_query

            # Replace window sizes
            import re

            # INWINDOW pattern
            new_query = re.sub(
                r"INWINDOW \d+", f"INWINDOW {window_size}", new_query, flags=re.IGNORECASE
            )
            new_desc = re.sub(r"within \d+ messages", f"within {window_size} messages", new_desc)

            example = TrainingExample(
                instruction=self.system_prompt,
                input=new_desc,
                output=new_query,
                reasoning=self._generate_reasoning(test_case),
                metadata={
                    "base_test_case": test_case.id,
                    "variation_type": "window_size",
                    "variation_index": i,
                    "window_size": window_size,
                },
            )
            variations.append(example)

        return variations

    def _vary_variable_names(self, test_case: Any, count: int) -> list[TrainingExample]:
        """Generate variations with different variable names."""
        variations = []
        var_names = ["$user", "$person", "$author", "$sender", "$participant"]

        for i, var_name in enumerate(var_names[:count]):
            new_query = test_case.ground_truth_query

            # Replace $user with new variable name
            if "$user" in new_query:
                new_query = new_query.replace("$user", var_name)

            example = TrainingExample(
                instruction=self.system_prompt,
                input=test_case.description,  # Keep description same
                output=new_query,
                reasoning=self._generate_reasoning(test_case),
                metadata={
                    "base_test_case": test_case.id,
                    "variation_type": "variable_name",
                    "variation_index": i,
                },
            )
            variations.append(example)

        return variations

    def generate_all(
        self, include_variations: bool = True, variations_per_case: int = 2
    ) -> list[TrainingExample]:
        """
        Generate training examples from all test cases.

        Args:
            include_variations: Generate variations for diversity
            variations_per_case: Number of variations per test case

        Returns:
            List of all training examples
        """
        examples = []

        for test_case in ALL_TEST_CASES:
            # Add base example
            examples.append(self.generate_from_test_case(test_case, include_reasoning=True))

            # Add variations if requested
            if include_variations:
                variations = self.generate_variations(test_case, variations_per_case)
                examples.extend(variations)

        return examples

    def export_alpaca_format(
        self, examples: list[TrainingExample], output_path: Path
    ) -> None:
        """
        Export in Alpaca format for LoRA fine-tuning.

        Format: {"instruction": str, "input": str, "output": str}
        """
        alpaca_data = []
        for ex in examples:
            alpaca_data.append(
                {
                    "instruction": ex.instruction,
                    "input": ex.input,
                    "output": ex.output,
                }
            )

        with open(output_path, "w") as f:
            json.dump(alpaca_data, f, indent=2)

        print(f"Exported {len(alpaca_data)} examples to {output_path} (Alpaca format)")

    def export_sharegpt_format(
        self, examples: list[TrainingExample], output_path: Path
    ) -> None:
        """
        Export in ShareGPT format for LoRA fine-tuning.

        Format: {"conversations": [{"from": "human/gpt", "value": str}]}
        """
        sharegpt_data = []
        for ex in examples:
            conversation = {
                "conversations": [
                    {"from": "system", "value": ex.instruction},
                    {"from": "human", "value": ex.input},
                    {"from": "gpt", "value": ex.output},
                ]
            }
            sharegpt_data.append(conversation)

        with open(output_path, "w") as f:
            json.dump(sharegpt_data, f, indent=2)

        print(f"Exported {len(sharegpt_data)} examples to {output_path} (ShareGPT format)")

    def export_with_reasoning(
        self, examples: list[TrainingExample], output_path: Path
    ) -> None:
        """
        Export with chain-of-thought reasoning for reasoning model fine-tuning.

        Uses special tokens: <think>reasoning</think> output
        """
        reasoning_data = []
        for ex in examples:
            if ex.reasoning:
                output_with_reasoning = f"<think>\n{ex.reasoning}\n</think>\n\n{ex.output}"
            else:
                output_with_reasoning = ex.output

            reasoning_data.append(
                {
                    "instruction": ex.instruction,
                    "input": ex.input,
                    "output": output_with_reasoning,
                }
            )

        with open(output_path, "w") as f:
            json.dump(reasoning_data, f, indent=2)

        print(
            f"Exported {len(reasoning_data)} examples with reasoning to {output_path}"
        )


def main():
    """Generate training data for PrismQL fine-tuning."""
    generator = PrismQLTrainingDataGenerator()

    # Generate all examples
    print("Generating training examples...")
    examples = generator.generate_all(include_variations=True, variations_per_case=2)
    print(f"Generated {len(examples)} total examples")

    # Count by category
    from collections import Counter

    categories = Counter(
        ex.metadata.get("category", ex.metadata.get("base_test_case", "unknown").split("_")[0])
        for ex in examples
    )
    print("\nExamples by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Export in different formats
    output_dir = Path("data/training")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\nExporting training data...")
    generator.export_alpaca_format(examples, output_dir / "prismql_alpaca.json")
    generator.export_sharegpt_format(examples, output_dir / "prismql_sharegpt.json")
    generator.export_with_reasoning(examples, output_dir / "prismql_reasoning.json")

    print("\nTraining data generation complete!")
    print(f"\nNext steps:")
    print("1. Review generated examples in data/training/")
    print("2. Choose format based on your training framework:")
    print("   - Alpaca: Standard instruction tuning")
    print("   - ShareGPT: Chat-based fine-tuning")
    print("   - Reasoning: Chain-of-thought training")
    print("3. Use with LoRA fine-tuning (see LORA_FINETUNING_GUIDE.md)")


if __name__ == "__main__":
    main()
