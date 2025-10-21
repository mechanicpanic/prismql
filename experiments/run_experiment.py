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
)
from experiments.analyze import (
    analyze_results,
    compare_models,
    compare_strategies,
    print_detailed_analysis,
    print_summary,
)
from experiments.test_cases import get_test_cases_by_difficulty

# Available models
MODELS = {
    "sonnet-4.5": "claude-sonnet-4-5-20250929",
    "opus-4.1": "claude-opus-4-20250514",
    "haiku-4.5": "claude-haiku-4-5-20250929",
}

STRATEGIES = {
    "zero_shot": ZERO_SHOT_STRATEGY,
    "few_shot": FEW_SHOT_STRATEGY,
    "with_reference": WITH_REFERENCE_STRATEGY,
    "self_correcting": SELF_CORRECTING_STRATEGY,
}


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

    harness = ExperimentHarness(api_key=api_key)

    # Just 5 easy test cases
    test_cases = get_test_cases_by_difficulty("easy")[:5]

    results = harness.run_experiment(
        models=[MODELS["sonnet-4.5"]],
        test_cases=test_cases,
        prompt_strategies=[ZERO_SHOT_STRATEGY],
        rate_limit_delay=0.5,
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quick_test_{timestamp}.json"
    harness.save_results(results, filename)

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

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    harness = ExperimentHarness(api_key=api_key)

    results = harness.run_experiment(
        models=list(MODELS.values()),
        test_cases=ALL_TEST_CASES,
        prompt_strategies=ALL_STRATEGIES,
        rate_limit_delay=1.0,
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"full_experiment_{timestamp}.json"
    harness.save_results(results, filename)

    print(f"\n\nResults saved to: {filename}")
    print(
        "Run analysis with: python experiments/run_experiment.py --analyze {filename}"
    )


def run_custom_experiment(model_names, strategy_names, test_case_filter):
    """Run custom experiment with specified parameters."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Resolve models
    models = [MODELS[name] for name in model_names if name in MODELS]
    if not models:
        print(f"ERROR: No valid models. Available: {list(MODELS.keys())}")
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
    print(f"  Models: {[m.split('-')[-1] for m in models]}")
    print(f"  Strategies: {[s.name for s in strategies]}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  Total API calls: {len(models) * len(strategies) * len(test_cases)}")
    print()

    harness = ExperimentHarness(api_key=api_key)

    results = harness.run_experiment(
        models=models,
        test_cases=test_cases,
        prompt_strategies=strategies,
        rate_limit_delay=1.0,
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"custom_experiment_{timestamp}.json"
    harness.save_results(results, filename)

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
