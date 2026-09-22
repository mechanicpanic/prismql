"""Variable binding and validation for pattern matching."""


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
