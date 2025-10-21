"""
Download real conversation data from HuggingFace for testing PrismQL.

This script downloads a sample of the LMSYS-Chat-1M dataset, which contains
real conversations with LLMs collected from the Chatbot Arena.
"""

import re

import pandas as pd
from datasets import load_dataset

print("Downloading conversation dataset from HuggingFace...")
print("(This may take a few minutes for the first download)")

# Try DialogSum dataset - publicly available conversation dataset
# Contains ~13k dialogues with summaries
try:
    dataset = load_dataset(
        "knkarthick/dialogsum",
        split="train[:5000]",  # First 5k conversations
    )
except Exception as e:
    print(f"DialogSum failed: {e}")
    print("\nTrying alternative dataset...")
    # Fallback to DailyDialog
    dataset = load_dataset(
        "daily_dialog",
        split="train[:5000]",
    )

print(f"\nLoaded {len(dataset)} conversations")

# Convert to DataFrame
df = dataset.to_pandas()

print(f"\nDataset shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print("\nFirst conversation:")
print(df.head(1).to_dict("records")[0])

# The DialogSum dataset has 'id', 'dialogue', 'summary', 'topic' fields
# The 'dialogue' is formatted as "#Person1#: ... #Person2#: ..."
# Let's flatten this to individual messages for PrismQL

messages = []
for _idx, row in df.iterrows():
    conversation_id = row["id"]
    dialogue = row["dialogue"]
    topic = row.get("topic", "unknown")
    summary = row.get("summary", "")

    # Split dialogue by speaker turns using regex
    # Format: "#Person1#: text #Person2#: text"
    turns = re.split(r"(#Person\d+#:)", dialogue)

    # Process turns (odd indices are speakers, even are content)
    current_speaker = None
    turn_idx = 0
    for part in turns:
        if "#Person" in part:
            # Extract just "person1", "person2" without # symbols
            current_speaker = (
                part.strip().replace(":", "").lower().replace("#", "")
            )  # "person1", "person2"
        elif part.strip() and current_speaker:
            messages.append(
                {
                    "id": f"{conversation_id}_{turn_idx}",
                    "conversation_id": conversation_id,
                    "turn": turn_idx,
                    "user": current_speaker,  # "person1", "person2"
                    "text": part.strip(),
                    "topic": topic,
                    "summary": summary,
                }
            )
            turn_idx += 1

messages_df = pd.DataFrame(messages)

print(f"\n\nFlattened to {len(messages_df)} individual messages")
print(f"Message columns: {list(messages_df.columns)}")
print("\nSample messages:")
print(messages_df.head(10))

# Save as Parquet for fast loading
parquet_path = "lmsys_sample_10k.parquet"
messages_df.to_parquet(parquet_path)
print(f"\n✓ Saved to {parquet_path}")

# Also save as CSV
csv_path = "lmsys_sample_10k.csv"
messages_df.to_csv(csv_path, index=False)
print(f"✓ Saved to {csv_path}")

print("\n" + "=" * 70)
print("Dataset Statistics:")
print("=" * 70)
print(f"Total conversations: {df['id'].nunique()}")
print(f"Total messages: {len(messages_df)}")
print("Messages by role:")
print(messages_df["user"].value_counts())
print("\nMessages by topic:")
print(messages_df["topic"].value_counts().head(10))

print("\n✓ Ready to use with PrismQL!")
print("\nNext step: Run test_real_data.py to query this dataset")
