"""Tests for IndexBuilder utility."""

from prismql import IndexBuilder, PrecomputedIndexes


class TestFromMessageAnnotations:
    """Test IndexBuilder.from_message_annotations()."""

    def test_basic_entity_extraction(self):
        """Test extracting entities from messages."""
        messages = [
            {"id": 1, "text": "Meeting with Acme Corp", "entities": ["ORG"]},
            {"id": 2, "text": "John Smith called", "entities": ["PERSON"]},
            {"id": 3, "text": "No entities here", "entities": []},
        ]

        indexes = IndexBuilder.from_message_annotations(
            messages, entity_field="entities"
        )

        assert indexes.entities == {"ORG": {1}, "PERSON": {2}}
        assert indexes.questions == set()
        assert indexes.custom_features == {}

    def test_question_detection_field(self):
        """Test question detection from is_question field."""
        messages = [
            {"id": 1, "text": "Hello", "is_question": False},
            {"id": 2, "text": "How are you?", "is_question": True},
            {"id": 3, "text": "What's up?", "is_question": True},
        ]

        indexes = IndexBuilder.from_message_annotations(messages)

        assert indexes.questions == {2, 3}

    def test_question_detection_text(self):
        """Test question detection from text content."""
        messages = [
            {"id": 1, "text": "Hello there"},
            {"id": 2, "text": "How are you?"},
            {"id": 3, "text": "What's up?"},
        ]

        indexes = IndexBuilder.from_message_annotations(messages)

        # Should detect questions from '?' in text
        assert indexes.questions == {2, 3}

    def test_custom_question_detector(self):
        """Test custom question detector function."""

        def is_question(msg):
            return msg.get("intent") == "question"

        messages = [
            {"id": 1, "text": "Hello", "intent": "greeting"},
            {"id": 2, "text": "Can you help?", "intent": "question"},
            {"id": 3, "text": "Sure", "intent": "response"},
        ]

        indexes = IndexBuilder.from_message_annotations(
            messages, question_detector=is_question
        )

        assert indexes.questions == {2}

    def test_single_value_custom_field(self):
        """Test extracting single-value custom fields."""
        messages = [
            {"id": 1, "intent": "request"},
            {"id": 2, "intent": "question"},
            {"id": 3, "intent": "request"},
        ]

        indexes = IndexBuilder.from_message_annotations(
            messages, custom_fields={"intent": None}
        )

        assert indexes.custom_features == {
            "intent_request": {1, 3},
            "intent_question": {2},
        }

    def test_list_value_custom_field(self):
        """Test extracting list-value custom fields."""
        messages = [
            {"id": 1, "topics": ["bug", "api"]},
            {"id": 2, "topics": ["feature"]},
            {"id": 3, "topics": ["bug", "ui"]},
        ]

        indexes = IndexBuilder.from_message_annotations(
            messages, custom_fields={"topics": list}
        )

        assert indexes.custom_features == {
            "topics_bug": {1, 3},
            "topics_api": {1},
            "topics_feature": {2},
            "topics_ui": {3},
        }

    def test_multiple_custom_fields(self):
        """Test extracting multiple custom fields."""
        messages = [
            {"id": 1, "intent": "request", "sentiment": "neutral"},
            {"id": 2, "intent": "question", "sentiment": "positive"},
        ]

        indexes = IndexBuilder.from_message_annotations(
            messages, custom_fields={"intent": None, "sentiment": None}
        )

        assert "intent_request" in indexes.custom_features
        assert "intent_question" in indexes.custom_features
        assert "sentiment_neutral" in indexes.custom_features
        assert "sentiment_positive" in indexes.custom_features

    def test_custom_id_field(self):
        """Test using custom ID field name."""
        messages = [
            {"msg_id": 101, "text": "Hello", "is_question": False},
            {"msg_id": 102, "text": "Hi?", "is_question": True},
        ]

        indexes = IndexBuilder.from_message_annotations(messages, id_field="msg_id")

        assert indexes.questions == {102}

    def test_missing_fields_ignored(self):
        """Test that missing fields are gracefully ignored."""
        messages = [
            {"id": 1, "intent": "request"},
            {"id": 2},  # Missing intent field
            {"id": 3, "intent": "question"},
        ]

        indexes = IndexBuilder.from_message_annotations(
            messages, custom_fields={"intent": None}
        )

        assert indexes.custom_features == {
            "intent_request": {1},
            "intent_question": {3},
        }


class TestFromSeparateAnnotations:
    """Test IndexBuilder.from_separate_annotations()."""

    def test_basic_entity_extraction(self):
        """Test extracting entities from separate annotations."""
        annotations = {
            1: {"entities": ["ORG"]},
            2: {"entities": ["PERSON", "ORG"]},
            3: {"entities": []},
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations, entity_key="entities"
        )

        assert indexes.entities == {"ORG": {1, 2}, "PERSON": {2}}

    def test_question_boolean_field(self):
        """Test question detection from boolean field."""
        annotations = {
            1: {"is_question": True},
            2: {"is_question": False},
            3: {"is_question": True},
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations, question_key="is_question"
        )

        assert indexes.questions == {1, 3}

    def test_question_truthy_field(self):
        """Test question detection from truthy field."""
        annotations = {
            1: {"question_type": "yes_no"},
            2: {"question_type": None},
            3: {"question_type": "wh"},
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations, question_key="question_type"
        )

        assert indexes.questions == {1, 3}

    def test_single_custom_feature(self):
        """Test extracting single-value custom features."""
        annotations = {
            1: {"importance": "high"},
            2: {"importance": "medium"},
            3: {"importance": "high"},
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations, custom_feature_keys=["importance"]
        )

        assert indexes.custom_features == {
            "high": {1, 3},
            "medium": {2},
        }

    def test_list_custom_features(self):
        """Test extracting list-value custom features."""
        annotations = {
            1: {"labels": ["important", "decision"]},
            2: {"labels": ["action_item"]},
            3: {"labels": ["important", "follow_up"]},
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations, custom_feature_keys=["labels"]
        )

        assert indexes.custom_features == {
            "important": {1, 3},
            "decision": {1},
            "action_item": {2},
            "follow_up": {3},
        }

    def test_multiple_custom_feature_keys(self):
        """Test extracting multiple custom feature types."""
        annotations = {
            1: {"labels": ["important"], "status": "open"},
            2: {"labels": ["action_item"], "status": "closed"},
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations, custom_feature_keys=["labels", "status"]
        )

        assert "important" in indexes.custom_features
        assert "action_item" in indexes.custom_features
        assert "open" in indexes.custom_features
        assert "closed" in indexes.custom_features

    def test_all_features_combined(self):
        """Test extracting entities, questions, and custom features together."""
        annotations = {
            1: {
                "entities": ["ORG"],
                "is_question": False,
                "labels": ["important"],
            },
            2: {
                "entities": ["PERSON"],
                "is_question": True,
                "labels": ["action_item"],
            },
        }

        indexes = IndexBuilder.from_separate_annotations(
            annotations,
            entity_key="entities",
            question_key="is_question",
            custom_feature_keys=["labels"],
        )

        assert indexes.entities == {"ORG": {1}, "PERSON": {2}}
        assert indexes.questions == {2}
        assert indexes.custom_features == {
            "important": {1},
            "action_item": {2},
        }


class TestMerge:
    """Test IndexBuilder.merge()."""

    def test_merge_entities(self):
        """Test merging entity indexes."""
        idx1 = PrecomputedIndexes(entities={"ORG": {1, 2}, "PERSON": {3}})
        idx2 = PrecomputedIndexes(entities={"ORG": {4}, "GPE": {5}})

        merged = IndexBuilder.merge(idx1, idx2)

        assert merged.entities == {
            "ORG": {1, 2, 4},
            "PERSON": {3},
            "GPE": {5},
        }

    def test_merge_questions(self):
        """Test merging question indexes."""
        idx1 = PrecomputedIndexes(questions={1, 2})
        idx2 = PrecomputedIndexes(questions={2, 3, 4})

        merged = IndexBuilder.merge(idx1, idx2)

        assert merged.questions == {1, 2, 3, 4}

    def test_merge_custom_features(self):
        """Test merging custom feature indexes."""
        idx1 = PrecomputedIndexes(custom_features={"important": {1, 2}, "urgent": {3}})
        idx2 = PrecomputedIndexes(custom_features={"important": {4}, "verified": {5}})

        merged = IndexBuilder.merge(idx1, idx2)

        assert merged.custom_features == {
            "important": {1, 2, 4},
            "urgent": {3},
            "verified": {5},
        }

    def test_merge_user_mentions(self):
        """Test merging user mention indexes."""
        idx1 = PrecomputedIndexes(user_mentions={"alice": {1, 2}})
        idx2 = PrecomputedIndexes(user_mentions={"alice": {3}, "bob": {4}})

        merged = IndexBuilder.merge(idx1, idx2)

        assert merged.user_mentions == {
            "alice": {1, 2, 3},
            "bob": {4},
        }

    def test_merge_multiple_indexes(self):
        """Test merging more than two indexes."""
        idx1 = PrecomputedIndexes(questions={1})
        idx2 = PrecomputedIndexes(questions={2})
        idx3 = PrecomputedIndexes(questions={3})

        merged = IndexBuilder.merge(idx1, idx2, idx3)

        assert merged.questions == {1, 2, 3}

    def test_merge_all_types(self):
        """Test merging indexes with all feature types."""
        idx1 = PrecomputedIndexes(
            entities={"ORG": {1}},
            questions={1},
            custom_features={"important": {1}},
        )
        idx2 = PrecomputedIndexes(
            entities={"PERSON": {2}},
            questions={2},
            custom_features={"urgent": {2}},
        )

        merged = IndexBuilder.merge(idx1, idx2)

        assert merged.entities == {"ORG": {1}, "PERSON": {2}}
        assert merged.questions == {1, 2}
        assert merged.custom_features == {
            "important": {1},
            "urgent": {2},
        }

    def test_merge_empty_indexes(self):
        """Test merging with empty indexes."""
        idx1 = PrecomputedIndexes()
        idx2 = PrecomputedIndexes(questions={1, 2})

        merged = IndexBuilder.merge(idx1, idx2)

        assert merged.questions == {1, 2}
        assert merged.entities == {}
        assert merged.custom_features == {}


class TestIntegration:
    """Integration tests combining IndexBuilder with PrismQL queries."""

    def test_llm_annotation_workflow(self):
        """Test complete workflow with LLM-style annotations."""
        # Simulate LLM-generated annotations
        messages = [
            {
                "id": 1,
                "text": "Can we schedule a meeting?",
                "intent": "request",
                "entities": [],
                "topics": ["meeting", "scheduling"],
            },
            {
                "id": 2,
                "text": "Sure, I'll set it up",
                "intent": "commit",
                "entities": [],
                "topics": ["meeting"],
            },
        ]

        # Build indexes
        indexes = IndexBuilder.from_message_annotations(
            messages,
            entity_field="entities",
            custom_fields={"intent": None, "topics": list},
        )

        # Verify features were extracted
        assert "intent_request" in indexes.custom_features
        assert "intent_commit" in indexes.custom_features
        assert "topics_meeting" in indexes.custom_features
        assert "topics_scheduling" in indexes.custom_features

        # Verify message IDs
        assert indexes.custom_features["intent_request"] == {1}
        assert indexes.custom_features["topics_meeting"] == {1, 2}

    def test_hybrid_annotation_workflow(self):
        """Test merging LLM and human annotations."""
        # LLM auto-annotations
        llm_messages = [
            {"id": 1, "topics": ["bug"]},
            {"id": 2, "topics": ["feature"]},
        ]
        llm_indexes = IndexBuilder.from_message_annotations(
            llm_messages, custom_fields={"topics": list}
        )

        # Human verification
        human_annotations = {
            1: {"verified": True, "severity": "high"},
            2: {"verified": False},
        }
        human_indexes = IndexBuilder.from_separate_annotations(
            human_annotations, custom_feature_keys=["verified", "severity"]
        )

        # Merge both sources
        combined = IndexBuilder.merge(llm_indexes, human_indexes)

        # Should have both LLM and human features
        assert "topics_bug" in combined.custom_features
        assert "topics_feature" in combined.custom_features
        assert True in combined.custom_features or "verified" in str(
            combined.custom_features
        )
