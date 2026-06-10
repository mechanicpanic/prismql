"""Access to the packaged language reference document."""

from importlib.resources import files


def load_reference() -> str:
    """Return the full LANGUAGE_REFERENCE.md text shipped with the package."""
    return (
        files("prismql").joinpath("LANGUAGE_REFERENCE.md").read_text(encoding="utf-8")
    )
