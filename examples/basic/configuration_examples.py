"""
Configuration Examples for PrismQL

This file demonstrates various configuration patterns for different
use cases and backend combinations.
"""

from prismql import BackendFactory, PrismQLEngine


def example_memory_only():
    """Simple in-memory configuration for testing or small datasets."""

    config = {
        "search_backend": {
            "type": "memory",
            "documents": [
                {
                    "id": 1,
                    "text": "Hello world",
                    "user": "alice",
                    "timestamp": "2024-01-01T10:00:00",
                },
                {
                    "id": 2,
                    "text": "How are you?",
                    "user": "bob",
                    "timestamp": "2024-01-01T10:01:00",
                },
                {
                    "id": 3,
                    "text": "I'm doing great!",
                    "user": "alice",
                    "timestamp": "2024-01-01T10:02:00",
                },
                {
                    "id": 4,
                    "text": "What's the weather like?",
                    "user": "charlie",
                    "timestamp": "2024-01-01T10:03:00",
                },
            ],
            "id_field": "id",
        },
        "user_dictionaries": {
            "greetings": ["hello", "hi", "hey"],
            "weather": ["weather", "rain", "sunny", "cloudy"],
        },
    }

    engine = PrismQLEngine.from_config(config)

    # Test queries
    print("Memory-only configuration:")
    print(f"  Users: {engine.execute('SELECT from(alice)')}")
    print(f"  Greetings: {engine.execute('SELECT contains(greetings)')}")
    print(f"  Questions: {engine.execute('SELECT is_question()')}")

    return engine


def example_spacy_nlp():
    """Configuration with spaCy NLP processing."""

    # Note: This requires spaCy installation
    # import spacy
    # nlp = spacy.load("en_core_web_sm")

    config = {
        "search_backend": {
            "type": "memory",
            "documents": [
                {
                    "id": 1,
                    "text": "John Doe visited New York last Tuesday",
                    "user": "reporter",
                },
                {
                    "id": 2,
                    "text": "Apple Inc. announced new products",
                    "user": "tech_news",
                },
                {"id": 3, "text": "The meeting is scheduled for 3pm", "user": "admin"},
            ],
        },
        "nlp_backend": {
            "type": "spacy",
            "model": "en_core_web_sm",  # Or pass loaded nlp object
            "entity_mappings": {
                # Map spaCy labels to your preferred labels
                "PERSON": "PERSON",
                "GPE": "LOCATION",
                "ORG": "ORGANIZATION",
                "DATE": "DATE",
                "TIME": "TIME",
                "CARDINAL": "NUMBER",
            },
            "question_patterns": [
                r"\\?$",  # Ends with ?
                r"^(what|who|when|where|why|how|which)\\b",  # Question words
                r"^(can|could|would|should|do|does|did)\\b",  # Auxiliary verbs
            ],
            "batch_size": 50,
        },
    }

    print("spaCy NLP configuration:")
    print(f"  Model: {config['nlp_backend']['model']}")
    print(f"  Entity mappings: {list(config['nlp_backend']['entity_mappings'].keys())}")

    # Uncomment when you have spaCy installed:
    # engine = PrismQLEngine.from_config(config)
    # print(f"  Entity extraction test: {engine.nlp_backend.extract_entities('John lives in Paris')}")
    # return engine


def example_precomputed_indexes():
    """Configuration using precomputed indexes for performance."""

    config = {
        "search_backend": {
            "type": "memory",
            "documents": [
                {"id": 1, "text": "Hello John", "user": "alice"},
                {"id": 2, "text": "How are you?", "user": "bob"},
                {"id": 3, "text": "Meeting with Sarah tomorrow", "user": "alice"},
                {"id": 4, "text": "Where is the conference?", "user": "charlie"},
            ],
        },
        "precomputed_indexes": {
            # Pre-identified questions (faster than pattern matching)
            "questions": [2, 4],
            # Pre-extracted entities
            "entities": {
                "PERSON": [1, 3],  # Messages mentioning people
                "EVENT": [3],  # Messages about events
                "LOCATION": [4],  # Messages mentioning places
            },
            # Pre-computed user message mappings
            "user_mentions": {"alice": [1, 3], "bob": [2], "charlie": [4]},
        },
    }

    engine = PrismQLEngine.from_config(config)

    print("Precomputed indexes configuration:")
    print(f"  Pre-identified questions: {engine.execute('SELECT is_question()')}")
    print(
        f"  Pre-extracted persons: {len(engine.precomputed_indexes.entities.get('PERSON', []))}"
    )

    return engine


def example_full_stack():
    """Complete configuration with all features."""

    config = {
        "search_backend": {
            "type": "memory",  # tantivy with index_path for large corpora
            "documents": [
                {
                    "id": 1,
                    "text": "Customer service inquiry about billing",
                    "user": "customer_001",
                    "channel": "email",
                },
                {
                    "id": 2,
                    "text": "Technical support needed for API integration",
                    "user": "developer_123",
                    "channel": "slack",
                },
                {
                    "id": 3,
                    "text": "Product feedback: loving the new features!",
                    "user": "customer_002",
                    "channel": "survey",
                },
                {
                    "id": 4,
                    "text": "When will the maintenance window be scheduled?",
                    "user": "admin_456",
                    "channel": "internal",
                },
            ],
        },
        "nlp_backend": {
            "type": "spacy",
            "model": "en_core_web_sm",
            "entity_mappings": {
                "PERSON": "PERSON",
                "ORG": "ORGANIZATION",
                "DATE": "DATE",
                "TIME": "TIME",
            },
        },
        "precomputed_indexes": {
            "questions": [4],
            "entities": {
                "TECHNICAL_TERM": [2],  # Custom entity type
                "BUSINESS_TERM": [1, 3],
            },
            "user_mentions": {
                "customer_001": [1],
                "developer_123": [2],
                "customer_002": [3],
                "admin_456": [4],
            },
        },
        "user_dictionaries": {
            "support_categories": ["billing", "technical", "product", "maintenance"],
            "sentiment_positive": ["loving", "great", "excellent", "amazing"],
            "sentiment_negative": ["issue", "problem", "broken", "frustrated"],
            "channels": ["email", "slack", "survey", "internal", "phone"],
            "user_types": ["customer", "developer", "admin", "support"],
        },
    }

    # Note: This would require spaCy for full functionality
    # engine = PrismQLEngine.from_config(config)

    print("Full stack configuration:")
    print("  ✓ Search backend with custom field mappings")
    print("  ✓ NLP backend with entity extraction")
    print("  ✓ Precomputed indexes for performance")
    print("  ✓ Custom dictionaries for domain-specific queries")

    # Example queries you could run:
    example_queries = [
        "SELECT contains(support_categories)",
        "SELECT from(customer_001) AND contains(sentiment_negative)",
        "SELECT is_question() AND contains(user_types)",
        "SELECT contains(technical), contains(business) INWIN 5",
    ]

    print("\n  Example queries:")
    for query in example_queries:
        print(f"    - {query}")

    return config


def example_configuration_validation():
    """Demonstrate configuration validation."""

    print("Configuration validation examples:")

    # Valid configuration
    valid_config = {"search_backend": {"type": "memory", "documents": []}}

    try:
        BackendFactory.validate_config(valid_config)
        print("  ✓ Valid configuration passed")
    except ValueError as e:
        print(f"  ✗ Unexpected validation error: {e}")

    # Invalid configurations
    invalid_configs = [
        {"search_backend": {}},  # Missing type
        {"nlp_backend": {"type": "spacy"}},  # Missing search_backend
        {"search_backend": "not_a_dict"},  # Wrong type
    ]

    for i, config in enumerate(invalid_configs):
        try:
            BackendFactory.validate_config(config)
            print(f"  ✗ Invalid config {i + 1} should have failed")
        except ValueError:
            print(f"  ✓ Invalid config {i + 1} correctly rejected")


def main():
    """Run all configuration examples."""
    print("PrismQL Configuration Examples")
    print("=" * 40)

    print("\n1. Memory-only configuration:")
    example_memory_only()

    print("\n3. spaCy NLP integration:")
    example_spacy_nlp()

    print("\n4. Precomputed indexes:")
    example_precomputed_indexes()

    print("\n5. Full stack configuration:")
    example_full_stack()

    print("\n6. Configuration validation:")
    example_configuration_validation()

    print("\n7. Available example configs:")
    examples = PrismQLEngine.get_example_configs()
    for name in examples:
        print(f"  - {name}")


if __name__ == "__main__":
    main()
