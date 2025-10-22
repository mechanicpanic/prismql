"""
Visual color legend for PrismQL syntax highlighting.
Shows what color each syntax element gets.
"""

from prismql.highlighting import PrismQLLexer
from pygments import highlight
from pygments.formatters import Terminal256Formatter


def show_color_legend():
    """Display color legend showing what each token type looks like."""
    lexer = PrismQLLexer()
    formatter = Terminal256Formatter(style="monokai")

    print("=" * 80)
    print("PrismQL Syntax Highlighting Color Legend (Monokai Theme)")
    print("=" * 80)
    print()

    examples = [
        ("Main Keywords", "SELECT"),
        ("Window Keywords", "INWIN"),
        ("Boolean Operators", "AND OR NOT"),
        ("Fluent Functions", "from() contains() is_question()"),
        ("Legacy Functions", "haswordofdict() byuser()"),
        ("Pattern Variables", "$user $topic"),
        ("Strings", "\"alice\" 'bob'"),
        ("Numbers", "10 42 100"),
        ("Quantifiers", "{3} {2,} {1,5}"),
        ("Comments", "-- single line comment"),
        ("Temporal Keywords", "BEFORE AFTER AGO"),
        ("Aggregation", "AGGREGATE GROUP BY COUNT"),
        ("Positional Operators", "FOLLOWED_BY PRECEDED_BY"),
    ]

    for description, code in examples:
        highlighted = highlight(code, lexer, formatter).strip()
        print(f"{description:25s} → {highlighted}")

    print()
    print("=" * 80)
    print("Complete Query Example:")
    print("=" * 80)
    print()

    query = """SELECT
    from($user),
    contains("problems"),
    is_question()
INWIN 10
GROUP BY $user
AGGREGATE count()
ORDER BY count DESC
LIMIT 5"""

    highlighted = highlight(query, lexer, formatter)
    print(highlighted)


if __name__ == "__main__":
    show_color_legend()
