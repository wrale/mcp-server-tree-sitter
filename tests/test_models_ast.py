"""Tests for ast.py module."""

import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List

import pytest

from mcp_server_tree_sitter.language.registry import LanguageRegistry
from mcp_server_tree_sitter.models.ast import (
    extract_node_path,
    find_node_at_position,
    node_to_dict,
    summarize_node,
)


@pytest.fixture
def test_files() -> Generator[Dict[str, Path], None, None]:
    """Create temporary test files in various languages."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)

        # Python file
        python_file = dir_path / "test.py"
        with open(python_file, "w") as f:
            f.write("""
def hello(name):
    return f"Hello, {name}!"

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return hello(self.name)

if __name__ == "__main__":
    person = Person("Alice", 30)
    print(person.greet())
""")

        # JavaScript file
        js_file = dir_path / "test.js"
        with open(js_file, "w") as f:
            f.write("""
function hello(name) {
    return `Hello, ${name}!`;
}

class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }

    greet() {
        return hello(this.name);
    }
}

const person = new Person("Alice", 30);
console.log(person.greet());
""")

        yield {
            "python": python_file,
            "javascript": js_file,
            "dir": dir_path,
        }


@pytest.fixture
def parsed_trees(test_files) -> Dict[str, Any]:
    """Parse the test files and return trees and source code."""
    result = {}

    # Initialize language registry
    registry = LanguageRegistry()

    # Parse Python file
    py_parser = registry.get_parser("python")
    with open(test_files["python"], "rb") as f:
        py_source = f.read()
    py_tree = py_parser.parse(py_source)
    result["python"] = {
        "tree": py_tree,
        "source": py_source,
        "language": "python",
    }

    # Parse JavaScript file
    js_parser = registry.get_parser("javascript")
    with open(test_files["javascript"], "rb") as f:
        js_source = f.read()
    js_tree = js_parser.parse(js_source)
    result["javascript"] = {
        "tree": js_tree,
        "source": js_source,
        "language": "javascript",
    }

    return result


# Test node_to_dict function
def test_node_to_dict_basic(parsed_trees):
    """Test basic functionality of node_to_dict."""
    # Get Python tree and source
    py_tree = parsed_trees["python"]["tree"]
    py_source = parsed_trees["python"]["source"]

    # Convert root node to dict
    root_dict = node_to_dict(py_tree.root_node, py_source, max_depth=2)

    # Verify basic structure
    assert root_dict["type"] == "module"
    assert "children" in root_dict
    assert "start_point" in root_dict
    assert "end_point" in root_dict
    assert "start_byte" in root_dict
    assert "end_byte" in root_dict
    assert "named" in root_dict

    # Verify children are included but limited by max_depth
    assert len(root_dict["children"]) > 0
    for child in root_dict["children"]:
        # Max depth is 2, so children of children should have truncated=True if they have children
        if "children" in child:
            for grandchild in child["children"]:
                if "children" in grandchild:
                    assert "truncated" in grandchild or len(grandchild["children"]) == 0


def test_node_to_dict_with_text(parsed_trees):
    """Test node_to_dict with include_text=True."""
    # Get Python tree only - source not needed for extract_node_path
    py_tree = parsed_trees["python"]["tree"]

    # Convert root node to dict with text
    py_source = parsed_trees["python"]["source"]
    root_dict = node_to_dict(py_tree.root_node, py_source, include_text=True, max_depth=2)

    # Verify text is included
    assert "text" in root_dict
    assert len(root_dict["text"]) > 0

    # Verify text is in children too
    for child in root_dict["children"]:
        if "text" in child:
            assert len(child["text"]) > 0


def test_node_to_dict_without_text(parsed_trees):
    """Test node_to_dict with include_text=False."""
    # Get Python tree and source
    py_tree = parsed_trees["python"]["tree"]
    py_source = parsed_trees["python"]["source"]

    # Convert root node to dict without text
    root_dict = node_to_dict(py_tree.root_node, py_source, include_text=False, max_depth=2)

    # Verify text is not included
    assert "text" not in root_dict

    # Verify text is not in children either
    for child in root_dict["children"]:
        assert "text" not in child


def test_node_to_dict_without_children(parsed_trees):
    """Test node_to_dict with include_children=False."""
    # Get Python tree and source
    py_tree = parsed_trees["python"]["tree"]
    py_source = parsed_trees["python"]["source"]

    # Convert root node to dict without children
    root_dict = node_to_dict(py_tree.root_node, py_source, include_children=False)

    # Verify children are not included
    assert "children" not in root_dict


def test_node_to_dict_different_languages(parsed_trees):
    """Test node_to_dict with different languages."""
    # Test with Python
    py_tree = parsed_trees["python"]["tree"]
    py_source = parsed_trees["python"]["source"]
    py_dict = node_to_dict(py_tree.root_node, py_source, max_depth=3)
    assert py_dict["type"] == "module"

    # Test with JavaScript
    js_tree = parsed_trees["javascript"]["tree"]
    js_source = parsed_trees["javascript"]["source"]
    js_dict = node_to_dict(js_tree.root_node, js_source, max_depth=3)
    assert js_dict["type"] == "program"


def test_node_to_dict_with_large_depth(parsed_trees):
    """Test node_to_dict with a large max_depth to ensure it handles deep trees."""
    # Get Python tree and source
    py_tree = parsed_trees["python"]["tree"]
    py_source = parsed_trees["python"]["source"]

    # Convert with large max_depth
    root_dict = node_to_dict(py_tree.root_node, py_source, max_depth=10)

    # Verify we can get deep into the tree (e.g., to function body)
    def find_deep_node(node_dict: Dict[str, Any], node_types: List[str]) -> bool:
        """Recursively search for a node of a specific type."""
        if node_dict["type"] in node_types:
            return True

        if "children" in node_dict:
            for child in node_dict["children"]:
                if find_deep_node(child, node_types):
                    return True

        return False

    # Should be able to find a function body block and string content deep in the tree
    assert find_deep_node(root_dict, ["block", "string_content"])


# Test summarize_node function
def test_summarize_node(parsed_trees):
    """Test the summarize_node function."""
    # Get Python tree and source
    py_tree = parsed_trees["python"]["tree"]
    py_source = parsed_trees["python"]["source"]

    # Summarize root node
    summary = summarize_node(py_tree.root_node, py_source)

    # Verify summary structure
    assert "type" in summary
    assert "start_point" in summary
    assert "end_point" in summary
    assert "preview" in summary

    # Verify preview is a string and reasonable length
    assert isinstance(summary["preview"], str)
    assert len(summary["preview"]) <= 53  # 50 + "..."


def test_summarize_node_without_source(parsed_trees):
    """Test summarize_node without source (should not include preview)."""
    # Get Python tree
    py_tree = parsed_trees["python"]["tree"]

    # Summarize root node without source
    summary = summarize_node(py_tree.root_node)

    # Verify summary structure
    assert "type" in summary
    assert "start_point" in summary
    assert "end_point" in summary
    assert "preview" not in summary


# Test find_node_at_position function
def test_find_node_at_position(parsed_trees):
    """Test the find_node_at_position function."""
    # Get Python tree
    py_tree = parsed_trees["python"]["tree"]

    # Find node at the beginning of a function definition (def hello)
    node = find_node_at_position(py_tree.root_node, 1, 0)  # row 1, column 0

    # Verify node type (accepting different tree-sitter version names)
    assert node is not None
    assert node.type in ["function_definition", "def"]

    # Find node at position of function name
    node = find_node_at_position(py_tree.root_node, 1, 5)  # row 1, column 5 (hello)

    # Verify node type (accepting different tree-sitter version names)
    assert node is not None
    assert node.type in ["identifier", "name"]


def test_find_node_at_position_out_of_bounds(parsed_trees):
    """Test find_node_at_position with out-of-bounds coordinates."""
    # Get Python tree
    py_tree = parsed_trees["python"]["tree"]

    # Negative coordinates
    node = find_node_at_position(py_tree.root_node, -1, -1)
    assert node is None

    # Beyond end of file
    max_row = py_tree.root_node.end_point[0] + 100
    node = find_node_at_position(py_tree.root_node, max_row, 0)
    assert node is None


# Test extract_node_path function
def test_extract_node_path(parsed_trees):
    """Test the extract_node_path function."""
    # Get Python tree only - source not needed for extract_node_path
    py_tree = parsed_trees["python"]["tree"]

    # Find a function name node
    function_node = find_node_at_position(py_tree.root_node, 1, 5)  # 'hello' function name
    assert function_node is not None

    # Extract path from root to function name
    path = extract_node_path(py_tree.root_node, function_node)

    # Verify path structure
    assert len(path) > 0
    assert path[0][0] == "module"  # Root node type
    assert path[-1][0] in ["identifier", "name"]  # Target node type


def test_extract_node_path_same_node(parsed_trees):
    """Test extract_node_path when root and target are the same node."""
    # Get Python tree
    py_tree = parsed_trees["python"]["tree"]

    # Path from root to root should be empty
    path = extract_node_path(py_tree.root_node, py_tree.root_node)
    assert len(path) == 0


def test_extract_node_path_intermediate_node(parsed_trees):
    """Test extract_node_path with an intermediate node."""
    # Get Python tree
    py_tree = parsed_trees["python"]["tree"]

    # Find class definition node
    class_node = None
    for child in py_tree.root_node.children:
        if child.type == "class_definition" or child.type == "class":
            class_node = child
            break

    assert class_node is not None

    # Get a method node within the class
    method_node = None
    class_body = None

    # Find the class body
    for child in class_node.children:
        if child.type == "block":
            class_body = child
            break

    if class_body:
        # Find a method in the class body
        for child in class_body.children:
            if child.type == "function_definition" or child.type == "method_definition":
                method_node = child
                break

    assert method_node is not None

    # Extract path from class to method
    path = extract_node_path(class_node, method_node)

    # Verify path structure
    assert len(path) > 0
    assert path[0][0] in ["class_definition", "class"]  # Root node
    assert path[-1][0] in ["function_definition", "method_definition"]  # Target node
