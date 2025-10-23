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
# WINDOW QUERIES (Medium) - INWIN tests unordered co-occurrence
# =============================================================================

WINDOW_QUERIES = [
    TestCase(
        id="window_001",
        description="Find conversations where greetings and support responses appear together within 3 messages (any order)",
        ground_truth_query="SELECT contains(greetings), from(support) INWIN 3",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey"]},
        notes="INWIN is unordered - greeting can come before or after support response",
    ),
    TestCase(
        id="window_002",
        description="Find conversations where problems and solutions are both mentioned within 10 messages (any order)",
        ground_truth_query="SELECT contains(problems), contains(solutions) INWIN 10",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "solved"],
        },
        notes="INWIN is unordered - problem and solution can appear in any order",
    ),
    TestCase(
        id="window_003",
        description="Find conversations where questions and support messages appear together within 5 messages (any order)",
        ground_truth_query="SELECT is_question(), from(support) INWIN 5",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="INWIN is unordered - question can come before or after support message",
    ),
]

# =============================================================================
# SEQUENTIAL PATTERNS (Medium-Hard) - FOLLOWED_BY tests ordered sequences
# =============================================================================

SEQUENTIAL_QUERIES = [
    TestCase(
        id="seq_001",
        description="Find messages from alice followed by messages from bob within 2 positions",
        ground_truth_query="SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 2",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="Order matters: alice THEN bob, not bob then alice",
    ),
    TestCase(
        id="seq_002",
        description="Find questions that are followed by a response from support within 3 messages",
        ground_truth_query="SELECT is_question() FOLLOWED_BY from(support) WITHIN 3",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
        notes="Order matters: question THEN support response",
    ),
    TestCase(
        id="seq_003",
        description="Find messages from customer that are NOT followed by support within 5 messages (unanswered)",
        ground_truth_query="SELECT from(customer) NOT_FOLLOWED_BY from(support) WITHIN 5",
        category="sequential_patterns",
        difficulty="hard",
        required_dictionaries={},
        notes="Tests understanding of negative lookahead",
    ),
    TestCase(
        id="seq_004",
        description="Find greetings followed by a response from support within 3 messages",
        ground_truth_query="SELECT contains(greetings) FOLLOWED_BY from(support) WITHIN 3",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey"]},
        notes="Order matters: greeting THEN support response",
    ),
    TestCase(
        id="seq_005",
        description="Find problem mentions followed by solution mentions within 10 messages",
        ground_truth_query="SELECT contains(problems) FOLLOWED_BY contains(solutions) WITHIN 10",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "solved"],
        },
        notes="Order matters: problem THEN solution (not solution then problem)",
    ),
]

# =============================================================================
# COMPLEX PATTERNS (Hard)
# =============================================================================

COMPLEX_QUERIES = [
    TestCase(
        id="complex_001",
        description="Find customer questions about problems that are followed by support providing solutions within 10 messages",
        ground_truth_query="SELECT (from(customer) AND is_question() AND contains(problems)) FOLLOWED_BY (from(support) AND contains(solutions)) WITHIN 10",
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
        ground_truth_query="SELECT from(customer) AND contains(greetings), from(support) AND contains(greetings), from(customer) AND is_question() INWIN 5",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
        notes="INWIN is unordered - these three elements can appear in any sequence",
    ),
    TestCase(
        id="complex_004",
        description="Find customer greeting followed by support greeting within 3 messages, then followed by customer question within 2 more messages",
        ground_truth_query="SELECT (from(customer) AND contains(greetings)) FOLLOWED_BY (from(support) AND contains(greetings)) WITHIN 3 FOLLOWED_BY (from(customer) AND is_question()) WITHIN 2",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
        notes="Chained sequential pattern with separate WITHIN constraints for each transition",
    ),
    TestCase(
        id="complex_003",
        description="Find questions from alice that are preceded by bob within 2 messages and followed by charlie within 3 messages",
        ground_truth_query="SELECT from(alice) AND is_question() PRECEDED_BY from(bob) WITHIN 2 FOLLOWED_BY from(charlie) WITHIN 3",
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
        ground_truth_query="SELECT (from($user) AND is_question()) FOLLOWED_BY (from($user) AND contains(gratitude)) WITHIN 10",
        category="edge_cases",
        difficulty="hard",
        required_dictionaries={"gratitude": ["thank", "thanks", "appreciate"]},
        notes="Sequential pattern: user asks THEN thanks (same user, ordered)",
    ),
]

# =============================================================================
# AMBIGUOUS QUERIES (Tests disambiguation)
# =============================================================================

AMBIGUOUS_QUERIES = [
    TestCase(
        id="ambig_001",
        description="Find alice and bob within 5 messages",
        ground_truth_query="SELECT from(alice), from(bob) INWIN 5",
        category="ambiguous",
        difficulty="medium",
        required_dictionaries={},
        notes="Could mean INWIN (co-occurrence) or FOLLOWED_BY (sequence) - INWIN is more common interpretation",
    ),
    TestCase(
        id="ambig_002",
        description="Find messages about problems from customers",
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
        description="Find the same user posting consecutively within 3 messages",
        ground_truth_query="SELECT from($user), from($user) INWIN 3",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Self-continuation pattern - same user posts multiple times",
    ),
    TestCase(
        id="pvar_002",
        description="Find someone asking, Bob responding, then the original person following up",
        ground_truth_query="SELECT from($asker) FOLLOWED_BY from(bob) WITHIN 5 FOLLOWED_BY from($asker) WITHIN 5",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential question-answer-acknowledgment: $asker THEN bob THEN $asker (ordered)",
    ),
    TestCase(
        id="pvar_003",
        description="Find two-person back-and-forth alternating conversation pattern",
        ground_truth_query="SELECT from($person1) FOLLOWED_BY from($person2) WITHIN 2 FOLLOWED_BY from($person1) WITHIN 2 FOLLOWED_BY from($person2) WITHIN 2",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential alternating pattern: person1 THEN person2 THEN person1 THEN person2 (ordered)",
    ),
    TestCase(
        id="pvar_004",
        description="Find the same user posting three consecutive messages",
        ground_truth_query="SELECT from($user) FOLLOWED_BY from($user) WITHIN 1 FOLLOWED_BY from($user) WITHIN 1",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential self-continuation: $user THEN $user THEN $user (consecutive, no gaps)",
    ),
]

# =============================================================================
# QUANTIFIER QUERIES (Advanced counting)
# =============================================================================

QUANTIFIER_QUERIES = [
    TestCase(
        id="quant_001",
        description="Find alice posting exactly 3 messages within 10 positions",
        ground_truth_query="SELECT from(alice){3} INWIN 10",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Exact quantifier for user burst detection",
    ),
    TestCase(
        id="quant_002",
        description="Find alice posting twice then bob responding",
        ground_truth_query="SELECT from(alice){2} FOLLOWED_BY from(bob) WITHIN 5",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential: alice posts twice THEN bob responds (ordered)",
    ),
    TestCase(
        id="quant_003",
        description="Find any user posting 3 times then someone else responding",
        ground_truth_query="SELECT from($user){3} FOLLOWED_BY NOT from($user) WITHIN 1",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential: user posts 3 times THEN someone ELSE responds (NOT from same user)",
    ),
    TestCase(
        id="quant_004",
        description="Find bob posting twice then alice posting twice",
        ground_truth_query="SELECT from(bob){2} FOLLOWED_BY from(alice){2} WITHIN 5",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential with quantifiers: bob twice THEN alice twice (ordered)",
    ),
]

# =============================================================================
# NEGATIVE PATTERN QUERIES (NOT operator in sequences)
# =============================================================================

NEGATIVE_PATTERN_QUERIES = [
    TestCase(
        id="neg_001",
        description="Find same user posting twice with no manager message in between",
        ground_truth_query="SELECT from($user), NOT from(manager), from($user) INWIN 5",
        category="negative_patterns",
        difficulty="hard",
        required_dictionaries={},
        notes="NOT in middle position - peer-to-peer conversations",
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
        description="Find questions with a non-thank-you response then bob responding",
        ground_truth_query="SELECT contains(questions) FOLLOWED_BY NOT contains(thanks) WITHIN 3 FOLLOWED_BY from(bob) WITHIN 3",
        category="negative_patterns",
        difficulty="hard",
        required_dictionaries={
            "questions": ["what", "how", "when", "where", "why"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="Sequential: question THEN non-thank-you response THEN bob (3-part ordered sequence)",
    ),
]

# =============================================================================
# AGGREGATION QUERIES
# =============================================================================

AGGREGATION_QUERIES = [
    TestCase(
        id="agg_001",
        description="Count total self-continuation instances",
        ground_truth_query="SELECT from($user), from($user) INWIN 3 AGGREGATE count()",
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
        description="Find customer and problem mentions appearing together, and support with solution appearing together, all within 15 messages (any order)",
        ground_truth_query="SELECT (SELECT from(customer), contains(problems) INWIN 3) ; (SELECT from(support), contains(solutions) INWIN 3) INWIN 15",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "try"],
        },
        notes="Subqueries with INWIN are UNORDERED - groups can appear in any order",
    ),
    TestCase(
        id="sub_002",
        description="Find question from user1, answer from user2, and thanks from user1 all appearing within 10 messages (any order)",
        ground_truth_query="SELECT (SELECT is_question(), from(user1) INWIN 2) ; (SELECT from(user2), contains(answers) INWIN 2) ; (SELECT from(user1), contains(thanks) INWIN 2) INWIN 10",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={
            "answers": ["yes", "no", "here", "this"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="Three groups merged with INWIN - can appear in any order (not a sequence!)",
    ),
    TestCase(
        id="sub_003",
        description="Find alice-bob conversation and charlie message appearing within 8 messages (any order)",
        ground_truth_query="SELECT (SELECT from(alice), from(bob) INWIN 3) ; (SELECT from(charlie) INWIN 2) INWIN 8",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={},
        notes="Two groups with INWIN - charlie could appear before or after alice-bob",
    ),
    TestCase(
        id="sub_004",
        description="Find customer problem, customer escalation, and manager message all within 20 messages (any order)",
        ground_truth_query="SELECT (SELECT contains(problems), from(customer) INWIN 3) ; (SELECT contains(escalation), from(customer) INWIN 2) ; (SELECT from(manager) INWIN 2) INWIN 20",
        category="subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "broken"],
            "escalation": ["manager", "escalate", "urgent"],
        },
        notes="Three groups merged with INWIN - order not guaranteed (unordered co-occurrence)",
    ),
]

# =============================================================================
# SEQUENTIAL SUBQUERY QUERIES (Ordered nested patterns)
# =============================================================================

SEQUENTIAL_SUBQUERY_QUERIES = [
    TestCase(
        id="seqsub_001",
        description="Find customer with problem mention, then support with solution mention within 10 messages",
        ground_truth_query="SELECT (SELECT from(customer), contains(problems) INWIN 3) FOLLOWED_BY (SELECT from(support), contains(solutions) INWIN 3) WITHIN 10",
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
        description="Find question from user1, then answer from user2, then thanks from user1 in sequence",
        ground_truth_query="SELECT (SELECT is_question(), from(user1) INWIN 2) FOLLOWED_BY (SELECT from(user2), contains(answers) INWIN 2) WITHIN 5 FOLLOWED_BY (SELECT from(user1), contains(thanks) INWIN 2) WITHIN 5",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={
            "answers": ["yes", "no", "here", "this"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="Three subqueries in sequence: question THEN answer THEN thanks (ordered chain)",
    ),
    TestCase(
        id="seqsub_003",
        description="Find alice-bob conversation followed by charlie responding within 8 messages",
        ground_truth_query="SELECT (SELECT from(alice), from(bob) INWIN 3) FOLLOWED_BY (SELECT from(charlie)) WITHIN 8",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={},
        notes="Sequential: alice-bob group THEN charlie message (charlie responds after conversation)",
    ),
    TestCase(
        id="seqsub_004",
        description="Find customer problem, then escalation from same customer, then manager response in sequence",
        ground_truth_query="SELECT (SELECT contains(problems), from(customer) INWIN 3) FOLLOWED_BY (SELECT contains(escalation), from(customer) INWIN 2) WITHIN 10 FOLLOWED_BY (SELECT from(manager)) WITHIN 10",
        category="sequential_subqueries",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "broken"],
            "escalation": ["manager", "escalate", "urgent"],
        },
        notes="Three sequential groups: problem THEN escalation THEN manager (ordered escalation pattern)",
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
