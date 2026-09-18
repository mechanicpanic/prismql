"""spaCy NLP backend implementation for PrismQL."""

import re
from collections.abc import Mapping
from typing import Any

from ..types import NERLabel
from .base import NLPBackend


class SpacyBackend(NLPBackend):
    """
    spaCy-based NLP backend for PrismQL.

    This backend uses spaCy for named entity recognition, question detection,
    and other natural language processing tasks.

    Example configuration:
        config = {
            "model": "en_core_web_sm",  # or your loaded nlp object
            "entity_mappings": {
                "PERSON": "PERSON",
                "GPE": "LOCATION",
                "ORG": "ORGANIZATION",
                "DATE": "DATE",
                "TIME": "TIME"
            },
            "question_patterns": [
                r"\\?$",  # Ends with question mark
                r"^(what|who|when|where|why|how)",  # Question words
            ],
            "batch_size": 100  # For batch processing
        }

        backend = SpacyBackend(nlp_model, config)
    """

    def __init__(self, nlp: Any, config: dict[str, Any] | None = None) -> None:
        """
        Initialize spaCy backend.

        Args:
            nlp: spaCy nlp object (e.g., spacy.load("en_core_web_sm"))
            config: Optional configuration dictionary
        """
        self.nlp = nlp
        self.config = config or {}

        # Entity label mappings (spaCy label -> PrismQL label)
        self.entity_mappings = self.config.get(
            "entity_mappings",
            {
                "PERSON": "PERSON",
                "GPE": "LOCATION",  # Geopolitical entity -> location
                "LOC": "LOCATION",  # Location
                "ORG": "ORGANIZATION",
                "DATE": "DATE",
                "TIME": "TIME",
                "CARDINAL": "NUMBER",
                "MONEY": "MONEY",
                "PERCENT": "PERCENT",
            },
        )

        # Question detection patterns
        self.question_patterns = self.config.get(
            "question_patterns",
            [
                r"\?$",  # Ends with question mark
                r"^(what|who|when|where|why|how|which|can|could|would|should|do|does|did|is|are|was|were|will|may|might)\b",
            ],
        )

        # Compile regex patterns
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.question_patterns
        ]

        # Batch processing size
        self.batch_size = self.config.get("batch_size", 100)

    def extract_entities(self, text: str) -> Mapping[NERLabel, list[str]]:
        """
        Extract named entities from text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping entity types to lists of entity texts
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)

            # Group entities by type
            entities: dict[NERLabel, list[str]] = {}

            for ent in doc.ents:
                # Map spaCy label to PrismQL label
                mapped_label = self.entity_mappings.get(ent.label_, ent.label_)

                # Add entity text (normalized)
                entity_text = ent.text.strip()
                if entity_text:  # Only process non-empty entities
                    if mapped_label not in entities:
                        entities[mapped_label] = []
                    if entity_text not in entities[mapped_label]:
                        entities[mapped_label].append(entity_text)

            return entities

        except Exception:
            # Return empty dict on error rather than failing
            return {}

    def has_question(self, text: str) -> bool:
        """
        Check if text contains a question.

        Args:
            text: Text to analyze

        Returns:
            True if text contains a question
        """
        text = text.strip()

        # Check against compiled patterns
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return True

        # Additional heuristics using spaCy
        try:
            doc = self.nlp(text)

            # Look for question-like dependency patterns
            for token in doc:
                # Check for question words in specific positions
                if (
                    token.pos_ == "PRON"
                    and token.dep_ in ["nsubj", "nsubjpass"]
                    and token.text.lower()
                    in ["what", "who", "which", "where", "when", "why", "how"]
                ):
                    return True

                # Check for auxiliary verbs at sentence start (common in questions)
                if (
                    token.i == 0
                    and token.pos_ == "AUX"
                    and token.text.lower()
                    in [
                        "is",
                        "are",
                        "was",
                        "were",
                        "do",
                        "does",
                        "did",
                        "can",
                        "could",
                        "will",
                        "would",
                        "should",
                        "may",
                        "might",
                    ]
                ):
                    return True

        except Exception:
            # Fallback to pattern matching only
            pass

        return False

    def extract_noun_phrases(self, text: str) -> list[str]:
        """
        Extract noun phrases from text.

        Args:
            text: Text to analyze

        Returns:
            List of noun phrases
        """
        try:
            doc = self.nlp(text)

            noun_phrases = []
            for chunk in doc.noun_chunks:
                phrase = chunk.text.strip()
                if phrase and len(phrase) > 1:  # Filter out single characters
                    noun_phrases.append(phrase)

            return noun_phrases

        except Exception:
            return []

    def process_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """
        Process multiple texts in batch for efficiency.

        Args:
            texts: List of texts to process

        Returns:
            List of processing results for each text
        """
        results = []

        try:
            # Process in batches using spaCy's pipe
            for doc in self.nlp.pipe(texts, batch_size=self.batch_size):
                result = {"entities": {}, "is_question": False, "noun_phrases": []}

                # Extract entities
                entities: dict[NERLabel, list[str]] = {}
                for ent in doc.ents:
                    mapped_label = self.entity_mappings.get(ent.label_, ent.label_)
                    entity_text = ent.text.strip()
                    if entity_text:  # Only process non-empty entities
                        if mapped_label not in entities:
                            entities[mapped_label] = []
                        if entity_text not in entities[mapped_label]:
                            entities[mapped_label].append(entity_text)
                result["entities"] = entities

                # Check if question
                text = doc.text.strip()
                is_question = False
                for pattern in self._compiled_patterns:
                    if pattern.search(text):
                        is_question = True
                        break

                if not is_question:
                    # Additional heuristics
                    for token in doc:
                        if (
                            token.pos_ == "PRON"
                            and token.dep_ in ["nsubj", "nsubjpass"]
                            and token.text.lower()
                            in ["what", "who", "which", "where", "when", "why", "how"]
                        ):
                            is_question = True
                            break
                        if (
                            token.i == 0
                            and token.pos_ == "AUX"
                            and token.text.lower()
                            in [
                                "is",
                                "are",
                                "was",
                                "were",
                                "do",
                                "does",
                                "did",
                                "can",
                                "could",
                                "will",
                                "would",
                                "should",
                                "may",
                                "might",
                            ]
                        ):
                            is_question = True
                            break

                result["is_question"] = is_question

                # Extract noun phrases
                noun_phrases = []
                for chunk in doc.noun_chunks:
                    phrase = chunk.text.strip()
                    if phrase and len(phrase) > 1:
                        noun_phrases.append(phrase)
                result["noun_phrases"] = noun_phrases

                results.append(result)

        except Exception:
            # Fallback to individual processing
            for text in texts:
                result = {
                    "entities": self.extract_entities(text),
                    "is_question": self.has_question(text),
                    "noun_phrases": self.extract_noun_phrases(text),
                }
                results.append(result)

        return results

    def get_supported_entities(self) -> list[str]:
        """
        Get list of supported entity types.

        Returns:
            List of entity type labels this backend can extract
        """
        return list(self.entity_mappings.values())

    def get_model_info(self) -> dict[str, Any]:
        """
        Get information about the loaded spaCy model.

        Returns:
            Dictionary with model information
        """
        try:
            meta = self.nlp.meta
            return {
                "name": meta.get("name", "unknown"),
                "version": meta.get("version", "unknown"),
                "language": meta.get("lang", "unknown"),
                "pipeline": list(self.nlp.pipe_names),
                "entity_types": list(self.nlp.get_pipe("ner").labels)
                if "ner" in self.nlp.pipe_names
                else [],
            }
        except Exception:
            return {
                "name": "unknown",
                "version": "unknown",
                "language": "unknown",
                "pipeline": [],
                "entity_types": [],
            }
