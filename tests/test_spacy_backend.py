"""Tests for spaCy NLP backend."""

from unittest.mock import MagicMock, Mock

from prismql.backends.spacy import SpacyBackend


class TestSpacyBackend:
    """Test suite for spaCy NLP backend."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create mock spaCy nlp object
        self.mock_nlp = MagicMock()

        # Mock doc objects
        self.mock_doc = MagicMock()
        self.mock_nlp.return_value = self.mock_doc

        # Basic configuration
        self.config = {
            "entity_mappings": {
                "PERSON": "PERSON",
                "GPE": "LOCATION",
                "ORG": "ORGANIZATION",
            },
            "question_patterns": [r"\?$", r"^(what|who|how)\b"],
            "batch_size": 50,
        }

        self.backend = SpacyBackend(self.mock_nlp, self.config)

    def test_init_with_config(self):
        """Test backend initialization with configuration."""
        assert self.backend.entity_mappings["PERSON"] == "PERSON"
        assert self.backend.entity_mappings["GPE"] == "LOCATION"
        assert self.backend.batch_size == 50
        assert len(self.backend._compiled_patterns) == 2

    def test_init_without_config(self):
        """Test backend initialization without configuration."""
        backend = SpacyBackend(self.mock_nlp)

        # Should use defaults
        assert "PERSON" in backend.entity_mappings
        assert "GPE" in backend.entity_mappings
        assert backend.batch_size == 100
        assert len(backend._compiled_patterns) > 0

    def test_extract_entities_basic(self):
        """Test basic entity extraction."""
        # Mock entities
        mock_ent1 = MagicMock()
        mock_ent1.text = "John Doe"
        mock_ent1.label_ = "PERSON"

        mock_ent2 = MagicMock()
        mock_ent2.text = "New York"
        mock_ent2.label_ = "GPE"

        self.mock_doc.ents = [mock_ent1, mock_ent2]

        result = self.backend.extract_entities("John Doe lives in New York")

        self.mock_nlp.assert_called_once_with("John Doe lives in New York")

        expected = {
            "PERSON": ["John Doe"],
            "LOCATION": ["New York"],  # GPE -> LOCATION mapping
        }
        assert result == expected

    def test_extract_entities_unmapped_label(self):
        """Test entity extraction with unmapped label."""
        mock_ent = MagicMock()
        mock_ent.text = "Apple Inc"
        mock_ent.label_ = "UNKNOWN_LABEL"

        self.mock_doc.ents = [mock_ent]

        result = self.backend.extract_entities("Apple Inc is great")

        # Should use original label when no mapping exists
        expected = {"UNKNOWN_LABEL": ["Apple Inc"]}
        assert result == expected

    def test_extract_entities_duplicate_removal(self):
        """Test that duplicate entities are removed."""
        mock_ent1 = MagicMock()
        mock_ent1.text = "John"
        mock_ent1.label_ = "PERSON"

        mock_ent2 = MagicMock()
        mock_ent2.text = "John"  # Duplicate
        mock_ent2.label_ = "PERSON"

        self.mock_doc.ents = [mock_ent1, mock_ent2]

        result = self.backend.extract_entities("John and John")

        expected = {"PERSON": ["John"]}  # Only one "John"
        assert result == expected

    def test_extract_entities_whitespace_handling(self):
        """Test entity extraction handles whitespace."""
        mock_ent = MagicMock()
        mock_ent.text = "  John Doe  "  # With whitespace
        mock_ent.label_ = "PERSON"

        self.mock_doc.ents = [mock_ent]

        result = self.backend.extract_entities("Text with whitespace")

        expected = {"PERSON": ["John Doe"]}  # Stripped
        assert result == expected

    def test_extract_entities_empty_text(self):
        """Test entity extraction with empty entity text."""
        mock_ent = MagicMock()
        mock_ent.text = "   "  # Only whitespace
        mock_ent.label_ = "PERSON"

        self.mock_doc.ents = [mock_ent]

        result = self.backend.extract_entities("Empty entity test")

        assert result == {}  # Empty entity should be filtered out

    def test_extract_entities_error_handling(self):
        """Test entity extraction error handling."""
        self.mock_nlp.side_effect = Exception("spaCy error")

        result = self.backend.extract_entities("This will fail")

        assert result == {}  # Should return empty dict on error

    def test_has_question_with_question_mark(self):
        """Test question detection with question mark."""
        result = self.backend.has_question("How are you?")
        assert result is True

    def test_has_question_with_question_word(self):
        """Test question detection with question word."""
        result = self.backend.has_question("What is your name")
        assert result is True

    def test_has_question_no_question(self):
        """Test question detection with non-question."""
        # Mock spaCy processing for dependency analysis
        mock_token = MagicMock()
        mock_token.pos_ = "NOUN"
        mock_token.text = "hello"
        mock_token.i = 0
        self.mock_doc.__iter__ = Mock(return_value=iter([mock_token]))

        result = self.backend.has_question("This is a statement")
        assert result is False

    def test_has_question_spacy_heuristics(self):
        """Test question detection using spaCy dependency patterns."""
        # Mock token for question word heuristic
        mock_token = MagicMock()
        mock_token.pos_ = "PRON"
        mock_token.dep_ = "nsubj"
        mock_token.text = "what"
        mock_token.i = 0
        self.mock_doc.__iter__ = Mock(return_value=iter([mock_token]))

        result = self.backend.has_question("what is happening")
        assert result is True

    def test_has_question_auxiliary_verb(self):
        """Test question detection with auxiliary verb at start."""
        mock_token = MagicMock()
        mock_token.pos_ = "AUX"
        mock_token.text = "is"
        mock_token.i = 0  # At start of sentence
        self.mock_doc.__iter__ = Mock(return_value=iter([mock_token]))

        result = self.backend.has_question("is this working")
        assert result is True

    def test_has_question_spacy_error_fallback(self):
        """Test question detection fallback when spaCy fails."""
        # Make spaCy analysis fail but pattern matching should still work
        self.mock_doc.__iter__ = Mock(side_effect=Exception("spaCy error"))

        result = self.backend.has_question("How are you?")  # Has question mark
        assert result is True

    def test_extract_noun_phrases(self):
        """Test noun phrase extraction."""
        # Mock noun chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "the big dog"

        mock_chunk2 = MagicMock()
        mock_chunk2.text = "a small cat"

        self.mock_doc.noun_chunks = [mock_chunk1, mock_chunk2]

        result = self.backend.extract_noun_phrases("The big dog chased a small cat")

        expected = ["the big dog", "a small cat"]
        assert result == expected

    def test_extract_noun_phrases_filtering(self):
        """Test noun phrase extraction filters short phrases."""
        mock_chunk = MagicMock()
        mock_chunk.text = "a"  # Single character

        self.mock_doc.noun_chunks = [mock_chunk]

        result = self.backend.extract_noun_phrases("a")

        assert result == []  # Should be filtered out

    def test_extract_noun_phrases_whitespace(self):
        """Test noun phrase extraction handles whitespace."""
        mock_chunk = MagicMock()
        mock_chunk.text = "  the house  "

        self.mock_doc.noun_chunks = [mock_chunk]

        result = self.backend.extract_noun_phrases("the house")

        assert result == ["the house"]  # Stripped

    def test_extract_noun_phrases_error(self):
        """Test noun phrase extraction error handling."""
        self.mock_nlp.side_effect = Exception("spaCy error")

        result = self.backend.extract_noun_phrases("This will fail")

        assert result == []

    def test_process_batch(self):
        """Test batch processing of texts."""
        texts = ["Hello John", "How are you?", "New York is nice"]

        # Mock pipe method
        mock_doc1 = MagicMock()
        mock_doc1.text = "Hello John"

        mock_ent1 = MagicMock()
        mock_ent1.text = "John"
        mock_ent1.label_ = "PERSON"
        mock_doc1.ents = [mock_ent1]

        mock_doc1.__iter__ = Mock(return_value=iter([]))  # No special tokens
        mock_doc1.noun_chunks = []

        mock_doc2 = MagicMock()
        mock_doc2.text = "How are you?"
        mock_doc2.ents = []
        mock_doc2.__iter__ = Mock(return_value=iter([]))
        mock_doc2.noun_chunks = []

        mock_doc3 = MagicMock()
        mock_doc3.text = "New York is nice"

        mock_ent3 = MagicMock()
        mock_ent3.text = "New York"
        mock_ent3.label_ = "GPE"
        mock_doc3.ents = [mock_ent3]

        mock_doc3.__iter__ = Mock(return_value=iter([]))
        mock_doc3.noun_chunks = []

        self.mock_nlp.pipe.return_value = [mock_doc1, mock_doc2, mock_doc3]

        results = self.backend.process_batch(texts)

        # Verify pipe was called with correct parameters
        self.mock_nlp.pipe.assert_called_once_with(texts, batch_size=50)

        assert len(results) == 3

        # First result - entity extraction
        assert results[0]["entities"] == {"PERSON": ["John"]}
        assert results[0]["is_question"] is False

        # Second result - question detection
        assert results[1]["entities"] == {}
        assert results[1]["is_question"] is True  # "How are you?" pattern

        # Third result - entity mapping
        assert results[2]["entities"] == {"LOCATION": ["New York"]}  # GPE -> LOCATION
        assert results[2]["is_question"] is False

    def test_process_batch_error_fallback(self):
        """Test batch processing falls back to individual processing on error."""
        texts = ["Hello", "World"]

        # Make pipe fail
        self.mock_nlp.pipe.side_effect = Exception("Pipe failed")

        # Mock individual calls
        mock_doc = MagicMock()
        mock_doc.ents = []
        mock_doc.__iter__ = Mock(return_value=iter([]))
        mock_doc.noun_chunks = []
        self.mock_nlp.return_value = mock_doc

        results = self.backend.process_batch(texts)

        # Should fall back to individual processing
        assert len(results) == 2
        # Each text is processed 3 times (entities, question, noun_phrases)
        assert self.mock_nlp.call_count == 6  # 2 texts * 3 methods = 6 calls

    def test_get_supported_entities(self):
        """Test getting supported entity types."""
        result = self.backend.get_supported_entities()

        expected = ["PERSON", "LOCATION", "ORGANIZATION"]  # Mapped values
        assert set(result) >= set(expected)

    def test_get_model_info(self):
        """Test getting model information."""
        # Mock model metadata
        self.mock_nlp.meta = {
            "name": "en_core_web_sm",
            "version": "3.4.0",
            "lang": "en",
        }
        self.mock_nlp.pipe_names = ["tagger", "parser", "ner"]

        # Mock NER pipe
        mock_ner = MagicMock()
        mock_ner.labels = ["PERSON", "GPE", "ORG"]
        self.mock_nlp.get_pipe.return_value = mock_ner

        result = self.backend.get_model_info()

        expected = {
            "name": "en_core_web_sm",
            "version": "3.4.0",
            "language": "en",
            "pipeline": ["tagger", "parser", "ner"],
            "entity_types": ["PERSON", "GPE", "ORG"],
        }
        assert result == expected

    def test_get_model_info_error_handling(self):
        """Test model info error handling."""
        self.mock_nlp.meta = None  # Simulate missing metadata

        result = self.backend.get_model_info()

        # Should return defaults on error
        expected = {
            "name": "unknown",
            "version": "unknown",
            "language": "unknown",
            "pipeline": [],
            "entity_types": [],
        }
        assert result == expected

    def test_custom_question_patterns(self):
        """Test custom question patterns in configuration."""
        config = {"question_patterns": [r"^tell me\b"]}
        backend = SpacyBackend(self.mock_nlp, config)

        assert backend.has_question("tell me about this") is True
        assert (
            backend.has_question("what is this") is False
        )  # Default patterns not included
