# Backend Integration Guide

This guide explains how to integrate PrismQL with your existing search infrastructure and NLP pipelines.

## Quick Start

```python
from prismql import PrismQLEngine

# Simple configuration for immediate use
config = {
    "search_backend": {
        "type": "opensearch",  # or "elasticsearch"
        "client": your_opensearch_client,
        "index_name": "your_index",
        "field_mappings": {
            "text": "your_text_field",
            "user": "your_user_field",
            "id": "your_id_field"
        }
    }
}

engine = PrismQLEngine.from_config(config)
results = engine.execute("SELECT from(alice) AND is_question()")
```

## Backend Types

### OpenSearch/Elasticsearch Backend

**Use case**: Production deployments with large datasets

```python
from opensearchpy import OpenSearch

client = OpenSearch([{"host": "your-cluster.com", "port": 443}])

config = {
    "search_backend": {
        "type": "opensearch",  # or "elasticsearch"
        "client": client,
        "index_name": "chat_messages",
        "field_mappings": {
            "text": "message_content",
            "user": "author_username",
            "id": "message_id"
        },
        "search_settings": {
            "default_operator": "OR",
            "fuzziness": "AUTO"
        }
    }
}
```

**Configuration options**:
- `client`: Your OpenSearch/Elasticsearch client instance
- `index_name`: Target index name
- `field_mappings`: Map PrismQL fields to your schema
- `search_settings`: Query behavior (operator, fuzziness, etc.)

### Memory Backend

**Use case**: Testing, development, small datasets

```python
config = {
    "search_backend": {
        "type": "memory",
        "documents": [
            {"id": 1, "text": "Hello", "user": "alice"},
            {"id": 2, "text": "World", "user": "bob"}
        ],
        "id_field": "id"
    }
}
```

### spaCy NLP Backend

**Use case**: Named entity recognition, question detection

```python
import spacy

nlp = spacy.load("en_core_web_sm")

config = {
    # ... search backend config ...
    "nlp_backend": {
        "type": "spacy",
        "nlp": nlp,  # or "model": "en_core_web_sm"
        "entity_mappings": {
            "PERSON": "PERSON",
            "GPE": "LOCATION",
            "ORG": "ORGANIZATION"
        },
        "question_patterns": [
            r"\\?$",
            r"^(what|who|how)\\b"
        ]
    }
}
```

## Field Mapping

Map PrismQL's expected fields to your index structure:

```python
"field_mappings": {
    "text": "content",           # Message text
    "user": "author",          # Message author
    "id": "message_id"         # Unique identifier
}
```

PrismQL queries like `from(alice)` will search your `author` field, while `contains(words)` will search your `content` field.

## Performance Optimization

### Precomputed Indexes

For large datasets, precompute NLP features:

```python
def build_indexes(your_corpus):
    questions = set()
    entities = {"PERSON": set(), "LOCATION": set()}
    user_mentions = {}

    for message in your_corpus:
        msg_id = message["id"]

        # Use existing annotations
        if message.get("is_question"):
            questions.add(msg_id)

        for ent in message.get("entities", []):
            if ent["label"] in entities:
                entities[ent["label"]].add(msg_id)

        # Index user messages
        user = message["user"]
        if user not in user_mentions:
            user_mentions[user] = set()
        user_mentions[user].add(msg_id)

    return {
        "entities": entities,
        "questions": questions,
        "user_mentions": user_mentions
    }

config["precomputed_indexes"] = build_indexes(your_data)
```

### Batch Processing

For initial indexing or bulk analysis:

```python
# Process multiple texts efficiently
texts = [msg["content"] for msg in your_messages]
results = nlp_backend.process_batch(texts)

for i, result in enumerate(results):
    your_messages[i]["entities"] = result["entities"]
    your_messages[i]["is_question"] = result["is_question"]
```

## User Dictionaries

Define domain-specific vocabularies:

```python
config["user_dictionaries"] = {
    "products": ["product_a", "premium_service", "basic_plan"],
    "sentiment_positive": ["great", "love", "excellent", "amazing"],
    "sentiment_negative": ["terrible", "hate", "broken", "awful"],
    "urgency": ["urgent", "asap", "critical", "emergency"]
}

# Query with dictionaries
results = engine.execute("SELECT contains(urgency) AND from(support_team)")
```

## Error Handling

```python
from prismql import PrismQLSyntaxError, PrismQLRuntimeError

try:
    engine = PrismQLEngine.from_config(config)
    results = engine.execute("SELECT from(alice)")
except ImportError:
    print("Missing dependencies (opensearch-py, spacy)")
except ValueError as e:
    print(f"Configuration error: {e}")
except PrismQLSyntaxError as e:
    print(f"Query syntax error: {e}")
except PrismQLRuntimeError as e:
    print(f"Query execution error: {e}")
```

## Configuration Validation

Validate your configuration before creating the engine:

```python
from prismql import BackendFactory

try:
    validated_config = BackendFactory.validate_config(config)
    engine = PrismQLEngine.from_config(validated_config)
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

## Example Configurations

### E-commerce Support

```python
config = {
    "search_backend": {
        "type": "opensearch",
        "client": opensearch_client,
        "index_name": "support_tickets",
        "field_mappings": {
            "text": "ticket_description",
            "user": "customer_id",
            "id": "ticket_id"
        }
    },
    "user_dictionaries": {
        "products": ["shoes", "shirts", "electronics"],
        "issues": ["defective", "damaged", "missing", "wrong_size"],
        "resolution": ["refund", "replacement", "exchange"]
    }
}

# Find refund requests for electronics
results = engine.execute("SELECT contains(products) AND contains(refund)")
```

### Chat Analysis

```python
config = {
    "search_backend": {
        "type": "opensearch",
        "client": opensearch_client,
        "index_name": "chat_logs",
        "field_mappings": {
            "text": "message",
            "user": "username",
            "id": "msg_id"
        }
    },
    "nlp_backend": {
        "type": "spacy",
        "model": "en_core_web_sm"
    },
    "user_dictionaries": {
        "greeting": ["hello", "hi", "hey"],
        "farewell": ["bye", "goodbye", "see_you"]
    }
}

# Find conversation patterns
results = engine.execute("SELECT contains(greeting), contains(farewell) INWIN 20")
```

### Social Media Monitoring

```python
config = {
    "search_backend": {
        "type": "elasticsearch",
        "client": elasticsearch_client,
        "index_name": "social_posts",
        "field_mappings": {
            "text": "post_content",
            "user": "author_handle",
            "id": "post_id"
        }
    },
    "precomputed_indexes": {
        "entities": {
            "BRAND": brand_mentions,
            "COMPETITOR": competitor_mentions
        },
        "questions": question_posts
    },
    "user_dictionaries": {
        "sentiment_positive": ["love", "amazing", "best"],
        "sentiment_negative": ["hate", "worst", "terrible"]
    }
}

# Monitor brand sentiment
results = engine.execute("SELECT mentions(BRAND) AND contains(sentiment_negative)")
```

## Migration from Memory Backend

Start with memory backend for development:

```python
# Development
dev_config = {
    "search_backend": {
        "type": "memory",
        "documents": sample_data
    }
}

# Production - just change the search backend
prod_config = {
    "search_backend": {
        "type": "opensearch",
        "client": production_client,
        "index_name": "production_index",
        "field_mappings": {...}
    },
    # Keep same dictionaries and NLP config
    "user_dictionaries": dev_config.get("user_dictionaries"),
    "nlp_backend": dev_config.get("nlp_backend")
}
```

## Best Practices

1. **Start Simple**: Begin with memory backend and basic queries
2. **Validate Early**: Use `BackendFactory.validate_config()`
3. **Map Fields**: Always define `field_mappings` for production
4. **Precompute**: Use precomputed indexes for better performance
5. **Test Queries**: Use `engine.validate()` before executing
6. **Handle Errors**: Wrap queries in try-catch blocks
7. **Monitor Performance**: Track query execution times
8. **Version Control**: Keep configurations in version control

## Dependencies

Install optional dependencies as needed:

```bash
# For OpenSearch/Elasticsearch
pip install opensearch-py  # or elasticsearch

# For spaCy NLP
pip install spacy
python -m spacy download en_core_web_sm

# Or install all at once
pip install prismql[opensearch,nlp]
```

## Next Steps

- See `examples/` directory for complete working examples
- Check `tests/test_integration.py` for testing patterns
- Review the main README for query language documentation
