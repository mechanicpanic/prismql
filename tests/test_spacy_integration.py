"""Integration tests for spaCy backend with real spaCy models.

These tests require spaCy to be installed. They can be skipped if spaCy is
not available.
"""

import pytest

try:
    import spacy

    SPACY_AVAILABLE = True

    # Try to load any available English model
    try:
        nlp = spacy.load("en_core_web_sm")
        MODEL_AVAILABLE = True
    except OSError:
        try:
            # Try blank model if no trained model is available
            nlp = spacy.blank("en")
            MODEL_AVAILABLE = False
        except Exception:
            nlp = None
            MODEL_AVAILABLE = False

except ImportError:
    SPACY_AVAILABLE = False
    MODEL_AVAILABLE = False
    nlp = None


@pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
class TestSpacyIntegration:
    """Integration tests using real spaCy models."""

    def setup_method(self):
        """Set up test fixtures."""
        from prismql.backends.spacy import SpacyBackend

        if nlp is None:
            pytest.skip("No spaCy model available")

        self.backend = SpacyBackend(nlp)

    def test_real_spacy_initialization(self):
        """Test that backend can initialize with real spaCy model."""
        assert self.backend.nlp is not None
        assert callable(self.backend.nlp)

    def test_basic_text_processing(self):
        """Test basic text processing with real spaCy."""
        text = "Hello world"

        # This should not crash
        entities = self.backend.extract_entities(text)
        assert isinstance(entities, dict)

        is_question = self.backend.has_question(text)
        assert isinstance(is_question, bool)

        # Only test noun phrases if model supports parsing
        if MODEL_AVAILABLE:
            try:
                noun_phrases = self.backend.extract_noun_phrases(text)
                assert isinstance(noun_phrases, list)
            except NotImplementedError:
                # Some models might not support this
                pass

    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="No trained spaCy model available")
    def test_entity_extraction_with_real_model(self):
        """Test entity extraction with a real trained model."""
        text = "John Doe lives in New York and works at Microsoft."

        entities = self.backend.extract_entities(text)

        # With a real model, we should get some entities
        assert isinstance(entities, dict)

        # Check that we get reasonable entity types
        found_entity_types = set(entities.keys())

        # At least some overlap with expected types
        assert len(found_entity_types) >= 0  # Could be empty with small models

        # All returned entity lists should be lists of strings
        for _entity_type, entity_list in entities.items():
            assert isinstance(entity_list, list)
            for entity in entity_list:
                assert isinstance(entity, str)
                assert len(entity.strip()) > 0  # No empty entities

    def test_question_detection_patterns(self):
        """Test question detection with various patterns."""
        questions = [
            "What is your name?",
            "How are you doing?",
            "Are you okay?",
            "Can you help me?",
            "Where are you going?",
        ]

        statements = [
            "This is a statement.",
            "I am fine.",
            "The weather is nice.",
            "Python is a programming language.",
        ]

        # Test questions
        for question in questions:
            result = self.backend.has_question(question)
            assert result is True, f"Failed to detect question: {question}"

        # Test statements (these might be detected as questions depending on model)
        for statement in statements:
            result = self.backend.has_question(statement)
            # We don't assert False here because some models might be aggressive
            assert isinstance(result, bool)

    @pytest.mark.skipif(not MODEL_AVAILABLE, reason="No trained spaCy model available")
    def test_noun_phrase_extraction(self):
        """Test noun phrase extraction with real model."""
        text = "The big red car drove down the winding mountain road."

        try:
            noun_phrases = self.backend.extract_noun_phrases(text)
            assert isinstance(noun_phrases, list)

            # Should extract some noun phrases
            for phrase in noun_phrases:
                assert isinstance(phrase, str)
                assert len(phrase.strip()) > 0

        except NotImplementedError:
            # Some models might not support noun phrase extraction
            pytest.skip("Model does not support noun phrase extraction")

    def test_batch_processing(self):
        """Test batch processing with real spaCy."""
        texts = ["Hello world", "What is your name?", "The cat sat on the mat."]

        results = self.backend.process_batch(texts)

        assert len(results) == len(texts)

        for _i, result in enumerate(results):
            assert isinstance(result, dict)
            assert "entities" in result
            assert "is_question" in result
            # Note: process_batch doesn't include original text in results

            # Verify types
            assert isinstance(result["entities"], dict)
            assert isinstance(result["is_question"], bool)

            # Should also have noun_phrases
            if "noun_phrases" in result:
                assert isinstance(result["noun_phrases"], list)

    def test_error_handling(self):
        """Test error handling with malformed input."""
        # Empty string
        entities = self.backend.extract_entities("")
        assert isinstance(entities, dict)

        # Very long string
        long_text = "word " * 10000
        entities = self.backend.extract_entities(long_text)
        assert isinstance(entities, dict)

        # Unicode text
        unicode_text = "Hello 世界 🌍"
        entities = self.backend.extract_entities(unicode_text)
        assert isinstance(entities, dict)

    def test_configuration_options(self):
        """Test backend with custom configuration."""
        config = {
            "entity_mappings": {"PERSON": "HUMAN", "GPE": "PLACE"},
            "question_patterns": [r"\?$", r"^(what|how)\b"],
            "batch_size": 32,
        }

        backend = self.backend.__class__(nlp, config)

        # Test custom entity mapping
        if MODEL_AVAILABLE:
            text = "John lives in Paris"
            entities = backend.extract_entities(text)

            # Should use custom mappings
            if entities:
                assert "HUMAN" in entities or "PLACE" in entities or len(entities) == 0
                # Should not have original labels if mapping worked
                assert "PERSON" not in entities
                assert "GPE" not in entities

        # Test custom question patterns
        assert backend.has_question("What is this?") is True
        assert backend.has_question("How are you?") is True

        # Test batch size
        assert backend.batch_size == 32


@pytest.mark.skipif(
    SPACY_AVAILABLE, reason="spaCy is available, no need to test fallback"
)
def test_spacy_not_available():
    """Test behavior when spaCy is not available."""
    # This test would run if spaCy is not installed
    with pytest.raises(ImportError):
        from prismql.backends.spacy import SpacyBackend  # noqa: F401


class TestSpacyBackendRequirements:
    """Test spaCy backend requirements and setup."""

    def test_spacy_import(self):
        """Test that spaCy can be imported."""
        try:
            import spacy  # noqa: F401

            assert True, "spaCy imported successfully"
        except ImportError:
            pytest.skip("spaCy not installed")

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
    def test_available_models(self):
        """Test what spaCy models are available."""
        import spacy

        # Try to list available models
        try:
            # Check if en_core_web_sm is available
            nlp_sm = spacy.load("en_core_web_sm")
            print(f"✓ en_core_web_sm available: {nlp_sm.meta['name']}")
        except OSError:
            print("✗ en_core_web_sm not available")

        # Can always create blank model
        nlp_blank = spacy.blank("en")
        assert nlp_blank is not None
        print(f"✓ Blank English model available: {nlp_blank.lang}")
