"""Backend factory for unified configuration and setup."""

from typing import Any, Optional

from .base import NLPBackend, PrecomputedIndexes, SearchBackend


class BackendFactory:
    """
    Factory for creating and configuring PrismQL backends.

    This factory provides a unified interface for setting up various
    backend combinations with a single configuration dictionary.

    Example configuration:
        config = {
            "search_backend": {
                "type": "opensearch",
                "client": opensearch_client,
                "index_name": "messages",
                "field_mappings": {
                    "text": "content",
                    "user": "author"
                }
            },
            "nlp_backend": {
                "type": "spacy",
                "nlp": spacy_model,
                "entity_mappings": {
                    "PERSON": "PERSON",
                    "GPE": "LOCATION"
                }
            },
            "precomputed_indexes": {
                "entities": {...},
                "questions": {...},
                "user_mentions": {...}
            },
            "user_dictionaries": {
                "sentiment_words": ["happy", "sad", "angry"]
            }
        }
    """

    @classmethod
    def create_backends(
        cls, config: dict[str, Any]
    ) -> tuple[
        SearchBackend,
        Optional[NLPBackend],
        Optional[PrecomputedIndexes],
        Optional[dict[str, Any]],
    ]:
        """
        Create backends from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Tuple of (search_backend, nlp_backend, precomputed_indexes,
            user_dictionaries)

        Raises:
            ValueError: If configuration is invalid
            ImportError: If required dependencies are not available
        """
        # Create search backend (required)
        search_backend = cls._create_search_backend(config.get("search_backend", {}))

        # Create NLP backend (optional)
        nlp_backend = None
        if "nlp_backend" in config:
            nlp_backend = cls._create_nlp_backend(config["nlp_backend"])

        # Create precomputed indexes (optional)
        precomputed_indexes = None
        if "precomputed_indexes" in config:
            precomputed_indexes = cls._create_precomputed_indexes(
                config["precomputed_indexes"]
            )

        # Extract user dictionaries
        user_dictionaries = config.get("user_dictionaries")

        return search_backend, nlp_backend, precomputed_indexes, user_dictionaries

    @classmethod
    def _create_search_backend(cls, config: dict[str, Any]) -> SearchBackend:
        """Create search backend from configuration."""
        backend_type = config.get("type", "").lower()

        if not backend_type:
            raise ValueError("search_backend.type is required")

        if backend_type == "memory":
            return cls._create_memory_backend(config)
        if backend_type in ["opensearch", "elasticsearch"]:
            return cls._create_opensearch_backend(config)
        raise ValueError(f"Unknown search backend type: {backend_type}")

    @classmethod
    def _create_memory_backend(cls, config: dict[str, Any]) -> SearchBackend:
        """Create memory backend."""
        try:
            from .memory import MemoryBackend
        except ImportError as e:
            raise ImportError("Memory backend is not available") from e

        documents = config.get("documents", [])
        id_field = config.get("id_field", "id")

        if not documents:
            raise ValueError("Memory backend requires 'documents' in configuration")

        return MemoryBackend(documents, id_field)

    @classmethod
    def _create_opensearch_backend(cls, config: dict[str, Any]) -> SearchBackend:
        """Create OpenSearch/Elasticsearch backend."""
        try:
            from .opensearch import OpenSearchBackend
        except ImportError as e:
            raise ImportError("OpenSearch backend is not available") from e

        client = config.get("client")
        if client is None:
            raise ValueError("OpenSearch backend requires 'client' in configuration")

        # Extract backend configuration
        backend_config = {
            "index_name": config.get("index_name"),
            "field_mappings": config.get("field_mappings", {}),
            "search_settings": config.get("search_settings", {}),
        }

        if not backend_config["index_name"]:
            raise ValueError(
                "OpenSearch backend requires 'index_name' in configuration"
            )

        return OpenSearchBackend(client, backend_config)

    @classmethod
    def _create_nlp_backend(cls, config: dict[str, Any]) -> NLPBackend:
        """Create NLP backend from configuration."""
        backend_type = config.get("type", "").lower()

        if not backend_type:
            raise ValueError("nlp_backend.type is required")

        if backend_type == "spacy":
            return cls._create_spacy_backend(config)
        raise ValueError(f"Unknown NLP backend type: {backend_type}")

    @classmethod
    def _create_spacy_backend(cls, config: dict[str, Any]) -> NLPBackend:
        """Create spaCy backend."""
        try:
            from .spacy import SpacyBackend
        except ImportError as e:
            raise ImportError("spaCy backend is not available") from e

        nlp = config.get("nlp")
        if nlp is None:
            # Try to load model by name
            model_name = config.get("model")
            if model_name:
                try:
                    import spacy  # type: ignore[import-not-found]

                    nlp = spacy.load(model_name)
                except Exception as e:
                    raise ValueError(
                        f"Failed to load spaCy model '{model_name}': {e}"
                    ) from e
            else:
                raise ValueError(
                    "spaCy backend requires 'nlp' object or 'model' name "
                    "in configuration"
                )

        # Extract backend configuration
        backend_config = {
            "entity_mappings": config.get("entity_mappings", {}),
            "question_patterns": config.get("question_patterns", []),
            "batch_size": config.get("batch_size", 100),
        }

        return SpacyBackend(nlp, backend_config)

    @classmethod
    def _create_precomputed_indexes(cls, config: dict[str, Any]) -> PrecomputedIndexes:
        """Create precomputed indexes from configuration."""
        entities = config.get("entities")
        questions = config.get("questions")
        user_mentions = config.get("user_mentions")

        # Convert to sets if needed
        if entities:
            entities = {
                label: set(ids) if not isinstance(ids, set) else ids
                for label, ids in entities.items()
            }

        if questions and not isinstance(questions, set):
            questions = set(questions)

        if user_mentions:
            user_mentions = {
                user: set(ids) if not isinstance(ids, set) else ids
                for user, ids in user_mentions.items()
            }

        return PrecomputedIndexes(
            entities=entities, questions=questions, user_mentions=user_mentions
        )

    @classmethod
    def validate_config(cls, config: dict[str, Any]) -> dict[str, Any]:
        """
        Validate configuration and return normalized version.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Normalized configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Validate search backend
        if "search_backend" not in config:
            raise ValueError("Configuration must include 'search_backend'")

        search_config = config["search_backend"]
        if not isinstance(search_config, dict):
            raise ValueError("search_backend must be a dictionary")

        if "type" not in search_config:
            raise ValueError("search_backend must specify 'type'")

        # Validate NLP backend if present
        if "nlp_backend" in config:
            nlp_config = config["nlp_backend"]
            if not isinstance(nlp_config, dict):
                raise ValueError("nlp_backend must be a dictionary")

            if "type" not in nlp_config:
                raise ValueError("nlp_backend must specify 'type'")

        # Validate precomputed indexes if present
        if "precomputed_indexes" in config:
            precomputed_config = config["precomputed_indexes"]
            if not isinstance(precomputed_config, dict):
                raise ValueError("precomputed_indexes must be a dictionary")

        # Validate user dictionaries if present
        if "user_dictionaries" in config:
            user_dicts = config["user_dictionaries"]
            if not isinstance(user_dicts, dict):
                raise ValueError("user_dictionaries must be a dictionary")

        return config

    @classmethod
    def get_example_configs(cls) -> dict[str, dict[str, Any]]:
        """
        Get example configurations for common setups.

        Returns:
            Dictionary mapping setup names to example configurations
        """
        return {
            "memory_only": {
                "search_backend": {
                    "type": "memory",
                    "documents": [
                        {"id": 1, "text": "Hello world", "user": "alice"},
                        {"id": 2, "text": "How are you?", "user": "bob"},
                    ],
                    "id_field": "id",
                }
            },
            "opensearch_spacy": {
                "search_backend": {
                    "type": "opensearch",
                    "client": "your_opensearch_client",
                    "index_name": "chat_messages",
                    "field_mappings": {
                        "text": "message_content",
                        "user": "author_name",
                        "id": "message_id",
                    },
                    "search_settings": {"default_operator": "OR", "fuzziness": "AUTO"},
                },
                "nlp_backend": {
                    "type": "spacy",
                    "model": "en_core_web_sm",
                    "entity_mappings": {
                        "PERSON": "PERSON",
                        "GPE": "LOCATION",
                        "ORG": "ORGANIZATION",
                    },
                },
                "user_dictionaries": {
                    "sentiment": ["happy", "sad", "angry", "excited"],
                    "tech_terms": ["python", "javascript", "react", "django"],
                },
            },
            "elasticsearch_precomputed": {
                "search_backend": {
                    "type": "elasticsearch",
                    "client": "your_elasticsearch_client",
                    "index_name": "messages",
                    "field_mappings": {"text": "content", "user": "username"},
                },
                "precomputed_indexes": {
                    "entities": {
                        "PERSON": ["msg_1", "msg_5"],
                        "DATE": ["msg_3", "msg_7"],
                    },
                    "questions": ["msg_2", "msg_4", "msg_8"],
                    "user_mentions": {
                        "alice": ["msg_1", "msg_3"],
                        "bob": ["msg_2", "msg_4"],
                    },
                },
            },
        }
