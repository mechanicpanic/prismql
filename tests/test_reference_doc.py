"""The language reference must ship inside the package."""

from prismql.reference import load_reference


def test_reference_loads_from_package():
    text = load_reference()
    assert "PrismQL Language Reference" in text
    assert "FOLLOWED_BY" in text
    assert len(text) > 5000
