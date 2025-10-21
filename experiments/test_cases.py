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
# WINDOW QUERIES (Medium)
# =============================================================================

WINDOW_QUERIES = [
    TestCase(
        id="window_001",
        description="Find greetings followed by a response within 3 messages",
        ground_truth_query="SELECT contains(greetings), from(support) INWIN 3",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey"]},
    ),
    TestCase(
        id="window_002",
        description="Find problem mentions followed by solution mentions within 10 messages",
        ground_truth_query="SELECT contains(problems), contains(solutions) INWIN 10",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "solved"],
        },
    ),
    TestCase(
        id="window_003",
        description="Find questions followed by answers from support within 5 messages",
        ground_truth_query="SELECT is_question(), from(support) INWIN 5",
        category="window_patterns",
        difficulty="medium",
        required_dictionaries={},
    ),
]

# =============================================================================
# SEQUENTIAL PATTERNS (Medium-Hard)
# =============================================================================

SEQUENTIAL_QUERIES = [
    TestCase(
        id="seq_001",
        description="Find messages from alice followed by messages from bob within 2 positions",
        ground_truth_query="SELECT from(alice) FOLLOWED_BY from(bob) WITHIN 2",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
    ),
    TestCase(
        id="seq_002",
        description="Find questions that are followed by a response from support within 3 messages",
        ground_truth_query="SELECT is_question() FOLLOWED_BY from(support) WITHIN 3",
        category="sequential_patterns",
        difficulty="medium",
        required_dictionaries={},
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
]

# =============================================================================
# COMPLEX PATTERNS (Hard)
# =============================================================================

COMPLEX_QUERIES = [
    TestCase(
        id="complex_001",
        description="Find customer questions about problems that are followed by support providing solutions, all within 10 messages",
        ground_truth_query="SELECT from(customer) AND is_question() AND contains(problems), from(support) AND contains(solutions) INWIN 10",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={
            "problems": ["error", "issue", "problem", "bug"],
            "solutions": ["fixed", "resolved", "solution", "try"],
        },
    ),
    TestCase(
        id="complex_002",
        description="Find greeting from customer, followed by greeting from support, followed by question from customer, all within 5 messages",
        ground_truth_query="SELECT from(customer) AND contains(greetings), from(support) AND contains(greetings), from(customer) AND is_question() INWIN 5",
        category="complex_patterns",
        difficulty="hard",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
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
        ground_truth_query="SELECT from($user) AND is_question(), from($user) AND contains(gratitude) INWIN 10",
        category="edge_cases",
        difficulty="hard",
        required_dictionaries={"gratitude": ["thank", "thanks", "appreciate"]},
        notes="Tests understanding of pattern variables",
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
        ground_truth_query="SELECT from($asker), from(bob), from($asker) INWIN 5",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Question-answer-acknowledgment pattern with variable",
    ),
    TestCase(
        id="pvar_003",
        description="Find two-person back-and-forth alternating conversation pattern",
        ground_truth_query="SELECT from($person1), from($person2), from($person1), from($person2) INWIN 5",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Alternating conversation between two people",
    ),
    TestCase(
        id="pvar_004",
        description="Find the same user posting three consecutive messages",
        ground_truth_query="SELECT from($user), from($user), from($user) INWIN 3",
        category="pattern_variables",
        difficulty="hard",
        required_dictionaries={},
        notes="Extended self-response pattern",
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
        ground_truth_query="SELECT from(alice){2}, from(bob) INWIN 10",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Quantifier in multi-user pattern",
    ),
    TestCase(
        id="quant_003",
        description="Find any user posting 3 times then someone else responding",
        ground_truth_query="SELECT from($user){3}, from($responder) INWIN 10",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Quantifiers with pattern variables",
    ),
    TestCase(
        id="quant_004",
        description="Find bob posting twice then alice posting twice",
        ground_truth_query="SELECT from(bob){2}, from(alice){2} INWIN 10",
        category="quantifiers",
        difficulty="hard",
        required_dictionaries={},
        notes="Multiple quantifiers in one pattern",
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
        ground_truth_query="SELECT NOT from(manager), contains(greetings) INWIN 3",
        category="negative_patterns",
        difficulty="medium",
        required_dictionaries={"greetings": ["hello", "hi", "hey", "good morning"]},
        notes="NOT at first position",
    ),
    TestCase(
        id="neg_003",
        description="Find questions with a non-thank-you response then bob responding",
        ground_truth_query="SELECT contains(questions), NOT contains(thanks), from(bob) INWIN 5",
        category="negative_patterns",
        difficulty="hard",
        required_dictionaries={
            "questions": ["what", "how", "when", "where", "why"],
            "thanks": ["thank", "thanks", "appreciate"],
        },
        notes="NOT excluding specific content",
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
