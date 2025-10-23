"""
LLM Query Generation Experiment Framework.

Tests Claude models' ability to generate PrismQL queries from natural language.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from prismql import QueryValidator
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine

from .providers import LLMProvider
from .test_cases import TestCase, get_all_required_dictionaries


@dataclass
class PromptStrategy:
    """Different ways to prompt the model."""

    name: str
    system_prompt: str
    include_examples: bool
    include_full_reference: bool
    use_validator_feedback: bool
    max_retries: int = 3


@dataclass
class QueryAttempt:
    """A single attempt at generating a query."""

    query: str
    validation_result: Optional[dict[str, Any]] = None
    retry_number: int = 0
    chain_of_thought: Optional[str] = None  # Reasoning/thinking tokens


@dataclass
class ExperimentResult:
    """Result of testing one model on one test case."""

    test_case_id: str
    model: str
    prompt_strategy: str
    attempts: list[QueryAttempt]
    final_query: Optional[str]
    # Correctness
    syntax_correct: bool
    semantically_correct: Optional[bool]  # None if syntax incorrect
    uses_fluent_syntax: bool
    uses_deprecated_syntax: bool
    # Metrics
    num_attempts: int
    edit_distance_from_ground_truth: int
    time_taken_ms: int
    # Errors
    syntax_errors: list[str]
    semantic_errors: list[str]
    warnings: list[str]
    # Reasoning/thinking
    has_chain_of_thought: bool = False
    final_chain_of_thought: Optional[str] = None


class ExperimentHarness:
    """
    Harness for running LLM query generation experiments.

    Usage:
        harness = ExperimentHarness(api_key=os.getenv("ANTHROPIC_API_KEY"))
        results = harness.run_experiment(
            models=["claude-sonnet-4-5-20250929", "claude-opus-4-20250514"],
            test_cases=ALL_TEST_CASES[:5],
            prompt_strategies=[ZERO_SHOT_STRATEGY]
        )
        harness.save_results(results, "experiment_2025_01_15.json")
    """

    def __init__(
        self,
        validator: Optional[QueryValidator] = None,
        engine: Optional[PrismQLEngine] = None,
    ):
        """
        Initialize experiment harness.

        Args:
            validator: Query validator (default: created with all test dicts)
            engine: Query engine for semantic validation (default: memory backend)
        """

        # Setup validator with all dictionaries from test cases
        all_dicts = get_all_required_dictionaries()
        self.validator = validator or QueryValidator(
            user_dictionaries=all_dicts, check_deprecated=True, check_performance=True
        )

        # Setup engine for semantic validation
        if engine is None:
            # Create simple test data
            test_messages = [
                {"id": i, "text": f"Message {i}", "user": "alice"} for i in range(10)
            ]
            backend = MemoryBackend(test_messages)
            self.engine = PrismQLEngine(backend, user_dictionaries=all_dicts)
        else:
            self.engine = engine

    def generate_query(
        self, test_case: TestCase, provider: LLMProvider, strategy: PromptStrategy
    ) -> list[QueryAttempt]:
        """
        Generate a query for a test case using specified provider and strategy.

        Returns list of attempts (1 if no retries, more if validator feedback enabled).
        """
        attempts: list[QueryAttempt] = []

        # Load reference docs if needed
        if strategy.include_full_reference:
            reference_path = Path(__file__).parent.parent / "QUICK_REFERENCE.md"
            with open(reference_path) as f:
                reference_docs = f.read()
        else:
            reference_docs = None

        # Create user message
        user_message = self._create_user_message(
            test_case, strategy, reference_docs=reference_docs
        )

        validation_feedback = ""

        # Use larger max_tokens for models with extended thinking/reasoning
        # (they need at least 1024 tokens for thinking + response)
        max_tokens = 2000 if provider.supports_extended_thinking() else 500

        for retry in range(strategy.max_retries):
            # Call LLM provider (returns content and optional chain-of-thought)
            response_text, chain_of_thought = provider.generate(
                system_prompt=strategy.system_prompt,
                user_message=user_message + validation_feedback,
                max_tokens=max_tokens,
            )

            # Extract query from response
            query = self._extract_query(response_text)

            # Validate
            validation_result = self.validator.validate(query)

            attempt = QueryAttempt(
                query=query,
                validation_result={
                    "valid": validation_result.valid,
                    "errors": [str(e) for e in validation_result.errors],
                    "warnings": [str(w) for w in validation_result.warnings],
                    "infos": [str(i) for i in validation_result.infos],
                },
                retry_number=retry,
                chain_of_thought=chain_of_thought,
            )
            attempts.append(attempt)

            # If valid or not using feedback, stop
            if validation_result.valid or not strategy.use_validator_feedback:
                break

            # Prepare feedback for next retry
            validation_feedback = f"\n\nYour query had errors:\n{validation_result}\n\nPlease fix the query."

        return attempts

    def _create_user_message(
        self,
        test_case: TestCase,
        strategy: PromptStrategy,
        reference_docs: Optional[str] = None,
    ) -> str:
        """Create the user message for the API call."""
        message = ""

        if reference_docs:
            message += f"# PrismQL Reference\n\n{reference_docs}\n\n"

        if strategy.include_examples:
            message += """# Examples

Basic query:
User: "Find messages from alice"
Query: SELECT from(alice)

Window query:
User: "Find questions followed by answers within 5 messages"
Query: SELECT is_question(), from(support) INWIN 5

Boolean query:
User: "Find questions from alice or bob"
Query: SELECT (from(alice) OR from(bob)) AND is_question()

"""

        # Available dictionaries
        if test_case.required_dictionaries:
            message += "# Available Dictionaries\n\n"
            for dict_name, words in test_case.required_dictionaries.items():
                message += f"- {dict_name}: {words}\n"
            message += "\n"

        # The actual task
        message += f"""# Task

Generate a PrismQL query for the following request:

"{test_case.description}"

Respond with ONLY the PrismQL query, starting with SELECT. Do not include any explanation."""

        return message

    def _extract_query(self, response_text: str) -> str:
        """Extract the query from model's response."""
        # Remove markdown code blocks if present
        text = response_text.strip()

        if "```" in text:
            # Extract from code block
            import re

            match = re.search(r"```(?:prismql|sql)?\s*\n?(.*?)\n?```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        # Find SELECT statement
        if "SELECT" in text:
            # Take everything from SELECT onwards
            start = text.find("SELECT")
            text = text[start:].strip()

            # Remove anything after the query (like explanations)
            # Simple heuristic: query ends at newline if there's text after
            lines = text.split("\n")
            if len(lines) > 1 and not lines[1].strip().startswith(
                (
                    "AND",
                    "OR",
                    "INWIN",
                    "FOLLOWED_BY",
                    "PRECEDED_BY",
                    "NOT_FOLLOWED_BY",
                    "NOT_PRECEDED_BY",
                    "AS",
                    "WITHIN",
                )
            ):
                text = lines[0].strip()

        return text.strip()

    def run_experiment(  # noqa: C901
        self,
        providers: list[LLMProvider],
        test_cases: list[TestCase],
        prompt_strategies: list[PromptStrategy],
        rate_limit_delay: float = 0.0,
        free_tier_delay: float = 5.0,
        output_file: Optional[str] = None,
    ) -> list[ExperimentResult]:
        """
        Run complete experiment across providers, test cases, and strategies.

        Args:
            providers: List of LLMProvider instances
            test_cases: Test cases to evaluate
            prompt_strategies: Different prompting approaches to test
            rate_limit_delay: Seconds to wait between API calls (paid models, default 0)
            free_tier_delay: Seconds to wait between API calls (free-tier models, default 5s)
            output_file: Optional filename to save results incrementally (recommended!)

        Returns:
            List of ExperimentResults
        """
        results: list[ExperimentResult] = []
        total = len(providers) * len(test_cases) * len(prompt_strategies)
        completed = 0

        # Setup output file path if provided
        output_path = None
        if output_file:
            output_dir = Path(__file__).parent / "results"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / output_file

            # Load existing results if file exists (resume support)
            if output_path.exists():
                print(f"Found existing results file: {output_path}")
                print("Loading previous results...")
                try:
                    with open(output_path) as f:
                        data = json.load(f)
                        existing_results = data.get("results", [])
                        # Convert dicts back to ExperimentResult objects
                        for r in existing_results:
                            results.append(ExperimentResult(**r))
                        print(f"Loaded {len(results)} existing results")
                except Exception as e:
                    print(f"Warning: Could not load existing results: {e}")
                    print("Starting fresh...")
                    results = []

        print(f"Starting experiment: {total} total evaluations")
        print(f"Providers: {[p.get_model_name() for p in providers]}")
        print(f"Test cases: {len(test_cases)}")
        print(f"Strategies: {[s.name for s in prompt_strategies]}")
        if output_path:
            print(f"Saving to: {output_path}")
        print()

        for provider in providers:
            model_name = provider.get_model_name()
            for strategy in prompt_strategies:
                for test_case in test_cases:
                    completed += 1
                    print(
                        f"[{completed}/{total}] {model_name} | {strategy.name} | {test_case.id}"
                    )

                    start_time = time.time()

                    try:
                        attempts = self.generate_query(test_case, provider, strategy)
                        final_query = attempts[-1].query if attempts else None

                        # Calculate metrics
                        result = self._calculate_metrics(
                            test_case=test_case,
                            model=model_name,
                            strategy=strategy,
                            attempts=attempts,
                            final_query=final_query,
                            time_taken_ms=int((time.time() - start_time) * 1000),
                        )

                        results.append(result)

                    except Exception as e:
                        print(f"  ERROR: {e}")
                        # Create error result
                        results.append(
                            ExperimentResult(
                                test_case_id=test_case.id,
                                model=model_name,
                                prompt_strategy=strategy.name,
                                attempts=[],
                                final_query=None,
                                syntax_correct=False,
                                semantically_correct=False,
                                uses_fluent_syntax=False,
                                uses_deprecated_syntax=False,
                                num_attempts=0,
                                edit_distance_from_ground_truth=999,
                                time_taken_ms=0,
                                syntax_errors=[str(e)],
                                semantic_errors=[],
                                warnings=[],
                            )
                        )

                    # Save incrementally after each result
                    if output_path:
                        self._save_results_to_file(results, output_path)

                    # Rate limiting (longer delay for free-tier models)
                    delay = (
                        free_tier_delay if provider.is_free_tier() else rate_limit_delay
                    )
                    time.sleep(delay)

        print(f"\nCompleted {len(results)} evaluations")
        return results

    def _calculate_metrics(
        self,
        test_case: TestCase,
        model: str,
        strategy: PromptStrategy,
        attempts: list[QueryAttempt],
        final_query: Optional[str],
        time_taken_ms: int,
    ) -> ExperimentResult:
        """Calculate all metrics for a result."""
        if not final_query or not attempts:
            return ExperimentResult(
                test_case_id=test_case.id,
                model=model,
                prompt_strategy=strategy.name,
                attempts=attempts,
                final_query=final_query,
                syntax_correct=False,
                semantically_correct=False,
                uses_fluent_syntax=False,
                uses_deprecated_syntax=False,
                num_attempts=len(attempts),
                edit_distance_from_ground_truth=999,
                time_taken_ms=time_taken_ms,
                syntax_errors=["No query generated"],
                semantic_errors=[],
                warnings=[],
                has_chain_of_thought=False,
                final_chain_of_thought=None,
            )

        validation = attempts[-1].validation_result

        # Syntax correctness
        syntax_correct = validation["valid"]

        # Extract errors/warnings
        syntax_errors = validation["errors"]
        warnings = validation["warnings"]

        # Check for deprecated syntax
        uses_deprecated = any("deprecated" in w.lower() for w in validation["warnings"])
        uses_fluent = not uses_deprecated

        # Semantic correctness (only if syntax correct)
        semantically_correct = None
        semantic_errors = []

        if syntax_correct:
            # TODO: Actually execute and compare results
            # For now, just compare query strings
            semantically_correct = self._queries_equivalent(
                final_query, test_case.ground_truth_query
            )
            if not semantically_correct:
                semantic_errors.append(
                    f"Query differs from ground truth: {test_case.ground_truth_query}"
                )

        # Edit distance
        edit_dist = self._levenshtein_distance(
            final_query.lower(), test_case.ground_truth_query.lower()
        )

        # Check if any attempt has chain-of-thought
        has_cot = any(attempt.chain_of_thought for attempt in attempts)
        final_cot = attempts[-1].chain_of_thought if attempts else None

        return ExperimentResult(
            test_case_id=test_case.id,
            model=model,
            prompt_strategy=strategy.name,
            attempts=attempts,
            final_query=final_query,
            syntax_correct=syntax_correct,
            semantically_correct=semantically_correct,
            uses_fluent_syntax=uses_fluent,
            uses_deprecated_syntax=uses_deprecated,
            num_attempts=len(attempts),
            edit_distance_from_ground_truth=edit_dist,
            time_taken_ms=time_taken_ms,
            syntax_errors=syntax_errors,
            semantic_errors=semantic_errors,
            warnings=warnings,
            has_chain_of_thought=has_cot,
            final_chain_of_thought=final_cot,
        )

    def _queries_equivalent(self, query1: str, query2: str) -> bool:
        """
        Check if two queries are semantically equivalent.

        Handles variable renaming: $asker vs $speaker are equivalent.
        """
        import re

        def normalize_variables(q: str) -> str:
            """Replace pattern variables with canonical names based on order of appearance."""
            # Find all pattern variables ($variable)
            variables = re.findall(r"\$\w+", q)

            # Create mapping: first unique var -> $var0, second -> $var1, etc.
            var_mapping = {}
            var_counter = 0

            for var in variables:
                if var not in var_mapping:
                    var_mapping[var] = f"$var{var_counter}"
                    var_counter += 1

            # Replace variables with canonical names
            result = q
            for original, canonical in var_mapping.items():
                result = result.replace(original, canonical)

            return result

        def normalize(q: str) -> str:
            # Normalize whitespace and case
            normalized = re.sub(r"\s+", " ", q.strip().lower())
            # Normalize variable names
            return normalize_variables(normalized)

        return normalize(query1) == normalize(query2)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # j+1 instead of j since previous_row and current_row are one character longer than s2
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _save_results_to_file(
        self, results: list[ExperimentResult], output_path: Path
    ) -> None:
        """Internal method to save results to file (used for incremental saves)."""
        # Convert to dict for JSON serialization
        data = {
            "timestamp": datetime.now().isoformat(),
            "num_results": len(results),
            "results": [asdict(r) for r in results],
        }

        # Write atomically (write to temp file, then rename)
        temp_path = output_path.with_suffix(".tmp")
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)

        # Atomic rename (safer than direct write)
        temp_path.replace(output_path)

    def save_results(self, results: list[ExperimentResult], filename: str) -> None:
        """Save experiment results to JSON file."""
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / filename

        self._save_results_to_file(results, output_path)
        print(f"Results saved to {output_path}")


# =============================================================================
# PROMPT STRATEGIES
# =============================================================================

# Load QUICK_REFERENCE.md for zero-shot prompt
_quick_ref_path = Path(__file__).parent.parent / "QUICK_REFERENCE.md"
with open(_quick_ref_path) as f:
    _QUICK_REFERENCE = f.read()

ZERO_SHOT_STRATEGY = PromptStrategy(
    name="zero_shot",
    system_prompt=f"""You are an expert at writing PrismQL queries. Use the reference documentation below to generate accurate queries.

{_QUICK_REFERENCE}

IMPORTANT: Respond with ONLY the PrismQL query, starting with SELECT. Do not include explanations, markdown code blocks, or any other text.""",
    include_examples=False,
    include_full_reference=False,
    use_validator_feedback=False,
)

FEW_SHOT_STRATEGY = PromptStrategy(
    name="few_shot",
    system_prompt=ZERO_SHOT_STRATEGY.system_prompt,
    include_examples=True,
    include_full_reference=False,
    use_validator_feedback=False,
)

WITH_REFERENCE_STRATEGY = PromptStrategy(
    name="with_reference",
    system_prompt="You are an expert at writing PrismQL queries. Use the provided reference documentation to generate accurate queries.",
    include_examples=False,
    include_full_reference=True,
    use_validator_feedback=False,
)

SELF_CORRECTING_STRATEGY = PromptStrategy(
    name="self_correcting",
    system_prompt=ZERO_SHOT_STRATEGY.system_prompt,
    include_examples=True,
    include_full_reference=False,
    use_validator_feedback=True,
    max_retries=3,
)

ALL_STRATEGIES = [
    ZERO_SHOT_STRATEGY,
    FEW_SHOT_STRATEGY,
    WITH_REFERENCE_STRATEGY,
    SELF_CORRECTING_STRATEGY,
]
