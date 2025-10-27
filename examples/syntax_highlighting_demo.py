"""
Demo of PrismQL syntax highlighting with Pygments.

Install pygments first:
    pip install pygments
    # or
    uv pip install pygments

Then run this script:
    python examples/syntax_highlighting_demo.py
"""

try:
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.styles import get_all_styles

    from prismql.highlighting import PrismQLLexer
except ImportError:
    print("Error: pygments not installed")
    print("Install with: pip install pygments")
    exit(1)


# Sample queries
QUERIES = [
    (
        "Basic Query",
        'SELECT from(alice), contains("problems") INWIN 10',
    ),
    (
        "Pattern Variables",
        "SELECT from($user), from($user) INWIN 3",
    ),
    (
        "Quantifiers",
        "SELECT from(alice){3} INWIN 10",
    ),
    (
        "Boolean Logic",
        "SELECT (from(alice) OR from(bob)) AND is_question()",
    ),
    (
        "Subquery",
        """SELECT
    (SELECT from(customer), contains(problems) INWIN 3) ;
    (SELECT from(support), contains(solutions) INWIN 3)
INWIN 15""",
    ),
    (
        "Aggregation",
        """SELECT from($user)
GROUP BY $user
AGGREGATE count(), distinct($user)
ORDER BY count DESC
LIMIT 10""",
    ),
    (
        "With Comments",
        """-- Find escalated issues
SELECT
    from(customer),  -- Customer messages
    contains(urgent) -- Urgent keywords
INWIN 5""",
    ),
]


def main() -> None:
    """Display highlighted queries."""
    lexer = PrismQLLexer()

    print("=" * 80)
    print("PrismQL Syntax Highlighting Demo")
    print("=" * 80)
    print()

    # Use a nice color scheme (monokai is popular)
    try:
        formatter = Terminal256Formatter(style="monokai")
    except Exception:
        # Fall back to default if monokai not available
        formatter = Terminal256Formatter()

    for title, query in QUERIES:
        print(f"\n{title}:")
        print("-" * 40)
        highlighted = highlight(query, lexer, formatter)
        print(highlighted)

    # Show available styles
    print("\n" + "=" * 80)
    print("Available Pygments Styles")
    print("=" * 80)
    print("\nYou can use any of these styles with Terminal256Formatter:")
    styles = list(get_all_styles())
    for i, style in enumerate(styles, 1):
        print(f"  {i:2d}. {style}")

    print("\n" + "=" * 80)
    print("Try different styles by changing the 'style' parameter:")
    print("  formatter = Terminal256Formatter(style='solarized-dark')")
    print("=" * 80)


if __name__ == "__main__":
    main()
