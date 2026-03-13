"""Example of using pytest with diagnostic plugin for testing."""

import contextlib
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from mcp_server_tree_sitter.api import get_project_registry
from mcp_server_tree_sitter.testing import DiagnosticData
from tests.test_helpers import get_ast, register_project_tool

# Load the diagnostic fixture
pytest.importorskip("mcp_server_tree_sitter.testing")


@pytest.fixture
def test_project(tmp_path: Path) -> Generator[dict[str, Any], None, None]:
    """Create a temporary test project with a sample file."""
    project_path = tmp_path

    # Create a test file
    test_file = project_path / "test.py"
    test_file.write_text("def hello():\n    print('Hello, world!')\n\nhello()\n")

    # Register project
    project_name = "diagnostic_test_project"
    register_project_tool(path=str(project_path), name=project_name)

    try:
        # Yield the project info
        yield {"name": project_name, "path": project_path, "file": "test.py"}
    finally:
        # Clean up
        project_registry = get_project_registry()
        with contextlib.suppress(Exception):
            project_registry.remove_project(project_name)


def test_get_ast_zero_or_negative_depth(test_project: dict[str, Any]) -> None:
    """Test that an AST tree is returned with zero or negative depth."""
    with pytest.raises(ValueError):
        get_ast(
            project=test_project["name"],
            path=test_project["file"],
            max_depth=0,
            include_text=True,
        )

    with pytest.raises(ValueError):
        get_ast(
            project=test_project["name"],
            path=test_project["file"],
            max_depth=-1,
            include_text=True,
        )


@pytest.mark.diagnostic
def test_ast_failure(test_project: dict[str, Any], diagnostic: DiagnosticData) -> None:
    """Test the get_ast functionality."""
    # Add test details to diagnostic data
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Try to get the AST
        ast_result = get_ast(
            project=test_project["name"],
            path=test_project["file"],
            max_depth=3,
            include_text=True,
        )

        # Add the result to diagnostics
        diagnostic.add_detail("ast_result", str(ast_result))

        # This assertion would fail if there's an issue with AST parsing
        assert "tree" in ast_result, "AST result should contain a tree"

        # Check that the tree doesn't contain an error
        if isinstance(ast_result["tree"], dict) and "error" in ast_result["tree"]:
            raise AssertionError(f"AST tree contains an error: {ast_result['tree']['error']}")

    except Exception as e:
        # Record the error in diagnostics
        diagnostic.add_error("AstParsingError", str(e))

        # Create the artifact
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
        }
        diagnostic.add_artifact("ast_failure", artifact)

        # Re-raise to fail the test
        raise
