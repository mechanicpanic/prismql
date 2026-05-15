"""Window processing for PrismQL queries."""

from collections import defaultdict

from ..types import MessageGroup, QueryResult

# Try to import Rust backend for performance
try:
    from prismql_rust import merge_histogram_pruned

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
                    return merge_histogram_pruned(groups, window_size)  # type: ignore[no-any-return]
                except Exception:  # noqa: S110
                    # Fall back to Python on any error (intentional)
                    pass

        # Python implementation using backtracking to find ALL valid combinations
        return WindowProcessor._merge_with_backtracking(groups, window_size)

    @staticmethod
    def _merge_with_backtracking(
        groups: list[MessageGroup], window_size: int
    ) -> QueryResult:
        """
        Merge groups using backtracking to find ALL valid combinations.

        This replaces the old greedy algorithm which missed combinations.
        Uses recursive backtracking to explore all possible message selections.
        """
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

        # Store results
        results = []
        seen_combinations = set()

        def check_distance(msg1, msg2, max_dist):
            """Check if two messages are within distance."""
            if isinstance(msg1, int) and isinstance(msg2, int):
                return abs(msg1 - msg2) <= max_dist
            # For strings, use position in sorted list
            idx1 = sorted_messages.index(msg1)
            idx2 = sorted_messages.index(msg2)
            return abs(idx1 - idx2) <= max_dist

        def is_within_window(combination):
            """Check if all messages in combination are within window."""
            if len(combination) <= 1:
                return True

            # Check all pairs are within window
            for i in range(len(combination)):
                for j in range(i + 1, len(combination)):
                    if not check_distance(combination[i], combination[j], window_size):
                        return False
            return True

        def backtrack(combination, groups_used, start_idx):
            """Recursively build all valid combinations."""
            # Base case: found message from all groups
            if len(groups_used) == len(groups):
                # Check if all messages are within window
                if is_within_window(combination):
                    # Sort for consistent ordering and dedupe
                    sorted_combo = sorted(combination)
                    combo_key = tuple(sorted_combo)
                    if combo_key not in seen_combinations:
                        seen_combinations.add(combo_key)
                        results.append(sorted_combo)
                return

            # Find next group we need to fill
            next_group = None
            for g in range(len(groups)):
                if g not in groups_used:
                    next_group = g
                    break

            if next_group is None:
                return

            # Try each message from next_group starting from start_idx
            for msg_idx in range(start_idx, len(sorted_messages)):
                msg = sorted_messages[msg_idx]

                # Skip if not in the group we need
                if next_group not in message_to_groups[msg]:
                    continue

                # Skip if already used
                if msg in combination:
                    continue

                # Check if within window of ALL existing messages (early pruning)
                within_window = True
                for existing_msg in combination:
                    if not check_distance(existing_msg, msg, window_size):
                        within_window = False
                        break

                if not within_window:
                    # If this message is too far from start, all later ones will be too
                    if (
                        combination
                        and isinstance(msg, int)
                        and isinstance(combination[0], int)
                    ):
                        if msg - min(combination) > window_size:
                            break
                    continue

                # Recursively try adding this message
                backtrack(
                    combination + [msg],
                    groups_used | {next_group},
                    msg_idx + 1,  # Only consider messages after this one
                )

        # Start backtracking from each message that belongs to group 0
        for msg_idx, start_msg in enumerate(sorted_messages):
            if 0 in message_to_groups[start_msg]:
                backtrack([start_msg], {0}, msg_idx + 1)

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
