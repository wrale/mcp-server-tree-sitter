"""Functional tests for get_node_types tool."""

from tests.test_helpers import get_node_types


def test_get_node_types_valid_language_returns_types() -> None:
    """Valid language (e.g. python) returns non-empty dict of node type -> description."""
    result = get_node_types("python")
    assert isinstance(result, dict)
    assert len(result) > 0
    assert "function_definition" in result or "module" in result


def test_get_node_types_output_structure() -> None:
    """Returned dict has string keys (node type names) and string values (descriptions)."""
    result = get_node_types("python")
    assert isinstance(result, dict)
    for node_type, description in result.items():
        assert isinstance(node_type, str), "Node type keys should be str"
        assert isinstance(description, str), "Description values should be str"
        assert len(node_type) > 0
        assert len(description.strip()) > 0


def test_get_node_types_unsupported_language_returns_empty() -> None:
    """Unsupported or unknown language returns empty dict (no exception)."""
    result = get_node_types("unsupported_language_xyz")
    assert isinstance(result, dict)
    assert result == {}
