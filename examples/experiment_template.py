"""
PrismQL Experiment Template

Copy this file and modify it for your experiment.
This template shows how to:
1. Load data from various sources
2. Define custom dictionaries
3. Run multiple query patterns
4. Collect and analyze results
"""

from typing import Any

from prismql import PrismQLEngine
from prismql.backends import RustMemoryBackend  # or MemoryBackend for smaller datasets

# =============================================================================
# 1. LOAD YOUR DATA
# =============================================================================


def load_data_from_dicts() -> list[dict[str, Any]]:
    """Load data from Python dicts (for quick testing)."""
    return [
        {"id": 1, "user": "alice", "text": "Hello everyone", "timestamp": "2024-01-01"},
        {"id": 2, "user": "bob", "text": "Hi alice", "timestamp": "2024-01-01"},
        {"id": 3, "user": "charlie", "text": "Hey there", "timestamp": "2024-01-01"},
        # Add more messages...
    ]


def load_data_from_csv(filepath: str) -> list[dict[str, Any]]:
    """Load data from CSV file."""
    import csv

    messages = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            messages.append(
                {
                    "id": int(row["id"]),
                    "user": row["user"],
                    "text": row["text"],
                    # Add other fields as needed
                }
            )
    return messages


def load_data_from_json(filepath: str) -> list[dict[str, Any]]:
    """Load data from JSON file."""
    import json

    with open(filepath) as f:
        return json.load(f)


# =============================================================================
# 2. DEFINE YOUR DICTIONARIES
# =============================================================================


def get_experiment_dictionaries() -> dict[str, list[str]]:
    """
    Define domain-specific word groups for your experiment.

    Customize these based on your research domain.
    """
    return {
        # Communication patterns
        "greetings": ["hello", "hi", "hey", "greetings", "good morning"],
        "farewells": ["bye", "goodbye", "see you", "farewell"],
        # Problem-solving patterns
        "problems": ["error", "issue", "bug", "problem", "broken", "not working"],
        "solutions": ["fixed", "solved", "resolved", "working", "try", "use"],
        "questions": ["how", "what", "why", "when", "where", "can you"],
        # Sentiment
        "positive": ["great", "thanks", "excellent", "good", "happy"],
        "negative": ["bad", "terrible", "awful", "frustrated", "angry"],
        # Add your domain-specific dictionaries here
        # "technical_terms": [...],
        # "domain_keywords": [...],
    }


# =============================================================================
# 3. DEFINE YOUR QUERY PATTERNS
# =============================================================================


def get_experiment_queries() -> dict[str, str]:
    """
    Define the patterns you want to find in your data.

    Each query should test a specific hypothesis or research question.
    """
    return {
        # Basic patterns
        "user_messages": "SELECT from(alice)",
        "greeting_messages": "SELECT contains(greetings)",
        # Interaction patterns
        "question_answer": """
            SELECT
                contains(questions)
                FOLLOWED_BY from(support)
            WITHIN 5
        """,
        "problem_resolution": """
            SELECT
                contains(problems),
                contains(solutions)
            INWIN 10
        """,
        # User behavior
        "engaged_users": "SELECT from(alice){3} INWIN 20",
        "question_clusters": "SELECT contains(questions){2} INWIN 15",
        # Sequential patterns (chained FOLLOWED_BY)
        "support_workflow": """
            SELECT
                (from(user) AND contains(problems))
                FOLLOWED_BY from(support)
                WITHIN 5
        """,
        # Complex patterns
        "problem_not_resolved": """
            SELECT
                from(user) AND contains(problems)
                NOT_FOLLOWED_BY contains(solutions)
            WITHIN 20
        """,
        # Add your custom patterns here
    }


# =============================================================================
# 4. COLLECT AND ANALYZE RESULTS
# =============================================================================


def analyze_results(
    engine: PrismQLEngine,
    backend: RustMemoryBackend,
    queries: dict[str, str],
) -> dict[str, dict]:
    """
    Run all queries and collect results for analysis.

    Returns a dictionary with query results and statistics.
    """
    results = {}

    for query_name, query_text in queries.items():
        print(f"\nRunning: {query_name}")
        print(f"Query: {query_text.strip()}")

        try:
            # Execute query
            result = engine.execute(query_text)

            # Collect statistics
            stats = {
                "query": query_text.strip(),
                "num_groups": len(result),
                "total_messages": sum(len(group) for group in result),
                "groups": result,
            }

            # Get actual message details
            all_message_ids = [msg_id for group in result for msg_id in group]
            messages = backend.get_documents(all_message_ids)
            stats["messages"] = messages

            results[query_name] = stats

            print(f"  Found: {stats['num_groups']} groups")
            print(f"  Total messages: {stats['total_messages']}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results[query_name] = {"error": str(e)}

    return results


def print_detailed_results(results: dict[str, dict]) -> None:
    """Print detailed results for inspection."""
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    for query_name, stats in results.items():
        print(f"\n{query_name}")
        print("-" * 80)

        if "error" in stats:
            print(f"ERROR: {stats['error']}")
            continue

        print(f"Query: {stats['query']}")
        print(f"Found {stats['num_groups']} groups:")

        # Show first few groups
        for i, group in enumerate(stats["groups"][:3]):
            print(f"\n  Group {i+1}: {group}")

        if len(stats["groups"]) > 3:
            print(f"\n  ... and {len(stats['groups']) - 3} more groups")


def export_results(results: dict[str, dict], output_file: str) -> None:
    """Export results to JSON for further analysis."""
    import json

    # Remove non-serializable objects
    export_data = {}
    for query_name, stats in results.items():
        if "error" in stats:
            export_data[query_name] = stats
        else:
            export_data[query_name] = {
                "query": stats["query"],
                "num_groups": stats["num_groups"],
                "total_messages": stats["total_messages"],
                "groups": stats["groups"],
                # Messages might not be JSON serializable - convert to dicts
                "messages": [dict(msg) for msg in stats["messages"]],
            }

    with open(output_file, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"\n✅ Results exported to {output_file}")


# =============================================================================
# 5. MAIN EXPERIMENT
# =============================================================================


def run_experiment():
    """Run the complete experiment."""
    print("=" * 80)
    print("PrismQL Experiment")
    print("=" * 80)

    # Step 1: Load data
    print("\n1. Loading data...")
    messages = load_data_from_dicts()
    # messages = load_data_from_csv('your_data.csv')
    # messages = load_data_from_json('your_data.json')
    print(f"   Loaded {len(messages)} messages")

    # Step 2: Setup engine
    print("\n2. Setting up PrismQL engine...")
    backend = RustMemoryBackend(messages)  # Use RustMemoryBackend for performance
    dictionaries = get_experiment_dictionaries()
    engine = PrismQLEngine(backend, user_dictionaries=dictionaries)
    print(f"   Initialized with {len(dictionaries)} dictionaries")

    # Step 3: Define queries
    print("\n3. Preparing queries...")
    queries = get_experiment_queries()
    print(f"   Prepared {len(queries)} queries")

    # Step 4: Run analysis
    print("\n4. Running analysis...")
    results = analyze_results(engine, backend, queries)

    # Step 5: Print results
    print_detailed_results(results)

    # Step 6: Export results
    export_results(results, "experiment_results.json")

    print("\n" + "=" * 80)
    print("Experiment complete!")
    print("=" * 80)


if __name__ == "__main__":
    run_experiment()
