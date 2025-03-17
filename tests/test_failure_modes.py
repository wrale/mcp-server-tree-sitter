"""Test cases for tree-sitter API robustness.

This module contains tests that verify proper error handling and robustness
in the tree-sitter integration:
1. The code properly handles error conditions
2. Appropriate error messages or exceptions are raised when expected
3. Edge cases are managed correctly

These tests help ensure robust behavior in various scenarios.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator

import pytest

# Import test helpers with DI-compatible functions
from tests.test_helpers import (
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


class TestQueryExecution:
    """Test query execution functionality."""

    def test_run_query_with_valid_query(self, mock_project) -> None:
        """Test that run_query executes and returns expected results."""
        # Simple query that should match functions
        query = "(function_definition name: (identifier) @function.name) @function.def"

        # Execute the query
        result = run_query(
            project=mock_project["name"],
            query=query,
            file_path="test.py",
            language="python",
        )

        # Verify that the query executes without errors and returns expected results
        assert result is not None, "Query should execute without exceptions"
        assert isinstance(result, list), "Query should return a list"

        # Should find the function "hello"
        found_hello = False
        for item in result:
            if item.get("capture") == "function.name" and item.get("text") == "hello":
                found_hello = True
                break

        assert found_hello, "Query should find the 'hello' function"

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

        # Verify result contains expected keys
        assert "original_language" in result
        assert "target_language" in result
        assert "original_query" in result
        assert "adapted_query" in result

        # Check that adaptation converted the function_definition to function_declaration
        assert "function_declaration" in result["adapted_query"]


class TestSymbolExtraction:
    """Test symbol extraction functionality."""

    def test_get_symbols_function_detection(self, mock_project) -> None:
        """Test that get_symbols properly extracts functions."""
        # Execute get_symbols on a file with known content
        result = get_symbols(project=mock_project["name"], file_path="test.py")

        # Verify the result structure contains the expected keys
        assert "functions" in result
        assert isinstance(result["functions"], list)

        # It should find the 'hello' function
        assert len(result["functions"]) > 0, "Should extract at least one function"
        function_names = [f.get("name", "") for f in result["functions"]]

        # Check for hello function - handling both bytes and strings
        hello_found = False
        for name in function_names:
            if (isinstance(name, bytes) and b"hello" in name) or (isinstance(name, str) and "hello" in name):
                hello_found = True
                break
        assert hello_found, "Should find the 'hello' function"

        assert "classes" in result
        assert isinstance(result["classes"], list)

        assert "imports" in result
        assert isinstance(result["imports"], list)

        # Should find the 'os' import
        assert len(result["imports"]) > 0, "Should extract at least one import"
        import_texts = [i.get("name", "") for i in result["imports"]]
        assert any("os" in text for text in import_texts), "Should find the 'os' import"


class TestDependencyAnalysis:
    """Test dependency analysis functionality."""

    def test_get_dependencies_import_detection(self, mock_project) -> None:
        """Test that get_dependencies properly detects imports."""
        # Execute get_dependencies on a file with known imports
        result = get_dependencies(project=mock_project["name"], file_path="test.py")

        # Verify the result structure and content
        assert isinstance(result, dict)

        # It should find the 'os' module
        found_os = False
        for _key, values in result.items():
            if any("os" in str(value) for value in values):
                found_os = True
                break

        assert found_os, "Should detect the 'os' import"


class TestCodeSearch:
    """Test code search operations."""

    def test_find_similar_code_with_exact_match(self, mock_project) -> None:
        """Test that find_similar_code finds exact matches."""
        # Execute find_similar_code with a snippet that exists in the file
        result = find_similar_code(
            project=mock_project["name"],
            snippet="print('Hello, world!')",
            language="python",
        )

        # Verify the function finds the match
        assert result is not None, "find_similar_code should execute without exceptions"
        assert isinstance(result, list), "find_similar_code should return a list"
        assert len(result) > 0, "Should find at least one match for an exact snippet"

    def test_find_usage_for_function(self, mock_project) -> None:
        """Test that find_usage finds function references."""
        # Execute find_usage with a symbol that exists in the file
        result = find_usage(project=mock_project["name"], symbol="hello", language="python")

        # Verify the function finds the usage
        assert result is not None, "find_usage should execute without exceptions"
        assert isinstance(result, list), "find_usage should return a list"
        assert len(result) > 0, "Should find at least one reference to 'hello'"


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
def test_error_handling_with_invalid_project(command_name, function, args) -> None:
    """Test that commands properly handle invalid project names."""
    # Use an invalid project name
    if "project" in args:
        args["project"] = "nonexistent_project"

    # The function should raise an exception for invalid project
    from mcp_server_tree_sitter.exceptions import ProjectError

    with pytest.raises(ProjectError):
        function(**args)


class TestASTHandling:
    """Test AST handling capabilities."""

    def test_ast_node_traversal(self, mock_project) -> None:
        """Test AST node traversal functionality."""
        # Get an AST for a file
        ast_result = get_ast(project=mock_project["name"], path="test.py", max_depth=5, include_text=True)

        # Verify complete AST structure
        assert "tree" in ast_result
        assert "file" in ast_result
        assert "language" in ast_result
        assert ast_result["language"] == "python"

        # Verify the tree structure
        tree = ast_result["tree"]
        assert "type" in tree
        assert "children" in tree
        assert tree["type"] == "module", "Root node should be a module"

        # Find the function definition
        function_nodes = []

        def find_functions(node) -> None:
            if isinstance(node, dict) and node.get("type") == "function_definition":
                function_nodes.append(node)
            if isinstance(node, dict) and "children" in node:
                for child in node["children"]:
                    find_functions(child)

        find_functions(tree)

        # Verify function details
        assert len(function_nodes) > 0, "Should find at least one function node"

        # Get the hello function
        hello_func = None
        for func in function_nodes:
            # Find the identifier node with name 'hello'
            if "children" in func:
                for child in func["children"]:
                    if child.get("type") == "identifier":
                        text = child.get("text", "")
                        if (isinstance(text, bytes) and b"hello" in text) or (
                            isinstance(text, str) and "hello" in text
                        ):
                            hello_func = func
                            break
                if hello_func:
                    break

        assert hello_func is not None, "Should find the 'hello' function node"
