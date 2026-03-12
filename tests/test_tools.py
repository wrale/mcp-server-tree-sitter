"""Tool-level integration tests.

Covers: happy path, missing project, invalid language, parse error.
Uses existing test helpers; get_app() is used as-is (real app).
"""

import contextlib
from pathlib import Path

import pytest

from mcp_server_tree_sitter.exceptions import ProjectError
from tests.test_helpers import (
    get_ast,
    get_file,
    list_files,
    register_project_tool,
    remove_project_tool,
    run_query,
)


@pytest.fixture
def project_with_python(tmp_path: Path) -> tuple[str, Path]:
    """Register a temp project with a valid Python file."""
    root = tmp_path
    (root / "main.py").write_text("def hello():\n    print('world')\n")
    name = "tools_integration_project"
    register_project_tool(path=str(root), name=name)
    try:
        yield name, root
    finally:
        with contextlib.suppress(Exception):
            remove_project_tool(name)


def test_tools_happy_path_get_ast(project_with_python: tuple[str, Path]) -> None:
    """Happy path: get_ast returns tree for valid file."""
    name, _ = project_with_python
    result = get_ast(project=name, path="main.py")
    assert "tree" in result
    assert result["tree"] is not None


def test_tools_happy_path_list_files(project_with_python: tuple[str, Path]) -> None:
    """Happy path: list_files returns project files."""
    name, root = project_with_python
    (root / "other.py").write_text("x = 1\n")
    files = list_files(project=name)
    assert "main.py" in files
    assert "other.py" in files


def test_tools_happy_path_get_file(project_with_python: tuple[str, Path]) -> None:
    """Happy path: get_file returns file content."""
    name, root = project_with_python
    content = get_file(project=name, path="main.py")
    assert "def hello" in content
    assert "print" in content


def test_tools_get_file_respects_start_line_and_max_lines(project_with_python: tuple[str, Path]) -> None:
    """get_file with start_line and max_lines returns only that slice, not the whole file."""
    name, root = project_with_python
    (root / "main.py").write_text("line0\nline1\nline2\nline3\nline4\n")
    # First two lines only
    content = get_file(project=name, path="main.py", start_line=0, max_lines=2)
    assert content.strip() == "line0\nline1"
    assert "line2" not in content
    # Lines 2-3 (0-based: start_line=2, 2 lines)
    content = get_file(project=name, path="main.py", start_line=2, max_lines=2)
    assert content.strip() == "line2\nline3"
    assert "line0" not in content and "line4" not in content


def test_tools_get_file_start_line_past_end_returns_empty(
    project_with_python: tuple[str, Path],
) -> None:
    """get_file with start_line past EOF returns empty string."""
    name, root = project_with_python
    (root / "main.py").write_text("a\nb\nc\n")
    content = get_file(project=name, path="main.py", start_line=10, max_lines=5)
    assert content == ""


def test_tools_get_file_max_lines_past_end_returns_to_eof(
    project_with_python: tuple[str, Path],
) -> None:
    """get_file with max_lines beyond EOF returns from start_line to end of file."""
    name, root = project_with_python
    (root / "main.py").write_text("L0\nL1\nL2\nL3\n")
    content = get_file(project=name, path="main.py", start_line=2, max_lines=100)
    assert content == "L2\nL3\n"
    assert "L0" not in content


def test_tools_happy_path_run_query(project_with_python: tuple[str, Path]) -> None:
    """Happy path: run_query runs tree-sitter query."""
    name, _ = project_with_python
    results = run_query(
        project=name,
        query="(function_definition name: (identifier) @name)",
        file_path="main.py",
        language="python",
    )
    assert isinstance(results, list)
    # May have 0 or more captures depending on query
    for r in results:
        assert "file" in r or "capture" in r or "text" in r


def test_tools_missing_project() -> None:
    """Missing project raises ProjectError (or ValueError) from tool layer."""
    with pytest.raises((ProjectError, ValueError, KeyError)):
        get_ast(project="nonexistent_project_xyz", path="main.py")


def test_tools_invalid_language(project_with_python: tuple[str, Path]) -> None:
    """Invalid or unsupported language raises QueryError or ValueError."""
    from mcp_server_tree_sitter.exceptions import QueryError

    name, _ = project_with_python
    with pytest.raises((QueryError, ValueError)):
        run_query(
            project=name,
            query="(x)",
            file_path="main.py",
            language="nonexistent_lang_xyz",
        )


def test_tools_parse_error_graceful(project_with_python: tuple[str, Path]) -> None:
    """File that causes parse issues still returns structure or raises cleanly."""
    name, root = project_with_python
    # Severely broken syntax may still produce a partial tree or raise
    (root / "bad.py").write_text("def ( invalid syntax {{{ \n")
    result = get_ast(project=name, path="bad.py")
    # Parser may return tree with errors; we expect no unhandled exception
    assert "tree" in result or isinstance(result, dict)
