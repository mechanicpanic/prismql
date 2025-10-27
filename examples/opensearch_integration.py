"""
Example: Integrating PrismQL with OpenSearch and spaCy

This example demonstrates how to set up PrismQL with an OpenSearch backend
and spaCy NLP processing for production use.
"""

import spacy
from opensearchpy import OpenSearch

from prismql import PrismQLEngine


def main():
    """Main example function."""

    # 1. Set up OpenSearch client
    opensearch_client = OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        # Add authentication if needed:
        # http_auth=("admin", "password"),
        # use_ssl=True,
        # verify_certs=False,
        timeout=30,
        max_retries=10,
        retry_on_timeout=True,
    )

    # 2. Load spaCy model
    try:
        nlp = spacy.load("en_core_web_sm")
        print("✓ Loaded spaCy model: en_core_web_sm")
    except OSError:
        print(
            "⚠ spaCy model not found. Install with: python -m spacy download en_core_web_sm"
        )
        nlp = None

    # 3. Configure PrismQL with both backends
    config = {
        "search_backend": {
            "type": "opensearch",
            "client": opensearch_client,
            "index_name": "chat_messages",  # Your index name
            "field_mappings": {
                "text": "message_content",  # Map PrismQL 'text' to your field
                "user": "author_username",  # Map PrismQL 'user' to your field
                "id": "message_id",  # Map PrismQL 'id' to your field
            },
            "search_settings": {"default_operator": "OR", "fuzziness": "AUTO"},
        }
    }

    # Add NLP backend if spaCy is available
    if nlp:
        config["nlp_backend"] = {
            "type": "spacy",
            "nlp": nlp,
            "entity_mappings": {
                "PERSON": "PERSON",
                "GPE": "LOCATION",  # Geographic entities -> locations
                "ORG": "ORGANIZATION",
                "DATE": "DATE",
                "TIME": "TIME",
            },
            "batch_size": 100,
        }

    # Add custom dictionaries
    config["user_dictionaries"] = {
        "sentiment_positive": ["happy", "great", "awesome", "love", "excellent"],
        "sentiment_negative": ["sad", "terrible", "hate", "awful", "bad"],
        "tech_terms": ["python", "javascript", "react", "django", "api", "database"],
        "question_words": ["what", "how", "why", "when", "where", "who"],
    }

    # 4. Create PrismQL engine
    try:
        engine = PrismQLEngine.from_config(config)
        print("✓ PrismQL engine created successfully")

        # Test connection by getting total document count
        total_docs = engine.search_backend.get_total_documents()
        print(f"✓ Connected to OpenSearch. Total documents: {total_docs}")

    except Exception as e:
        print(f"✗ Failed to create engine: {e}")
        return

    # 5. Example queries
    queries = [
        # Basic user queries
        "SELECT from(alice)",
        "SELECT from(support_team)",
        # Text search
        "SELECT contains(tech_terms)",
        "SELECT contains(sentiment_positive)",
        # Boolean combinations
        "SELECT from(alice) AND contains(sentiment_positive)",
        "SELECT from(support_team) OR contains(tech_terms)",
        # Questions
        "SELECT is_question()",
        "SELECT from(alice) AND is_question()",
        # Window constraints (find patterns within message ranges)
        "SELECT from(user), from(support_team) INWIN 5",
        "SELECT contains(sentiment_negative), contains(sentiment_positive) INWIN 10",
    ]

    print("\n" + "=" * 50)
    print("EXAMPLE QUERIES")
    print("=" * 50)

    for query in queries:
        print(f"\nQuery: {query}")
        try:
            # Validate query first
            is_valid = engine.validate(query)
            if not is_valid:
                print("  ✗ Invalid query syntax")
                continue

            # Execute query
            results = engine.execute(query)
            print(f"  ✓ Found {len(results)} result groups")

            # Show first few results
            for i, group in enumerate(results[:3]):
                print(f"    Group {i + 1}: {group}")

            if len(results) > 3:
                print(f"    ... and {len(results) - 3} more groups")

        except Exception as e:
            print(f"  ✗ Query failed: {e}")

    # 6. Advanced: Using precomputed indexes for better performance
    print("\n" + "=" * 50)
    print("PRECOMPUTED INDEXES EXAMPLE")
    print("=" * 50)

    print("\nFor better performance with large datasets, precompute NLP features:")
    print(
        """
    # Example precomputation script:
    def build_indexes(your_corpus):
        questions = set()
        entities = {"PERSON": set(), "LOCATION": set(), "ORGANIZATION": set()}
        user_mentions = {}

        for message in your_corpus:
            msg_id = message["message_id"]

            # Use your existing spaCy annotations
            if message.get("is_question"):
                questions.add(msg_id)

            for ent in message.get("entities", []):
                if ent["label"] in entities:
                    entities[ent["label"]].add(msg_id)

            # User indexing
            user = message["author_username"]
            if user not in user_mentions:
                user_mentions[user] = set()
            user_mentions[user].add(msg_id)

        return PrecomputedIndexes(
            entities=entities,
            questions=questions,
            user_mentions=user_mentions
        )

    # Then add to config:
    config["precomputed_indexes"] = build_indexes(your_data)
    """
    )

    print("\n✓ Setup complete! PrismQL is ready for production use.")


if __name__ == "__main__":
    main()
