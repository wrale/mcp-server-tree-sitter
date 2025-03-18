"""Pytest-based diagnostic tests for cursor-based AST functionality."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Tuple

import pytest

from mcp_server_tree_sitter.api import get_language_registry, get_project_registry
from mcp_server_tree_sitter.models.ast import node_to_dict
from mcp_server_tree_sitter.models.ast_cursor import node_to_dict_cursor
from tests.test_helpers import register_project_tool


def parse_file(file_path: Path, language: str) -> Tuple[Any, bytes]:
    """Replacement for the relocated parse_file function."""
    language_registry = get_language_registry()

    # Get language object
    # We don't need to store language_obj directly as it's used by ast_parse_file
    _ = language_registry.get_language(language)

    # Use the tools.ast_operations.parse_file function
    from mcp_server_tree_sitter.api import get_tree_cache
    from mcp_server_tree_sitter.tools.ast_operations import parse_file as ast_parse_file

    return ast_parse_file(file_path, language, language_registry, get_tree_cache())


@pytest.fixture
def test_project() -> Generator[Dict[str, Any], None, None]:
    """Create a temporary test project with a sample file."""
    # Set up a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create a test file
        test_file = project_path / "test.py"
        with open(test_file, "w") as f:
            f.write("def hello():\n    print('Hello, world!')\n\nhello()\n")

        # Register project
        project_registry = get_project_registry()
        project_name = "cursor_test_project"
        register_project_tool(path=str(project_path), name=project_name)

        # Yield the project info
        yield {"name": project_name, "path": project_path, "file": "test.py"}

        # Clean up
        try:
            project_registry.remove_project(project_name)
        except Exception:
            pass


@pytest.mark.diagnostic
def test_cursor_ast_implementation(test_project, diagnostic) -> None:
    """Test the cursor-based AST implementation."""
    # Add test details to diagnostic data
    diagnostic.add_detail("project", test_project["name"])
    diagnostic.add_detail("file", test_project["file"])

    try:
        # Get language
        registry = get_language_registry()
        language = registry.language_for_file(test_project["file"])
        assert language is not None, "Could not detect language for file"
        _language_obj = registry.get_language(language)

        # Parse file
        file_path = test_project["path"] / test_project["file"]
        tree, source_bytes = parse_file(file_path, language)

        # Get AST using cursor-based approach
        cursor_ast = node_to_dict_cursor(tree.root_node, source_bytes, max_depth=3)

        # Add results to diagnostic data
        diagnostic.add_detail("cursor_ast_keys", list(cursor_ast.keys()))
        diagnostic.add_detail("cursor_ast_type", cursor_ast["type"])
        diagnostic.add_detail("cursor_ast_children_count", cursor_ast.get("children_count", 0))

        # Basic validation
        assert "id" in cursor_ast, "AST should include node ID"
        assert cursor_ast["type"] == "module", "Root node should be a module"
        assert "children" in cursor_ast, "AST should include children"
        assert len(cursor_ast["children"]) > 0, "AST should have at least one child"

        # Check function definition
        if cursor_ast["children"]:
            function_node = cursor_ast["children"][0]
            diagnostic.add_detail("function_node_keys", list(function_node.keys()))
            diagnostic.add_detail("function_node_type", function_node["type"])
            diagnostic.add_detail("function_node_children_count", function_node.get("children_count", 0))

            assert function_node["type"] == "function_definition", "Expected function definition"

            # Check if children are properly included
            assert "children" in function_node, "Function should have children"
            assert function_node["children_count"] > 0, "Function should have children"

            # Verify text extraction works if available
            if "text" in function_node:
                # Check for 'hello' in the text, handling both string and bytes
                if isinstance(function_node["text"], bytes):
                    assert b"hello" in function_node["text"], "Function text should contain 'hello'"
                else:
                    assert "hello" in function_node["text"], "Function text should contain 'hello'"

        # Success!
        diagnostic.add_detail("cursor_ast_success", True)

    except Exception as e:
        # Record the error in diagnostics
        diagnostic.add_error("CursorAstError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
            "file": test_project["file"],
        }
        diagnostic.add_artifact("cursor_ast_failure", artifact)

        # Re-raise to fail the test
        raise


@pytest.mark.diagnostic
def test_large_ast_handling(test_project, diagnostic) -> None:
    """Test handling of a slightly larger AST to ensure cursor-based approach works."""
    # Add test details to diagnostic data
    diagnostic.add_detail("project", test_project["name"])

    try:
        # Create a larger Python file with more structures
        large_file_path = test_project["path"] / "large.py"
        with open(large_file_path, "w") as f:
            f.write(
                """
# Test file with multiple classes and functions
import os
import sys
from typing import List, Dict, Optional

class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, my name is {self.name} and I'm {self.age} years old."

    def celebrate_birthday(self) -> None:
        self.age += 1
        print(f"Happy Birthday! {self.name} is now {self.age}!")

class Employee(Person):
    def __init__(self, name: str, age: int, employee_id: str):
        super().__init__(name, age)
        self.employee_id = employee_id

    def greet(self) -> str:
        return f"{super().greet()} I work here and my ID is {self.employee_id}."

def process_people(people: List[Person]) -> Dict[str, int]:
    result = {}
    for person in people:
        result[person.name] = person.age
    return result

if __name__ == "__main__":
    p1 = Person("Alice", 30)
    p2 = Person("Bob", 25)
    e1 = Employee("Charlie", 35, "E12345")

    print(p1.greet())
    print(p2.greet())
    print(e1.greet())

    results = process_people([p1, p2, e1])
    print(f"Results: {results}")
"""
            )

        # Get language
        registry = get_language_registry()
        language = registry.language_for_file("large.py")
        assert language is not None, "Could not detect language for large.py"
        _language_obj = registry.get_language(language)

        # Parse file
        tree, source_bytes = parse_file(large_file_path, language)

        # Get AST using cursor-based approach
        cursor_ast = node_to_dict(tree.root_node, source_bytes, max_depth=5)

        # Add results to diagnostic data
        diagnostic.add_detail("large_ast_type", cursor_ast["type"])
        diagnostic.add_detail("large_ast_children_count", cursor_ast.get("children_count", 0))

        # Find class and function counts
        class_nodes = []
        function_nodes = []

        def count_nodes(node_dict) -> None:
            if node_dict["type"] == "class_definition":
                class_nodes.append(node_dict["id"])
            elif node_dict["type"] == "function_definition":
                function_nodes.append(node_dict["id"])

            if "children" in node_dict:
                for child in node_dict["children"]:
                    count_nodes(child)

        count_nodes(cursor_ast)

        # Report counts
        diagnostic.add_detail("class_count", len(class_nodes))
        diagnostic.add_detail("function_count", len(function_nodes))

        # Basic validation
        assert len(class_nodes) >= 2, "Should find at least 2 classes"
        assert len(function_nodes) >= 5, "Should find at least 5 functions/methods"

        # Success!
        diagnostic.add_detail("large_ast_success", True)

    except Exception as e:
        # Record the error in diagnostics
        diagnostic.add_error("LargeAstError", str(e))

        # Create an artifact with detailed information
        artifact = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "project": test_project["name"],
        }
        diagnostic.add_artifact("large_ast_failure", artifact)

        # Re-raise to fail the test
        raise
