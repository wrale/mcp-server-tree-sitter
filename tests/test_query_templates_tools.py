"""Functional tests for list_query_templates_tool and get_query_template_tool."""

import pytest

from tests.test_helpers import get_query_template_tool, list_query_templates_tool

# ---- list_query_templates_tool ----


def test_list_query_templates_tool_returns_non_empty_list() -> None:
    """list_query_templates_tool() with no language returns non-empty dict of languages."""
    result = list_query_templates_tool()
    assert isinstance(result, dict)
    assert len(result) > 0, "Should return at least one language with templates"


def test_list_query_templates_tool_correct_structure() -> None:
    """Returned dict has language ids as keys; each value is a dict of template name -> query string."""
    result = list_query_templates_tool()
    assert isinstance(result, dict)
    for lang_id, templates in result.items():
        assert isinstance(lang_id, str), "Keys should be language ids (str)"
        assert isinstance(templates, dict), "Values should be template name -> query dicts"
        for name, query in templates.items():
            assert isinstance(name, str), "Template names should be str"
            assert isinstance(query, str), "Template query should be str"


def test_list_query_templates_tool_with_known_language_returns_templates() -> None:
    """Filtering by a known language (e.g. python) returns single-key dict with non-empty templates."""
    result = list_query_templates_tool(language="python")
    assert isinstance(result, dict)
    assert "python" in result
    assert isinstance(result["python"], dict)
    assert len(result["python"]) > 0, "Python should have at least one query template"
    for name, query in result["python"].items():
        assert isinstance(name, str) and isinstance(query, str)
        assert len(query.strip()) > 0


def test_list_query_templates_tool_handles_unregistered_language() -> None:
    """Unregistered language returns dict with that key and empty templates (no exception)."""
    result = list_query_templates_tool(language="unregistered_lang_xyz_123")
    assert isinstance(result, dict)
    assert "unregistered_lang_xyz_123" in result
    assert result["unregistered_lang_xyz_123"] == {}


# ---- get_query_template_tool ----


def test_get_query_template_tool_valid_fetch() -> None:
    """Valid language and template name returns dict with language, name, and query."""
    result = get_query_template_tool("python", "functions")
    assert isinstance(result, dict)
    assert result["language"] == "python"
    assert result["name"] == "functions"
    assert "query" in result
    assert isinstance(result["query"], str)
    assert len(result["query"].strip()) > 0


def test_get_query_template_tool_invalid_language() -> None:
    """Invalid (unregistered) language raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_query_template_tool("invalid_language_xyz", "functions")
    assert "invalid_language_xyz" in str(exc_info.value)
    assert "functions" in str(exc_info.value) or "template" in str(exc_info.value).lower()


def test_get_query_template_tool_invalid_template_name() -> None:
    """Valid language but invalid template name raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_query_template_tool("python", "nonexistent_template_name")
    assert "python" in str(exc_info.value)
    assert "nonexistent_template_name" in str(exc_info.value)


def test_get_query_template_tool_template_content_correctness() -> None:
    """Returned query string has expected tree-sitter structure (node types, captures)."""
    result = get_query_template_tool("python", "functions")
    query = result["query"]
    assert "function_definition" in query
    assert "identifier" in query or "@" in query
    assert "(" in query and ")" in query
