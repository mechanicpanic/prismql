"""Window processing for PrismQL queries."""

from collections import defaultdict

from ..types import MessageGroup, QueryResult

# Try to import Rust backend for performance
try:
    from prismql_rust import merge_histogram_pruned, merge_p_s
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class WindowProcessor:
    """
    Handles window-based merging of query results.

    The window processing logic groups messages that appear within
    a specified distance (window_size) of each other.
    """

    @staticmethod
    def merge_restrictions(groups: list[MessageGroup], window_size: int) -> QueryResult:
        """
        Merge restriction results within sliding windows.

        This finds combinations of messages (one from each restriction group)
        that appear within window_size of each other.

        Uses Rust backend (merge_histogram_pruned) when available for 50-100x speedup.
        Falls back to Python implementation for string IDs or when Rust is unavailable.

        Args:
            groups: List of message groups from each restriction
            window_size: Maximum distance between messages in a result

        Returns:
            List of merged message groups
        """
        if not groups:
            return []

        # Single group case - each message becomes its own group
        if len(groups) == 1:
            return [[msg_id] for msg_id in groups[0]]

        # Try Rust backend for numeric IDs (massive performance boost!)
        if RUST_AVAILABLE and groups:
            # Check if all message IDs are integers
            all_messages = set()
            for group in groups:
                all_messages.update(group)

            if all_messages and all(isinstance(msg_id, int) for msg_id in all_messages):
                # Use Rust for 50-100x speedup!
                try:
                    return merge_histogram_pruned(groups, window_size)
                except Exception:
                    # Fall back to Python on any error
                    pass

        # Get all unique messages and sort them
        all_messages = set()
        for group in groups:
            all_messages.update(group)

        # Sort messages (works for both int and str IDs)
        sorted_messages = sorted(all_messages, key=lambda x: (isinstance(x, str), x))

        # Build index of which groups contain each message
        message_to_groups = defaultdict(set)
        for group_idx, group in enumerate(groups):
            for msg_id in group:
                message_to_groups[msg_id].add(group_idx)

        # Find valid combinations within windows
        results = []

        # For each message, try to find a valid combination starting with it
        for start_idx, start_msg in enumerate(sorted_messages):
            # Try to build combinations for any group that contains this message
            for start_group in message_to_groups[start_msg]:
                combination = [start_msg]
                groups_used = {start_group}

                # Look for messages from other groups within the window
                for msg_idx in range(len(sorted_messages)):
                    if msg_idx == start_idx:
                        continue

                    msg = sorted_messages[msg_idx]

                    # Check if within window (both directions)
                    # For numeric IDs, use distance; for others, use position
                    # in sorted list
                    if isinstance(start_msg, int) and isinstance(msg, int):
                        if abs(msg - start_msg) > window_size:
                            continue
                    else:
                        # For string IDs or mixed types, use position difference
                        if abs(msg_idx - start_idx) > window_size:
                            continue

                    # Check which groups this message belongs to
                    msg_groups = message_to_groups[msg]

                    # Find a group we haven't used yet
                    for group_idx in msg_groups:
                        if group_idx not in groups_used:
                            combination.append(msg)
                            groups_used.add(group_idx)
                            break

                    # If we've found messages from all groups, we have a valid result
                    if len(groups_used) == len(groups):
                        combination.sort()  # Sort for consistent ordering
                        if combination not in results:
                            results.append(list(combination))
                        break

        return results

    @staticmethod
    def merge_queries(groups: list[MessageGroup], window_size: int) -> QueryResult:
        """
        Merge results from multiple subqueries.

        This is similar to merge_restrictions but treats each input group
        as a potential result rather than requiring one message from each.

        Args:
            groups: List of message groups from subqueries
            window_size: Maximum distance for grouping

        Returns:
            List of merged message groups
        """
        if not groups:
            return []

        # Collect all messages with their source groups
        message_sources = defaultdict(list)
        for group_idx, group in enumerate(groups):
            for msg_id in group:
                message_sources[msg_id].append(group_idx)

        # Sort all unique messages
        sorted_messages = sorted(
            message_sources.keys(), key=lambda x: (isinstance(x, str), x)
        )

        # Group messages that are within window_size of each other
        results = []
        used_messages = set()

        for start_idx, start_msg in enumerate(sorted_messages):
            if start_msg in used_messages:
                continue

            # Find all messages within window
            window_group = [start_msg]
            used_messages.add(start_msg)

            for msg_idx, msg in enumerate(
                sorted_messages[start_idx + 1 :], start=start_idx + 1
            ):
                # Check distance based on type
                if isinstance(start_msg, int) and isinstance(msg, int):
                    if msg - start_msg > window_size:
                        break
                else:
                    # For string IDs or mixed types, use position difference
                    if msg_idx - start_idx > window_size:
                        break
                if msg not in used_messages:
                    window_group.append(msg)
                    used_messages.add(msg)

            # Only include groups with messages from multiple sources
            group_sources = set()
            for msg in window_group:
                group_sources.update(message_sources[msg])

            if len(group_sources) >= 2:
                results.append(list(window_group))

        return results
