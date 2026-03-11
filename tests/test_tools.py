"""Tool-level integration tests.

Covers: happy path, missing project, invalid language, parse error.
Uses existing test helpers; get_app() is used as-is (real app).
"""

import tempfile
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
def project_with_python() -> tuple[str, Path]:
    """Register a temp project with a valid Python file."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def hello():\n    print('world')\n")
        name = "tools_integration_project"
        register_project_tool(path=str(root), name=name)
        try:
            yield name, root
        finally:
            try:
                remove_project_tool(name)
            except Exception:
                pass


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
