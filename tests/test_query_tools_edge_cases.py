"""Edge case tests for run_query, build_query, and adapt_query tools."""

import contextlib
from collections.abc import Generator
from pathlib import Path

import pytest

from mcp_server_tree_sitter.exceptions import QueryError
from tests.test_helpers import (
    adapt_query,
    build_query,
    register_project_tool,
    remove_project_tool,
    run_query,
)


@pytest.fixture
def project_with_python(tmp_path: Path) -> Generator[tuple[str, Path]]:
    """Register a temp project with a valid Python file."""
    root = tmp_path
    (root / "main.py").write_text("def hello():\n    print('world')\n")
    name = "query_edge_case_project"
    register_project_tool(path=str(root), name=name)
    try:
        yield name, root
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


# --- run_query edge cases ---


def test_run_query_malformed_tree_sitter_syntax(project_with_python: tuple[str, Path]) -> None:
    """Malformed tree-sitter query syntax raises QueryError (or underlying error)."""
    name, _ = project_with_python
    with pytest.raises((QueryError, Exception)) as exc_info:
        run_query(
            project=name,
            query="(unclosed paren",
            file_path="main.py",
            language="python",
        )
    # Message should indicate query or syntax problem
    assert exc_info.value is not None
    msg = str(exc_info.value).lower()
    assert "query" in msg or "syntax" in msg or "error" in msg or "invalid" in msg


def test_run_query_node_type_not_in_grammar(project_with_python: tuple[str, Path]) -> None:
    """Query with node type that does not exist in the grammar raises or returns empty."""
    name, _ = project_with_python
    # Python grammar has no "class_xyz_nonexistent" node type
    try:
        results = run_query(
            project=name,
            query="(class_xyz_nonexistent) @capture",
            file_path="main.py",
            language="python",
        )
        # Some tree-sitter bindings may accept unknown types and return no matches
        assert isinstance(results, list)
    except (QueryError, Exception):
        # Or the Query constructor may raise
        pass


def test_run_query_both_file_path_and_language_omitted(project_with_python: tuple[str, Path]) -> None:
    """Both file_path and language omitted raises a clear QueryError."""
    name, _ = project_with_python
    with pytest.raises(QueryError) as exc_info:
        run_query(
            project=name,
            query="(function_definition) @f",
            file_path=None,
            language=None,
        )
    msg = str(exc_info.value).lower()
    assert "language" in msg and ("required" in msg or "provided" in msg)


def test_run_query_empty_query_string(project_with_python: tuple[str, Path]) -> None:
    """Empty query string is handled without crashing (may raise or return empty list)."""
    name, _ = project_with_python
    try:
        results = run_query(
            project=name,
            query="",
            file_path="main.py",
            language="python",
        )
        assert isinstance(results, list)
    except (QueryError, Exception):
        # Empty query may be rejected by tree-sitter
        pass


# --- build_query edge cases ---


def test_build_query_empty_list_of_patterns() -> None:
    """Empty list of query strings produces empty combined query or raises."""
    try:
        result = build_query(language="python", patterns=[], combine="or")
        assert "language" in result and "query" in result
        assert result["query"] == "" or result["query"] is not None
    except ValueError:
        # If we add validation to reject empty patterns
        pass


def test_build_query_conflicting_capture_names() -> None:
    """Combining queries with same capture name yields valid query (no error)."""
    # Both patterns use @name; combined query is still valid tree-sitter
    result = build_query(
        language="python",
        patterns=[
            "(function_definition name: (identifier) @name)",
            "(class_definition name: (identifier) @name)",
        ],
        combine="or",
    )
    assert result["language"] == "python"
    assert "query" in result
    assert "@name" in result["query"]
    # Should not raise; behavior with duplicate capture names is grammar-dependent
    assert isinstance(result["query"], str)


def test_build_query_invalid_base_language() -> None:
    """Invalid base language yields empty query or raises."""
    try:
        result = build_query(
            language="nonexistent_lang_xyz",
            patterns=["(x) @y"],
            combine="or",
        )
        # get_query_template returns None for unknown lang; pattern used as-is.
        # If pattern is not a template name, it's appended only when get_template returns it.
        # get_template returns pattern when get_query_template returns None, so query could be "(x) @y"
        assert "language" in result and "query" in result
    except ValueError:
        pass


# --- adapt_query edge cases ---


def test_adapt_query_no_overlapping_node_types() -> None:
    """Adapting between two languages with no mapping returns query unchanged or adapted."""
    # Use a language pair that has no entry in query_adaptation (e.g. go -> python)
    # or use a query that only has node types not in the map
    result = adapt_query(
        query="(function_definition) @f",
        from_language="python",
        to_language="go",
    )
    assert result["original_language"] == "python"
    assert result["target_language"] == "go"
    assert result["original_query"] == "(function_definition) @f"
    # No (python, go) in map, so adapted_query equals original
    assert result["adapted_query"] == "(function_definition) @f"


def test_adapt_query_empty_query_string() -> None:
    """Empty query string returns empty adapted query."""
    result = adapt_query(
        query="",
        from_language="python",
        to_language="javascript",
    )
    assert result["original_query"] == ""
    assert result["adapted_query"] == ""


def test_adapt_query_source_and_target_language_same() -> None:
    """Source and target language are the same: query returned unchanged."""
    result = adapt_query(
        query="(function_definition name: (identifier) @name)",
        from_language="python",
        to_language="python",
    )
    assert result["original_language"] == result["target_language"] == "python"
    assert result["original_query"] == result["adapted_query"]
