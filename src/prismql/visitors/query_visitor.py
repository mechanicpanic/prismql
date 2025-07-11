"""PrismQL query visitor implementation."""

import itertools
from typing import Any, Optional, Union
from collections.abc import Set, Sequence, Mapping

from antlr4 import InputStream, CommonTokenStream

from ..grammar.generated.PrismQLLexer import PrismQLLexer
from ..grammar.generated.PrismQLParser import PrismQLParser
from ..grammar.generated.PrismQLVisitor import PrismQLVisitor
from ..backends.base import SearchBackend, NLPBackend, PrecomputedIndexes
from ..types import MessageId, MessageGroup, QueryResult
from ..exceptions import PrismQLRuntimeError


class PrismQLVisitor(PrismQLVisitor):
    """
    Visitor that traverses the PrismQL parse tree and executes the query.
    
    This is the core query execution engine that interprets the query
    and calls appropriate backend methods.
    """
    
    DEFAULT_WINDOW_SIZE = 70
    MAX_MESSAGES_NOT = 1_000_000
    
    def __init__(
        self,
        search_backend: SearchBackend,
        nlp_backend: Optional[NLPBackend] = None,
        user_dictionaries: Optional[Mapping[str, Sequence[str]]] = None,
        precomputed_indexes: Optional[PrecomputedIndexes] = None,
    ):
        self.search_backend = search_backend
        self.nlp_backend = nlp_backend
        self.user_dictionaries = user_dictionaries or {}
        self.precomputed_indexes = precomputed_indexes or PrecomputedIndexes()
        
    def visitQuery(self, ctx: PrismQLParser.QueryContext) -> QueryResult:
        """Entry point - visit the query body."""
        return self.visitBody(ctx.body())
    
    def visitBody(self, ctx: PrismQLParser.BodyContext) -> QueryResult:
        """Process the query body with optional window constraint."""
        # Extract window size if specified
        window_size = self.DEFAULT_WINDOW_SIZE
        if ctx.InWin():
            window_size = int(ctx.number().getText())
        
        # Process either restrictions or query sequence
        if ctx.restrictions():
            # Single query with comma-separated restrictions
            restriction_results = self.visitRestrictions(ctx.restrictions())
            return self._merge_restrictions(restriction_results, window_size)
            
        elif ctx.query_seq():
            # Multiple subqueries in sequence
            subquery_results = self.visitQuery_seq(ctx.query_seq())
            return self._merge_queries(subquery_results, window_size)
        
        return []
    
    def visitQuery_seq(self, ctx: PrismQLParser.Query_seqContext) -> list[QueryResult]:
        """Process a sequence of subqueries."""
        results = []
        for query_ctx in ctx.query():
            result = self.visitQuery(query_ctx)
            results.append(result)
        return results
    
    def visitRestrictions(self, ctx: PrismQLParser.RestrictionsContext) -> list[MessageGroup]:
        """
        Process comma-separated restrictions.
        
        Returns a list of message groups, one for each restriction.
        If UNR flag is present, returns all permutations.
        """
        restriction_results = []
        
        # Process each restriction
        for restriction_ctx in ctx.restriction():
            result = self.visitRestriction(restriction_ctx)
            # Convert set to sorted list
            sorted_result = sorted(list(result))
            restriction_results.append(sorted_result)
        
        # Handle UNR (unrelated) flag - generate permutations
        if ctx.Unr():
            # Generate all permutations of taking one message from each group
            permutations = []
            for perm in itertools.product(*restriction_results):
                permutations.append(list(perm))
            return permutations
        else:
            # Return as-is (will be merged by window processor)
            return restriction_results
    
    def visitRestriction(self, ctx: PrismQLParser.RestrictionContext) -> Set[MessageId]:
        """Process a single restriction with boolean operators."""
        # Handle AND operator
        if ctx.And():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            return lhs & rhs  # Set intersection
        
        # Handle OR operator
        elif ctx.Or():
            lhs = self.visitRestriction(ctx.restriction(0))
            rhs = self.visitRestriction(ctx.restriction(1))
            return lhs | rhs  # Set union
        
        # Handle NOT operator
        elif ctx.Not():
            excluded = self.visitRestriction(ctx.restriction(0))
            # Get all message IDs up to a reasonable limit
            total_docs = min(self.MAX_MESSAGES_NOT, self.search_backend.get_total_documents())
            all_messages = self.search_backend.get_all_document_ids(limit=total_docs)
            return all_messages - excluded  # Set difference
        
        # Handle parentheses - just visit the inner restriction
        elif ctx.getChildCount() == 3 and ctx.getChild(0).getText() == '(':
            return self.visitRestriction(ctx.restriction(0))
        
        # Handle condition
        elif ctx.condition():
            return self.visitCondition(ctx.condition())
        
        # This shouldn't happen with a valid parse tree
        raise PrismQLRuntimeError("Invalid restriction in parse tree")
    
    def visitCondition(self, ctx: PrismQLParser.ConditionContext) -> Set[MessageId]:
        """Evaluate a single condition."""
        
        # New fluent operators (preferred)
        # contains(dict_name) - same as haswordofdict
        if ctx.Contains():
            dict_name = ctx.hdict().getText()
            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            words = self.user_dictionaries[dict_name]
            return self.search_backend.search_text(words, field="text", operator="OR")
        
        # from(username) - same as byuser
        elif ctx.From():
            username = ctx.huser().getText()
            return self.search_backend.search_by_field("user", username, exact=True)
        
        # mentions_user(username) - same as hasusermentioned
        elif ctx.MentionsUser():
            username = ctx.huser().getText()
            # First check precomputed index
            if username in self.precomputed_indexes.user_mentions:
                return self.precomputed_indexes.user_mentions[username]
            # Otherwise search in text
            return self.search_backend.search_text([username], field="text")
        
        # is_question() - same as hasquestion
        elif ctx.IsQuestion():
            return self._get_questions()
        
        # NER-based fluent conditions
        elif ctx.MentionsDate():
            return self._get_ner_messages("DATE")
        elif ctx.MentionsTime():
            return self._get_ner_messages("TIME")
        elif ctx.MentionsPlace():
            return self._get_ner_messages("GPE")  # or "LOC" depending on NLP backend
        elif ctx.MentionsOrg():
            return self._get_ner_messages("ORG")
        elif ctx.ContainsLink():
            return self._get_ner_messages("URL")
        
        # Legacy operators (backward compatibility)
        elif ctx.HasWordOfDict():
            dict_name = ctx.hdict().getText()
            if dict_name not in self.user_dictionaries:
                raise PrismQLRuntimeError(f"Dictionary '{dict_name}' not found")
            words = self.user_dictionaries[dict_name]
            return self.search_backend.search_text(words, field="text", operator="OR")
        
        elif ctx.ByUser():
            username = ctx.huser().getText()
            return self.search_backend.search_by_field("user", username, exact=True)
        
        elif ctx.HasUserMentioned():
            username = ctx.huser().getText()
            if username in self.precomputed_indexes.user_mentions:
                return self.precomputed_indexes.user_mentions[username]
            return self.search_backend.search_text([username], field="text")
        
        elif ctx.HasQuestion():
            return self._get_questions()
        
        elif ctx.HasDate():
            return self._get_ner_messages("DATE")
        elif ctx.HasTime():
            return self._get_ner_messages("TIME")
        elif ctx.HasLocation():
            return self._get_ner_messages("GPE")
        elif ctx.HasOrganization():
            return self._get_ner_messages("ORG")
        elif ctx.HasURL():
            return self._get_ner_messages("URL")
        
        raise PrismQLRuntimeError("Unknown condition type")
    
    def _get_questions(self) -> Set[MessageId]:
        """Helper method to get questions (used by both new and legacy operators)."""
        # First check precomputed index
        if self.precomputed_indexes.questions:
            return self.precomputed_indexes.questions
        
        # Check if backend supports question detection
        if hasattr(self.search_backend, 'get_questions'):
            return self.search_backend.get_questions()
        
        # Otherwise would need NLP backend
        if not self.nlp_backend:
            raise PrismQLRuntimeError("Question detection requires NLP backend or precomputed indexes")
        # This would require iterating through all messages - not efficient
        raise PrismQLRuntimeError("Question detection requires precomputed indexes for large datasets")
    
    def _get_ner_messages(self, ner_label: str) -> Set[MessageId]:
        """Get messages containing specific NER type."""
        # First check precomputed index
        if ner_label in self.precomputed_indexes.entities:
            return self.precomputed_indexes.entities[ner_label]
        
        # Otherwise would need NLP backend
        if not self.nlp_backend:
            raise PrismQLRuntimeError(f"NER condition requires NLP backend or precomputed indexes")
        
        # This would require iterating through all messages - not efficient
        raise PrismQLRuntimeError(f"NER conditions require precomputed indexes for large datasets")
    
    def _merge_restrictions(self, groups: list[MessageGroup], window_size: int) -> QueryResult:
        """
        Merge restriction results within sliding windows.
        
        This implements the core windowing logic that groups messages
        that appear within window_size of each other.
        """
        if not groups:
            return []
        
        # If single group, each message becomes its own result group
        if len(groups) == 1:
            return [[msg_id] for msg_id in groups[0]]
        
        
        # Otherwise, implement sliding window merge
        # This is a simplified version - full implementation would use
        # the histogram-based algorithm from the C# code
        from ..processors.window import WindowProcessor
        return WindowProcessor.merge_restrictions(groups, window_size)
    
    def _merge_queries(self, subquery_results: list[QueryResult], window_size: int) -> QueryResult:
        """Merge results from multiple subqueries."""
        if not subquery_results:
            return []
        
        # Flatten all groups from all subqueries
        all_groups = []
        for subquery_result in subquery_results:
            all_groups.extend(subquery_result)
        
        # Apply window processing
        from ..processors.window import WindowProcessor
        return WindowProcessor.merge_queries(all_groups, window_size)