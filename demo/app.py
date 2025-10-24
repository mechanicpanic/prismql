"""
PrismQL Interactive Demo - Streamlit Web App

A web-based demonstration of PrismQL query language for conversational data.
"""

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from prismql import PrecomputedIndexes
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError, PrismQLSyntaxError

# Try to import syntax highlighting
try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter

    from prismql.highlighting import PrismQLLexer

    HAS_HIGHLIGHTING = True
except ImportError:
    HAS_HIGHLIGHTING = False

# Handle imports when running directly vs as module
try:
    from demo.generate_demo_data import (
        generate_demo_conversations,
        generate_demo_custom_features,
        get_demo_dictionaries,
    )
except ModuleNotFoundError:
    # Add demo directory to path when running directly
    demo_dir = Path(__file__).parent
    if str(demo_dir) not in sys.path:
        sys.path.insert(0, str(demo_dir))
    from generate_demo_data import (
        generate_demo_conversations,
        generate_demo_custom_features,
        get_demo_dictionaries,
    )

# Page configuration
st.set_page_config(
    page_title="PrismQL Interactive Demo",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_engine():
    """Load PrismQL engine with demo data."""
    conversations = generate_demo_conversations()
    backend = MemoryBackend(documents=conversations)
    dictionaries = get_demo_dictionaries()

    # Generate custom features (simulated LLM annotations)
    custom_features = generate_demo_custom_features(conversations)
    indexes = PrecomputedIndexes(custom_features=custom_features)

    return PrismQLEngine(
        search_backend=backend,
        user_dictionaries=dictionaries,
        precomputed_indexes=indexes,
    )


def format_message(msg: dict) -> str:
    """Format a message for display."""
    return f"**[{msg['id']}] {msg['user']}:** {msg['text']}"


def format_result_group(group: list, engine: PrismQLEngine) -> str:
    """Format a result group with message details."""
    output = []
    for msg_id in group:
        # Get the actual message
        docs = engine.search_backend.get_documents([msg_id])
        if docs:
            msg = docs[0]
            output.append(format_message(msg))
    return "\n\n".join(output)


def display_query_with_highlighting(query: str) -> None:
    """Display query with syntax highlighting if available."""
    if HAS_HIGHLIGHTING:
        lexer = PrismQLLexer()
        formatter = HtmlFormatter(
            style="monokai",
            noclasses=True,
            cssclass="highlight",
        )
        highlighted = highlight(query, lexer, formatter)
        # Add monospace font styling and proper HTML structure
        styled_html = f"""
        <style>
        .highlight {{
            font-family: 'Courier New', Courier, monospace !important;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .highlight pre {{
            margin: 0;
            font-family: 'Courier New', Courier, monospace !important;
        }}
        </style>
        {highlighted}
        """
        # Use components.html for proper HTML rendering
        components.html(styled_html, height=100, scrolling=True)
    else:
        st.code(query, language=None)


# Example queries organized by category
EXAMPLE_QUERIES = {
    "Basic Queries": {
        "All messages from alice": "SELECT from(alice)",
        "All support agent messages": "SELECT from(support_sarah)",
        "Messages containing problems": "SELECT contains(problems)",
        "Messages with greetings": "SELECT contains(greetings)",
        "All messages (wildcard)": "SELECT from(*)",
    },
    "Boolean Operations": {
        "Messages from alice OR bob": "SELECT from(alice) OR from(bob)",
        "Problems from customers": "SELECT contains(problems) AND (from(alice) OR from(bob))",
        "Messages NOT from support": "SELECT NOT from(support_sarah)",
        "Anyone with greetings": "SELECT from(*) AND contains(greetings)",
    },
    "Window Patterns": {
        "Alice and support together": "SELECT from(alice), from(support_sarah) INWIN 5",
        "Problem and solution nearby": "SELECT contains(problems), contains(solutions) INWIN 5",
        "Greeting and thanks together": "SELECT contains(greetings), contains(thanks) INWIN 10",
        "Multiple users same window": "SELECT from(alice), from(bob), from(charlie) INWIN 10",
    },
    "Sequential Patterns (FOLLOWED_BY)": {
        "Customer then support": "SELECT from(alice) FOLLOWED_BY from(support_sarah) WITHIN 5",
        "Problem then solution": "SELECT contains(problems) FOLLOWED_BY contains(solutions) WITHIN 10",
        "Three-way sequence": "SELECT from(alice) FOLLOWED_BY from(support_sarah) WITHIN 3 FOLLOWED_BY from(alice) WITHIN 3",
        "Question then answer": "SELECT contains(questions) FOLLOWED_BY contains(solutions) WITHIN 5",
    },
    "Pattern Variables": {
        "Same user posting twice": "SELECT from($user), from($user) INWIN 5",
        "Any user with problems": "SELECT from($user) AND contains(problems)",
        "Any user with questions": "SELECT from($user) AND contains(questions)",
    },
    "Quantifiers": {
        "Alice posting 3 times": "SELECT from(alice){3} INWIN 10",
        "Support posting 2 times": "SELECT from(support_sarah){2} INWIN 5",
        "Bob posting 3+ times": "SELECT from(bob){3} INWIN 10",
    },
    "Advanced": {
        "Complex boolean": "SELECT (contains(problems) OR contains(questions)) AND NOT from(support_sarah)",
        "Multiple dictionaries": "SELECT contains(greetings), contains(problems), contains(questions) INWIN 10",
    },
    "Custom Features (LLM Annotations)": {
        "All positive sentiment": "SELECT has_feature(sentiment_positive)",
        "Negative sentiment messages": "SELECT labeled_as(sentiment_negative)",
        "High priority complaints": "SELECT has_feature(intent_complaint) AND has_feature(priority_high)",
        "Question with negative sentiment": "SELECT has_feature(intent_question) AND has_feature(sentiment_negative)",
        "Technical account issues": "SELECT has_feature(topic_technical) AND has_feature(topic_account)",
        "Complaint then response": "SELECT has_feature(intent_complaint) FOLLOWED_BY has_feature(intent_response) WITHIN 3",
        "Greeting then thanks": "SELECT labeled_as(intent_greeting), labeled_as(intent_thanks) INWIN 10",
    },
    "Understanding INWIN (Important!)": {
        "❌ Common mistake": "SELECT from(alice){2}, contains(solutions) INWIN 10",
        "✅ Alice WITH solutions": "SELECT from(alice) AND contains(solutions)",
        "✅ Two alice, both solutions": "SELECT (from(alice) AND contains(solutions)){2} INWIN 10",
        "✅ Two alice, one solutions": "SELECT (from(alice) AND contains(solutions)), from(alice) INWIN 10",
    },
}


def main():
    """Main Streamlit app."""
    st.title("🔍 PrismQL Interactive Demo")
    st.markdown(
        """
    **PrismQL** is a domain-specific language for pattern matching in conversational data.
    Try queries below to explore customer support conversations!
    """
    )

    # Load engine
    engine = load_engine()

    # Sidebar with examples and help
    with st.sidebar:
        st.header("📚 Example Queries")

        # Category selector
        category = st.selectbox("Select category:", list(EXAMPLE_QUERIES.keys()))

        # Example queries in category
        if category:
            # Show explanation for INWIN category
            if category == "Understanding INWIN (Important!)":
                st.info(
                    """
                    **INWIN is unordered!** It finds ANY combination of messages
                    within the window, even if they satisfy different restrictions.

                    `from(alice){2}, contains(solutions) INWIN 10` means:
                    - 2 messages from alice
                    - 1 message with solutions
                    - Can be from ANYONE (including bob!)

                    Use AND to filter properly!
                    """
                )

            st.markdown(f"**{category}**")
            for description, query in EXAMPLE_QUERIES[category].items():
                if st.button(description, key=f"btn_{query}", use_container_width=True):
                    st.session_state.query_input = query
                    st.rerun()

        st.markdown("---")

        st.header("📖 Quick Reference")
        st.markdown(
            """
        **Operators:**
        - `from(user)` - messages from user
        - `contains(dict)` - messages with words
        - `has_feature(name)` - custom features
        - `labeled_as(name)` - alias for has_feature
        - `from(*)` - wildcard (all messages)
        - `AND`, `OR`, `NOT` - boolean logic
        - `FOLLOWED_BY` - sequential order
        - `INWIN N` - within N messages
        - `$var` - pattern variables
        - `{N}` - quantifiers

        **Examples:**
        ```prismql
        SELECT from(alice)
        SELECT has_feature(sentiment_positive)
        SELECT from(alice) AND contains(problems)
        SELECT labeled_as(intent_complaint) FOLLOWED_BY from(support_sarah) WITHIN 3
        ```
        """
        )

        # Show data stats
        st.markdown("---")
        st.header("📊 Dataset Info")
        total_docs = engine.search_backend.get_total_documents()
        st.metric("Total Messages", total_docs)

        # Show available dictionaries
        st.markdown("**Available Dictionaries:**")
        for dict_name in engine.user_dictionaries.keys():
            st.code(dict_name, language=None)

        # Show available custom features
        st.markdown("**Custom Features (LLM):**")
        custom_features = list(engine.precomputed_indexes.custom_features.keys())
        if custom_features:
            # Show in compact columns
            features_by_category = {}
            for f in sorted(custom_features):
                category = f.split("_")[0]
                if category not in features_by_category:
                    features_by_category[category] = []
                features_by_category[category].append(f)

            for category, features in features_by_category.items():
                with st.expander(f"📌 {category.title()}", expanded=False):
                    for feature in features:
                        st.code(feature, language=None)

    # Custom CSS for monospace input
    st.markdown(
        """
        <style>
        textarea[aria-label="Enter your PrismQL query:"] {
            font-family: 'Courier New', Courier, monospace !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize default query if not set
    if "query_input" not in st.session_state:
        st.session_state.query_input = "SELECT from(alice)"

    # Main query interface
    query = st.text_area(
        "Enter your PrismQL query:",
        height=100,
        key="query_input",
        help="Type a PrismQL query or select an example from the sidebar",
    )

    # Buttons in columns for horizontal layout
    col1, col2 = st.columns([1, 1])
    with col1:
        run_button = st.button("▶️ Run Query", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)

    if clear_button:
        st.session_state.query_input = ""
        st.rerun()

    # Execute query
    if run_button and query:
        with st.spinner("Executing query..."):
            try:
                result = engine.execute(query)

                # Display results
                st.success("✅ Query executed successfully!")

                # Show the query with syntax highlighting
                with st.expander("📝 Query", expanded=False):
                    display_query_with_highlighting(query)

                # Show result count
                if isinstance(result, list):
                    st.info(f"Found **{len(result)}** result(s)")

                    # Display results
                    if len(result) > 0:
                        st.markdown("### Results")

                        # Show results (limit to 20 for performance)
                        display_limit = 20
                        if len(result) > display_limit:
                            st.warning(
                                f"Showing first {display_limit} of {len(result)} results. Use LIMIT in query for more control."
                            )

                        for i, group in enumerate(result[:display_limit], 1):
                            st.markdown(f"**Result {i}** - {len(group)} message(s)")
                            st.markdown(format_result_group(group, engine))
                            st.markdown("---")
                    else:
                        st.info("No results found")
                else:
                    # Handle aggregation results
                    st.json(result)

            except PrismQLSyntaxError as e:
                st.error(f"❌ **Syntax Error:** {e}")
                if hasattr(e, "line") and hasattr(e, "column"):
                    st.code(f"Line {e.line}, Column {e.column}")

            except PrismQLRuntimeError as e:
                st.error(f"❌ **Runtime Error:** {e}")

            except Exception as e:
                st.error(f"❌ **Unexpected Error:** {e}")
                st.exception(e)

    # Footer with links
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center'>
        <p>
            <strong>PrismQL</strong> - Pattern Recognition in Sequential Messages Query Language<br>
            <a href="https://github.com/prismql/prismql" target="_blank">GitHub</a> •
            <a href="https://prismql.readthedocs.io" target="_blank">Documentation</a>
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
