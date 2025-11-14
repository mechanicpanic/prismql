"""
Temporal Operators Example for PrismQL.

This example demonstrates the temporal filtering and grouping capabilities
of PrismQL, including:
- BEFORE/AFTER/BETWEEN temporal filtering
- Temporal grouping by HOUR/DAY/WEEK/MONTH/YEAR
- Combining temporal operations with aggregation
"""

from datetime import datetime, timedelta

from prismql import PrismQLEngine
from prismql.backends.memory import MemoryBackend

# Create sample chat data with timestamps spanning several days
base_time = datetime(2024, 1, 15, 10, 0, 0)

MESSAGES = [
    # Day 1 (Jan 15) - Morning conversation
    {
        "id": 1,
        "text": "Good morning team!",
        "user": "alice",
        "timestamp": base_time.isoformat(),
    },
    {
        "id": 2,
        "text": "Morning Alice! Ready for the sprint planning?",
        "user": "bob",
        "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
    },
    {
        "id": 3,
        "text": "Absolutely! Let's discuss the new features.",
        "user": "alice",
        "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
    },
    # Day 1 - Afternoon discussion
    {
        "id": 4,
        "text": "The database migration went smoothly",
        "user": "charlie",
        "timestamp": (base_time + timedelta(hours=4)).isoformat(),
    },
    {
        "id": 5,
        "text": "Great work Charlie!",
        "user": "alice",
        "timestamp": (base_time + timedelta(hours=4, minutes=2)).isoformat(),
    },
    # Day 2 (Jan 16) - Stand-up
    {
        "id": 6,
        "text": "Daily stand-up time",
        "user": "bob",
        "timestamp": (base_time + timedelta(days=1)).isoformat(),
    },
    {
        "id": 7,
        "text": "I finished the authentication module",
        "user": "alice",
        "timestamp": (base_time + timedelta(days=1, minutes=2)).isoformat(),
    },
    {
        "id": 8,
        "text": "Working on the API endpoints",
        "user": "charlie",
        "timestamp": (base_time + timedelta(days=1, minutes=4)).isoformat(),
    },
    # Day 2 - Afternoon
    {
        "id": 9,
        "text": "Code review: looks good to merge",
        "user": "bob",
        "timestamp": (base_time + timedelta(days=1, hours=5)).isoformat(),
    },
    # Day 3 (Jan 17) - Bug reports
    {
        "id": 10,
        "text": "Found a bug in the login flow",
        "user": "alice",
        "timestamp": (base_time + timedelta(days=2, hours=1)).isoformat(),
    },
    {
        "id": 11,
        "text": "I'll investigate that",
        "user": "charlie",
        "timestamp": (base_time + timedelta(days=2, hours=1, minutes=5)).isoformat(),
    },
    {
        "id": 12,
        "text": "Fixed! It was a validation issue",
        "user": "charlie",
        "timestamp": (base_time + timedelta(days=2, hours=2)).isoformat(),
    },
    # Week 2 (Jan 22) - Sprint retrospective
    {
        "id": 13,
        "text": "Time for sprint retrospective",
        "user": "bob",
        "timestamp": (base_time + timedelta(weeks=1)).isoformat(),
    },
    {
        "id": 14,
        "text": "We delivered all planned features!",
        "user": "alice",
        "timestamp": (base_time + timedelta(weeks=1, minutes=10)).isoformat(),
    },
    {
        "id": 15,
        "text": "Great teamwork everyone",
        "user": "charlie",
        "timestamp": (base_time + timedelta(weeks=1, minutes=15)).isoformat(),
    },
]


def main():
    """Run temporal operators examples."""
    # Create PrismQL engine with timestamp field configured
    backend = MemoryBackend(MESSAGES)
    engine = PrismQLEngine(search_backend=backend, timestamp_field="timestamp")

    print("=" * 70)
    print("PrismQL Temporal Operators Examples")
    print("=" * 70)

    # Example 1: BEFORE - Find messages before a specific time
    print("\n1. BEFORE: Messages before Jan 16, 2024")
    print("-" * 70)
    cutoff = base_time + timedelta(days=1)
    query = f'SELECT from(alice) OR from(bob) BEFORE("{cutoff.isoformat()}")'
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} message groups from before Jan 16")
    for group in results[:3]:  # Show first 3
        print(f"  Message IDs: {group}")

    # Example 2: AFTER - Find messages after a specific time
    print("\n2. AFTER: Messages after Jan 16, 2024")
    print("-" * 70)
    query = f'SELECT from(alice) AFTER("{cutoff.isoformat()}")'
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} message groups from after Jan 16")
    for group in results[:3]:
        print(f"  Message IDs: {group}")

    # Example 3: BETWEEN - Find messages in a time range
    print("\n3. BETWEEN: Messages between Jan 15-17, 2024")
    print("-" * 70)
    start = base_time
    end = base_time + timedelta(days=2)
    query = f'SELECT from(alice) OR from(bob) OR from(charlie) BETWEEN("{start.isoformat()}", "{end.isoformat()}")'
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} message groups in the time range")

    # Example 4: Date-only filtering
    print("\n4. Date-only BETWEEN: All messages on Jan 15")
    print("-" * 70)
    query = 'SELECT from(alice) OR from(bob) BETWEEN("2024-01-15", "2024-01-16")'
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} message groups on Jan 15")

    # Example 5: Temporal grouping by DAY
    print("\n5. GROUP BY DAY: Group messages by day")
    print("-" * 70)
    query = "SELECT from(alice) OR from(bob) OR from(charlie) GROUP BY DAY(timestamp)"
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Grouped into {len(results.groups)} day groups:")
    for day, groups in sorted(results.groups.items())[:5]:
        print(f"  {day}: {len(groups)} message groups")

    # Example 6: Temporal grouping with aggregation
    print("\n6. GROUP BY DAY + COUNT: Count messages per day")
    print("-" * 70)
    query = "SELECT from(alice) OR from(bob) OR from(charlie) GROUP BY DAY(timestamp) AGGREGATE count()"
    print(f"Query: {query}")
    results = engine.execute(query)
    print("Message counts by day:")
    for day, count in sorted(results.grouped_values.items()):
        print(f"  {day}: {count} messages")

    # Example 7: GROUP BY HOUR - Hourly activity
    print("\n7. GROUP BY HOUR: Hourly message distribution")
    print("-" * 70)
    query = 'SELECT from(alice) OR from(bob) BETWEEN("2024-01-15", "2024-01-16") GROUP BY HOUR(timestamp) AGGREGATE count()'
    print(f"Query: {query}")
    results = engine.execute(query)
    print("Messages per hour on Jan 15:")
    for hour, count in sorted(results.grouped_values.items()):
        print(f"  {hour}: {count} messages")

    # Example 8: GROUP BY WEEK - Weekly summary
    print("\n8. GROUP BY WEEK: Weekly message counts")
    print("-" * 70)
    query = "SELECT from(alice) OR from(bob) OR from(charlie) GROUP BY WEEK(timestamp) AGGREGATE count()"
    print(f"Query: {query}")
    results = engine.execute(query)
    print("Messages per week:")
    for week, count in sorted(results.grouped_values.items()):
        print(f"  Week {week}: {count} messages")

    # Example 9: Combining BEFORE with GROUP BY
    print("\n9. BEFORE + GROUP BY DAY: Daily counts before Jan 17")
    print("-" * 70)
    query = 'SELECT from(alice) OR from(bob) OR from(charlie) BEFORE("2024-01-17") GROUP BY DAY(timestamp) AGGREGATE count()'
    print(f"Query: {query}")
    results = engine.execute(query)
    print("Daily message counts before Jan 17:")
    for day, count in sorted(results.grouped_values.items()):
        print(f"  {day}: {count} messages")

    # Example 10: User activity by day
    print("\n10. User mentions per day")
    print("-" * 70)
    query = "SELECT from(alice) GROUP BY DAY(timestamp) AGGREGATE count()"
    print(f"Query: {query}")
    results = engine.execute(query)
    print("Alice's messages per day:")
    for day, count in sorted(results.grouped_values.items()):
        print(f"  {day}: {count} messages")

    # Example 11: Recent activity (last 2 days)
    print("\n11. Recent activity: Messages from last 2 days")
    print("-" * 70)
    recent_cutoff = base_time + timedelta(days=1)
    query = f'SELECT from(alice) OR from(bob) OR from(charlie) AFTER("{recent_cutoff.isoformat()}")'
    print(f"Query: {query}")
    results = engine.execute(query)
    print(f"Found {len(results)} recent message groups")

    # Example 12: Peak hours analysis
    print("\n12. BETWEEN + HOUR grouping: Morning activity (8 AM - 12 PM)")
    print("-" * 70)
    morning_start = base_time.replace(hour=8, minute=0)
    morning_end = base_time.replace(hour=12, minute=0)
    query = f'SELECT from(alice) OR from(bob) BETWEEN("{morning_start.isoformat()}", "{morning_end.isoformat()}") GROUP BY HOUR(timestamp) AGGREGATE count()'
    print(f"Query: {query}")
    results = engine.execute(query)
    print("Hourly message counts (morning):")
    for hour, count in sorted(results.grouped_values.items()):
        print(f"  {hour}: {count} messages")

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
