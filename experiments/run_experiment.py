"""
Main script to run LLM query generation experiments.

Usage:
    # Run full experiment (all models, all strategies, all test cases)
    python experiments/run_experiment.py --full

    # Run quick test (one model, one strategy, subset of tests)
    python experiments/run_experiment.py --quick

    # Custom run
    python experiments/run_experiment.py \\
        --models claude-sonnet-4-5-20250929 claude-opus-4-20250514 \\
        --strategies zero_shot few_shot \\
        --test-cases all

    # Analyze existing results
    python experiments/run_experiment.py --analyze results/experiment_2025_01_15.json
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments import (
    ALL_STRATEGIES,
    ALL_TEST_CASES,
    FEW_SHOT_STRATEGY,
    SELF_CORRECTING_STRATEGY,
    WITH_REFERENCE_STRATEGY,
    ZERO_SHOT_STRATEGY,
    ExperimentHarness,
    create_provider,
)
from experiments.analyze import (
    analyze_results,
    compare_models,
    compare_strategies,
    print_detailed_analysis,
    print_summary,
)
from experiments.providers import LLMProvider
from experiments.test_cases import get_test_cases_by_difficulty

# Available models: (provider_type, model_id, friendly_name)
MODELS = {
    # Anthropic models
    "sonnet-4.5": ("anthropic", "claude-sonnet-4-5-20250929"),
    "sonnet-4.5-thinking": (
        "anthropic",
        "claude-sonnet-4-5-20250929",
    ),  # Extended thinking
    "opus-4.1": ("anthropic", "claude-opus-4-1-20250805"),
    "opus-4.1-thinking": ("anthropic", "claude-opus-4-1-20250805"),  # Extended thinking
    "haiku-4.5": ("anthropic", "claude-haiku-4-5-20251001"),
    # MiniMax models (Anthropic-compatible API)
    "minimax-m2": ("minimax", "MiniMax-M2"),
    "minimax-m2-thinking": ("minimax", "MiniMax-M2"),  # Extended thinking
    "minimax-m2-stable": ("minimax", "MiniMax-M2-Stable"),
    "minimax-m2-stable-thinking": ("minimax", "MiniMax-M2-Stable"),  # Extended thinking
    # OpenAI models
    "gpt-4": ("openai", "gpt-4"),
    "gpt-4-turbo": ("openai", "gpt-4-turbo-preview"),
    "gpt-3.5": ("openai", "gpt-3.5-turbo"),
    # OpenAI reasoning models
    "gpt-5": ("openai", "gpt-5"),
    "gpt-5-preview": ("openai", "gpt-5-preview"),
    # OpenRouter models (Claude/OpenAI via OpenRouter)
    "or-sonnet-4": ("openrouter", "anthropic/claude-sonnet-4"),
    "or-gpt-4": ("openrouter", "openai/gpt-4"),
    # OpenRouter reasoning models
    "or-gpt-5": ("openrouter", "openai/gpt-5"),
    "or-gpt-5-preview": ("openrouter", "openai/gpt-5-preview"),
    "or-gpt-5-pro": ("openrouter", "openai/gpt-5-pro"),
    "or-gpt-5-thinking": ("openrouter", "openai/gpt-5-thinking"),
    "or-o3-pro": ("openrouter", "openai/o3-pro"),
    "or-deepseek-r1": ("openrouter", "deepseek/deepseek-r1-0528:free"),
    "or-deepseek-r1-qwen3-8b": (
        "openrouter",
        "deepseek/deepseek-r1-0528-qwen3-8b:free",
    ),
    "or-gemini-2.5-pro": ("openrouter", "google/gemini-2.5-pro"),
    "or-deepseek-v3.2": ("openrouter", "deepseek/deepseek-v3.2-exp"),
    "or-kimi-k2-thinking": ("openrouter", "moonshotai/kimi-k2-thinking"),
    # OpenRouter models (Other comprehensive models)
    "or-glm-4-air": ("openrouter", "z-ai/glm-4.5-air:free"),
    "or-qwen-coder-72b": ("openrouter", "qwen/qwen-3-coder-72b"),
    "or-mistral-medium": ("openrouter", "mistralai/mistral-medium-3-1"),
    "or-mixtral-8x22b": ("openrouter", "mistralai/mixtral-8x22b-instruct"),
    "or-llama-4-maverick": ("openrouter", "meta-llama/llama-4-maverick:free"),
    "or-llama-3.3-8b": ("openrouter", "meta-llama/llama-3.3-8b-instruct:free"),
    "or-ministral-8b": ("openrouter", "mistralai/ministral-8b"),
}

STRATEGIES = {
    "zero_shot": ZERO_SHOT_STRATEGY,
    "few_shot": FEW_SHOT_STRATEGY,
    "with_reference": WITH_REFERENCE_STRATEGY,
    "self_correcting": SELF_CORRECTING_STRATEGY,
}


def create_provider_for_model(model_key: str, api_key: str) -> LLMProvider:
    """
    Create a provider for the given model key with appropriate settings.

    Args:
        model_key: Key from MODELS dict (e.g., "sonnet-4.5-thinking")
        api_key: API key for the provider

    Returns:
        Configured LLMProvider instance
    """
    provider_type, model_id = MODELS[model_key]

    # Configure reasoning/thinking for supported models
    kwargs = {}

    # Anthropic extended thinking
    if model_key in ["sonnet-4.5-thinking", "opus-4.1-thinking"]:
        kwargs["extended_thinking"] = True

    # MiniMax extended thinking
    if model_key in ["minimax-m2-thinking", "minimax-m2-stable-thinking"]:
        kwargs["extended_thinking"] = True

    # OpenRouter reasoning models
    reasoning_keys = [
        "or-gpt-5",
        "or-gpt-5-preview",
        "or-gpt-5-pro",
        "or-gpt-5-thinking",
        "or-o3-pro",
        "or-deepseek-r1",
        "or-deepseek-r1-qwen3-8b",
        "or-deepseek-v3.2",
        "or-gemini-2.5-pro",
        "or-kimi-k2-thinking",
    ]
    if model_key in reasoning_keys:
        kwargs["enable_reasoning"] = True

    return create_provider(provider_type, model_id, api_key, **kwargs)


def run_quick_test():
    """Run a quick test with minimal API calls."""
    print("Running QUICK TEST...")
    print("Model: Sonnet 4.5")
    print("Strategy: Zero-shot")
    print("Test cases: 5 easy cases")
    print()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    harness = ExperimentHarness()

    # Create provider (use create_provider_for_model for correct settings)
    provider = create_provider_for_model("sonnet-4.5", api_key)

    # Just 5 easy test cases
    test_cases = get_test_cases_by_difficulty("easy")[:5]

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_test_{timestamp}.json"

    results = harness.run_experiment(
        providers=[provider],
        test_cases=test_cases,
        prompt_strategies=[ZERO_SHOT_STRATEGY],
        # No rate limiting for paid models (default 0.0)
        free_tier_delay=5.0,
        output_file=filename,  # Save incrementally!
    )

    # Analyze
    tc_map = {
        tc.id: {"difficulty": tc.difficulty, "category": tc.category}
        for tc in ALL_TEST_CASES
    }
    metrics = analyze_results({"results": [r.__dict__ for r in results]}, tc_map)

    print_summary(metrics)
    for m in metrics.values():
        print_detailed_analysis(m)


def run_full_experiment():
    """Run the complete experiment (WARNING: Many API calls!)."""
    print("=" * 80)
    print("WARNING: This will make MANY API calls!")
    print("=" * 80)
    print(f"Models: {len(MODELS)}")
    print(f"Strategies: {len(ALL_STRATEGIES)}")
    print(f"Test cases: {len(ALL_TEST_CASES)}")
    print(f"Total API calls: {len(MODELS) * len(ALL_STRATEGIES) * len(ALL_TEST_CASES)}")
    print()

    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Aborted.")
        return

    # Get API keys for all provider types
    api_keys = {
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "openrouter": os.getenv("OPENROUTER_API_KEY"),
        "minimax": os.getenv("MINIMAX_API_KEY"),
    }

    harness = ExperimentHarness()

    # Create providers for all models
    providers = []
    for name, (provider_type, _) in MODELS.items():
        api_key = api_keys.get(provider_type)
        if api_key:
            # Use create_provider_for_model to get correct thinking/reasoning settings
            providers.append(create_provider_for_model(name, api_key))
        else:
            print(f"Skipping {name}: {provider_type.upper()}_API_KEY not set")

    if not providers:
        print("ERROR: No API keys set. Set at least one of:")
        print("  - ANTHROPIC_API_KEY")
        print("  - OPENAI_API_KEY")
        print("  - OPENROUTER_API_KEY")
        print("  - MINIMAX_API_KEY")
        sys.exit(1)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"full_experiment_{timestamp}.json"

    _ = harness.run_experiment(
        providers=providers,
        test_cases=ALL_TEST_CASES,
        prompt_strategies=ALL_STRATEGIES,
        # No rate limiting for paid models (default 0.0)
        free_tier_delay=10.0,
        output_file=filename,  # Save incrementally!
    )

    print(f"\n\nResults saved to: experiments/results/{filename}")
    print(
        f"Run analysis with: python experiments/run_experiment.py --analyze experiments/results/{filename}"
    )


def run_custom_experiment(model_names, strategy_names, test_case_filter):
    """Run custom experiment with specified parameters."""
    # Get API keys for all provider types
    api_keys = {
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "openai": os.getenv("OPENAI_API_KEY"),
        "openrouter": os.getenv("OPENROUTER_API_KEY"),
        "minimax": os.getenv("MINIMAX_API_KEY"),
    }

    # Resolve models and create providers
    providers = []
    for name in model_names:
        if name not in MODELS:
            print(f"WARNING: Unknown model '{name}', skipping")
            continue

        provider_type, _ = MODELS[name]
        api_key = api_keys.get(provider_type)
        if not api_key:
            print(f"Skipping {name}: {provider_type.upper()}_API_KEY not set")
            continue

        # Use create_provider_for_model to get correct thinking/reasoning settings
        providers.append(create_provider_for_model(name, api_key))

    if not providers:
        print(f"ERROR: No valid providers. Available models: {list(MODELS.keys())}")
        print(
            "Set at least one API key: ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY, or MINIMAX_API_KEY"
        )
        sys.exit(1)

    # Resolve strategies
    strategies = [STRATEGIES[name] for name in strategy_names if name in STRATEGIES]
    if not strategies:
        print(f"ERROR: No valid strategies. Available: {list(STRATEGIES.keys())}")
        sys.exit(1)

    # Resolve test cases
    if test_case_filter == "all":
        test_cases = ALL_TEST_CASES
    elif test_case_filter in ["easy", "medium", "hard"]:
        test_cases = get_test_cases_by_difficulty(test_case_filter)
    else:
        print(f"ERROR: Invalid test-case filter: {test_case_filter}")
        sys.exit(1)

    print("Running experiment:")
    print(f"  Providers: {[p.get_model_name() for p in providers]}")
    print(f"  Strategies: {[s.name for s in strategies]}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  Total API calls: {len(providers) * len(strategies) * len(test_cases)}")
    print()

    harness = ExperimentHarness()

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_experiment_{timestamp}.json"

    results = harness.run_experiment(
        providers=providers,
        test_cases=test_cases,
        prompt_strategies=strategies,
        # No rate limiting for paid models (default 0.0)
        free_tier_delay=10.0,
        output_file=filename,  # Save incrementally!
    )

    # Analyze
    tc_map = {
        tc.id: {"difficulty": tc.difficulty, "category": tc.category}
        for tc in ALL_TEST_CASES
    }
    metrics = analyze_results({"results": [r.__dict__ for r in results]}, tc_map)

    print_summary(metrics)


def analyze_existing_results(filename):
    """Analyze already-run experiment results."""
    from experiments.analyze import load_results

    data = load_results(filename)

    tc_map = {
        tc.id: {"difficulty": tc.difficulty, "category": tc.category}
        for tc in ALL_TEST_CASES
    }
    metrics = analyze_results(data, tc_map)

    print_summary(metrics)

    for m in metrics.values():
        print_detailed_analysis(m)

    # Comparisons
    if metrics:
        compare_models(metrics, "zero_shot")
        first_model = list(metrics.values())[0].model
        compare_strategies(metrics, first_model)


def main():
    parser = argparse.ArgumentParser(description="Run PrismQL LLM experiments")

    # Modes
    parser.add_argument(
        "--quick", action="store_true", help="Run quick test (5 easy cases)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full experiment (WARNING: many API calls)",
    )
    parser.add_argument("--analyze", type=str, help="Analyze existing results file")

    # Custom experiment options
    parser.add_argument(
        "--models",
        nargs="+",
        choices=list(MODELS.keys()),
        help=f"Models to test. Available: {list(MODELS.keys())}",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        choices=list(STRATEGIES.keys()),
        help=f"Strategies to test. Available: {list(STRATEGIES.keys())}",
    )
    parser.add_argument(
        "--test-cases",
        type=str,
        choices=["all", "easy", "medium", "hard"],
        default="all",
        help="Which test cases to run",
    )

    args = parser.parse_args()

    # Determine which mode to run
    if args.analyze:
        analyze_existing_results(args.analyze)
    elif args.quick:
        run_quick_test()
    elif args.full:
        run_full_experiment()
    elif args.models and args.strategies:
        run_custom_experiment(args.models, args.strategies, args.test_cases)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  # Quick test")
        print("  python experiments/run_experiment.py --quick")
        print()
        print("  # Test Sonnet vs Opus on zero-shot")
        print(
            "  python experiments/run_experiment.py --models sonnet-4.5 opus-4.1 --strategies zero_shot --test-cases easy"
        )
        print()
        print("  # Analyze results")
        print(
            "  python experiments/run_experiment.py --analyze results/experiment_20250115.json"
        )


if __name__ == "__main__":
    main()
