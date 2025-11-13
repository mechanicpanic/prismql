"""
Test cases for LLM query generation experiments.

Each test case has:
- Natural language request
- Ground truth PrismQL query
- Expected result (for semantic validation)
- Difficulty level
- Category
"""

from dataclasses import dataclass


@dataclass
class TestCase:
    """A single test case for query generation."""

    id: str
    description: str  # What we tell the LLM
    ground_truth_query: str  # Correct PrismQL query
    category: str  # Type of query (basic, window, pattern, etc.)
    difficulty: str  # easy, medium, hard
    required_dictionaries: dict[str, list[str]]  # Dictionaries needed
    notes: str = ""  # Additional context

    def __str__(self) -> str:
        return f"TestCase({self.id}: {self.description})"


# =============================================================================
# BASIC QUERIES (Easy)
# =============================================================================

BASIC_QUERIES = [
    TestCase(
        id="basic_001",
        description="Find all messages from alice",
        ground_truth_query="SELECT from(alice)",
        category="basic_filtering",
        difficulty="easy",
        required_dictionaries={},
    ),
    TestCase(
        id="basic_002",
        description="Find all questions in the conversation",
        ground_truth_query="SELECT is_question()",
        category="basic_filtering",
        difficulty="easy",
        required_dictionaries={},
    ),
    TestCase(
        id="basic_003",
        description="Find messages containing greeting words like 'hello' or 'hi'",
        ground_truth_query="SELECT contains(greetings)",
        category="basic_filtering",
        difficulty="easy",
        required_dictionaries={"greetings": ["hello", "hi", "hey"]},
    ),
    TestCase(
        id="basic_004",
        description="Find messages from bob or charlie",
        ground_truth_query="SELECT from(bob) OR from(charlie)",
        category="boolean_operations",
        difficulty="easy",
        required_dictionaries={},
    ),
    TestCase(
        id="basic_005",
        description="Find questions from alice",
        ground_truth_query="SELECT from(alice) AND is_question()",
        category="boolean_operations",
        difficulty="easy",
        required_dictionaries={},
    ),
]

# =============================================================================
# WINDOW QUERIES (Medium) - INWINDOW tests unordered co-occurrence
# =============================================================================

WINDOW_QUERIES = [
    TestCase(
        id="window_001",
        description="Find conversations where greetings and support responses appear together within 3 messages (any order)",
        ground_truth_query="SELECT contains(greetings), from(support) INWINDOW 3",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey"]},
        notes="INWINDOW is unordered - greeting can come before or after support response",
    ),
    TestCase(
        id="window_002",
        description="Find conversations where problems and solutions are both mentioned within 10 messages (any order)",
        ground_truth_query="SELECT contains(problems), contains(solutions) INWINDOW 10",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "solved"],
        },
        notes="INWINDOW is unordered - problem and solution can appear in any order",
    ),
    TestCase(
        id="window_003",
        description="Find conversations where questions and support messages appear together within 5 messages (any order)",
        ground_truth_query="SELECT is_question(), from(support) INWINDOW 5",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="INWINDOW is unordered - question can come before or after support message",
    ),
]

# =============================================================================
# SEQUENTIAL PATTERNS (Medium-Hard) - FOLLOWED_BY tests ordered sequences
# =============================================================================

SEQUENTIAL_QUERIES = [
    TestCase(
        id="seq_001",
        description="Find messages from alice followed by messages from bob within 2 positions",
        ground_truth_query="SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 2",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="Order matters: alice THEN bob, not bob then alice",
    ),
    TestCase(
        id="seq_002",
        description="Find questions that are followed by a response from support within 3 messages",
        ground_truth_query="SELECT is_question() FOLLOWED_BY from(support) INWINDOW 3",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="Order matters: question THEN support response",
    ),
    TestCase(
        id="seq_003",
        description="Find messages from customer that are NOT followed by support within 5 messages (unanswered)",
        ground_truth_query="SELECT from(customer) NOT_FOLLOWED_BY from(support) INWINDOW 5",
        category="sequential_patterns",
        difficulty="hard",
        required_dictionaries={},
        notes="Tests understanding of negative lookahead",
    ),
    TestCase(
        id="seq_004",
        description="Find greetings followed by a response from support within 3 messages",
        ground_truth_query="SELECT contains(greetings) FOLLOWED_BY from(support) INWINDOW 3",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey"]},
        notes="Order matters: greeting THEN support response",
    ),
    TestCase(
        id="seq_005",
        description="Find problem mentions followed by solution mentions within 10 messages",
        ground_truth_query="SELECT contains(problems) FOLLOWED_BY contains(solutions) INWINDOW 10",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "solved"],
        },
        notes="Order matters: problem THEN solution (not solution then problem)",
    ),
    TestCase(
        id="seq_006",
        description="Find messages from support that are preceded by a question within 3 messages",
        ground_truth_query="SELECT from(support) PRECEDED_BY is_question() INWINDOW 3",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="Order matters: question THEN support (PRECEDED_BY is reverse of FOLLOWED_BY)",
    ),
    TestCase(
        id="seq_007",
        description="Find support messages that are NOT preceded by a question within 5 messages",
        ground_truth_query="SELECT from(support) NOT_PRECEDED_BY is_question() INWINDOW 5",
        category="sequential_patterns",
        difficulty="hard",
        required_dictionaries={},
        notes="Tests understanding of negative lookbehind - support messages without prior questions",
    ),
]

# =============================================================================
# COMPLEX PATTERNS (Hard)
# =============================================================================

COMPLEX_QUERIES = [
    TestCase(
        id="complex_001",
        description="Find customer questions about problems that are followed by support providing solutions within 10 messages",
        ground_truth_query="SELECT (from(customer) AND is_question() AND contains(problems)) FOLLOWED_BY (from(support) AND contains(solutions)) INWINDOW 10",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "try"],
        },
        notes="Sequential pattern: customer problem THEN support solution",
    ),
    TestCase(
        id="complex_002",
        description="Find conversations with customer greeting, support greeting, and customer question all appearing within 5 messages (any order)",
        ground_truth_query="SELECT from(customer) AND contains(greetings), from(support) AND contains(greetings), from(customer) AND is_question() INWINDOW 5",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
        notes="INWINDOW is unordered - these three elements can appear in any sequence",
    ),
    TestCase(
        id="complex_004",
        description="Find customer greeting followed by support greeting within 3 messages, then followed by customer question within 2 more messages",
        ground_truth_query="SELECT (from(customer) AND contains(greetings)) FOLLOWED_BY (from(support) AND contains(greetings)) WITHIN 3 FOLLOWED_BY (from(customer) AND is_question()) INWINDOW 2",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
        notes="Chained sequential pattern with separate WITHIN constraints for each transition",
    ),
    TestCase(
        id="complex_003",
        description="Find questions from alice that are preceded by bob within 2 messages and followed by charlie within 3 messages",
        ground_truth_query="SELECT from(alice) AND is_question() PRECEDED_BY from(bob) INWINDOW 2 FOLLOWED_BY from(charlie) INWINDOW 3",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={},
        notes="Tests chaining of positional operators",
    ),
]

# =============================================================================
# EDGE CASES (Tests understanding of syntax nuances)
# =============================================================================

EDGE_CASE_QUERIES = [
    TestCase(
        id="edge_001",
        description="Find messages that are NOT from alice",
        ground_truth_query="SELECT NOT from(alice)",
        category="edge_cases",
        difficulty="medium",
        required_dictionaries={},
        notes="Tests understanding of NOT operator",
    ),
    TestCase(
        id="edge_002",
        description="Find messages from alice OR bob, where they ask questions",
        ground_truth_query="SELECT (from(alice) OR from(bob)) AND is_question()",
        category="edge_cases",
        difficulty="medium",
        required_dictionaries={},
        notes="Tests understanding of operator precedence",
    ),
    TestCase(
        id="edge_003",
        description="Find the same user asking a question and then thanking within 10 messages",
        ground_truth_query="SELECT (from($user) AND is_question()) FOLLOWED_BY (from($user) AND contains(gratitude)) INWINDOW 10",
        category="edge_cases",
        difficulty="hard",
        required_dictionaries={"gratitude": ["thank", "thanks", "appreciate"]},
        notes="Sequential pattern: user asks THEN thanks (same user, ordered)",
    ),
    TestCase(
        id="edge_004",
        description="Find messages that are from alice or bob, and also contain greetings or thanks",
        ground_truth_query="SELECT (from(alice) OR from(bob)) AND (contains(greetings) OR contains(gratitude))",
        category="edge_cases",
        difficulty="medium",
        required_dictionaries={
            "greetings": ["hello", "hi", "hey"],
            "gratitude": ["thank", "thanks", "appreciate"],
        },
        notes="Tests nested parentheses and operator precedence - (A OR B) AND (C OR D)",
    ),
    TestCase(
        id="edge_005",
        description="Find three-way conversation where user1 posts, then user2 responds within 3 messages, then user3 responds within 3 more messages",
        ground_truth_query="SELECT from($user1) FOLLOWED_BY from($user2) WITHIN 3 FOLLOWED_BY from($user3) INWINDOW 3",
        category="edge_cases",
        difficulty="hard",
        required_dictionaries={},
        notes="Three different pattern variables - tests LLM understanding of multiple distinct users",
    ),
]

# =============================================================================
# AMBIGUOUS QUERIES (Tests disambiguation)
# =============================================================================

AMBIGUOUS_QUERIES = [
    TestCase(
        id="ambig_001",
        description="Find alice and bob within 5 messages",
        ground_truth_query="SELECT from(alice), from(bob) INWINDOW 5",
        category="ambiguous",
        difficulty="medium",
        required_dictionaries={},
        notes="Could mean INWINDOW (co-occurrence) or FOLLOWED_BY (sequence) - INWINDOW is more common interpretation",
    ),
    TestCase(
        id="ambig_002",
        description="Find messages about problems from customer",
        ground_truth_query="SELECT from(customer) AND contains(problems)",
        category="ambiguous",
        difficulty="easy",
        required_dictionaries={"problems": ["error", "issue", "problem"]},
        notes="Order of conditions doesn't matter for AND",
    ),
]

# =============================================================================
# PATTERN VARIABLE QUERIES (Advanced)
# =============================================================================

PATTERN_VARIABLE_QUERIES = [
    TestCase(
        id="pvar_001",
        description="Find the same user posting twice in a row within 3 messages",
        ground_truth_query="SELECT from($user) FOLLOWED_BY from($user) INWINDOW 3",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential self-continuation: same user posts, then posts again (ordered)",
    ),
    TestCase(
        id="pvar_002",
        description="Find someone asking a question, Bob responding within 5 messages, then the original person following up within 5 more messages",
        ground_truth_query="SELECT from($asker) AND is_question() FOLLOWED_BY from(bob) WITHIN 5 FOLLOWED_BY from($asker) INWINDOW 5",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential question-answer-acknowledgment: $asker asks THEN bob THEN $asker (ordered)",
    ),
    TestCase(
        id="pvar_003",
        description="Find two-person back-and-forth alternating conversation pattern with responses within 2 messages each",
        ground_truth_query="SELECT from($person1) FOLLOWED_BY from($person2) WITHIN 2 FOLLOWED_BY from($person1) WITHIN 2 FOLLOWED_BY from($person2) INWINDOW 2",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential alternating pattern: person1 THEN person2 THEN person1 THEN person2 (ordered)",
    ),
    TestCase(
        id="pvar_004",
        description="Find the same user posting three consecutive messages (immediately after each other)",
        ground_truth_query="SELECT from($user) FOLLOWED_BY from($user) WITHIN 1 FOLLOWED_BY from($user) INWINDOW 1",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential self-continuation: $user THEN $user THEN $user (consecutive, no gaps)",
    ),
    TestCase(
        id="pvar_005",
        description="Find any user asking twice and getting a support response, all within 8 messages",
        ground_truth_query="SELECT from($user) AND is_question(), from($user) AND is_question(), from(support) INWINDOW 8",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Pattern variable with INWINDOW - same user asks twice (unordered) + support responds (unordered)",
    ),
]

# =============================================================================
# QUANTIFIER QUERIES (Advanced counting)
# =============================================================================

QUANTIFIER_QUERIES = [
    TestCase(
        id="quant_001",
        description="Find alice posting exactly 3 messages within 10 positions",
        ground_truth_query="SELECT from(alice){3} INWINDOW 10",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Exact quantifier for user burst detection",
    ),
    TestCase(
        id="quant_002",
        description="Find alice posting twice then bob responding within 5 messages",
        ground_truth_query="SELECT from(alice){2} FOLLOWED_BY from(bob) INWINDOW 5",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential: alice posts twice THEN bob responds (ordered)",
    ),
    TestCase(
        id="quant_003",
        description="Find any user posting 3 times then someone else responding immediately after",
        ground_truth_query="SELECT from($user){3} FOLLOWED_BY NOT from($user) INWINDOW 1",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential: user posts 3 times THEN someone ELSE responds (NOT from same user)",
    ),
    TestCase(
        id="quant_004",
        description="Find bob posting twice then alice posting twice within 5 messages",
        ground_truth_query="SELECT from(bob){2} FOLLOWED_BY from(alice){2} INWINDOW 5",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential with quantifiers: bob twice THEN alice twice (ordered)",
    ),
    TestCase(
        id="quant_005",
        description="Find the same user posting exactly 2 messages within 5 positions",
        ground_truth_query="SELECT from($user){2} INWINDOW 5",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Pattern variable with quantifier - finds bursts from same user (unordered)",
    ),
    TestCase(
        id="quant_006",
        description="Find alice posting immediately followed by bob within 1 message (consecutive messages with no gap)",
        ground_truth_query="SELECT from(alice) FOLLOWED_BY from(bob) INWINDOW 1",
        category="quantifiers",
        difficulty="medium",
        required_dictionaries={},
        notes="WITHIN 1 means immediately adjacent - no messages in between",
    ),
]

# =============================================================================
# NEGATIVE PATTERN QUERIES (NOT operator in sequences)
# =============================================================================

NEGATIVE_PATTERN_QUERIES = [
    TestCase(
        id="neg_001",
        description="Find windows with two messages from the same user and no messages from manager, all within 5 messages",
        ground_truth_query="SELECT from($user), NOT from(manager), from($user) INWINDOW 5",
        category="negative_patterns",
        difficulty="hard",
        required_dictionaries={},
        notes="INWINDOW is unordered - finds windows with 2 user messages + 0 manager messages (positions can be any order)",
    ),
    TestCase(
        id="neg_002",
        description="Find greetings from someone who is not the manager",
        ground_truth_query="SELECT contains(greetings) AND NOT from(manager)",
        category="negative_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
        notes="Single message with both conditions: greeting AND not from manager",
    ),
    TestCase(
        id="neg_003",
        description="Find messages containing question words, then a non-thank-you response within 3 messages, then bob responding within 3 more messages",
        ground_truth_query="SELECT contains(questions) FOLLOWED_BY NOT contains(thanks) WITHIN 3 FOLLOWED_BY from(bob) INWINDOW 3",
        category="negative_patterns",
        difficulty="hard",
        required_dictionaries={
            "questions": ["what", "how", "when", "where", "why"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="Sequential: question words THEN non-thank-you response THEN bob (3-part ordered sequence)",
    ),
]

# =============================================================================
# AGGREGATION QUERIES
# =============================================================================

AGGREGATION_QUERIES = [
    TestCase(
        id="agg_001",
        description="Count total self-continuation instances (same user posting twice within 3 messages)",
        ground_truth_query="SELECT from($user), from($user) INWINDOW 3 AGGREGATE count()",
        category="aggregation",
        difficulty="hard",
        required_dictionaries={},
        notes="Aggregation with pattern variables",
    ),
]

# =============================================================================
# SUBQUERY QUERIES (Nested patterns)
# =============================================================================

SUBQUERY_QUERIES = [
    TestCase(
        id="sub_001",
        description="Find customer and problem mentions within 3 messages of each other, and support with solution within 3 messages of each other, all within 15 messages (any order)",
        ground_truth_query="SELECT (SELECT from(customer), contains(problems) INWINDOW 3) ; (SELECT from(support), contains(solutions) INWINDOW 3) INWINDOW 15",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "try"],
        },
        notes="Subqueries with INWINDOW are UNORDERED - groups can appear in any order",
    ),
    TestCase(
        id="sub_002",
        description="Find question from user1, answer from user2, and thanks from user1 all appearing within 10 messages (any order)",
        ground_truth_query="SELECT from(user1) AND is_question(), from(user2) AND contains(answers), from(user1) AND contains(thanks) INWINDOW 10",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={
            "answers": ["yes", "no", "here", "this"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="Three elements merged with INWINDOW - can appear in any order (not a sequence!)",
    ),
    TestCase(
        id="sub_003",
        description="Find alice-bob conversation (within 3 messages of each other) and charlie message appearing within 8 messages (any order)",
        ground_truth_query="SELECT (SELECT from(alice), from(bob) INWINDOW 3) ; from(charlie) INWINDOW 8",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={},
        notes="Subquery defines alice-bob cluster, then merged with charlie using INWINDOW - charlie could appear before or after alice-bob",
    ),
    TestCase(
        id="sub_004",
        description="Find customer problem (within 3 messages), customer escalation (within 2 messages), and manager message all within 20 messages (any order)",
        ground_truth_query="SELECT (SELECT contains(problems), from(customer) INWINDOW 3) ; (SELECT contains(escalation), from(customer) INWINDOW 2) ; from(manager) INWINDOW 20",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "broken"],
            "escalation": ["manager", "escalate", "urgent"],
        },
        notes="Two subqueries define customer clusters, merged with manager message - order not guaranteed (unordered co-occurrence)",
    ),
]

# =============================================================================
# SEQUENTIAL SUBQUERY QUERIES (Ordered nested patterns)
# =============================================================================

SEQUENTIAL_SUBQUERY_QUERIES = [
    TestCase(
        id="seqsub_001",
        description="Find customer with problem mention (within 3 messages of each other), then support with solution mention (within 3 messages of each other) within 10 messages",
        ground_truth_query="SELECT (SELECT from(customer), contains(problems) INWINDOW 3) FOLLOWED_BY (SELECT from(support), contains(solutions) INWINDOW 3) INWINDOW 10",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "try"],
        },
        notes="Sequential subqueries: customer+problem group THEN support+solution group (ordered)",
    ),
    TestCase(
        id="seqsub_002",
        description="Find question from user1, then answer from user2 within 5 messages, then thanks from user1 within 5 more messages (in sequence)",
        ground_truth_query="SELECT from(user1) AND is_question() FOLLOWED_BY from(user2) AND contains(answers) WITHIN 5 FOLLOWED_BY from(user1) AND contains(thanks) INWINDOW 5",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={
            "answers": ["yes", "no", "here", "this"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="Three-part sequence: user1 question THEN user2 answer THEN user1 thanks (ordered chain)",
    ),
    TestCase(
        id="seqsub_003",
        description="Find alice-bob conversation (within 3 messages of each other) followed by charlie responding within 8 messages",
        ground_truth_query="SELECT (SELECT from(alice), from(bob) INWINDOW 3) FOLLOWED_BY (SELECT from(charlie)) INWINDOW 8",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential: alice-bob cluster THEN charlie message (charlie responds after conversation)",
    ),
    TestCase(
        id="seqsub_004",
        description="Find customer problem (within 3 messages), then escalation from same customer (within 2 messages) within 10 messages, then manager response within 10 more messages (in sequence)",
        ground_truth_query="SELECT (SELECT contains(problems), from(customer) INWINDOW 3) FOLLOWED_BY (SELECT contains(escalation), from(customer) INWINDOW 2) WITHIN 10 FOLLOWED_BY (SELECT from(manager)) INWINDOW 10",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "broken"],
            "escalation": ["manager", "escalate", "urgent"],
        },
        notes="Sequential: customer problem cluster THEN customer escalation cluster THEN manager message (ordered escalation pattern)",
    ),
]

# =============================================================================
# ALL TEST CASES
# =============================================================================

ALL_TEST_CASES = (
    BASIC_QUERIES
    + WINDOW_QUERIES
    + SEQUENTIAL_QUERIES
    + COMPLEX_QUERIES
    + EDGE_CASE_QUERIES
    + AMBIGUOUS_QUERIES
    + PATTERN_VARIABLE_QUERIES
    + QUANTIFIER_QUERIES
    + NEGATIVE_PATTERN_QUERIES
    + AGGREGATION_QUERIES
    + SUBQUERY_QUERIES
    + SEQUENTIAL_SUBQUERY_QUERIES
)


def get_test_cases_by_difficulty(difficulty: str) -> list[TestCase]:
    """Get all test cases of a specific difficulty."""
    return [tc for tc in ALL_TEST_CASES if tc.difficulty == difficulty]


def get_test_cases_by_category(category: str) -> list[TestCase]:
    """Get all test cases of a specific category."""
    return [tc for tc in ALL_TEST_CASES if tc.category == category]


def get_all_required_dictionaries() -> dict[str, list[str]]:
    """Get union of all dictionaries needed across all test cases."""
    all_dicts: dict[str, list[str]] = {}
    for tc in ALL_TEST_CASES:
        all_dicts.update(tc.required_dictionaries)
    return all_dicts


# Summary stats
if __name__ == "__main__":
    print(f"Total test cases: {len(ALL_TEST_CASES)}")
    print("\nBy difficulty:")
    for diff in ["easy", "medium", "hard"]:
        count = len(get_test_cases_by_difficulty(diff))
        print(f"  {diff}: {count}")

    print("\nBy category:")
    categories = set(tc.category for tc in ALL_TEST_CASES)
    for cat in sorted(categories):
        count = len(get_test_cases_by_category(cat))
        print(f"  {cat}: {count}")

    print(f"\nTotal unique dictionaries: {len(get_all_required_dictionaries())}")
    print(f"Dictionaries: {list(get_all_required_dictionaries().keys())}")
