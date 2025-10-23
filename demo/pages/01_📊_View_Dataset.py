"""
Dataset Viewer - View all messages in the demo dataset.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Handle imports when running directly vs as module
try:
    from demo.generate_demo_data import (
        generate_demo_conversations,
        get_demo_dictionaries,
    )
except ModuleNotFoundError:
    # Add demo directory to path when running directly
    demo_dir = Path(__file__).parent.parent
    if str(demo_dir) not in sys.path:
        sys.path.insert(0, str(demo_dir))
    from generate_demo_data import generate_demo_conversations, get_demo_dictionaries


st.set_page_config(
    page_title="Dataset Viewer - PrismQL Demo",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Demo Dataset")
st.markdown(
    """
View all messages in the synthetic customer support conversation dataset.
This dataset is used for all demo queries.
"""
)

# Load data
conversations = generate_demo_conversations()
dictionaries = get_demo_dictionaries()

# Statistics
st.header("Dataset Statistics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Messages", len(conversations))

with col2:
    unique_users = len({msg["user"] for msg in conversations})
    st.metric("Unique Users", unique_users)

with col3:
    customers = len(
        [
            msg
            for msg in conversations
            if not msg["user"].startswith(("support_", "manager_"))
        ]
    )
    st.metric("Customer Messages", customers)

with col4:
    staff = len(
        [
            msg
            for msg in conversations
            if msg["user"].startswith(("support_", "manager_"))
        ]
    )
    st.metric("Staff Messages", staff)

# User breakdown
st.header("User Breakdown")
user_counts = {}
for msg in conversations:
    user = msg["user"]
    user_counts[user] = user_counts.get(user, 0) + 1

user_df = pd.DataFrame(
    [
        {"User": user, "Message Count": count}
        for user, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    ]
)
st.dataframe(user_df, use_container_width=True, hide_index=True)

# Dictionaries
st.header("Available Dictionaries")
st.markdown("Word lists used for `contains()` queries:")

dict_cols = st.columns(3)
for idx, (dict_name, words) in enumerate(sorted(dictionaries.items())):
    with dict_cols[idx % 3]:
        st.markdown(f"**{dict_name}**")
        st.code(", ".join(words[:5]) + ("..." if len(words) > 5 else ""), language=None)

# View options
st.header("Messages")

# Filters
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    filter_user = st.selectbox(
        "Filter by user:",
        ["All"] + sorted(user_counts.keys()),
    )

with col2:
    search_text = st.text_input(
        "Search message text:",
        placeholder="Enter text to search...",
    )

with col3:
    st.markdown("###")
    view_mode = st.radio(
        "View:", ["Table", "List"], horizontal=True, label_visibility="visible"
    )

# Filter messages
filtered = conversations

if filter_user != "All":
    filtered = [msg for msg in filtered if msg["user"] == filter_user]

if search_text:
    search_lower = search_text.lower()
    filtered = [msg for msg in filtered if search_lower in msg["text"].lower()]

st.info(f"Showing {len(filtered)} of {len(conversations)} messages")

# Display
if view_mode == "Table":
    # Table view
    df = pd.DataFrame(filtered)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "user": st.column_config.TextColumn("User", width="medium"),
            "text": st.column_config.TextColumn("Message", width="large"),
        },
    )
else:
    # List view
    for msg in filtered:
        user_type = "👤"
        if msg["user"].startswith("support_"):
            user_type = "👨‍💼"
        elif msg["user"].startswith("manager_"):
            user_type = "👔"

        st.markdown(f"**{user_type} [{msg['id']}] {msg['user']}**")
        st.markdown(f"> {msg['text']}")
        st.markdown("---")

# Export option
st.header("Export Dataset")
st.markdown("Download the dataset as JSON or CSV:")

col1, col2 = st.columns(2)

with col1:
    # JSON export
    import json

    json_data = json.dumps(conversations, indent=2)
    st.download_button(
        label="📥 Download JSON",
        data=json_data,
        file_name="prismql_demo_dataset.json",
        mime="application/json",
        use_container_width=True,
    )

with col2:
    # CSV export
    csv_data = pd.DataFrame(conversations).to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name="prismql_demo_dataset.csv",
        mime="text/csv",
        use_container_width=True,
    )
