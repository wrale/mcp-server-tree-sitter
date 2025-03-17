"""Example of using pytest with diagnostic plugin for testing."""

import tempfile
from pathlib import Path

import pytest

from mcp_server_tree_sitter.api import get_project_registry
from mcp_server_tree_sitter.language.registry import LanguageRegistry
from tests.test_helpers import get_ast, register_project_tool

# Load the diagnostic fixture
pytest.importorskip("mcp_server_tree_sitter.testing")


@pytest.fixture
def test_project():
    """Create a temporary test project with a sample file."""
    # Set up a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a test file
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")

        # Register project
        project_name = "diagnostic_test_project"
        register_project_tool(path=str(project_path), name=project_name)

        # Yield the project info
        yield {"name": project_name, "path": project_path, "file": "test.py"}

        # Clean up
        project_registry = get_project_registry()
        try:
            project_registry.remove_project(project_name)
        except Exception:
            pass


@pytest.mark.diagnostic
def test_ast_failure(test_project, diagnostic) -> None:
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


@pytest.mark.diagnostic
def test_language_detection(diagnostic) -> None:
    """Test language detection functionality."""
    registry = LanguageRegistry()

    # Test a few common file extensions
    test_files = {
        "test.py": "python",
        "test.js": "javascript",
        "test.ts": "typescript",
        "test.unknown": None,
    }

    results = {}
    failures = []

    for filename, expected in test_files.items():
        detected = registry.language_for_file(filename)
        match = detected == expected

        results[filename] = {"detected": detected, "expected": expected, "match": match}

        if not match:
            failures.append(filename)

    # Add all results to diagnostic data
    diagnostic.add_detail("detection_results", results)
    if failures:
        diagnostic.add_detail("failed_files", failures)

    # Check results with proper assertions
    for filename, expected in test_files.items():
        assert registry.language_for_file(filename) == expected, f"Language detection failed for {filename}"
