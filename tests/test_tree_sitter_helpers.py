"""Tests for tree_sitter_helpers.py module."""

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from mcp_server_tree_sitter.utils.tree_sitter_helpers import (
    create_edit,
    edit_tree,
    find_all_descendants,
    get_changed_ranges,
    get_node_text,
    get_node_with_text,
    is_node_inside,
    parse_file_incremental,
    parse_file_with_detection,
    parse_source,
    parse_source_incremental,
    walk_tree,
)


# Fixtures
@pytest.fixture
def test_files() -> Dict[str, Path]:
    """Create temporary test files for different languages."""
    python_file = Path(tempfile.mktemp(suffix=".py"))
    js_file = Path(tempfile.mktemp(suffix=".js"))

    # Write Python test file
    with open(python_file, "w") as f:
        f.write(
            """def hello(name):
    print(f"Hello, {name}!")

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hi, I'm {self.name} and I'm {self.age} years old."

if __name__ == "__main__":
    person = Person("Alice", 30)
    print(person.greet())
"""
        )

    # Write JavaScript test file
    with open(js_file, "w") as f:
        f.write(
            """
function hello(name) {
    return `Hello, ${name}!`;
}

class Person {
    constructor(name, age) {
        this.name = name;
        this.age = age;
    }

    greet() {
        return `Hi, I'm ${this.name} and I'm ${this.age} years old.`;
    }
}

const person = new Person("Alice", 30);
console.log(person.greet());
"""
        )

    return {"python": python_file, "javascript": js_file}


@pytest.fixture
def parsed_files(test_files) -> Dict[str, Dict[str, Any]]:
    """Create parsed source trees for different languages."""
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    registry = LanguageRegistry()
    result = {}

    # Parse Python file
    py_parser = registry.get_parser("python")
    with open(test_files["python"], "rb") as f:
        py_source = f.read()
    py_tree = py_parser.parse(py_source)
    result["python"] = {
        "tree": py_tree,
        "source": py_source,
        "language": "python",
        "parser": py_parser,
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
        "parser": js_parser,
    }

    return result


# Tests for file parsing functions
def test_parse_file_with_detection(test_files, tmp_path):
    """Test parsing a file."""
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    registry = LanguageRegistry()

    # Parse Python file
    tree, source = parse_file_with_detection(test_files["python"], "python", registry)
    assert tree is not None
    assert source is not None
    assert isinstance(source, bytes)
    assert len(source) > 0
    assert source.startswith(b"def hello")

    # Parse JavaScript file
    tree, source = parse_file_with_detection(test_files["javascript"], "javascript", registry)
    assert tree is not None
    assert source is not None
    assert isinstance(source, bytes)
    assert len(source) > 0
    assert b"function hello" in source


def test_parse_file_with_unknown_language(tmp_path):
    """Test handling of unknown language when parsing a file."""
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    registry = LanguageRegistry()

    # Create a file with unknown extension
    unknown_file = tmp_path / "test.unknown"
    with open(unknown_file, "w") as f:
        f.write("This is a test file with unknown language")

    # Try to parse with auto-detection (should fail gracefully)
    with pytest.raises(ValueError):
        parse_file_with_detection(unknown_file, None, registry)

    # Try to parse with explicit unknown language (should also fail)
    with pytest.raises(ValueError):
        parse_file_with_detection(unknown_file, "nonexistent_language", registry)


def test_parse_source(parsed_files):
    """Test parsing source code."""
    # Get Python parser and source
    py_parser = parsed_files["python"]["parser"]
    py_source = parsed_files["python"]["source"]

    # Parse source
    tree = parse_source(py_source, py_parser)
    assert tree is not None
    assert tree.root_node is not None
    assert tree.root_node.type == "module"

    # Get JavaScript parser and source
    js_parser = parsed_files["javascript"]["parser"]
    js_source = parsed_files["javascript"]["source"]

    # Parse source
    tree = parse_source(js_source, js_parser)
    assert tree is not None
    assert tree.root_node is not None
    assert tree.root_node.type == "program"


def test_parse_source_incremental(parsed_files):
    """Test incremental parsing of source code."""
    # Get Python parser, tree, and source
    py_parser = parsed_files["python"]["parser"]
    # Only source is needed for this test (tree is unused)
    py_source = parsed_files["python"]["source"]

    # Modify the source
    modified_source = py_source.replace(b"Hello", b"Greetings")

    # Parse with original tree
    original_tree = py_parser.parse(py_source)
    incremental_tree = parse_source_incremental(modified_source, original_tree, py_parser)

    # Verify the new tree reflects the changes
    assert incremental_tree is not None
    assert incremental_tree.root_node is not None
    node_text = get_node_text(incremental_tree.root_node, modified_source, decode=False)
    assert b"Greetings" in node_text


def test_edit_tree(parsed_files):
    """Test editing a syntax tree."""
    # Get Python tree and source
    py_tree = parsed_files["python"]["tree"]
    py_source = parsed_files["python"]["source"]

    # Find the position of "Hello" in the source
    hello_pos = py_source.find(b"Hello")
    assert hello_pos > 0

    # Create an edit to replace "Hello" with "Greetings"
    start_byte = hello_pos
    old_end_byte = hello_pos + len("Hello")
    new_end_byte = hello_pos + len("Greetings")
    edit = create_edit(
        start_byte,
        old_end_byte,
        new_end_byte,
        (0, hello_pos),
        (0, hello_pos + len("Hello")),
        (0, hello_pos + len("Greetings")),
    )

    # Apply the edit
    py_tree = edit_tree(py_tree, edit)

    # Modify the source to match the edit
    modified_source = py_source.replace(b"Hello", b"Greetings")

    # Verify the edited tree works with the modified source
    root_text = get_node_text(py_tree.root_node, modified_source, decode=False)
    assert b"Greetings" in root_text


def test_get_changed_ranges(parsed_files):
    """Test getting changed ranges between trees."""
    # Get Python parser, tree, and source
    py_parser = parsed_files["python"]["parser"]
    py_tree = parsed_files["python"]["tree"]
    py_source = parsed_files["python"]["source"]

    # Modify the source
    modified_source = py_source.replace(b"Hello", b"Greetings")

    # Parse the modified source
    modified_tree = py_parser.parse(modified_source)

    # Get the changed ranges
    ranges = get_changed_ranges(py_tree, modified_tree)

    # Verify we have changed ranges
    assert len(ranges) > 0
    assert isinstance(ranges[0], tuple)
    assert len(ranges[0]) == 2  # (start_byte, end_byte)


def test_get_node_text(parsed_files):
    """Test extracting text from a node."""
    # Get Python tree and source
    py_tree = parsed_files["python"]["tree"]
    py_source = parsed_files["python"]["source"]

    # Get text from root node
    root_text = get_node_text(py_tree.root_node, py_source, decode=False)
    assert isinstance(root_text, bytes)
    assert root_text == py_source

    # Get text from a specific node (e.g., first function definition)
    function_node = None
    cursor = walk_tree(py_tree.root_node)
    while cursor.goto_first_child():
        if cursor.node.type == "function_definition":
            function_node = cursor.node
            break

    assert function_node is not None
    function_text = get_node_text(function_node, py_source, decode=False)
    assert isinstance(function_text, bytes)
    assert b"def hello" in function_text


def test_get_node_with_text(parsed_files):
    """Test finding a node with specific text."""
    # Get Python tree and source
    py_tree = parsed_files["python"]["tree"]
    py_source = parsed_files["python"]["source"]

    # Find node containing "Hello"
    hello_node = get_node_with_text(py_tree.root_node, py_source, b"Hello")
    assert hello_node is not None
    node_text = get_node_text(hello_node, py_source, decode=False)
    assert b"Hello" in node_text


def test_walk_tree(parsed_files):
    """Test walking a tree with cursor."""
    # Get Python tree
    py_tree = parsed_files["python"]["tree"]

    # Walk the tree and collect node types
    node_types = []
    cursor = walk_tree(py_tree.root_node)
    node_types.append(cursor.node.type)

    # Go to first child (should be function_definition)
    assert cursor.goto_first_child()
    node_types.append(cursor.node.type)

    # Go to next sibling
    while cursor.goto_next_sibling():
        node_types.append(cursor.node.type)

    # Go back to parent
    assert cursor.goto_parent()
    assert cursor.node.type == "module"

    # Verify we found some nodes
    assert len(node_types) > 0
    assert "module" in node_types
    assert "function_definition" in node_types or "def" in node_types


def test_is_node_inside(parsed_files):
    """Test checking if a node is inside another."""
    # Get Python tree
    py_tree = parsed_files["python"]["tree"]

    # Get root node and first child
    root_node = py_tree.root_node
    assert root_node.child_count > 0
    child_node = root_node.children[0]

    # Verify child is inside root
    assert is_node_inside(child_node, root_node)
    assert not is_node_inside(root_node, child_node)
    assert is_node_inside(child_node, child_node)  # Node is inside itself

    # Test with specific positions
    # Root node contains all positions in the file
    assert is_node_inside((0, 0), root_node)
    # First line should be within first child
    assert is_node_inside((0, 5), child_node)
    # Invalid position outside file
    assert not is_node_inside((999, 0), root_node)


def test_find_all_descendants(parsed_files):
    """Test finding all descendants of a node."""
    # Get Python tree
    py_tree = parsed_files["python"]["tree"]

    # Get all descendants
    all_descendants = find_all_descendants(py_tree.root_node)
    assert len(all_descendants) > 0

    # Get descendants with depth limit
    limited_descendants = find_all_descendants(py_tree.root_node, max_depth=2)

    # Verify depth limiting works (there should be fewer descendants)
    assert len(limited_descendants) <= len(all_descendants)


# Test edge cases and error handling
def test_get_node_text_with_invalid_byte_range(parsed_files):
    """Test get_node_text with invalid byte range."""
    # Only source is needed for this test
    py_source = parsed_files["python"]["source"]

    # Create a node with an invalid byte range by modifying properties
    # This is a bit of a hack, but it's effective for testing error handling
    class MockNode:
        def __init__(self):
            self.start_byte = len(py_source) + 100  # Beyond source length
            self.end_byte = len(py_source) + 200
            self.type = "invalid"
            self.start_point = (999, 0)
            self.end_point = (999, 10)
            self.is_named = True

    # Create mock node and try to get text
    mock_node = MockNode()
    result = get_node_text(mock_node, py_source, decode=False)

    # Should return empty bytes for invalid range
    assert result == b""


def test_parse_file_incremental(test_files, tmp_path):
    """Test incremental parsing of a file."""
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    registry = LanguageRegistry()

    # Initial parse
    tree1, source1 = parse_file_with_detection(test_files["python"], "python", registry)

    # Create a modified version of the file
    modified_file = tmp_path / "modified.py"
    with open(test_files["python"], "rb") as f:
        content = f.read()
    modified_content = content.replace(b"Hello", b"Greetings")
    with open(modified_file, "wb") as f:
        f.write(modified_content)

    # Parse incrementally
    tree2, source2 = parse_file_incremental(modified_file, tree1, "python", registry)

    # Verify the new tree reflects the changes
    assert tree2 is not None
    assert source2 is not None
    assert b"Greetings" in source2
    assert b"Greetings" in get_node_text(tree2.root_node, source2, decode=False)


def test_parse_file_nonexistent():
    """Test handling of nonexistent file."""
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    registry = LanguageRegistry()

    # Try to parse a nonexistent file
    with pytest.raises(FileNotFoundError):
        parse_file_with_detection(Path("/nonexistent/file.py"), "python", registry)


def test_parse_file_without_language(test_files):
    """Test parsing a file without specifying language."""
    from mcp_server_tree_sitter.language.registry import LanguageRegistry

    registry = LanguageRegistry()

    # Parse Python file by auto-detecting language from extension
    tree, source = parse_file_with_detection(test_files["python"], None, registry)
    assert tree is not None
    assert source is not None
    assert isinstance(source, bytes)
    assert len(source) > 0
    assert tree.root_node.type == "module"  # Python tree
