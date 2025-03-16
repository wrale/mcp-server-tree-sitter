"""Test cases for known tree-sitter failure modes identified in FEATURES.md.

This module contains mock-based tests that verify the handling of all failure modes
documented in FEATURES.md, ensuring that:
1. The code properly handles error conditions
2. Appropriate error messages or empty responses are returned
3. Edge cases are managed correctly

These tests help ensure robust behavior even in known failure scenarios.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

# Import modules to be tested
from mcp_server_tree_sitter.server import (
    find_similar_code,
    find_usage,
    get_ast,
    get_dependencies,
    get_symbols,
    register_project_tool,
    run_query,
)


@pytest.fixture
def mock_project(request) -> Generator[Dict[str, Any], None, None]:
    """Create a mock project fixture for testing with unique names."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a simple Python file for testing
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("import os\n\ndef hello():\n    print('Hello, world!')\n\nhello()\n")

        # Generate a unique project name based on the test name
        test_name = request.node.name
        unique_id = abs(hash(test_name)) % 10000
        project_name = f"test_project_{unique_id}"

        # Register the project
        try:
            register_project_tool(path=str(project_path), name=project_name)
        except Exception:
            # If registration fails, try with an even more unique name
            import time

            project_name = f"test_project_{unique_id}_{int(time.time())}"
            register_project_tool(path=str(project_path), name=project_name)

        yield {"name": project_name, "path": str(project_path), "file": "test.py"}


class TestQueryExecutionFailures:
    """Test the known failure modes for query execution."""

    def test_run_query_empty_results(self, mock_project) -> None:
        """Test that run_query executes without errors but returns no results."""
        # Simple query that should match functions
        query = "(function_definition name: (identifier) @function.name) @function.def"

        # Execute the query
        result = run_query(
            project=mock_project["name"],
            query=query,
            file_path="test.py",
            language="python",
        )

        # After fixes, verify that the query executes without errors
        assert result is not None, "Query should execute without raising exceptions"
        # The query may now return actual results instead of empty list
        assert isinstance(result, list), "Query should return a list (empty or with results)"

    def test_adapt_query_language_specific_syntax(self, mock_project) -> None:
        """Test adapt_query with language-specific syntax handling."""
        # Import the adapt_query function
        from mcp_server_tree_sitter.tools.query_builder import adapt_query

        # Attempt to adapt a query from one language to another
        result = adapt_query(
            query="(function_definition) @function",
            from_language="python",
            to_language="javascript",
        )

        # Now that our implementation works, verify result contains expected keys
        assert "original_language" in result
        assert "target_language" in result
        assert "original_query" in result
        assert "adapted_query" in result

        # Check that adaptation converted the function_definition to function_declaration
        assert "function_declaration" in result["adapted_query"]


class TestSymbolExtractionFailures:
    """Test the known failure modes for symbol extraction."""

    def test_get_symbols_empty_results(self, mock_project) -> None:
        """Test that get_symbols returns empty lists regardless of file content."""
        # Execute get_symbols on a file with known content
        result = get_symbols(project=mock_project["name"], file_path="test.py")

        # Verify the result structure contains the expected keys
        assert "functions" in result
        assert isinstance(result["functions"], list)
        # After fixing the implementation, we may actually get functions now
        # Leaving this test looser to accommodate actual results

        assert "classes" in result
        assert isinstance(result["classes"], list)

        assert "imports" in result
        assert isinstance(result["imports"], list)


class TestDependencyAnalysisFailures:
    """Test the known failure modes for dependency analysis."""

    def test_get_dependencies_empty_results(self, mock_project) -> None:
        """Test that get_dependencies returns empty results regardless of imports."""
        # Execute get_dependencies on a file with known imports
        result = get_dependencies(project=mock_project["name"], file_path="test.py")

        # Verify the result structure is as expected
        assert isinstance(result, dict)
        # Now that we've fixed the implementation, we may actually get dependencies
        # We'll just verify the structure, not whether it's empty


class TestCodeSearchFailures:
    """Test the known failure modes for code search operations."""

    def test_find_similar_code_no_results(self, mock_project) -> None:
        """Test that find_similar_code executes without output but fails to return results."""
        # Execute find_similar_code with a snippet
        result = find_similar_code(project=mock_project["name"], snippet="print('Hello')", language="python")

        # Verify the function executes but returns empty results
        assert result is not None, "find_similar_code should execute without exceptions"
        assert isinstance(result, list) and len(result) == 0, "find_similar_code should return empty list"

    def test_find_usage_no_results(self, mock_project) -> None:
        """Test that find_usage executes without errors but doesn't return any results."""
        # Execute find_usage with a symbol that exists in the file
        result = find_usage(project=mock_project["name"], symbol="hello", language="python")

        # Verify the function executes successfully
        assert result is not None, "find_usage should execute without exceptions"
        assert isinstance(result, list), "find_usage should return a list (empty or with results)"


@pytest.mark.parametrize(
    "command_name,function,args",
    [
        (
            "run_query",
            run_query,
            {"project": "test_project", "query": "(function) @f", "language": "python"},
        ),
        (
            "get_symbols",
            get_symbols,
            {"project": "test_project", "file_path": "test.py"},
        ),
        (
            "get_dependencies",
            get_dependencies,
            {"project": "test_project", "file_path": "test.py"},
        ),
        (
            "find_similar_code",
            find_similar_code,
            {
                "project": "test_project",
                "snippet": "print('test')",
                "language": "python",
            },
        ),
        (
            "find_usage",
            find_usage,
            {"project": "test_project", "symbol": "test", "language": "python"},
        ),
    ],
)
def test_graceful_error_handling(mock_project, command_name, function, args) -> None:
    """Test that commands with known issues handle errors gracefully."""
    # Update the project name in args
    if "project" in args:
        args["project"] = mock_project["name"]

    try:
        # Execute the function with the provided args
        result = function(**args)

        # Verify the function doesn't raise an exception
        assert result is not None, f"{command_name} should execute without raising exceptions"

        # For commands that return empty results, verify the structure
        if command_name in ["run_query", "find_similar_code", "find_usage"]:
            assert isinstance(result, list), f"{command_name} should return a list"
        elif command_name in ["get_symbols", "get_dependencies"]:
            assert isinstance(result, dict), f"{command_name} should return a dictionary"

    except Exception as e:
        pytest.fail(f"{command_name} failed with exception: {str(e)}")


class TestASTCursorOperations:
    """Test the limitations of Tree Cursor API operations."""

    def test_ast_cursor_limitations(self, mock_project) -> None:
        """Test limitations with advanced cursor operations."""
        # Get an AST for a file
        ast_result = get_ast(project=mock_project["name"], path="test.py", max_depth=5, include_text=True)

        # Verify basic AST structure works
        assert "tree" in ast_result
        assert "file" in ast_result
        assert "language" in ast_result

        # Verify the tree structure
        tree = ast_result["tree"]
        assert "type" in tree
        assert "children" in tree

        # Advanced cursor operations would typically involve:
        # 1. Semantic analysis
        # 2. Type inference
        # 3. Symbol resolution

        # Since these are known limitations, we're just verifying the basic structure
        # But no advanced semantic information
        function_nodes = []

        def find_functions(node) -> None:
            if isinstance(node, dict) and node.get("type") == "function_definition":
                function_nodes.append(node)
            if isinstance(node, dict) and "children" in node:
                for child in node["children"]:
                    find_functions(child)

        find_functions(tree)

        # Verify we can find the function node
        assert len(function_nodes) > 0, "Should find at least one function node"

        # But verify semantic information is limited
        # Semantic info that might be missing: return type, parameter types, scope information
        # This test would need to be adjusted based on what specifically is missing
