"""
PrismQL Interactive Demo - Streamlit Web App

A web-based demonstration of PrismQL query language for conversational data.
"""

import sys
from pathlib import Path

import streamlit as st
from prismql.backends.memory import MemoryBackend
from prismql.engine import PrismQLEngine
from prismql.exceptions import PrismQLRuntimeError, PrismQLSyntaxError

# Handle imports when running directly vs as module
try:
    from demo.generate_demo_data import (
        generate_demo_conversations,
        get_demo_dictionaries,
    )
except ModuleNotFoundError:
    # Add demo directory to path when running directly
    demo_dir = Path(__file__).parent
    if str(demo_dir) not in sys.path:
        sys.path.insert(0, str(demo_dir))
    from generate_demo_data import generate_demo_conversations, get_demo_dictionaries

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
    return PrismQLEngine(search_backend=backend, user_dictionaries=dictionaries)


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
    "Sequential Patterns": {
        "Customer then support response": "SELECT from(alice) FOLLOWED_BY from(support_sarah) WITHIN 3",
        "Problem then solution": "SELECT contains(problems) FOLLOWED_BY contains(solutions) WITHIN 5",
        "Greeting then question": "SELECT contains(greetings) FOLLOWED_BY contains(questions) WITHIN 2",
        "Customer NOT followed by support": "SELECT from(alice) NOT_FOLLOWED_BY from(support_sarah) WITHIN 10",
    },
    "Window Patterns (Unordered)": {
        "Customer and support together": "SELECT from(alice), from(support_sarah) INWIN 3",
        "Problem and solution nearby": "SELECT contains(problems), contains(solutions) INWIN 5",
        "Greeting and thanks together": "SELECT contains(greetings), contains(thanks) INWIN 10",
    },
    "Pattern Variables": {
        "Same user posting twice": "SELECT from($user), from($user) INWIN 3",
        "User then support then user": "SELECT from($customer) FOLLOWED_BY from(support_sarah) WITHIN 5 FOLLOWED_BY from($customer) WITHIN 5",
        "Same user three times": "SELECT from($user) FOLLOWED_BY from($user) WITHIN 2 FOLLOWED_BY from($user) WITHIN 2",
    },
    "Quantifiers": {
        "Alice posting 3 times": "SELECT from(alice){3} INWIN 10",
        "Customer posting twice then support": "SELECT from(alice){2} FOLLOWED_BY from(support_sarah) WITHIN 5",
        "User posting 3+ times": "SELECT from($user){3} INWIN 5",
    },
    "Advanced": {
        "Escalation pattern": "SELECT contains(problems) FOLLOWED_BY contains(urgent) WITHIN 3 FOLLOWED_BY from(manager_john) WITHIN 5",
        "Question-answer-thanks": "SELECT contains(questions) FOLLOWED_BY from(support_sarah) WITHIN 3 FOLLOWED_BY contains(thanks) WITHIN 3",
        "Multiple customers same issue": "SELECT from(alice), from(bob), from(charlie) INWIN 5",
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
            st.markdown(f"**{category}**")
            for description, query in EXAMPLE_QUERIES[category].items():
                if st.button(description, key=f"btn_{query}", use_container_width=True):
                    st.session_state.query = query

        st.markdown("---")

        st.header("📖 Quick Reference")
        st.markdown(
            """
        **Operators:**
        - `from(user)` - messages from user
        - `contains(dict)` - messages with words
        - `from(*)` - wildcard (all messages)
        - `AND`, `OR`, `NOT` - boolean logic
        - `FOLLOWED_BY` - sequential order
        - `INWIN N` - within N messages
        - `$var` - pattern variables
        - `{N}` - quantifiers

        **Examples:**
        ```prismql
        SELECT from(alice)
        SELECT from(alice) AND contains(problems)
        SELECT from(*) FOLLOWED_BY from(bob) WITHIN 3
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

    # Main query interface
    query = st.text_area(
        "Enter your PrismQL query:",
        value=st.session_state.get("query", "SELECT from(alice)"),
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
        st.session_state.query = ""
        st.rerun()

    # Update session state
    if query != st.session_state.get("query", ""):
        st.session_state.query = query

    # Execute query
    if run_button and query:
        with st.spinner("Executing query..."):
            try:
                result = engine.execute(query)

                # Display results
                st.success("✅ Query executed successfully!")

                # Show result count
                if isinstance(result, list):
                    st.info(f"Found **{len(result)}** result(s)")

                    # Display results
                    if len(result) > 0:
                        st.markdown("### Results")

                        # Show in tabs for better organization
                        if len(result) <= 10:
                            # Show all results
                            for i, group in enumerate(result, 1):
                                with st.expander(
                                    f"Result {i} - {len(group)} message(s)",
                                    expanded=(i == 1),
                                ):
                                    st.markdown(format_result_group(group, engine))
                        else:
                            # Show first 10 with pagination
                            st.warning(
                                f"Showing first 10 of {len(result)} results. Use LIMIT in query for more control."
                            )
                            for i, group in enumerate(result[:10], 1):
                                with st.expander(
                                    f"Result {i} - {len(group)} message(s)",
                                    expanded=(i == 1),
                                ):
                                    st.markdown(format_result_group(group, engine))
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
