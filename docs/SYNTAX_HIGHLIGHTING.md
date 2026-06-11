# PrismQL Syntax Highlighting

PrismQL includes a Pygments lexer for syntax highlighting in documentation, code blocks, and other contexts.

## Installation

Install PrismQL with highlighting support:

```bash
pip install prismql[highlighting]
```

Or with uv:

```bash
uv pip install prismql[highlighting]
```

## Usage

### In Python Code

Use the lexer programmatically:

```python
from pygments import highlight
from pygments.formatters import TerminalFormatter, HtmlFormatter
from prismql.highlighting import PrismQLLexer

query = """
SELECT from(alice), contains(problems) INWIN 10
"""

# Terminal output with colors
print(highlight(query, PrismQLLexer(), TerminalFormatter()))

# HTML output
html = highlight(query, PrismQLLexer(), HtmlFormatter())
```

### In Markdown/ReStructuredText

Once PrismQL is installed, Pygments will automatically recognize PrismQL code blocks:

**Markdown:**
````markdown
```prismql
SELECT from(alice), contains(problems) INWIN 10
```
````

**ReStructuredText:**
```rst
.. code-block:: prismql

   SELECT from(alice), contains(problems) INWIN 10
```

### In Sphinx Documentation

Add to your `conf.py`:

```python
extensions = [
    'sphinx.ext.autodoc',
    # ... other extensions
]

# Pygments will automatically find the lexer if prismql is installed
pygments_style = 'sphinx'
```

Then use in your `.rst` files:

```rst
.. code-block:: prismql

   SELECT
       from(customer),
       contains(issues)
   INWIN 5
```

### In Jupyter Notebooks

Use IPython magic:

```python
%load_ext pygments.formatters

# Display highlighted query
from IPython.display import HTML
from pygments import highlight
from pygments.formatters import HtmlFormatter
from prismql.highlighting import PrismQLLexer

query = "SELECT from(alice), is_question() INWIN 3"
html = highlight(query, PrismQLLexer(), HtmlFormatter())
HTML(html)
```

### With MkDocs

If using MkDocs with `pymdown-extensions`:

```yaml
# mkdocs.yml
markdown_extensions:
  - pymdownx.highlight:
      use_pygments: true
  - pymdownx.superfences
```

Then in your Markdown:

````markdown
```prismql
SELECT from($user), from($user) INWIN 3
```
````

### Command-Line Tool

Use `pygmentize` directly:

```bash
# Highlight a file
pygmentize -l prismql -f terminal256 query.pql

# Highlight with HTML output
pygmentize -l prismql -f html -o query.html query.pql

# List available formatters
pygmentize -L formatters
```

## Syntax Features

The lexer highlights:

### Keywords
- **SELECT, INWINDOW, DURING, AS** (and the deprecated INWIN, WITHIN)
- **AND, OR, NOT** (boolean operators)
- **AGGREGATE, GROUP BY, ORDER BY, LIMIT** (aggregation)
- **BEFORE, AFTER, BETWEEN, AGO** (temporal)

### Functions
- **Fluent syntax** (preferred): `contains()`, `from()`, `is_question()`, `mentions_date()`, etc.
- **Legacy syntax**: `haswordofdict()`, `byuser()`, `hasquestion()`, etc.

### Operators
- **Positional**: `FOLLOWED_BY`, `PRECEDED_BY`, `NOT_FOLLOWED_BY`, `NOT_PRECEDED_BY`

### Literals
- **Pattern variables**: `$user`, `$topic`
- **Strings**: `"alice"`, `'problems'`
- **Numbers**: `5`, `10`, `100`

### Quantifiers
- **Exact**: `{3}` (exactly 3 occurrences)
- **At least**: `{2,}` (2 or more occurrences)
- **Range**: `{1,5}` (between 1 and 5 occurrences)

### Comments
- Single-line: `-- comment` or `// comment`
- Multi-line: `/* comment */`

## Example Queries

### Basic Pattern Matching
```prismql
-- Find questions from alice
SELECT from(alice), is_question() INWIN 3
```

### Pattern Variables
```prismql
-- Same user posting consecutively
SELECT from($user), from($user) INWIN 3
```

### Quantifiers
```prismql
-- Alice posting exactly 3 messages
SELECT from(alice){3} INWIN 10
```

### Subqueries
```prismql
SELECT
    (SELECT from(customer), contains(problems) INWIN 3) ;
    (SELECT from(support), contains(solutions) INWIN 3)
INWIN 15
```

### Aggregation
```prismql
SELECT from($user)
GROUP BY $user
AGGREGATE count()
ORDER BY $user DESC
LIMIT 10
```

## Color Schemes

The lexer uses standard Pygments token types, so it works with any Pygments theme:

- **default**: Standard colors
- **monokai**: Dark theme
- **solarized-dark**: Solarized dark
- **github-dark**: GitHub dark theme
- **nord**: Nord color scheme

Example with different themes:

```python
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.styles import get_style_by_name
from prismql.highlighting import PrismQLLexer

query = "SELECT from(alice), contains(problems) INWIN 10"

# Try different themes
for theme in ['monokai', 'solarized-dark', 'github-dark']:
    style = get_style_by_name(theme)
    formatter = Terminal256Formatter(style=style)
    print(f"\n=== {theme.upper()} ===")
    print(highlight(query, PrismQLLexer(), formatter))
```

## Verifying Installation

Check if Pygments can find the lexer:

```bash
# List all lexers (should include prismql)
pygmentize -L lexers | grep -i prism

# Output should show:
# * prismql, pql:
#     PrismQL (filenames *.pql, *.prismql)
```

Or in Python:

```python
from pygments.lexers import get_lexer_by_name

try:
    lexer = get_lexer_by_name('prismql')
    print(f"✓ PrismQL lexer found: {lexer}")
except Exception as e:
    print(f"✗ PrismQL lexer not found: {e}")
```

## File Extensions

The lexer automatically activates for files with these extensions:
- `.pql`
- `.prismql`

## Troubleshooting

### Lexer not found
1. Ensure PrismQL is installed: `pip show prismql`
2. Reinstall with highlighting: `pip install -e .[highlighting]`
3. Restart your Python interpreter or Jupyter kernel

### No syntax highlighting in Sphinx
1. Ensure Pygments is installed: `pip install pygments`
2. Ensure PrismQL is installed in the same environment as Sphinx
3. Run `make clean html` to rebuild docs

### No colors in terminal
Use `Terminal256Formatter` instead of `TerminalFormatter` for better colors.

## Contributing

To improve syntax highlighting:
1. Edit `src/prismql/highlighting/pygments_lexer.py`
2. Test with sample queries
3. Submit a pull request

See also:
- [Pygments documentation](https://pygments.org/docs/)
- [Writing a Lexer](https://pygments.org/docs/lexerdevelopment/)
- [Token types](https://pygments.org/docs/tokens/)
