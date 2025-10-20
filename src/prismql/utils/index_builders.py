"""Utilities for building PrecomputedIndexes from various annotation formats."""

from collections.abc import Mapping, Sequence
from typing import Any, Callable, Optional

from ..backends.base import PrecomputedIndexes
from ..types import MessageId, NERLabel


class IndexBuilder:
    """
    Builder for creating PrecomputedIndexes from various annotation formats.

    This class provides utilities to convert annotations from different sources
    (LLM outputs, annotation platforms, NLP libraries) into PrismQL-compatible
    PrecomputedIndexes.

    Example:
        >>> # From message annotations
        >>> messages = [
        ...     {'id': 1, 'text': '...', 'intent': 'question', 'entities': ['ORG']},
        ...     {'id': 2, 'text': '...', 'intent': 'request', 'topics': ['bug']},
        ... ]
        >>>
        >>> # Build indexes
        >>> builder = IndexBuilder()
        >>> indexes = builder.from_message_annotations(
        ...     messages,
        ...     entity_field='entities',
        ...     custom_fields={'intent': None, 'topics': None}
        ... )
    """

    @staticmethod
    def from_message_annotations(
        messages: Sequence[Mapping[str, Any]],
        id_field: str = "id",
        entity_field: Optional[str] = None,
        question_detector: Optional[Callable[[Mapping[str, Any]], bool]] = None,
        custom_fields: Optional[Mapping[str, Optional[Callable[[Any], Any]]]] = None,
    ) -> PrecomputedIndexes:
        """
        Build indexes from message annotations.

        This is the most flexible builder - it extracts features from arbitrary
        fields in your message data.

        Args:
            messages: List of message dictionaries
            id_field: Field name containing message ID (default: 'id')
            entity_field: Field containing entity types (e.g., ['ORG', 'PERSON'])
                         If None, no entity indexes are built
            question_detector: Optional function to determine if message is a question
                             If None, checks for 'is_question' field or '?' in text
            custom_fields: Mapping of field names to optional value extractors
                         Example: {'intent': None, 'topics': list}
                         - If extractor is None, treats field value as single feature name
                         - If extractor is callable, applies it to get feature name(s)

        Returns:
            PrecomputedIndexes with features extracted from messages

        Example:
            >>> messages = [
            ...     {'id': 1, 'intent': 'question', 'entities': ['ORG'], 'topics': ['bug', 'api']},
            ...     {'id': 2, 'intent': 'request', 'topics': ['feature']},
            ... ]
            >>> indexes = IndexBuilder.from_message_annotations(
            ...     messages,
            ...     entity_field='entities',
            ...     custom_fields={'intent': None, 'topics': list}
            ... )
            >>> # Results in:
            >>> # entities: {'ORG': {1}}
            >>> # custom_features: {'intent_question': {1}, 'intent_request': {2},
            >>> #                  'topic_bug': {1}, 'topic_api': {1}, 'topic_feature': {2}}
        """
        entities: dict[NERLabel, set[MessageId]] = {}
        questions: set[MessageId] = set()
        custom_features: dict[str, set[MessageId]] = {}

        for msg in messages:
            msg_id = msg[id_field]

            # Extract entities
            if entity_field and entity_field in msg:
                entity_list = msg[entity_field]
                if isinstance(entity_list, (list, tuple)):
                    for entity_type in entity_list:
                        if entity_type not in entities:
                            entities[entity_type] = set()
                        entities[entity_type].add(msg_id)

            # Detect questions
            if question_detector:
                if question_detector(msg):
                    questions.add(msg_id)
            elif "is_question" in msg and msg["is_question"]:
                questions.add(msg_id)
            elif "text" in msg and "?" in msg["text"]:
                questions.add(msg_id)

            # Extract custom features
            if custom_fields:
                for field_name, extractor in custom_fields.items():
                    if field_name not in msg:
                        continue

                    field_value = msg[field_name]

                    if extractor is None:
                        # Treat field value as single feature name
                        feature_name = f"{field_name}_{field_value}"
                        if feature_name not in custom_features:
                            custom_features[feature_name] = set()
                        custom_features[feature_name].add(msg_id)

                    elif callable(extractor):
                        # Apply extractor to get feature name(s)
                        extracted = extractor(field_value)
                        if isinstance(extracted, (list, tuple)):
                            # Multiple features
                            for feature_val in extracted:
                                feature_name = f"{field_name}_{feature_val}"
                                if feature_name not in custom_features:
                                    custom_features[feature_name] = set()
                                custom_features[feature_name].add(msg_id)
                        else:
                            # Single feature
                            feature_name = f"{field_name}_{extracted}"
                            if feature_name not in custom_features:
                                custom_features[feature_name] = set()
                            custom_features[feature_name].add(msg_id)

        return PrecomputedIndexes(
            entities=entities,
            questions=questions,
            custom_features=custom_features,
        )

    @staticmethod
    def from_separate_annotations(
        annotation_dict: Mapping[MessageId, Mapping[str, Any]],
        entity_key: Optional[str] = None,
        question_key: Optional[str] = None,
        custom_feature_keys: Optional[Sequence[str]] = None,
    ) -> PrecomputedIndexes:
        """
        Build indexes from separate annotation dictionary.

        Use this when annotations are stored separately from messages,
        e.g., in an annotation platform database.

        Args:
            annotation_dict: Mapping of message ID to annotations
                           Example: {1: {'labels': ['important'], 'entities': ['ORG']}}
            entity_key: Key in annotations containing entity types
            question_key: Key in annotations indicating question (boolean or string)
            custom_feature_keys: Keys to extract as custom features

        Returns:
            PrecomputedIndexes built from annotations

        Example:
            >>> annotations = {
            ...     1: {'labels': ['important', 'decision'], 'entities': ['ORG']},
            ...     2: {'labels': ['action_item'], 'is_question': True},
            ... }
            >>> indexes = IndexBuilder.from_separate_annotations(
            ...     annotations,
            ...     entity_key='entities',
            ...     question_key='is_question',
            ...     custom_feature_keys=['labels']
            ... )
        """
        entities: dict[NERLabel, set[MessageId]] = {}
        questions: set[MessageId] = set()
        custom_features: dict[str, set[MessageId]] = {}

        for msg_id, annotations in annotation_dict.items():
            # Extract entities
            if entity_key and entity_key in annotations:
                entity_list = annotations[entity_key]
                if isinstance(entity_list, (list, tuple)):
                    for entity_type in entity_list:
                        if entity_type not in entities:
                            entities[entity_type] = set()
                        entities[entity_type].add(msg_id)

            # Extract questions
            if question_key and question_key in annotations:
                is_question = annotations[question_key]
                if isinstance(is_question, bool) and is_question:
                    questions.add(msg_id)
                elif is_question:  # Truthy value
                    questions.add(msg_id)

            # Extract custom features
            if custom_feature_keys:
                for feature_key in custom_feature_keys:
                    if feature_key not in annotations:
                        continue

                    feature_values = annotations[feature_key]

                    # Handle both single values and lists
                    if isinstance(feature_values, (list, tuple)):
                        for feature_val in feature_values:
                            if feature_val not in custom_features:
                                custom_features[feature_val] = set()
                            custom_features[feature_val].add(msg_id)
                    else:
                        if feature_values not in custom_features:
                            custom_features[feature_values] = set()
                        custom_features[feature_values].add(msg_id)

        return PrecomputedIndexes(
            entities=entities,
            questions=questions,
            custom_features=custom_features,
        )

    @staticmethod
    def merge(*indexes: PrecomputedIndexes) -> PrecomputedIndexes:
        """
        Merge multiple PrecomputedIndexes into one.

        Useful when combining indexes from different sources or processing stages.

        Args:
            *indexes: PrecomputedIndexes to merge

        Returns:
            Merged PrecomputedIndexes

        Example:
            >>> llm_indexes = IndexBuilder.from_message_annotations(...)
            >>> human_indexes = IndexBuilder.from_separate_annotations(...)
            >>> combined = IndexBuilder.merge(llm_indexes, human_indexes)
        """
        merged_entities: dict[NERLabel, set[MessageId]] = {}
        merged_questions: set[MessageId] = set()
        merged_user_mentions: dict[str, set[MessageId]] = {}
        merged_custom: dict[str, set[MessageId]] = {}

        for idx in indexes:
            # Merge entities
            for entity_type, msg_ids in idx.entities.items():
                if entity_type not in merged_entities:
                    merged_entities[entity_type] = set()
                merged_entities[entity_type].update(msg_ids)

            # Merge questions
            merged_questions.update(idx.questions)

            # Merge user mentions
            for user, msg_ids in idx.user_mentions.items():
                if user not in merged_user_mentions:
                    merged_user_mentions[user] = set()
                merged_user_mentions[user].update(msg_ids)

            # Merge custom features
            for feature, msg_ids in idx.custom_features.items():
                if feature not in merged_custom:
                    merged_custom[feature] = set()
                merged_custom[feature].update(msg_ids)

        return PrecomputedIndexes(
            entities=merged_entities,
            questions=merged_questions,
            user_mentions=merged_user_mentions,
            custom_features=merged_custom,
        )
