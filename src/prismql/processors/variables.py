"""Variable binding and validation for pattern matching."""

from collections.abc import Sequence
from typing import Any, Optional

from ..backends.base import SearchBackend
from ..types import MessageGroup, MessageId, QueryResult


class VariableConstraint:
    """
    Represents a variable constraint in a pattern.

    For example, in `from($user), ..., from($user)`:
    - Position 0 has variable "user" bound to field "user"
    - Position 2 has variable "user" bound to field "user"
    - These must have the same value
    """

    def __init__(self, variable_name: str, field_name: str, position: int) -> None:
        """
        Initialize variable constraint.

        Args:
            variable_name: Name of the variable (e.g., "user" from "$user")
            field_name: Field to extract value from (e.g., "user" for from())
            position: Position in the pattern sequence (0-indexed)
        """
        self.variable_name = variable_name
        self.field_name = field_name
        self.position = position

    def __repr__(self) -> str:
        return (
            f"VariableConstraint(${self.variable_name}={self.field_name}"
            f"@pos{self.position})"
        )


class VariableValidator:
    """
    Validates query results against variable constraints.

    After pattern matching produces candidate message groups, this validator
    ensures that variables are bound consistently across the pattern.
    """

    def __init__(
        self, search_backend: SearchBackend, constraints: Sequence[VariableConstraint]
    ) -> None:
        """
        Initialize variable validator.

        Args:
            search_backend: Backend to retrieve field values from documents
            constraints: List of variable constraints to enforce
        """
        self.search_backend = search_backend
        self.constraints = list(constraints)

        # Group constraints by variable name
        self.constraints_by_var: dict[str, list[VariableConstraint]] = {}
        for constraint in self.constraints:
            if constraint.variable_name not in self.constraints_by_var:
                self.constraints_by_var[constraint.variable_name] = []
            self.constraints_by_var[constraint.variable_name].append(constraint)

    def validate_results(self, results: QueryResult) -> QueryResult:
        """
        Filter query results to only include groups that satisfy all variable constraints.

        Args:
            results: Query results to validate

        Returns:
            Filtered results where all variable constraints are satisfied
        """
        if not self.constraints:
            # No constraints, return as-is
            return results

        validated_results: QueryResult = []

        for group in results:
            if self._validate_group(group):
                validated_results.append(group)

        return validated_results

    def _validate_group(self, group: MessageGroup) -> bool:
        """
        Check if a message group satisfies all variable constraints.

        Args:
            group: Message group to validate

        Returns:
            True if all variable constraints are satisfied
        """
        # Get documents for all messages in group
        try:
            documents = self.search_backend.get_documents(list(group))
        except NotImplementedError:
            # Backend doesn't support document retrieval
            # Cannot validate variables, accept all
            return True

        # Build lookup: message_id -> document
        doc_lookup: dict[MessageId, dict[str, Any]] = {}
        for doc in documents:
            msg_id = doc.get("id")
            if msg_id is not None:
                doc_lookup[msg_id] = doc

        # Check each variable
        for var_name, var_constraints in self.constraints_by_var.items():
            if not self._validate_variable(
                group, doc_lookup, var_name, var_constraints
            ):
                return False

        return True

    def _validate_variable(
        self,
        group: MessageGroup,
        doc_lookup: dict[MessageId, dict[str, Any]],
        var_name: str,
        constraints: list[VariableConstraint],
    ) -> bool:
        """
        Check if a specific variable is bound consistently across the group.

        Args:
            group: Message group
            doc_lookup: Lookup from message ID to document
            var_name: Variable name to check
            constraints: All constraints for this variable

        Returns:
            True if variable is bound consistently
        """
        # Extract values for this variable at each position
        values: list[Optional[Any]] = []

        for constraint in constraints:
            # Check position is valid
            if constraint.position >= len(group):
                return False

            msg_id = group[constraint.position]
            doc = doc_lookup.get(msg_id)

            if doc is None:
                # Message not found
                return False

            # Extract field value
            value = doc.get(constraint.field_name)
            values.append(value)

        # All values must be the same and not None
        if not values or any(v is None for v in values):
            return False

        first_value = values[0]
        return all(v == first_value for v in values)

    def get_variable_bindings(self, group: MessageGroup) -> Optional[dict[str, Any]]:
        """
        Get the variable bindings for a validated message group.

        Args:
            group: Message group (must be validated first)

        Returns:
            Dictionary mapping variable names to their bound values,
            or None if group cannot be validated
        """
        try:
            documents = self.search_backend.get_documents(list(group))
        except NotImplementedError:
            return None

        # Build lookup
        doc_lookup: dict[MessageId, dict[str, Any]] = {}
        for doc in documents:
            msg_id = doc.get("id")
            if msg_id is not None:
                doc_lookup[msg_id] = doc

        # Extract bindings
        bindings: dict[str, Any] = {}

        for var_name, var_constraints in self.constraints_by_var.items():
            # Take value from first constraint for this variable
            if not var_constraints:
                continue

            constraint = var_constraints[0]
            if constraint.position >= len(group):
                return None

            msg_id = group[constraint.position]
            msg_doc = doc_lookup.get(msg_id)

            if msg_doc is None:
                return None

            value = msg_doc.get(constraint.field_name)
            if value is None:
                return None

            bindings[var_name] = value

        return bindings
