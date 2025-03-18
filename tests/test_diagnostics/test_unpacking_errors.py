"""Pytest-based diagnostic tests for the unpacking errors in analysis functions."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

from mcp_server_tree_sitter.api import get_project_registry
from tests.test_helpers import analyze_complexity, get_dependencies, get_symbols, register_project_tool, run_query


@pytest.fixture
def test_project() -> Generator[Dict[str, Any], None, None]:
    """Create a temporary test project with a sample file."""
    # Set up a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a sample Python file
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write(
                """
# Test file for unpacking errors
import os
import sys

def hello(name):
    \"\"\"Say hello to someone.\"\"\"
    return f"Hello, {name}!"

class Person:
    def __init__(self, name):
        self.name = name

    def greet(self) -> None:
        return hello(self.name)

if __name__ == "__main__":
    person = Person("World")
    print(person.greet())
"""
            )

        # Register project
        project_name = "unpacking_test_project"
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
def test_get_symbols_error(test_project, diagnostic) -> None:
    """Test get_symbols and diagnose unpacking errors."""
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Try to extract symbols from test file
        symbols = get_symbols(project=test_project["name"], file_path=test_project["file"])

        # If successful, record the symbols
        diagnostic.add_detail("symbols", symbols)

        # Check the structure of the symbols dictionary
        assert isinstance(symbols, dict), "Symbols should be a dictionary"
        for category, items in symbols.items():
            assert isinstance(items, list), f"Symbol category {category} should contain a list"

    except Exception as e:
        # Record the error
        diagnostic.add_error("GetSymbolsError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
        }
        diagnostic.add_artifact("get_symbols_failure", artifact)

        # Re-raise to fail the test
        raise


@pytest.mark.diagnostic
def test_get_dependencies_error(test_project, diagnostic) -> None:
    """Test get_dependencies and diagnose unpacking errors."""
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Try to find dependencies in test file
        dependencies = get_dependencies(project=test_project["name"], file_path=test_project["file"])

        # If successful, record the dependencies
        diagnostic.add_detail("dependencies", dependencies)

        # Check the structure of the dependencies dictionary
        assert isinstance(dependencies, dict), "Dependencies should be a dictionary"

    except Exception as e:
        # Record the error
        diagnostic.add_error("GetDependenciesError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
        }
        diagnostic.add_artifact("get_dependencies_failure", artifact)

        # Re-raise to fail the test
        raise


@pytest.mark.diagnostic
def test_analyze_complexity_error(test_project, diagnostic) -> None:
    """Test analyze_complexity and diagnose unpacking errors."""
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Try to analyze code complexity
        complexity = analyze_complexity(project=test_project["name"], file_path=test_project["file"])

        # If successful, record the complexity metrics
        diagnostic.add_detail("complexity", complexity)

        # Check the structure of the complexity dictionary
        assert "line_count" in complexity, "Complexity should include line_count"
        assert "function_count" in complexity, "Complexity should include function_count"

    except Exception as e:
        # Record the error
        diagnostic.add_error("AnalyzeComplexityError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
        }
        diagnostic.add_artifact("analyze_complexity_failure", artifact)

        # Re-raise to fail the test
        raise


@pytest.mark.diagnostic
def test_run_query_error(test_project, diagnostic) -> None:
    """Test run_query and diagnose unpacking errors."""
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Try to run a simple query
        query_result = run_query(
            project=test_project["name"],
            query="(function_definition name: (identifier) @function.name)",
            file_path=test_project["file"],
            language="python",
        )

        # If successful, record the query results
        diagnostic.add_detail("query_result", query_result)

        # Check the structure of the query results
        assert isinstance(query_result, list), "Query result should be a list"
        if query_result:
            assert "capture" in query_result[0], "Query result items should have 'capture' field"

    except Exception as e:
        # Record the error
        diagnostic.add_error("RunQueryError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
            "query": "(function_definition name: (identifier) @function.name)",
        }
        diagnostic.add_artifact("run_query_failure", artifact)

        # Re-raise to fail the test
        raise
